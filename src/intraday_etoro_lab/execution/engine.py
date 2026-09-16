"""One executor owns all submissions, cumulative accounting and safe exits."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from types import TracebackType
from uuid import NAMESPACE_URL, uuid5

from intraday_etoro_lab.brokers.authorization import RejectedBeforeSend
from intraday_etoro_lab.execution.models import (
    ACTIVE_STATES,
    BrokerOrder,
    ExecutionBroker,
    LifecycleError,
    OrderIntent,
    OrderState,
    PreparedSubmission,
    PreparingBroker,
)
from intraday_etoro_lab.persistence import StateStore
from intraday_etoro_lab.risk import EntryRequest, RiskDecision, RiskEngine


@dataclass(frozen=True)
class SubmissionResult:
    intent: OrderIntent | None
    decision: RiskDecision
    duplicate: bool = False


class Executor:
    def __init__(
        self,
        store: StateStore,
        broker: ExecutionBroker,
        risk_engine: RiskEngine,
        session_id: str,
    ):
        self.store = store
        self.broker = broker
        self.risk = risk_engine
        self.session_id = session_id
        self._started = False
        self._incident_management = False

    def __enter__(self) -> "Executor":
        self.store.executor_lock.acquire()
        try:
            self.store.ensure_session(self.session_id, self.risk.config.allocated_capital)
            self.store.pause(self.session_id)
            self.store.set_meta("reconciliation_ok", "false")
            self._started = True
            # No crash-recovered entry is automatically resubmitted.
            for intent in self.store.intents():
                if intent.state == OrderState.SUBMITTING:
                    self.store.transition(intent.intent_id, OrderState.UNKNOWN)
                elif intent.state in {OrderState.CREATED, OrderState.APPROVED}:
                    self.store.transition(intent.intent_id, OrderState.EXPIRED)
            self.reconcile()
        except BaseException:
            self._started = False
            self.store.executor_lock.release()
            raise
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.pause_entries()
        if self.store.positions() or any(i.state in ACTIVE_STATES for i in self.store.intents()):
            self.store.audit("STOP_WITH_RESIDUAL_EXPOSURE")
        self._started = False
        self.store.executor_lock.release()

    def _require_started(self) -> None:
        if not self._started or self.store.executor_lock.handle is None:
            raise RuntimeError("BLOCKED: command must run through the owning executor")

    def arm_offline(self) -> None:
        self._require_started()
        if self.store.mode not in {"offline", "backtest"}:
            raise RuntimeError("BLOCKED: this method only arms local simulation")
        if self.store.get_meta("reconciliation_ok") != "true":
            raise RuntimeError("BLOCKED: unresolved reconciliation")
        self.store.pause(self.session_id, False)

    def pause_entries(self) -> None:
        self._require_started()
        self.store.pause(self.session_id)

    def submit_entry(self, request: EntryRequest) -> SubmissionResult:
        self._require_started()
        if request.session_id != self.session_id:
            raise ValueError("Signal session differs from executor session")
        for old in self.store.intents():
            if (old.strategy, old.version, old.session_id, old.symbol, old.kind) == (
                request.strategy,
                request.version,
                request.session_id,
                request.symbol,
                "entry",
            ):
                return SubmissionResult(old, RiskDecision(False, "DUPLICATE_INTENT"), True)
        if self.store.mode == "shadow":
            return SubmissionResult(None, RiskDecision(False, "SHADOW_MUTATION_BLOCKED"))
        decision = self.risk.assess(request, self.store.portfolio(self.session_id))
        if not decision.approved:
            self.store.audit("ENTRY_REJECTED", details=decision.reason)
            return SubmissionResult(None, decision)
        identifier = str(
            uuid5(
                NAMESPACE_URL,
                ":".join(
                    (
                        self.store.mode,
                        request.strategy,
                        request.version,
                        request.session_id,
                        request.symbol,
                        "entry",
                    )
                ),
            )
        )
        intent = OrderIntent(
            intent_id=identifier,
            signal_id=request.signal_id,
            session_id=request.session_id,
            symbol=request.symbol,
            units=decision.units,
            entry_price=request.entry_price,
            stop_price=request.stop_price,
            state=OrderState.APPROVED,
            created_at=request.now,
            strategy=request.strategy,
            version=request.version,
            mode=self.store.mode,
            planned_risk=decision.planned_risk,
            estimated_cost=decision.estimated_cost,
        )
        intent, created = self.store.create_intent(intent)
        if not created:
            return SubmissionResult(intent, RiskDecision(False, "DUPLICATE_INTENT"), True)
        prepared = None
        if isinstance(self.broker, PreparingBroker):
            try:
                prepared = self.broker.prepare(intent)
            except RejectedBeforeSend as exc:
                self._reject_pre_send(intent, exc)
                return SubmissionResult(self.store.intent(intent.intent_id), decision)
            self.store.set_meta("prepared:" + intent.intent_id, json.dumps(prepared.metadata))
            self.store.audit("PREPARED", intent.intent_id)
        intent = self.store.transition(intent.intent_id, OrderState.SUBMITTING)
        self._send(intent, request.now, prepared)
        return SubmissionResult(self.store.intent(intent.intent_id), decision)

    def _reject_pre_send(self, intent: OrderIntent, exc: RejectedBeforeSend) -> None:
        current = self.store.intent(intent.intent_id)
        if (
            current.state not in {OrderState.APPROVED, OrderState.SUBMITTING}
            or current.filled_units
        ):
            raise LifecycleError("PRE_SEND_REJECTION_STATE_CONTRADICTION") from None
        self.store.transition(intent.intent_id, OrderState.REJECTED)
        self.store.pause(self.session_id)
        self.store.audit("REJECTED_PRE_SEND", intent.intent_id, str(exc))

    def _send(
        self, intent: OrderIntent, now: datetime, prepared: PreparedSubmission | None = None
    ) -> None:
        try:
            update = (
                prepared.send(intent)
                if prepared is not None
                else self.broker.submit(intent)
                if intent.kind == "entry"
                else self.broker.close(intent)
            )
            self._apply(update, now)
        except RejectedBeforeSend as exc:
            # Only the adapter's measured pre-dispatch failure can release reserves.
            self._reject_pre_send(intent, exc)
        except Exception:
            # An arbitrary exception may happen AFTER the external side effect. Never retry.
            current = self.store.intent(intent.intent_id)
            if current.state in ACTIVE_STATES and current.state != OrderState.UNKNOWN:
                self.store.transition(intent.intent_id, OrderState.UNKNOWN)
            self.store.pause(self.session_id)
            self.store.set_meta("reconciliation_ok", "false")
            self.store.audit("SUBMISSION_AMBIGUOUS", intent.intent_id)

    def _apply(self, update: BrokerOrder, now: datetime) -> None:
        intent = self.store.apply_broker_order(update, now)
        if intent.kind == "entry" and update.filled_units and update.position_id:
            position = self.store.position(update.position_id)
            _, incident = self.risk.post_fill_risk(
                position.units,
                position.average_entry,
                position.stop_price,
                position.planned_risk,
                update.protected,
            )
            if incident:
                self.store.pause(self.session_id)
                self.store.audit(incident, intent.intent_id)
                if not self._incident_management:
                    self._incident_management = True
                    try:
                        self.cancel_pending_entries()
                        self.close_owned(position.position_id, price=position.average_entry)
                    finally:
                        self._incident_management = False

    def reconcile(self) -> bool:
        self._require_started()
        clean = True
        # Query owned terminal orders too: cancellation and fill delivery may cross.
        for intent in self.store.intents():
            if intent.state in {OrderState.CREATED, OrderState.APPROVED, OrderState.REJECTED}:
                continue
            try:
                update = self.broker.query(intent.intent_id)
                if update is None:
                    if intent.state in ACTIVE_STATES:
                        if intent.state != OrderState.UNKNOWN:
                            self.store.transition(intent.intent_id, OrderState.UNKNOWN)
                        clean = False
                        self.store.audit("RECONCILIATION_UNRESOLVED", intent.intent_id)
                else:
                    self._apply(update, datetime.now(UTC))
                    if update.state == OrderState.UNKNOWN:
                        clean = False
            except Exception:
                clean = False
                self.store.audit("RECONCILIATION_FAILED", intent.intent_id)
        if any(i.state == OrderState.UNKNOWN for i in self.store.intents()):
            clean = False
        if any(not p.accounting_complete for p in self.store.positions(open_only=False)):
            clean = False
        self.store.set_meta("reconciliation_ok", str(clean).lower())
        if not clean:
            self.store.pause(self.session_id)
        self.store.audit("RECONCILIATION_COMPLETE", details="OK" if clean else "BLOCKED")
        return clean

    def cancel_pending_entries(self) -> None:
        self._require_started()
        for intent in self.store.intents():
            if intent.kind != "entry" or intent.state not in ACTIVE_STATES:
                continue
            if intent.state in {OrderState.CREATED, OrderState.APPROVED}:
                self.store.transition(intent.intent_id, OrderState.EXPIRED)
                continue
            try:
                intent = self.store.transition(intent.intent_id, OrderState.CANCEL_PENDING)
                self._apply(self.broker.cancel(intent), datetime.now(UTC))
            except Exception:
                current = self.store.intent(intent.intent_id)
                if current.state in ACTIVE_STATES and current.state != OrderState.UNKNOWN:
                    self.store.transition(intent.intent_id, OrderState.UNKNOWN)
                self.store.set_meta("reconciliation_ok", "false")
                self.store.pause(self.session_id)
                self.store.audit("CANCEL_AMBIGUOUS", intent.intent_id)

    def close_owned(
        self,
        position_id: str,
        price: Decimal | None = None,
        now: datetime | None = None,
    ) -> OrderIntent | None:
        self._require_started()
        if self.store.mode == "shadow":
            raise RuntimeError("BLOCKED: shadow cannot mutate trading")
        position = self.store.position(position_id)
        for old in self.store.intents():
            if old.kind == "close" and old.position_id == position_id:
                return old
        if position.units <= 0:
            return None
        if not position.accounting_complete:
            self.pause_entries()
            self.store.audit("CLOSE_BLOCKED_ACCOUNTING_PENDING", position.owner_intent_id)
            return None
        if any(
            i.kind == "entry"
            and i.intent_id == position.owner_intent_id
            and i.state in ACTIVE_STATES
            for i in self.store.intents()
        ):
            self.cancel_pending_entries()
            position = self.store.position(position_id)
            if any(
                i.intent_id == position.owner_intent_id and i.state in ACTIVE_STATES
                for i in self.store.intents()
            ):
                self.store.audit("CLOSE_BLOCKED_PENDING_ENTRY", position.owner_intent_id)
                return None
        at = now or datetime.now(UTC)
        executable_price = price or position.mark_price or position.average_entry
        intent = OrderIntent(
            intent_id=str(uuid5(NAMESPACE_URL, f"{self.store.mode}:close:{position_id}")),
            session_id=self.session_id,
            signal_id=f"close:{position_id}",
            symbol=position.symbol,
            units=position.units,
            entry_price=executable_price,
            stop_price=position.stop_price,
            state=OrderState.APPROVED,
            kind="close",
            position_id=position_id,
            mode=self.store.mode,
            created_at=at,
        )
        intent, created = self.store.create_intent(intent)
        if created:
            intent = self.store.transition(intent.intent_id, OrderState.SUBMITTING)
            self._send(intent, at)
        return self.store.intent(intent.intent_id)

    def flatten_owned(self) -> bool:
        self._require_started()
        self.pause_entries()
        self.cancel_pending_entries()
        for position in self.store.positions():
            self.close_owned(position.position_id)
        reconciled = self.reconcile()
        flat = (
            reconciled
            and not self.store.positions()
            and not any(i.state in ACTIVE_STATES for i in self.store.intents())
        )
        self.store.audit("FLAT_CONFIRMED" if flat else "RESIDUAL_EXPOSURE")
        return flat

    def tighten_stop(self, position_id: str, stop_price: Decimal) -> bool:
        self._require_started()
        position = self.store.position(position_id)
        if not stop_price.is_finite() or stop_price < position.stop_price:
            raise LifecycleError("STOP_WIDENING_BLOCKED")
        if self.store.mode == "shadow":
            raise RuntimeError("BLOCKED: shadow cannot modify protection")
        try:
            protected = self.broker.protect(position_id, stop_price)
        except Exception:
            protected = False
        if protected:
            self.store.set_protection(position_id, stop_price, True)
        else:
            self.pause_entries()
            self.store.audit("PROTECTION_FAILED", position.owner_intent_id)
            self.cancel_pending_entries()
            self.close_owned(position_id)
        return protected

    def enforce_daily_loss(self) -> bool:
        self._require_started()
        portfolio = self.store.portfolio(self.session_id)
        reached = portfolio.realized_pnl + portfolio.unrealized_pnl <= -(
            portfolio.reference_capital * self.risk.config.daily_loss_fraction
        )
        if reached:
            self.store.audit("DAILY_LOSS_LIMIT")
            self.flatten_owned()
        return reached

    def process_commands(self) -> int:
        self._require_started()
        count = 0
        actions = {
            "PAUSE_ENTRIES": self.pause_entries,
            "RECONCILE": self.reconcile,
            "CANCEL_PENDING_ENTRIES": self.cancel_pending_entries,
            "FLATTEN_OWNED": self.flatten_owned,
        }
        for command in self.store.pending_commands():
            try:
                outcome = actions[command["kind"]]()
                if outcome is False:
                    raise RuntimeError("CONTROL_OUTCOME_NOT_CONFIRMED")
                self.store.finish_command(command["command_id"], "DONE")
            except Exception:
                self.store.finish_command(command["command_id"], "BLOCKED")
                self.store.audit("CONTROL_COMMAND_BLOCKED")
            count += 1
        return count
