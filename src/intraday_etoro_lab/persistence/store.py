"""SQLite v1 schema, atomic reservations, cumulative fills and process ownership."""

import json
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import TracebackType
from typing import IO, Any, Literal

from intraday_etoro_lab.execution.models import (
    ACTIVE_STATES,
    BrokerOrder,
    LifecycleError,
    OrderIntent,
    OrderState,
    Position,
    TradingSession,
    validate_transition,
)
from intraday_etoro_lab.risk import RiskPortfolio

D = Decimal
Mode = Literal["offline", "backtest", "shadow", "etoro_demo"]


class ExecutorLock:
    """OS-owned non-expiring lock; process death releases it, stalled calls do not."""

    def __init__(self, path: Path):
        self.path = path
        self.handle: IO[bytes] | None = None

    def acquire(self) -> None:
        if self.handle is not None:
            raise RuntimeError("Executor lock already acquired")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise RuntimeError("BLOCKED: another executor owns this database") from None
        self.handle = handle

    def release(self) -> None:
        if self.handle is None:
            return
        if sys.platform == "win32":
            import msvcrt

            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()
        self.handle = None

    def __enter__(self) -> "ExecutorLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()


class StateStore:
    def __init__(self, path: str | Path, mode: Mode = "offline"):
        if mode not in {"offline", "backtest", "shadow", "etoro_demo"}:
            raise ValueError("Unsupported mode")
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.connection = sqlite3.connect(self.path, isolation_level=None, timeout=5)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._migrate()
        old_mode = self.get_meta("mode")
        if old_mode is not None and old_mode != mode:
            self.close()
            raise ValueError("Database mode mismatch; use separate state for each mode")
        self.set_meta("mode", mode)
        self.executor_lock = ExecutorLock(
            self.path.with_suffix(self.path.suffix + ".executor.lock")
        )

    def _migrate(self) -> None:
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            raise RuntimeError(f"Unsupported database schema {version}")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(
                session_id TEXT PRIMARY KEY, reference_capital TEXT NOT NULL,
                realized_pnl TEXT NOT NULL DEFAULT '0', entries_paused INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS intents(
                intent_id TEXT PRIMARY KEY, strategy TEXT NOT NULL, version TEXT NOT NULL,
                session_id TEXT NOT NULL, symbol TEXT NOT NULL, kind TEXT NOT NULL,
                uniqueness_key TEXT NOT NULL, payload TEXT NOT NULL,
                UNIQUE(strategy, version, session_id, uniqueness_key, kind)
            );
            CREATE TABLE IF NOT EXISTS reservations(
                intent_id TEXT PRIMARY KEY REFERENCES intents(intent_id),
                cash TEXT NOT NULL, risk TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS positions(
                position_id TEXT PRIMARY KEY, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS fills(
                fill_id TEXT PRIMARY KEY, intent_id TEXT NOT NULL REFERENCES intents(intent_id),
                units TEXT NOT NULL, price TEXT NOT NULL, cost TEXT NOT NULL, at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS broker_costs(
                intent_id TEXT PRIMARY KEY REFERENCES intents(intent_id), total TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit(
                event_id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
                kind TEXT NOT NULL, intent_id TEXT, details TEXT NOT NULL, mode TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS simulator_orders(intent_id TEXT PRIMARY KEY, payload TEXT);
            CREATE TABLE IF NOT EXISTS commands(
                command_id TEXT PRIMARY KEY, kind TEXT NOT NULL, at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING'
            );
            PRAGMA user_version=1;
        """)

    @contextmanager
    def transaction(self) -> Iterator[None]:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise
        else:
            self.connection.execute("COMMIT")

    def close(self) -> None:
        self.connection.close()

    def get_meta(self, key: str) -> str | None:
        row = self.connection.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        return None if row is None else str(row[0])

    def set_meta(self, key: str, value: str) -> None:
        self.connection.execute(
            "INSERT INTO metadata(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

    def ensure_session(self, session_id: str, capital: Decimal) -> TradingSession:
        if not capital.is_finite() or capital <= 0:
            raise ValueError("Reference capital must be positive finite Decimal")
        self.connection.execute(
            "INSERT OR IGNORE INTO sessions(session_id,reference_capital) VALUES(?,?)",
            (session_id, str(capital)),
        )
        session = self.session(session_id)
        if session.reference_capital != capital:
            raise ValueError("Cannot change session reference capital")
        return session

    def session(self, session_id: str) -> TradingSession:
        row = self.connection.execute(
            "SELECT * FROM sessions WHERE session_id=?",
            (session_id,),
        ).fetchone()
        if row is None:
            raise KeyError("Unknown trading session")
        return TradingSession(**dict(row))

    def pause(self, session_id: str, paused: bool = True) -> None:
        self.connection.execute(
            "UPDATE sessions SET entries_paused=? WHERE session_id=?",
            (int(paused), session_id),
        )
        self.audit("PAUSE_ENTRIES" if paused else "ENTRIES_ARMED", details=session_id)

    def audit(self, kind: str, intent_id: str | None = None, details: str = "") -> None:
        # Callers pass bounded local reason codes; never broker payloads or exception text.
        self.connection.execute(
            "INSERT INTO audit(at,kind,intent_id,details,mode) VALUES(?,?,?,?,?)",
            (datetime.now(UTC).isoformat(), kind, intent_id, details, self.mode),
        )

    def events(self) -> list[dict[str, Any]]:
        return [
            dict(row) for row in self.connection.execute("SELECT * FROM audit ORDER BY event_id")
        ]

    def create_intent(self, intent: OrderIntent) -> tuple[OrderIntent, bool]:
        if intent.mode != self.mode or intent.state != OrderState.APPROVED:
            raise ValueError("Only approved intents in this database mode may reserve exposure")
        uniqueness_key = intent.symbol if intent.kind == "entry" else intent.position_id
        if uniqueness_key is None:
            raise ValueError("Close requires owned position identifier")
        with self.transaction():
            row = self.connection.execute(
                "SELECT payload FROM intents WHERE strategy=? AND version=? AND session_id=? "
                "AND uniqueness_key=? AND kind=?",
                (intent.strategy, intent.version, intent.session_id, uniqueness_key, intent.kind),
            ).fetchone()
            if row is not None:
                return OrderIntent.model_validate_json(row[0]), False
            self.connection.execute(
                "INSERT INTO intents VALUES(?,?,?,?,?,?,?,?)",
                (
                    intent.intent_id,
                    intent.strategy,
                    intent.version,
                    intent.session_id,
                    intent.symbol,
                    intent.kind,
                    uniqueness_key,
                    intent.model_dump_json(),
                ),
            )
            if intent.kind == "entry":
                self.connection.execute(
                    "INSERT INTO reservations VALUES(?,?,?)",
                    (
                        intent.intent_id,
                        str(intent.units * intent.entry_price + intent.estimated_cost),
                        str(intent.planned_risk),
                    ),
                )
            self.audit("INTENT_DURABLE", intent.intent_id)
        return intent, True

    def intent(self, intent_id: str) -> OrderIntent:
        row = self.connection.execute(
            "SELECT payload FROM intents WHERE intent_id=?",
            (intent_id,),
        ).fetchone()
        if row is None:
            raise KeyError("Unknown intent")
        return OrderIntent.model_validate_json(row[0])

    def intents(self) -> list[OrderIntent]:
        return [
            OrderIntent.model_validate_json(row[0])
            for row in self.connection.execute(
                "SELECT payload FROM intents ORDER BY rowid",
            )
        ]

    def _save_intent(self, intent: OrderIntent) -> None:
        self.connection.execute(
            "UPDATE intents SET payload=? WHERE intent_id=?",
            (intent.model_dump_json(), intent.intent_id),
        )

    def transition(self, intent_id: str, state: OrderState) -> OrderIntent:
        with self.transaction():
            intent = self.intent(intent_id)
            validate_transition(intent.state, state)
            updated = intent.model_copy(update={"state": state})
            self._save_intent(updated)
            if state not in ACTIVE_STATES:
                self.connection.execute("DELETE FROM reservations WHERE intent_id=?", (intent_id,))
            self.audit("ORDER_STATE", intent_id, state)
        return updated

    def positions(self, open_only: bool = True) -> list[Position]:
        positions = [
            Position.model_validate_json(row[0])
            for row in self.connection.execute(
                "SELECT payload FROM positions ORDER BY position_id",
            )
        ]
        return [p for p in positions if p.units > 0] if open_only else positions

    def position(self, position_id: str) -> Position:
        row = self.connection.execute(
            "SELECT payload FROM positions WHERE position_id=?",
            (position_id,),
        ).fetchone()
        if row is None:
            raise LifecycleError("OWNERSHIP_UNPROVEN")
        position = Position.model_validate_json(row[0])
        origin = self.intent(position.owner_intent_id)
        if origin.kind != "entry" or origin.mode != self.mode or origin.filled_units <= 0:
            raise LifecycleError("OWNERSHIP_UNPROVEN")
        return position

    def _save_position(self, position: Position) -> None:
        self.connection.execute(
            "INSERT INTO positions VALUES(?,?) ON CONFLICT(position_id) "
            "DO UPDATE SET payload=excluded.payload",
            (position.position_id, position.model_dump_json()),
        )

    def mark(self, position_id: str, liquidation_price: Decimal) -> None:
        if not liquidation_price.is_finite() or liquidation_price <= 0:
            raise ValueError("Invalid liquidation mark")
        position = self.position(position_id)
        self._save_position(position.model_copy(update={"mark_price": liquidation_price}))

    def set_protection(self, position_id: str, stop_price: Decimal, protected: bool) -> None:
        with self.transaction():
            position = self.position(position_id)
            if not stop_price.is_finite() or stop_price < position.stop_price:
                raise LifecycleError("STOP_WIDENING_BLOCKED")
            self._save_position(
                position.model_copy(
                    update={
                        "stop_price": stop_price,
                        "protected": protected,
                    }
                )
            )
            self.audit("PROTECTION_UPDATED", position.owner_intent_id)

    def apply_broker_order(self, update: BrokerOrder, now: datetime) -> OrderIntent:
        with self.transaction():
            intent = self.intent(update.intent_id)
            validate_transition(intent.state, update.state)
            if intent.broker_order_id and intent.broker_order_id != update.broker_order_id:
                raise LifecycleError("BROKER_ID_CHANGED")
            if not update.broker_order_id or update.filled_units > intent.units:
                raise LifecycleError("OVERFILL_OR_MISSING_BROKER_ID")
            if update.filled_units < intent.filled_units:
                raise LifecycleError("CUMULATIVE_FILL_REGRESSION")
            if update.state == OrderState.FILLED and update.filled_units != intent.units:
                raise LifecycleError("FILLED_QUANTITY_MISMATCH")
            if update.state == OrderState.PARTIALLY_FILLED and not (
                0 < update.filled_units < intent.units
            ):
                raise LifecycleError("PARTIAL_QUANTITY_MISMATCH")
            if update.filled_units and (not update.position_id or update.average_price is None):
                raise LifecycleError("FILL_EVIDENCE_MISSING")
            old_cost_row = self.connection.execute(
                "SELECT total FROM broker_costs WHERE intent_id=?",
                (intent.intent_id,),
            ).fetchone()
            old_cost = D(old_cost_row[0]) if old_cost_row else D("0")
            if update.cumulative_cost < old_cost:
                raise LifecycleError("CUMULATIVE_COST_REGRESSION")
            cost_delta = update.cumulative_cost - old_cost
            delta = update.filled_units - intent.filled_units
            updated = intent.model_copy(
                update={
                    "state": update.state,
                    "broker_order_id": update.broker_order_id,
                    "filled_units": update.filled_units,
                    "average_price": update.average_price,
                }
            )
            self._save_intent(updated)
            if delta > 0:
                assert update.average_price is not None and update.position_id is not None
                prior_notional = intent.filled_units * (intent.average_price or D("0"))
                delta_price = (update.filled_units * update.average_price - prior_notional) / delta
                if delta_price <= 0:
                    raise LifecycleError("INVALID_INCREMENTAL_FILL_PRICE")
                self._apply_fill(intent, update, delta, delta_price, cost_delta, now)
                if intent.state in {OrderState.CANCELLED, OrderState.EXPIRED}:
                    self.pause(intent.session_id)
                    self.audit("INCIDENT_LATE_FILL", intent.intent_id)
            elif cost_delta:
                self._add_pnl(intent.session_id, -cost_delta)
            self.connection.execute(
                "INSERT INTO broker_costs VALUES(?,?) ON CONFLICT(intent_id) "
                "DO UPDATE SET total=excluded.total",
                (intent.intent_id, str(update.cumulative_cost)),
            )
            if intent.kind == "entry" and update.state in ACTIVE_STATES:
                remaining_fraction = (intent.units - update.filled_units) / intent.units
                self.connection.execute(
                    "INSERT INTO reservations VALUES(?,?,?) ON CONFLICT(intent_id) "
                    "DO UPDATE SET cash=excluded.cash,risk=excluded.risk",
                    (
                        intent.intent_id,
                        str(
                            (intent.units * intent.entry_price + intent.estimated_cost)
                            * remaining_fraction
                        ),
                        str(intent.planned_risk * remaining_fraction),
                    ),
                )
            else:
                self.connection.execute(
                    "DELETE FROM reservations WHERE intent_id=?",
                    (intent.intent_id,),
                )
            self.audit("BROKER_RECONCILED", intent.intent_id, update.state)
        return updated

    def _apply_fill(
        self,
        intent: OrderIntent,
        update: BrokerOrder,
        delta: Decimal,
        price: Decimal,
        cost: Decimal,
        now: datetime,
    ) -> None:
        assert update.position_id is not None
        if intent.kind == "entry":
            existing_row = self.connection.execute(
                "SELECT payload FROM positions WHERE position_id=?",
                (update.position_id,),
            ).fetchone()
            existing = Position.model_validate_json(existing_row[0]) if existing_row else None
            if existing and existing.owner_intent_id != intent.intent_id:
                raise LifecycleError("POSITION_OWNERSHIP_COLLISION")
            old_units = existing.units if existing else D("0")
            old_notional = old_units * existing.average_entry if existing else D("0")
            position = Position(
                position_id=update.position_id,
                owner_intent_id=intent.intent_id,
                session_id=intent.session_id,
                symbol=intent.symbol,
                units=old_units + delta,
                average_entry=(old_notional + delta * price) / (old_units + delta),
                stop_price=intent.stop_price,
                protected=update.protected,
                mode=intent.mode,
                realized_pnl=existing.realized_pnl if existing else D("0"),
                planned_risk=intent.planned_risk * update.filled_units / intent.units,
                mark_price=price,
            )
            pnl = -cost
        else:
            if intent.position_id != update.position_id:
                raise LifecycleError("CLOSE_POSITION_ID_MISMATCH")
            existing = self.position(update.position_id)
            if delta > existing.units:
                raise LifecycleError("CLOSE_WOULD_OPEN_SHORT")
            pnl = delta * (price - existing.average_entry) - cost
            position = existing.model_copy(
                update={
                    "units": existing.units - delta,
                    "realized_pnl": existing.realized_pnl + pnl,
                    "mark_price": price,
                }
            )
        self._save_position(position)
        self._add_pnl(intent.session_id, pnl)
        self.connection.execute(
            "INSERT INTO fills VALUES(?,?,?,?,?,?)",
            (
                f"{update.broker_order_id}:{update.filled_units.normalize()}",
                intent.intent_id,
                str(delta),
                str(price),
                str(cost),
                now.isoformat(),
            ),
        )

    def _add_pnl(self, session_id: str, pnl: Decimal) -> None:
        session = self.session(session_id)
        self.connection.execute(
            "UPDATE sessions SET realized_pnl=? WHERE session_id=?",
            (str(session.realized_pnl + pnl), session_id),
        )

    def portfolio(self, session_id: str) -> RiskPortfolio:
        session = self.session(session_id)
        positions = self.positions()
        reserved = self.connection.execute("SELECT cash,risk FROM reservations").fetchall()
        exposure = sum((p.units * p.average_entry for p in positions), D("0"))
        unrealized = sum(
            (p.units * ((p.mark_price or p.average_entry) - p.average_entry) for p in positions),
            D("0"),
        )
        pending_entries = [
            i for i in self.intents() if i.kind == "entry" and i.state in ACTIVE_STATES
        ]
        owners = {p.owner_intent_id for p in positions}
        potential = len(owners | {i.intent_id for i in pending_entries})
        all_pnl = sum(
            (
                D(row[0])
                for row in self.connection.execute(
                    "SELECT realized_pnl FROM sessions",
                )
            ),
            D("0"),
        )
        open_risk = sum((p.planned_risk for p in positions), D("0"))
        return RiskPortfolio(
            reference_capital=session.reference_capital,
            equity=session.reference_capital + all_pnl + unrealized,
            cash=session.reference_capital + all_pnl - exposure,
            gross_exposure=exposure,
            reserved_cash=sum((D(row[0]) for row in reserved), D("0")),
            reserved_risk=sum((D(row[1]) for row in reserved), D("0")) + open_risk,
            potential_positions=potential,
            realized_pnl=session.realized_pnl,
            unrealized_pnl=unrealized,
            entries_paused=session.entries_paused,
            reconciliation_ok=self.get_meta("reconciliation_ok") == "true",
        )

    def simulator_save(self, order: BrokerOrder) -> None:
        self.connection.execute(
            "INSERT INTO simulator_orders VALUES(?,?) ON CONFLICT(intent_id) "
            "DO UPDATE SET payload=excluded.payload",
            (order.intent_id, order.model_dump_json()),
        )

    def simulator_get(self, intent_id: str) -> BrokerOrder | None:
        row = self.connection.execute(
            "SELECT payload FROM simulator_orders WHERE intent_id=?",
            (intent_id,),
        ).fetchone()
        return None if row is None else BrokerOrder.model_validate_json(row[0])

    def enqueue_command(self, command_id: str, kind: str) -> bool:
        if kind not in {"PAUSE_ENTRIES", "RECONCILE", "CANCEL_PENDING_ENTRIES", "FLATTEN_OWNED"}:
            raise ValueError("Unsupported executor command")
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO commands(command_id,kind,at) VALUES(?,?,?)",
            (command_id, kind, datetime.now(UTC).isoformat()),
        )
        return cursor.rowcount == 1

    def pending_commands(self) -> list[dict[str, str]]:
        return [
            dict(row)
            for row in self.connection.execute(
                "SELECT command_id,kind,status FROM commands WHERE status='PENDING' ORDER BY rowid",
            )
        ]

    def finish_command(self, command_id: str, status: Literal["DONE", "BLOCKED"]) -> None:
        self.connection.execute(
            "UPDATE commands SET status=? WHERE command_id=?", (status, command_id)
        )

    def backup(self, destination: str | Path) -> Path:
        destination = Path(destination).resolve()
        if destination.exists():
            raise FileExistsError("Backup destination already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(destination) as target:
            self.connection.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed")
        self.audit("BACKUP_CREATED")
        return destination

    @staticmethod
    def restore(source: str | Path, destination: str | Path) -> Path:
        source, destination = Path(source).resolve(), Path(destination).resolve()
        if not source.is_file():
            raise FileNotFoundError("Backup does not exist")
        if destination.exists():
            raise FileExistsError("Restore must use a new destination; original stays intact")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True) as backup:
            if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed")
            with sqlite3.connect(destination) as target:
                backup.backup(target)
                target.execute("UPDATE sessions SET entries_paused=1")
                target.execute("DELETE FROM metadata WHERE key='reconciliation_ok'")
        return destination

    def snapshot(self, session_id: str) -> dict[str, Any]:
        portfolio = self.portfolio(session_id)
        return {
            "mode": self.mode,
            "session": self.session(session_id).model_dump(mode="json"),
            "orders": [i.model_dump(mode="json") for i in self.intents()],
            "positions": [p.model_dump(mode="json") for p in self.positions()],
            "portfolio": json.loads(json.dumps(portfolio.__dict__, default=str)),
            "events": self.events(),
        }
