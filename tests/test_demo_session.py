"""A6 orchestration: real frozen strategy, durable fake broker, no external sockets."""

import json
import socket
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import httpx
import pytest

from intraday_etoro_lab.brokers import transport
from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.simulator import SimulatorBroker
from intraday_etoro_lab.config import load_config
from intraday_etoro_lab.execution.engine import Executor
from intraday_etoro_lab.execution.models import OrderState
from intraday_etoro_lab.execution.session import DemoSessionRunner
from intraday_etoro_lab.execution.session_fixture import synthetic_session
from intraday_etoro_lab.persistence import StateStore
from intraday_etoro_lab.risk import RiskEngine
from intraday_etoro_lab.strategies.orb import ORBStrategy


@pytest.fixture(scope="module")
def scenario():
    return synthetic_session()


@pytest.fixture
def setup(tmp_path):
    store = StateStore(tmp_path / "a6.sqlite")
    runner = DemoSessionRunner(load_config("configs/strategy-1-v1.yaml"), store)
    yield store, runner
    store.close()


@pytest.fixture(autouse=True)
def no_external_escape(monkeypatch):
    attempts = []

    def forbidden(*args, **kwargs):
        attempts.append("socket")
        raise AssertionError("A6 may never access external sockets")

    original = transport.create_http_client

    def guarded_client(**kwargs):
        if type(kwargs.get("transport")) is not httpx.MockTransport:
            attempts.append("external_client")
            raise AssertionError("A6 attempted a non-mock HTTP transport")
        return original(**kwargs)

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(transport, "create_http_client", guarded_client)
    yield
    # Assertions swallowed by execution error handling still fail this suite.
    assert attempts == []


def events(store, kind):
    return [json.loads(e["details"]) for e in store.events() if e["kind"] == "A6_" + kind]


def test_signal_risk_persistence_execution_reconciliation_and_flat(setup, scenario, monkeypatch):
    store, runner = setup
    original = SimulatorBroker.submit
    calls = []

    def spy(self, intent):
        persisted = store.intent(intent.intent_id)
        assert persisted.state == OrderState.SUBMITTING
        assert persisted.planned_risk > 0 and persisted.estimated_cost > 0
        assert store.portfolio(intent.session_id).reserved_cash > 0
        assert any(e["kind"] == "INTENT_DURABLE" for e in store.events())
        calls.append(intent.intent_id)
        return original(self, intent)

    monkeypatch.setattr(SimulatorBroker, "submit", spy)
    result = runner.run(*scenario)
    assert result["status"] == "PASS" and result["flat"] and result["reconciled"]
    assert result["signals"] == 1 and result["intents"] == 2
    assert result["external_writes"] == result["external_reads"] == 0
    assert len(calls) == 1
    assert runner.broker.submit_calls == runner.broker.close_calls == 1
    assert {i.kind for i in store.intents()} == {"entry", "close"}
    assert all(i.state == OrderState.FILLED for i in store.intents())
    assert not store.positions() and store.session(result["session_id"]).entries_paused
    assert events(store, "RISK")[0]["decision"]["approved"]
    assert events(store, "SIGNAL")[0]["signal"]["strategy_version"] == "ORB_RVOL_v1.0"
    assert events(store, "RECONCILIATION")[-1] == {
        "session_id": result["session_id"],
        "clean": True,
        "flat": True,
    }


def test_no_signal_does_not_manufacture_orders(setup):
    store, runner = setup
    result = runner.run(*synthetic_session(no_signal=True))
    assert result["status"] == "PASS" and result["signals"] == 0
    assert not store.intents() and runner.broker.submit_calls == 0
    assert events(store, "NO_SIGNAL")


