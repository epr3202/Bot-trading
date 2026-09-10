"""Fault injection against durable local accounting; no external account operations."""

from datetime import timedelta
from decimal import Decimal as D

import pytest
from test_execution_engine import NOW, SESSION, request

from intraday_etoro_lab.brokers.simulator import SimulatorBroker
from intraday_etoro_lab.execution.engine import Executor
from intraday_etoro_lab.execution.models import LifecycleError, OrderIntent, OrderState
from intraday_etoro_lab.persistence import StateStore
from intraday_etoro_lab.risk import RiskEngine


class DelayedClose(SimulatorBroker):
    fault = "ack"
    lookup_fault = False

    def close(self, intent):
        assert self.store.intent(intent.intent_id) == intent
        assert intent.state == OrderState.SUBMITTING
        if self.fault == "before":
            self.close_calls += 1
            raise TimeoutError
        result = super().close(intent)
        if self.fault == "after":
            raise TimeoutError
        if self.fault == "crash":
            raise SystemExit("injected process death")
        result = result.model_copy(
            update={
                "state": OrderState.REJECTED if self.fault == "reject" else OrderState.ACKNOWLEDGED,
                "filled_units": D(0),
                "average_price": None,
                "cumulative_cost": D(0),
            }
        )
        self.store.simulator_save(result)
        return result

    def query(self, intent_id):
        if self.lookup_fault and self.store.intent(intent_id).kind == "close":
            raise TimeoutError
        return super().query(intent_id)


def start(store, broker, executor):
    executor.arm_offline()
    entry = executor.submit_entry(request()).intent
    return entry, store.positions()[0]


@pytest.mark.parametrize("fault", ["ack", "before", "after", "reject", "crash"])
def test_close_fault_restart_never_repeats_submission(tmp_path, fault):
    path = tmp_path / "book.sqlite"
    store = StateStore(path)
    broker = DelayedClose(store)
    broker.fault = fault
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        entry, position = start(store, broker, executor)
        cash_before = store.portfolio(SESSION).cash
        if fault == "crash":
            with pytest.raises(SystemExit):
                executor.close_owned(position.position_id, D(101), NOW)
            closing = store.intents()[-1]
            assert closing.state == OrderState.SUBMITTING
        else:
            closing = executor.close_owned(position.position_id, D(101), NOW)
            assert closing.state != OrderState.FILLED
        assert store.portfolio(SESSION).cash == cash_before
        assert executor.close_owned(position.position_id, D(103)) == closing
        assert broker.close_calls == 1
    store.close()
    restored = StateStore(path)
    broker = DelayedClose(restored)
    with Executor(restored, broker, RiskEngine(), SESSION) as executor:
        assert restored.session(SESSION).entries_paused
        result = restored.intent(closing.intent_id)
        if fault in {"after", "crash"}:
            assert result.state == OrderState.FILLED
            assert not restored.positions()
            assert restored.session(SESSION).realized_pnl == entry.units * D(".99")
        else:
            assert restored.positions()[0].units == entry.units
        pnl = restored.session(SESSION).realized_pnl
        executor.reconcile()
        executor.close_owned(position.position_id)
        assert restored.session(SESSION).realized_pnl == pnl
        assert broker.close_calls == 0
    restored.close()


