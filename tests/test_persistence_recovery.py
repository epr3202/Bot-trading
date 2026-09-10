import sqlite3
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest
from test_execution_engine import NOW, SESSION, request

from intraday_etoro_lab.brokers.simulator import SimulatorBroker
from intraday_etoro_lab.execution.engine import Executor
from intraday_etoro_lab.execution.models import (
    BrokerOrder,
    ExecutionBroker,
    LifecycleError,
    OrderIntent,
    OrderState,
)
from intraday_etoro_lab.persistence.store import ExecutorLock, StateStore
from intraday_etoro_lab.risk import RiskEngine

D = Decimal


def approved(symbol: str = "ONE") -> OrderIntent:
    return OrderIntent(
        intent_id=str(uuid4()),
        session_id=SESSION,
        signal_id=f"signal-{symbol}",
        symbol=symbol,
        units=D(5),
        entry_price=D(100),
        stop_price=D(99),
        state=OrderState.APPROVED,
        created_at=NOW,
        planned_risk=D(6),
        estimated_cost=D(1),
    )


def test_backup_restore_preserves_unknown_pnl_and_original(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "original.db")
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        executor.submit_entry(request())
        executor.close_owned(store.positions()[0].position_id, D(101))
        ambiguous = approved()
        store.create_intent(ambiguous)
        store.transition(ambiguous.intent_id, OrderState.SUBMITTING)
        store.transition(ambiguous.intent_id, OrderState.UNKNOWN)
        pnl = store.session(SESSION).realized_pnl
        backup = store.backup(tmp_path / "backup.db")
        with pytest.raises(FileExistsError):
            store.backup(backup)
        restored_path = StateStore.restore(backup, tmp_path / "restored.db")
        with pytest.raises(FileExistsError):
            StateStore.restore(backup, store.path)
        with pytest.raises(FileNotFoundError):
            StateStore.restore(tmp_path / "absent.db", tmp_path / "new.db")
        restored = StateStore(restored_path)
        assert restored.session(SESSION).realized_pnl == pnl
        assert restored.session(SESSION).entries_paused
        assert restored.intent(ambiguous.intent_id).state == OrderState.UNKNOWN
        assert restored.get_meta("reconciliation_ok") is None
        assert store.session(SESSION).realized_pnl == pnl
        assert restored.events()
        restored.close()
    store.close()


def test_process_lock_excludes_another_process_and_releases(tmp_path: Path) -> None:
    path = tmp_path / "owner.lock"
    lock = ExecutorLock(path)
    with lock:
        with pytest.raises(RuntimeError, match="already acquired"):
            lock.acquire()
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; from intraday_etoro_lab.persistence.store "
                "import ExecutorLock; import sys; ExecutorLock(Path(sys.argv[1])).acquire()",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "another executor" in result.stderr
    lock.release()
    with ExecutorLock(path):
        pass


def test_schema_config_and_transactions_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        StateStore(tmp_path / "real.db", mode="real")
    store = StateStore(tmp_path / "state.db")
    with pytest.raises(ValueError):
        store.ensure_session(SESSION, D("NaN"))
    store.ensure_session(SESSION, D(10000))
    with pytest.raises(ValueError):
        store.ensure_session(SESSION, D(20000))
    with pytest.raises(KeyError):
        store.session("unknown")
    with pytest.raises(KeyError):
        store.intent("unknown")
    with pytest.raises(RuntimeError):
        with store.transaction():
            store.set_meta("must-rollback", "yes")
            raise RuntimeError("injected")
    assert store.get_meta("must-rollback") is None
    with pytest.raises(ValueError):
        store.create_intent(approved().model_copy(update={"state": OrderState.CREATED}))
    with pytest.raises(ValueError):
        store.create_intent(approved().model_copy(update={"kind": "close", "position_id": None}))
    intent = approved()
    assert store.create_intent(intent)[1]
    assert not store.create_intent(intent.model_copy(update={"intent_id": str(uuid4())}))[1]
    store.close()
    with pytest.raises(ValueError, match="mode mismatch"):
        StateStore(tmp_path / "state.db", mode="shadow")
    with sqlite3.connect(tmp_path / "future.db") as conn:
        conn.execute("PRAGMA user_version=99")
    with pytest.raises(RuntimeError, match="schema"):
        StateStore(tmp_path / "future.db")


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"broker_order_id": ""}, "BROKER_ID_CHANGED"),
        ({"broker_order_id": "changed"}, "BROKER_ID_CHANGED"),
        ({"filled_units": D(6)}, "OVERFILL"),
        ({"filled_units": D(1)}, "REGRESSION"),
        ({"state": OrderState.FILLED}, "FILLED_QUANTITY"),
        ({"state": OrderState.PARTIALLY_FILLED, "filled_units": D(5)}, "PARTIAL_QUANTITY"),
        ({"position_id": None}, "FILL_EVIDENCE"),
        ({"average_price": None}, "FILL_EVIDENCE"),
        ({"cumulative_cost": D(0)}, "COST_REGRESSION"),
        ({"filled_units": D(3), "average_price": D(1)}, "INCREMENTAL_FILL_PRICE"),
    ],
)
def test_bad_cumulative_updates_are_atomic(tmp_path: Path, change: dict, reason: str) -> None:
    store = StateStore(tmp_path / "state.db")
    store.ensure_session(SESSION, D(10000))
    intent = approved()
    store.create_intent(intent)
    store.transition(intent.intent_id, OrderState.SUBMITTING)
    first = BrokerOrder(
        broker_order_id="",
        intent_id=intent.intent_id,
        state=OrderState.PARTIALLY_FILLED,
        filled_units=D(2),
        average_price=D(100),
        position_id="own",
        protected=True,
        cumulative_cost=D(1),
    )
    with pytest.raises(LifecycleError, match="OVERFILL"):
        store.apply_broker_order(first, NOW)
    first = first.model_copy(update={"broker_order_id": "order1"})
    store.apply_broker_order(first, NOW)
    before = store.snapshot(SESSION)
    with pytest.raises(LifecycleError, match=reason):
        store.apply_broker_order(first.model_copy(update=change), NOW)
    after = store.snapshot(SESSION)
    assert before["portfolio"] == after["portfolio"]
    assert before["orders"] == after["orders"]
    assert before["positions"] == after["positions"]
    store.close()