@pytest.mark.parametrize("failure", ["missing", "unverified", "stale", "identity", "at_signal"])
def test_eligibility_rejects_potential_signal(setup, scenario, failure):
    store, runner = setup
    bundle, day, inputs = scenario
    assert ORBStrategy(runner.config.strategy).process_session(bundle, day).signals
    evidence = inputs.eligibility["SIMA"]
    if failure == "unverified":
        evidence = replace(evidence, rules=replace(evidence.rules, eligibility_verified=False))
    elif failure == "stale":
        evidence = replace(evidence, expires_at=evidence.observed_at)
    elif failure == "at_signal":
        evidence = replace(evidence, expires_at=evidence.observed_at + timedelta(minutes=5))
    elif failure == "identity":
        evidence = replace(evidence, instrument=bundle.instruments[1])
    inputs = replace(inputs, eligibility={} if failure == "missing" else {"SIMA": evidence})
    result = runner.run(bundle, day, inputs)
    assert result["status"] == "PASS"
    assert not store.intents() and runner.broker.submit_calls == 0
    assert events(store, "ELIGIBILITY_REJECTED") or any(
        e["reason"] != "VERIFIED_SIMULATED" for e in events(store, "ELIGIBILITY")
    )


@pytest.mark.parametrize(
    "failure,reason",
    [
        ("spread", "SPREAD_LIMIT"),
        ("stale", "STALE_QUOTE"),
        ("expired", "SIGNAL_EXPIRED"),
        ("protection", "NATIVE_STOP_REQUIRED"),
        ("product", "PRODUCT_INELIGIBLE"),
        ("step", "INVALID_INSTRUMENT_RULES"),
        ("price", "PRICE_DEVIATION"),
    ],
)
def test_signal_risk_rejection_zero_execution(setup, scenario, failure, reason, monkeypatch):
    store, runner = setup
    bundle, day, inputs = scenario
    quote = inputs.quotes["SIMA"]
    evidence = inputs.eligibility["SIMA"]
    if failure == "spread":
        quote = replace(quote, bid=quote.ask - Decimal(5))
    elif failure == "stale":
        quote = replace(quote, observed_at=quote.observed_at - timedelta(seconds=5))
    elif failure == "expired":
        quote = replace(quote, decision_at=quote.decision_at + timedelta(seconds=20))
    elif failure == "price":
        quote = replace(quote, ask=quote.ask + Decimal(1), bid=quote.bid + Decimal(1))
    else:
        change = {
            "protection": {"native_stop_supported": False},
            "product": {"effective_product": "cfd"},
            "step": {"unit_step": Decimal(0)},
        }
        evidence = replace(evidence, rules=replace(evidence.rules, **change[failure]))
    inputs = replace(inputs, quotes={"SIMA": quote}, eligibility={"SIMA": evidence})
    calls = []
    monkeypatch.setattr(SimulatorBroker, "submit", lambda *args: calls.append("submit"))
    result = runner.run(bundle, day, inputs)
    assert result["status"] == "PASS" and result["signals"] == 1
    assert events(store, "RISK")[0]["decision"]["reason"] == reason
    assert not calls and not store.intents()


@pytest.mark.parametrize(
    "failure", ["real", "unknown", "context_expired", "quote", "quote_identity", "source"]
)
def test_missing_critical_precondition_is_blocked(setup, scenario, failure):
    store, runner = setup
    bundle, day, inputs = scenario
    if failure in {"real", "unknown"}:
        identity = (
            {"realCid": 99, "scopes": ["etoro-public:real:read"]} if failure == "real" else {}
        )
        inputs = replace(inputs, demo=replace(inputs.demo, identity=identity))
    elif failure == "context_expired":
        inputs = replace(inputs, demo=replace(inputs.demo, expires_at=inputs.demo.observed_at))
    elif failure == "source":
        inputs = replace(inputs, demo=replace(inputs.demo, source="EXTERNAL"))
    elif failure == "quote":
        inputs = replace(inputs, quotes={})
    else:
        inputs = replace(
            inputs,
            quotes={"SIMA": replace(inputs.quotes["SIMA"], instrument=bundle.instruments[1])},
        )
    result = runner.run(bundle, day, inputs)
    assert result["status"] == "BLOCKED"
    assert not store.intents() and runner.broker.submit_calls == 0
    assert events(store, "SESSION_BLOCKED")