def test_partial_remaining_duplicate_out_of_order_and_final_cost(tmp_path):
    store = StateStore(tmp_path / "state.sqlite")
    broker = DelayedClose(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        entry, position = start(store, broker, executor)
        closing = executor.close_owned(position.position_id, D(101), NOW)
        ack = store.simulator_get(closing.intent_id)
        partial = ack.model_copy(
            update={
                "state": OrderState.PARTIALLY_FILLED,
                "filled_units": entry.units / 2,
                "average_price": D(101),
                "cumulative_cost": D(".1"),
            }
        )
        store.simulator_save(partial)
        assert executor.reconcile()
        assert store.position(position.position_id).units == entry.units / 2
        pnl = store.session(SESSION).realized_pnl
        assert executor.reconcile() and store.session(SESSION).realized_pnl == pnl
        broker.lookup_fault = True
        assert not executor.reconcile()
        assert store.session(SESSION).entries_paused
        broker.lookup_fault = False
        store.simulator_save(ack)  # delayed snapshot cannot regress accounted units
        assert not executor.reconcile()
        assert store.session(SESSION).realized_pnl == pnl
        final = partial.model_copy(
            update={
                "state": OrderState.FILLED,
                "filled_units": entry.units,
                "average_price": D(102),
                "cumulative_cost": D(".2"),
            }
        )
        store.simulator_save(final)
        assert executor.reconcile()
        assert not store.positions()
        assert store.session(SESSION).realized_pnl == entry.units * D("1.995") - D(".2")
        store.simulator_save(final.model_copy(update={"cumulative_cost": D(".3")}))
        assert executor.reconcile()
        assert store.position(position.position_id).realized_pnl == entry.units * 2 - D(".3")
        assert executor.flatten_owned() and broker.close_calls == 1
    store.close()


def test_closed_exposure_without_accounting_survives_restart_and_keeps_cash(tmp_path):
    path = tmp_path / "state.sqlite"
    store = StateStore(path)
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        entry, position = start(store, broker, executor)
        cash = store.portfolio(SESSION).cash
        observation = store.simulator_get(entry.intent_id).model_copy(
            update={
                "remaining_units": D(0),
                "observed_at": NOW,
            }
        )
        store.simulator_save(observation)
        assert not executor.reconcile()
        observed = store.position(position.position_id)
        assert observed.observed_units == 0 and observed.units == entry.units
        assert not observed.accounting_complete
        assert store.portfolio(SESSION).cash == cash
        assert not executor.flatten_owned()
        assert broker.close_calls == 0
    store.close()
    store = StateStore(path)
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        assert not executor.reconcile()
        assert store.portfolio(SESSION).cash == cash
        assert not store.position(position.position_id).accounting_complete
        assert executor.close_owned(position.position_id) is None
        assert broker.close_calls == 0
    store.close()


@pytest.mark.parametrize(
    "change",
    [
        {"observed_at": NOW - timedelta(seconds=1)},
        {"observed_at": NOW, "remaining_units": D(1)},
        {"observed_at": NOW + timedelta(seconds=1), "remaining_units": D(100)},
        {"observed_at": NOW.replace(tzinfo=None)},
        {"observed_at": None},
        {"position_id": "manual-same-symbol"},
    ],
)
def test_inconsistent_exposure_observation_rolls_back(tmp_path, change):
    store = StateStore(tmp_path / "state.sqlite")
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        entry, position = start(store, broker, executor)
        observation = store.simulator_get(entry.intent_id).model_copy(
            update={
                "remaining_units": D(0),
                "observed_at": NOW,
            }
        )
        store.apply_broker_order(observation, NOW)
        before = store.position(position.position_id)
        pnl = store.session(SESSION).realized_pnl
        with pytest.raises(LifecycleError):
            store.apply_broker_order(
                observation.model_copy(update=change), NOW + timedelta(seconds=2)
            )
        assert store.position(position.position_id) == before
        assert store.session(SESSION).realized_pnl == pnl
    store.close()


def test_stop_and_scheduled_exit_share_one_intent_and_reject_foreign_owner(tmp_path):
    store = StateStore(tmp_path / "state.sqlite")
    broker = DelayedClose(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        _, position = start(store, broker, executor)
        stop = executor.close_owned(position.position_id, D(99))
        assert not executor.flatten_owned()
        assert executor.close_owned(position.position_id, D(98)) == stop
        assert broker.close_calls == 1
        with pytest.raises(LifecycleError, match="OWNERSHIP"):
            executor.close_owned("manual-same-symbol")
        foreign = OrderIntent.model_validate(
            stop.model_dump()
            | {"intent_id": "foreign", "position_id": "manual-same-symbol", "state": "APPROVED"}
        )
        with pytest.raises(LifecycleError, match="OWNERSHIP"):
            store.create_intent(foreign)
    store.close()


def test_flat_requires_successful_reconciliation_even_after_book_closed(tmp_path):
    store = StateStore(tmp_path / "state.sqlite")
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        entry, position = start(store, broker, executor)
        executor.close_owned(position.position_id)
        broker.query = lambda _: (_ for _ in ()).throw(TimeoutError())
        assert not executor.flatten_owned()
        assert not store.positions() and store.get_meta("reconciliation_ok") == "false"
    store.close()


@pytest.mark.parametrize("state", [OrderState.APPROVED, OrderState.SUBMITTING])
def test_restart_between_close_intent_persistence_and_send(tmp_path, state):
    path = tmp_path / "state.sqlite"
    store = StateStore(path)
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        entry, position = start(store, broker, executor)
        closing = entry.model_copy(
            update={
                "intent_id": "durable-close-before-send",
                "kind": "close",
                "state": OrderState.APPROVED,
                "position_id": position.position_id,
                "filled_units": D(0),
                "average_price": None,
                "broker_order_id": None,
                "cumulative_cost": D(0),
            }
        )
        store.create_intent(closing)
        if state == OrderState.SUBMITTING:
            store.transition(closing.intent_id, state)
        assert broker.close_calls == 0
    store.close()
    store = StateStore(path)
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        recovered = store.intent(closing.intent_id)
        assert recovered.state == (
            OrderState.UNKNOWN if state == OrderState.SUBMITTING else OrderState.EXPIRED
        )
        assert executor.close_owned(position.position_id) == recovered
        assert store.position(position.position_id).units == entry.units
        assert broker.close_calls == 0
    store.close()


def test_duplicate_quantity_with_changed_price_requires_accounting_review(tmp_path):
    store = StateStore(tmp_path / "state.sqlite")
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        _, position = start(store, broker, executor)
        closing = executor.close_owned(position.position_id, D(101))
        pnl = store.session(SESSION).realized_pnl
        update = store.simulator_get(closing.intent_id).model_copy(update={"average_price": D(102)})
        store.simulator_save(update)
        assert not executor.reconcile()
        assert store.session(SESSION).realized_pnl == pnl
        assert store.intent(closing.intent_id).average_price == D(101)
    store.close()
