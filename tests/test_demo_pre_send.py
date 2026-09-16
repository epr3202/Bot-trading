"""Measured pre-send failures must never masquerade as external uncertainty."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import httpx
import pytest
from test_etoro_adapter import build_adapter, eligibility, order_response, quote_rows
from test_etoro_transport import NOW
from test_execution_engine import request as entry_request

from intraday_etoro_lab.brokers.authorization import BrokerBlocked, RejectedBeforeSend
from intraday_etoro_lab.brokers.market_data import EtoroMarketDataProvider
from intraday_etoro_lab.brokers.transport import (
    COSTS,
    ELIGIBILITY,
    LOOKUP,
    ME,
    ORDERS,
    PORTFOLIO,
    RATES,
)
from intraday_etoro_lab.execution.engine import Executor
from intraday_etoro_lab.execution.models import OrderState
from intraday_etoro_lab.persistence import StateStore
from intraday_etoro_lab.risk import InstrumentRules, RiskEngine


def setup(tmp_path, responses=None):
    ledger = StateStore(tmp_path / "state.sqlite", mode="etoro_demo")
    adapter, item, calls, _, _ = build_adapter(responses=responses)
    adapter.intent_loader = ledger.intent
    adapter.position_loader = ledger.position
    request = replace(
        entry_request("TEST"),
        session_id="session",
        now=NOW,
        quote_at=NOW,
        available_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=9),
        entry_price=Decimal("100.01"),
        ask=Decimal("100.01"),
        bid=Decimal(100),
        rules=InstrumentRules(unit_step=Decimal(1)),
    )
    return ledger, adapter, calls, request


@pytest.mark.parametrize(
    "failure", ["identity", "eligibility", "minimum", "leverage", "costs", "prepare"]
)
def test_pre_send_rejection_releases_reserve_and_records_cause(tmp_path, failure, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    responses = {}
    if failure == "identity":
        responses[ME] = {}
    if failure in {"eligibility", "minimum", "leverage"}:
        doc = eligibility()
        row = doc["eligibilities"][0]
        if failure == "eligibility":
            row["allowOpenPosition"] = False
        if failure == "minimum":
            row["minPositionExposure"] = 999999
        if failure == "leverage":
            row["leverageConfigs"][0]["leverageValues"] = [2]
        responses[ELIGIBILITY] = doc
    if failure == "costs":
        responses[COSTS] = {}
    ledger, adapter, calls, request = setup(tmp_path, responses)
    if failure == "prepare":

        def invalid(_):
            raise ValueError("PRIVATE_DETAIL")

        adapter.entry_review = invalid
    with Executor(ledger, adapter, RiskEngine(), "session") as executor:
        ledger.pause("session", False)
        result = executor.submit_entry(request)
        assert result.intent.state == OrderState.REJECTED
        assert ledger.portfolio("session").reserved_cash == 0
        assert ledger.portfolio("session").reserved_risk == 0
        assert adapter.transport.mutation_attempts == 0
        assert all(r.url.path != ORDERS for r in calls)
        events = ledger.events()
        assert any(e["kind"] == "REJECTED_PRE_SEND" for e in events)
        assert not any(e["details"] == "SUBMITTING" for e in events)
        assert "PRIVATE_DETAIL" not in str(events)
        assert executor.reconcile()
    ledger.close()


@pytest.mark.parametrize("failure", ["timeout", "bad_response", "server_error"])
def test_post_attempt_failures_remain_unknown_and_never_resubmit(tmp_path, monkeypatch, failure):
    monkeypatch.delenv("CI", raising=False)
    ledger, adapter, calls, request = setup(tmp_path)
    mock = adapter.transport._contract_transport
    original = mock.handler

    def handler(http_request):
        if http_request.url.path == ORDERS:
            calls.append(http_request)
            saved = ledger.intents()[0]
            assert saved.state == OrderState.SUBMITTING
            assert ledger.get_meta("prepared:" + saved.intent_id) is not None
            if failure == "timeout":
                raise httpx.ReadTimeout("PRIVATE_DETAIL")
            if failure == "server_error":
                return httpx.Response(500)
            return httpx.Response(200, json={"orderId": 7})
        return original(http_request)

    mock.handler = handler
    with Executor(ledger, adapter, RiskEngine(), "session") as executor:
        ledger.pause("session", False)
        result = executor.submit_entry(request)
        assert result.intent.state == OrderState.UNKNOWN
        assert adapter.transport.mutation_attempts == 1
        assert ledger.portfolio("session").reserved_cash > 0
        assert executor.submit_entry(request).duplicate
        assert len([r for r in calls if r.url.path == ORDERS]) == 1
        assert not any(e["kind"] == "REJECTED_PRE_SEND" for e in ledger.events())
    ledger.close()


class Crash(BaseException):
    pass


def test_crash_during_preparation_expires_without_external_unknown(tmp_path, monkeypatch):
    ledger, adapter, calls, request = setup(tmp_path)

    def crash(_):
        raise Crash()

    adapter.entry_review = crash
    with pytest.raises(Crash), Executor(ledger, adapter, RiskEngine(), "session") as executor:
        ledger.pause("session", False)
        executor.submit_entry(request)
    assert ledger.intents()[0].state == OrderState.APPROVED
    assert adapter.transport.mutation_attempts == 0
    # No result was sent; recovery expires the durable prepared intent without resending.
    with Executor(ledger, adapter, RiskEngine(), "session"):
        assert ledger.intents()[0].state == OrderState.EXPIRED
        assert adapter.transport.mutation_attempts == 0
    ledger.close()


def test_provider_utc_without_suffix_preserves_stale_event_time():
    document = quote_rows()
    document["results"][0]["date"] = "2026-09-10T13:58:00.123"
    adapter, _, _, _, _ = build_adapter(responses={RATES: document})
    quote = EtoroMarketDataProvider(adapter.transport).quotes([123])[0]
    assert quote.event_time.isoformat() == "2026-09-10T13:58:00.123000+00:00"
    assert (quote.received_at - quote.event_time).total_seconds() > 3


@pytest.mark.parametrize("path", [ELIGIBILITY, COSTS])
def test_demo_preview_has_fresh_identity_and_no_trading_mutations(path):
    adapter, _, calls, _, _ = build_adapter()
    adapter.transport.request("POST", path, body={}, demo_preview=True)
    assert [r.url.path for r in calls] == [ME, PORTFOLIO, path]
    assert adapter.transport.mutation_attempts == 0


@pytest.mark.parametrize(
    "document", [{}, {"realCid": 99, "demoCid": 42, "scopes": ["etoro-public:real:write"]}]
)
def test_preview_rejects_non_demo_before_post(document):
    adapter, _, calls, _, _ = build_adapter(responses={ME: document})
    with pytest.raises(BrokerBlocked):
        adapter.transport.request("POST", COSTS, body={}, demo_preview=True)
    assert all(r.method == "GET" for r in calls)


def test_preview_cannot_enable_trading_route():
    adapter, _, calls, _, _ = build_adapter()
    with pytest.raises(BrokerBlocked, match="PREVIEW_ROUTE_REQUIRED"):
        adapter.transport.request("POST", ORDERS, body={}, demo_preview=True)
    assert calls == []


def test_prepared_intent_change_is_rejected(tmp_path, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    ledger, adapter, _, request = setup(tmp_path)
    with Executor(ledger, adapter, RiskEngine(), "session"):
        from test_etoro_adapter import intent

        item = intent(state=OrderState.APPROVED)
        ledger.create_intent(item)
        prepared = adapter.prepare(item)
        changed = item.model_copy(update={"state": OrderState.SUBMITTING, "units": Decimal(99)})
        with pytest.raises(RejectedBeforeSend, match="PREPARED_INTENT_CHANGED"):
            prepared.send(changed)
        assert adapter.transport.mutation_attempts == 0
    ledger.close()


@pytest.mark.parametrize("stage", ["before_post", "during_post", "after_response"])
def test_restart_uses_durable_reference_without_duplicate_post(tmp_path, monkeypatch, stage):
    monkeypatch.delenv("CI", raising=False)
    ledger, adapter, calls, request = setup(tmp_path)
    mock = adapter.transport._contract_transport
    original = mock.handler

    def handler(http_request):
        if http_request.url.path == ORDERS:
            calls.append(http_request)
            if stage == "during_post":
                raise Crash()
            return httpx.Response(
                200, json={"orderId": 7, "referenceId": http_request.headers["x-request-id"]}
            )
        if http_request.url.path == LOOKUP:
            calls.append(http_request)
            if stage != "after_response":
                return httpx.Response(404)
            response = order_response()
            response["positionExecutions"][0]["openingData"]["units"] = int(
                ledger.intents()[0].units
            )
            return httpx.Response(200, json=response)
        return original(http_request)

    mock.handler = handler
    transition = StateStore.transition

    def stop_before_post(self, identifier, state):
        if state == OrderState.SUBMITTING:
            raise Crash()
        return transition(self, identifier, state)

    def stop_before_booking(*args):
        raise Crash()

    with monkeypatch.context() as patch:
        if stage == "before_post":
            patch.setattr(StateStore, "transition", stop_before_post)
        if stage == "after_response":
            patch.setattr(Executor, "_apply", stop_before_booking)
        with pytest.raises(Crash), Executor(ledger, adapter, RiskEngine(), "session") as executor:
            ledger.pause("session", False)
            executor.submit_entry(request)
    identifier = ledger.intents()[0].intent_id
    assert ledger.get_meta("prepared:" + identifier)
    ledger.close()
    ledger = StateStore(tmp_path / "state.sqlite", mode="etoro_demo")
    adapter.intent_loader = ledger.intent
    adapter.position_loader = ledger.position
    expected = {
        "before_post": OrderState.EXPIRED,
        "during_post": OrderState.UNKNOWN,
        "after_response": OrderState.FILLED,
    }
    with Executor(ledger, adapter, RiskEngine(), "session") as restarted:
        assert ledger.intent(identifier).state == expected[stage]
        assert restarted.submit_entry(request).duplicate
        assert len([r for r in calls if r.url.path == ORDERS]) == (stage != "before_post")
        if stage == "after_response":
            assert ledger.intent(identifier).broker_order_id == "7"
            assert ledger.positions()[0].position_id == "8"
        if stage == "during_post":
            assert ledger.portfolio("session").reserved_cash > 0
    ledger.close()