def test_retry_restart_reconcile_are_idempotent(setup, scenario):
    store, runner = setup
    first = runner.run(*scenario)
    orders = store.intents()
    pnl = store.session(first["session_id"]).realized_pnl
    again = DemoSessionRunner(runner.config, store)
    assert again.run(*scenario) == first
    assert again.broker.submit_calls == again.broker.close_calls == 0
    with Executor(
        store,
        again.broker,
        RiskEngine(runner.config.risk, runner.config.costs),
        first["session_id"],
    ) as executor:
        assert executor.reconcile() and executor.reconcile()
    assert store.intents() == orders
    assert store.session(first["session_id"]).realized_pnl == pnl


class Crash(BaseException):
    pass


@pytest.mark.parametrize("stage", ["approved", "submitting", "accepted"])
def test_recovery_after_durable_boundaries(tmp_path, scenario, monkeypatch, stage):
    path = tmp_path / "crash.sqlite"
    config = load_config("configs/strategy-1-v1.yaml")
    store = StateStore(path)
    runner = DemoSessionRunner(config, store)
    original_transition = StateStore.transition
    original_submit = SimulatorBroker.submit

    def transition(self, intent_id, state):
        if state == OrderState.SUBMITTING and stage == "approved":
            raise Crash()
        return original_transition(self, intent_id, state)

    def submit(self, intent):
        if stage == "accepted":
            original_submit(self, intent)
        raise Crash()

    with monkeypatch.context() as patch:
        patch.setattr(StateStore, "transition", transition)
        patch.setattr(SimulatorBroker, "submit", submit)
        with pytest.raises(Crash):
            runner.run(*scenario)
    identifier = store.intents()[0].intent_id
    store.close()
    store = StateStore(path)
    try:
        restarted = DemoSessionRunner(config, store)
        result = restarted.run(*scenario)
        assert restarted.broker.submit_calls == 0
        assert len([i for i in store.intents() if i.kind == "entry"]) == 1
        assert store.intents()[0].intent_id == identifier
        if stage == "accepted":
            assert result["status"] == "PASS" and not store.positions()
        else:
            assert result["status"] == "BLOCKED"
            assert store.intent(identifier).state == (
                OrderState.EXPIRED if stage == "approved" else OrderState.UNKNOWN
            )
    finally:
        store.close()


def test_response_loss_is_reconciled_without_resubmit(setup, scenario):
    store, runner = setup
    runner.broker.timeout_after_accept = True
    result = runner.run(*scenario)
    assert result["status"] == "PASS" and result["flat"]
    assert runner.broker.submit_calls == runner.broker.close_calls == 1
    assert any(e["kind"] == "SUBMISSION_AMBIGUOUS" for e in store.events())


def test_external_adapter_injection_is_rejected(setup, scenario):
    store, runner = setup
    runner.broker = object()
    result = runner.run(*scenario)
    assert result["reason"] == "A6_LOCAL_BROKER_REQUIRED"
    assert not store.intents()


def test_binding_changes_fail_before_execution(setup, scenario):
    store, runner = setup
    assert runner.run(*scenario)["status"] == "PASS"
    bundle, day, inputs = scenario
    inputs = replace(inputs, quotes={})
    again = DemoSessionRunner(runner.config, store)
    result = again.run(bundle, day, inputs)
    assert result["reason"] == "A6_SESSION_INPUTS_CHANGED"
    assert again.broker.submit_calls == again.broker.close_calls == 0


def test_configuration_does_not_enable_demo_or_mutate_frozen_rules(tmp_path):
    store = StateStore(tmp_path / "wrong.sqlite", mode="etoro_demo")
    try:
        with pytest.raises(BrokerBlocked, match="OFFLINE"):
            DemoSessionRunner(load_config("configs/strategy-1-v1.yaml"), store)
    finally:
        store.close()