def test_position_collision_marks_and_cost_only_update(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.ensure_session(SESSION, D(10000))
    first, second = approved("FIRST"), approved("SECOND")
    for intent in (first, second):
        store.create_intent(intent)
        store.transition(intent.intent_id, OrderState.SUBMITTING)
    update = BrokerOrder(
        broker_order_id="one",
        intent_id=first.intent_id,
        state=OrderState.FILLED,
        filled_units=D(5),
        average_price=D(100),
        position_id="own",
        protected=True,
        cumulative_cost=D(1),
    )
    store.apply_broker_order(update, NOW)
    with pytest.raises(LifecycleError, match="OWNERSHIP_COLLISION"):
        store.apply_broker_order(
            update.model_copy(update={"intent_id": second.intent_id, "broker_order_id": "two"}), NOW
        )
    assert store.intent(second.intent_id).filled_units == 0
    store.apply_broker_order(update.model_copy(update={"cumulative_cost": D(2)}), NOW)
    assert store.session(SESSION).realized_pnl == -2
    with pytest.raises(ValueError):
        store.mark("own", D("NaN"))
    with pytest.raises(LifecycleError):
        store.set_protection("own", D(98), True)
    store._save_intent(store.intent(first.intent_id).model_copy(update={"filled_units": D(0)}))
    with pytest.raises(LifecycleError, match="OWNERSHIP_UNPROVEN"):
        store.position("own")
    store.close()


def test_restart_does_not_send_created_or_submitting_again(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    store.ensure_session(SESSION, D(10000))
    pending, unsent = approved("PENDING"), approved("UNSENT")
    store.create_intent(pending)
    store.transition(pending.intent_id, OrderState.SUBMITTING)
    store.create_intent(unsent)
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        assert store.intent(pending.intent_id).state == OrderState.UNKNOWN
        assert store.intent(unsent.intent_id).state == OrderState.EXPIRED
        assert broker.submit_calls == 0
        with pytest.raises(RuntimeError, match="unresolved"):
            executor.arm_offline()
        assert not executor.flatten_owned()
        assert store.portfolio(SESSION).reserved_cash > 0
    store.close()


def test_reconciliation_error_and_protection_exception_preserve_controls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = StateStore(tmp_path / "state.db")
    broker = SimulatorBroker(store)
    with Executor(store, broker, RiskEngine(), SESSION) as executor:
        executor.arm_offline()
        executor.submit_entry(request())
        position = store.positions()[0]
        original_query = broker.query

        def fail(*args):
            raise TimeoutError("synthetic failure")

        monkeypatch.setattr(broker, "query", fail)
        assert not executor.reconcile()
        assert store.session(SESSION).entries_paused
        monkeypatch.setattr(broker, "query", original_query)
        monkeypatch.setattr(broker, "protect", fail)
        assert not executor.tighten_stop(position.position_id, D(99))
        assert not store.positions()
        assert not executor.enforce_daily_loss()
    store.close()


def test_failed_start_releases_lock_and_shadow_never_calls_mutations(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "mismatch.db")
    store.ensure_session(SESSION, D(500))
    with pytest.raises(ValueError, match="reference capital"):
        with Executor(store, SimulatorBroker(store), RiskEngine(), SESSION):
            pass
    with ExecutorLock(store.path.with_suffix(".db.executor.lock")):
        pass
    store.close()
    shadow = StateStore(tmp_path / "shadow.db", mode="shadow")
    broker = Mock(spec=ExecutionBroker)
    with Executor(shadow, broker, RiskEngine(), SESSION) as executor:
        with pytest.raises(RuntimeError, match="local simulation"):
            executor.arm_offline()
        assert executor.submit_entry(request()).decision.reason == "SHADOW_MUTATION_BLOCKED"
        with pytest.raises(RuntimeError, match="shadow"):
            executor.close_owned("foreign")
        assert not broker.submit.called and not broker.close.called
    with pytest.raises(ValueError):
        SimulatorBroker(shadow)
    shadow.close()


def test_unresolved_command_is_not_recorded_as_done(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.db")
    with Executor(store, SimulatorBroker(store), RiskEngine(), SESSION) as executor:
        pending = approved()
        store.create_intent(pending)
        store.transition(pending.intent_id, OrderState.SUBMITTING)
        store.enqueue_command("unresolved", "RECONCILE")
        assert executor.process_commands() == 1
        status = store.connection.execute(
            "SELECT status FROM commands WHERE command_id='unresolved'"
        ).fetchone()[0]
        assert status == "BLOCKED"
        assert store.session(SESSION).entries_paused
    store.close()
