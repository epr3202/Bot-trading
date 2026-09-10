from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from intraday_etoro_lab.brokers.simulator import SimulatorBroker
from intraday_etoro_lab.execution.engine import Executor
from intraday_etoro_lab.execution.models import (
    TRANSITIONS,
    BrokerOrder,
    LifecycleError,
    OrderState,
    validate_transition,
)
from intraday_etoro_lab.persistence import StateStore
from intraday_etoro_lab.risk import CostConfig, EntryRequest, RiskEngine

D = Decimal
NOW = datetime(2026, 9, 9, 13, 36, 1, tzinfo=UTC)
SESSION = "2026-09-09"


def request(symbol: str = "SYNTH") -> EntryRequest:
    return EntryRequest(
        signal_id=f"signal-{symbol}",
        session_id=SESSION,
        symbol=symbol,
        available_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=9),
        now=NOW,
        entry_price=D("100"),
        stop_price=D("99"),
        bid=D("99.99"),
        ask=D("100"),
        quote_at=NOW,
    )


def test_offline_roundtrip_pause_does_not_block_owned_exit(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        assert store.session(SESSION).entries_paused
        assert executor.submit_entry(request()).decision.reason == "ENTRIES_PAUSED"
        executor.arm_offline()
        result = executor.submit_entry(request())
        assert result.intent and result.intent.state == OrderState.FILLED
        assert len(store.positions()) == 1
        assert store.portfolio(SESSION).reserved_cash == 0
        executor.pause_entries()
        duplicate = executor.submit_entry(request())
        assert duplicate.duplicate and broker.submit_calls == 1
        position = store.positions()[0]
        assert executor.tighten_stop(position.position_id, D("99.50"))
        with pytest.raises(LifecycleError, match="STOP_WIDENING"):
            executor.tighten_stop(position.position_id, D("99"))
        close = executor.close_owned(position.position_id, D("101"))
        assert close and close.state == OrderState.FILLED
        assert not store.positions()
        assert executor.close_owned(position.position_id, D("101")) == close
        assert broker.close_calls == 1
        # .005 commission per unit on each side, no cash charge for reserve slippage.
        assert store.session(SESSION).realized_pnl == result.intent.units * D(".99")
        assert executor.flatten_owned()
        assert store.snapshot(SESSION)["mode"] == "offline"
    with pytest.raises(RuntimeError, match="owning executor"):
        executor.pause_entries()
    store.close()


def test_pending_reserves_capital_slots_and_atomic_duplicate(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    broker = SimulatorBroker(store, fill_fraction=D("0"))
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        first = executor.submit_entry(request("ONE"))
        second = executor.submit_entry(request("TWO"))
        assert first.intent and second.intent
        assert store.portfolio(SESSION).potential_positions == 2
        assert store.portfolio(SESSION).reserved_cash > 1900
        assert store.portfolio(SESSION).reserved_risk > 19
        assert executor.submit_entry(request("THREE")).decision.reason == "POSITION_LIMIT"
        assert executor.submit_entry(request("ONE")).duplicate
        executor.cancel_pending_entries()
        assert all(i.state == OrderState.CANCELLED for i in store.intents())
        assert store.portfolio(SESSION).reserved_cash == 0
        assert executor.submit_entry(request("ONE")).duplicate
    store.close()


def test_timeout_after_accept_restart_reconciles_once_and_keeps_pnl(tmp_path: Path) -> None:
    path = tmp_path / "state.db"
    store = StateStore(path)
    broker = SimulatorBroker(store, timeout_after_accept=True)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        result = executor.submit_entry(request())
        assert result.intent and result.intent.state == OrderState.UNKNOWN
        assert store.portfolio(SESSION).reserved_cash > 0
        assert executor.submit_entry(request()).duplicate
    store.close()
    restored = StateStore(path)
    broker2 = SimulatorBroker(restored)
    with Executor(restored, broker2, RiskEngine(), SESSION) as executor:
        assert broker2.submit_calls == 0
        assert restored.intents()[0].state == OrderState.FILLED
        assert len(restored.positions()) == 1
        assert restored.session(SESSION).entries_paused
        pnl = restored.session(SESSION).realized_pnl
        assert pnl < 0
        assert executor.reconcile()
        assert restored.session(SESSION).realized_pnl == pnl
        executor.flatten_owned()
    restored.close()


def test_partial_fill_cancel_race_and_duplicate_events(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    broker = SimulatorBroker(store, fill_fraction=D(".5"))
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        result = executor.submit_entry(request())
        assert result.intent and result.intent.state == OrderState.PARTIALLY_FILLED
        intent = result.intent
        assert store.portfolio(SESSION).potential_positions == 1
        assert store.portfolio(SESSION).reserved_cash > 0
        initial_units = store.positions()[0].units
        initial_pnl = store.session(SESSION).realized_pnl
        executor.reconcile()
        assert store.positions()[0].units == initial_units
        assert store.session(SESSION).realized_pnl == initial_pnl
        executor.cancel_pending_entries()
        assert store.intent(intent.intent_id).state == OrderState.CANCELLED
        result_broker = broker.query(intent.intent_id)
        assert result_broker
        # Late fill crosses cancellation: cumulative units advance, ownership stays proven.
        broker.set_order(
            result_broker.model_copy(
                update={
                    "state": OrderState.FILLED,
                    "filled_units": intent.units,
                    "cumulative_cost": intent.units * D(".005"),
                }
            )
        )
        assert executor.reconcile()
        assert store.positions()[0].units == intent.units
        assert store.session(SESSION).entries_paused
        assert any(e["kind"] == "INCIDENT_LATE_FILL" for e in store.events())
        broker.fill_fraction = D("1")
        assert executor.flatten_owned()
    store.close()


@pytest.mark.parametrize("missing_stop", [True, False])
def test_post_fill_incident_cancels_and_closes_owned(tmp_path: Path, missing_stop: bool) -> None:
    store = StateStore(tmp_path / "state.db")
    broker = SimulatorBroker(store, fill_fraction=D("0"))
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        result = executor.submit_entry(request())
        assert result.intent
        existing = broker.query(result.intent.intent_id)
        assert existing
        broker.set_order(
            existing.model_copy(
                update={
                    "state": OrderState.FILLED,
                    "filled_units": result.intent.units,
                    "average_price": D("100") if missing_stop else D("102"),
                    "protected": not missing_stop,
                }
            )
        )
        broker.fill_fraction = D("1")
        executor.reconcile()
        assert not store.positions()
        assert store.session(SESSION).entries_paused
        reason = "MISSING_PROTECTION" if missing_stop else "POST_FILL_RISK_EXCEEDED"
        assert any(event["kind"] == reason for event in store.events())
    store.close()


def test_daily_loss_uses_owned_liquidation_marks_and_persists(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        result = executor.submit_entry(request())
        assert result.intent
        position = store.positions()[0]
        store.mark(position.position_id, D("90"))
        assert store.portfolio(SESSION).unrealized_pnl < -50
        assert executor.enforce_daily_loss()
        assert not store.positions()
        assert store.session(SESSION).realized_pnl < -50
        assert executor.submit_entry(request("OTHER")).decision.reason == "ENTRIES_PAUSED"
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        assert executor.submit_entry(request("OTHER")).decision.reason == "DAILY_LOSS_LIMIT"
    store.close()


def test_foreign_position_and_cross_session_rejected(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    with Executor(store, SimulatorBroker(store), RiskEngine(), SESSION) as executor:
        with pytest.raises(LifecycleError, match="OWNERSHIP"):
            executor.close_owned("foreign-manual-position")
        with pytest.raises(ValueError, match="session"):
            executor.submit_entry(replace(request(), session_id="other"))
    store.close()


def test_stop_failure_keeps_exit_available_while_paused(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        executor.submit_entry(request())
        broker.native_protection = False
        assert not executor.tighten_stop(store.positions()[0].position_id, D("99.5"))
        assert not store.positions()
        assert store.session(SESSION).entries_paused
    store.close()


def test_ambiguous_cancel_and_unknown_never_flat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = StateStore(tmp_path / "state.db")
    broker = SimulatorBroker(store, fill_fraction=D(".5"))
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        executor.submit_entry(request())

        def fail(*args: object) -> BrokerOrder:
            raise TimeoutError("test secret must never be logged")

        monkeypatch.setattr(broker, "cancel", fail)
        monkeypatch.setattr(broker, "query", lambda _: None)
        assert not executor.flatten_owned()
        assert store.positions()
        assert store.intents()[0].state == OrderState.UNKNOWN
        assert store.portfolio(SESSION).reserved_cash > 0
        assert "test secret" not in str(store.events())
        with pytest.raises(RuntimeError, match="unresolved"):
            executor.arm_offline()
    store.close()


def test_control_commands_are_durable_and_idempotent(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    with Executor(store, SimulatorBroker(store), RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        assert store.enqueue_command("command-1", "PAUSE_ENTRIES")
        assert not store.enqueue_command("command-1", "PAUSE_ENTRIES")
        assert executor.process_commands() == 1
        assert store.session(SESSION).entries_paused
        assert executor.process_commands() == 0
        with pytest.raises(ValueError):
            store.enqueue_command("bad", "BUY_ARBITRARY")
    store.close()


@pytest.mark.parametrize("old", list(OrderState))
@pytest.mark.parametrize("new", list(OrderState))
def test_explicit_transition_matrix(old: OrderState, new: OrderState) -> None:
    if new == old or new in TRANSITIONS[old]:
        validate_transition(old, new)
    else:
        with pytest.raises(LifecycleError):
            validate_transition(old, new)


def test_fixed_minimum_cost_partial_fill_can_exceed_reserved_risk(tmp_path: Path) -> None:
    costs = CostConfig(minimum_per_side=D("1"))
    store = StateStore(tmp_path / "state.db")
    broker = SimulatorBroker(store, costs=costs, fill_fraction=D(".1"))
    with Executor(store, broker, RiskEngine(costs=costs), SESSION) as executor:
        executor.arm_offline()
        executor.submit_entry(request())
        assert any(e["kind"] == "POST_FILL_RISK_EXCEEDED" for e in store.events())
        assert store.session(SESSION).entries_paused
    store.close()