def test_partial_execution_keeps_residual_exposure_blocked(setup, scenario):
    store, runner = setup
    runner.broker.fill_fraction = Decimal("0.5")
    result = runner.run(*scenario)
    assert result["reason"] == "A6_RESIDUAL_EXPOSURE"
    assert store.positions() and store.session(result["session_id"]).entries_paused
    entry = [i for i in store.intents() if i.kind == "entry"][0]
    assert entry.state == OrderState.CANCELLED and entry.filled_units > 0
    count = len(store.intents())
    again = DemoSessionRunner(runner.config, store)
    assert again.run(*scenario)["status"] == "BLOCKED"
    assert len(store.intents()) == count
    assert again.broker.submit_calls == again.broker.close_calls == 0


@pytest.mark.parametrize("failure", ["missing", "stale", "negative", "wrong_identity", "early"])
def test_closing_requires_explicit_executable_quote(setup, scenario, failure):
    store, runner = setup
    bundle, day, inputs = scenario
    quote = inputs.closing_quotes["SIMA"]
    if failure == "stale":
        quote = replace(quote, observed_at=quote.observed_at - timedelta(seconds=10))
    elif failure == "negative":
        quote = replace(quote, bid=Decimal(-1))
    elif failure == "wrong_identity":
        quote = replace(quote, instrument=bundle.instruments[1])
    elif failure == "early":
        quote = replace(quote, decision_at=inputs.quotes["SIMA"].decision_at)
    inputs = replace(inputs, closing_quotes={} if failure == "missing" else {"SIMA": quote})
    result = runner.run(bundle, day, inputs)
    assert result["reason"] == "A6_CLOSING_QUOTE_INVALID"
    assert runner.broker.submit_calls == 1 and runner.broker.close_calls == 0
    assert len(store.positions()) == 1 and store.session(result["session_id"]).entries_paused


def test_data_provenance_never_falls_back_to_synthetic(setup, scenario):
    store, runner = setup
    bundle, day, inputs = scenario
    bundle = replace(bundle, manifest=bundle.manifest.model_copy(update={"synthetic": False}))
    result = runner.run(bundle, day, inputs)
    assert result["reason"] == "A6_EXPLICIT_SYNTHETIC_DATA_REQUIRED"
    assert not store.intents()


def test_demo_context_expiring_before_signal_is_blocked(setup, scenario):
    store, runner = setup
    bundle, day, inputs = scenario
    inputs = replace(
        inputs, demo=replace(inputs.demo, expires_at=inputs.demo.observed_at + timedelta(minutes=5))
    )
    assert runner.run(bundle, day, inputs)["reason"] == "A6_DEMO_CONTEXT_EXPIRED"
    assert runner.broker.submit_calls == 0 and not store.intents()


def test_unexpected_failure_is_sanitized_and_disarms(setup, scenario, monkeypatch):
    store, runner = setup

    def fail(*args):
        raise ValueError("private-response-must-not-be-logged")

    monkeypatch.setattr(ORBStrategy, "process_session", fail)
    result = runner.run(*scenario)
    assert result["reason"] == "A6_INTERNAL_ERROR"
    assert "private-response" not in json.dumps(store.events())
    assert store.session(result["session_id"]).entries_paused
    assert not store.intents()


def test_independent_runs_have_identical_functional_results(tmp_path, scenario):
    results = []
    orders = []
    for index in (1, 2):
        store = StateStore(tmp_path / f"run-{index}.sqlite")
        try:
            runner = DemoSessionRunner(load_config("configs/strategy-1-v1.yaml"), store)
            results.append(runner.run(*scenario))
            orders.append(store.intents())
        finally:
            store.close()
    assert results[0] == results[1] and orders[0] == orders[1]


def test_allocated_capital_must_fit_simulated_virtual_credit(setup, scenario):
    store, runner = setup
    bundle, day, inputs = scenario
    portfolio = {"clientPortfolio": {**inputs.demo.portfolio["clientPortfolio"], "credit": 1}}
    inputs = replace(inputs, demo=replace(inputs.demo, portfolio=portfolio))
    assert runner.run(bundle, day, inputs)["reason"] == "A6_VIRTUAL_BUDGET_INVALID"
    assert not store.intents() and runner.broker.submit_calls == 0
