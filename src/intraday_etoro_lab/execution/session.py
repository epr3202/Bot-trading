"""A6 session orchestration with a pinned durable local execution boundary."""

import hashlib
import json
from dataclasses import asdict, replace
from datetime import date, timedelta
from typing import Any

from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.simulator import SimulatorBroker
from intraday_etoro_lab.config import AppConfig
from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.execution.engine import Executor
from intraday_etoro_lab.execution.models import ACTIVE_STATES, OrderState
from intraday_etoro_lab.execution.session_inputs import SessionInputs, within
from intraday_etoro_lab.persistence.store import ExecutorLock, StateStore
from intraday_etoro_lab.risk import RiskEngine
from intraday_etoro_lab.strategies.orb import ORBStrategy


class DemoSessionRunner:
    """Synthetic Demo contract evidence, offline ledger; no external adapter injection."""

    def __init__(self, config: AppConfig, store: StateStore) -> None:
        self.config = AppConfig.model_validate(config.model_dump())
        if (
            store.mode != "offline"
            or self.config.mode.value != "offline"
            or self.config.order_submission_enabled
            or self.config.strategy.version != "ORB_RVOL_v1.0"
        ):
            raise BrokerBlocked("A6_REQUIRES_OFFLINE_FROZEN_STRATEGY")
        self.store = store
        # Construct the concrete local broker here. No factory/adapter/transport argument.
        self.broker = SimulatorBroker(store, costs=self.config.costs)

    def _event(self, sid: str, kind: str, **details: Any) -> None:
        self.store.audit(
            "A6_" + kind,
            details=json.dumps({"session_id": sid, **details}, sort_keys=True, default=str),
        )

    def run(self, bundle: DataBundle, day: date, inputs: SessionInputs) -> dict[str, Any]:
        # Actual bars, not a possibly stale manifest checksum, bind retries/recovery.
        digest = hashlib.sha256()
        for bar in bundle.bars:
            digest.update(bar.model_dump_json().encode())
        binding = hashlib.sha256(
            json.dumps(
                {
                    "config": self.config.config_hash,
                    "day": day.isoformat(),
                    "data": digest.hexdigest(),
                    "manifest": bundle.manifest.model_dump(mode="json"),
                    "instruments": [i.model_dump(mode="json") for i in bundle.instruments],
                    "inputs": asdict(inputs),
                },
                sort_keys=True,
                default=str,
            ).encode()
        ).hexdigest()
        sid = f"a6-{day.isoformat()}-{binding[:16]}"
        # Same OS lock primitive as the existing executor, covering context binding too.
        with ExecutorLock(self.store.path.with_suffix(".a6-owner.lock")):
            try:
                if type(self.broker) is not SimulatorBroker or self.broker.store is not self.store:
                    raise BrokerBlocked("A6_LOCAL_BROKER_REQUIRED")
                previous = self.store.get_meta("a6_binding")
                if previous not in (None, binding):
                    raise BrokerBlocked("A6_SESSION_INPUTS_CHANGED")
                if previous is None and (self.store.intents() or self.store.events()):
                    raise BrokerBlocked("A6_DEDICATED_DATABASE_REQUIRED")
                if (
                    not bundle.manifest.synthetic
                    or bundle.manifest.availability_kind != "synthetic"
                ):
                    raise BrokerBlocked("A6_EXPLICIT_SYNTHETIC_DATA_REQUIRED")
                if day not in bundle.evaluation_sessions:
                    raise BrokerBlocked("A6_SESSION_DATE_INVALID")
                market = session(day)
                demo = inputs.demo.verify(market.open)
                if self.config.risk.allocated_capital > demo.available_cash:
                    raise BrokerBlocked("A6_VIRTUAL_BUDGET_INVALID")
                self.store.set_meta("a6_binding", binding)
                self._event(
                    sid,
                    "SESSION_START",
                    source="SIMULATED",
                    external_writes=0,
                    config_hash=self.config.config_hash,
                    data_hash=digest.hexdigest(),
                )
                self._event(sid, "DEMO_CONTEXT_VERIFIED", source="MOCK_CONTRACT_ONLY")
                with Executor(
                    self.store, self.broker, RiskEngine(self.config.risk, self.config.costs), sid
                ) as executor:
                    if self.store.get_meta("reconciliation_ok") != "true":
                        raise BrokerBlocked("A6_RECOVERY_UNRESOLVED")
                    cached = self.store.get_meta("a6_result")
                    if cached is not None:
                        if self.store.positions() or any(
                            i.state in ACTIVE_STATES for i in self.store.intents()
                        ):
                            raise BrokerBlocked("A6_COMPLETED_SESSION_EXPOSURE_CHANGED")
                        self._event(sid, "RETRY_RECONCILED")
                        return dict(json.loads(cached))
                    eligible = []
                    for instrument in bundle.instruments:
                        if instrument.symbol in self.config.strategy.rs_benchmarks:
                            eligible.append(instrument)
                            continue
                        evidence = inputs.eligibility.get(instrument.symbol)
                        reason = (
                            evidence.reason(instrument, market.open)
                            if evidence
                            else "ELIGIBILITY_MISSING"
                        )
                        self._event(
                            sid,
                            "ELIGIBILITY",
                            symbol=instrument.symbol,
                            reason=reason or "VERIFIED_SIMULATED",
                            rules=asdict(evidence.rules) if evidence else None,
                            observed_at=evidence.observed_at if evidence else None,
                            expires_at=evidence.expires_at if evidence else None,
                        )
                        if reason is None:
                            eligible.append(instrument)
                    symbols = {i.symbol for i in eligible}
                    view = replace(
                        bundle,
                        instruments=tuple(eligible),
                        bars=tuple(b for b in bundle.bars if b.instrument.symbol in symbols),
                    )
                    decision = ORBStrategy(self.config.strategy).process_session(view, day)
                    self.store.set_meta("a6_strategy_decision", decision.model_dump_json())
                    self._event(
                        sid,
                        "SIGNALS" if decision.signals else "NO_SIGNAL",
                        count=len(decision.signals),
                        rejections=[r.model_dump(mode="json") for r in decision.rejections],
                    )
                    executor.arm_offline()
                    for signal in sorted(decision.signals, key=lambda s: (s.available_at, s.rank)):
                        symbol = signal.instrument.symbol
                        quote = inputs.quotes.get(symbol)
                        if quote is None:
                            raise BrokerBlocked("A6_EXECUTABLE_QUOTE_MISSING")
                        if not within(
                            inputs.demo.observed_at, inputs.demo.expires_at, quote.decision_at
                        ):
                            raise BrokerBlocked("A6_DEMO_CONTEXT_EXPIRED")
                        evidence = inputs.eligibility[symbol]
                        reason = evidence.reason(signal.instrument, quote.decision_at)
                        self._event(sid, "SIGNAL", signal=signal.model_dump(mode="json"))
                        if reason:
                            self._event(sid, "ELIGIBILITY_REJECTED", symbol=symbol, reason=reason)
                            continue
                        request = quote.entry(
                            signal,
                            sid,
                            evidence.rules,
                            market.open
                            + timedelta(minutes=self.config.strategy.entry_window_minutes),
                        )
                        outcome = executor.submit_entry(request)
                        self._event(
                            sid,
                            "RISK",
                            symbol=symbol,
                            signal_id=signal.signal_id,
                            decision=asdict(outcome.decision),
                            duplicate=outcome.duplicate,
                            intent_id=outcome.intent.intent_id if outcome.intent else None,
                        )
                        if outcome.intent:
                            self._event(
                                sid,
                                "SIMULATED_EXECUTION",
                                intent_id=outcome.intent.intent_id,
                                state=outcome.intent.state.value,
                            )
                            if outcome.intent.state == OrderState.EXPIRED:
                                raise BrokerBlocked("A6_RECOVERED_UNSENT_INTENT_EXPIRED")
                        if not executor.reconcile():
                            raise BrokerBlocked("A6_RECONCILIATION_UNRESOLVED")
                    executor.pause_entries()
                    # Full synthetic session close uses explicit supplied executable bids.
                    executor.cancel_pending_entries()
                    for position in self.store.positions():
                        quote = inputs.closing_quotes.get(position.symbol)
                        if (
                            quote is None
                            or quote.instrument != inputs.eligibility[position.symbol].instrument
                            or not within(market.flatten_at, market.close, quote.decision_at)
                            or quote.observed_at > quote.decision_at
                            or (quote.decision_at - quote.observed_at).total_seconds()
                            > self.config.risk.max_quote_age_seconds
                            or not quote.bid.is_finite()
                            or quote.bid <= 0
                        ):
                            raise BrokerBlocked("A6_CLOSING_QUOTE_INVALID")
                        executor.close_owned(position.position_id, quote.bid, quote.decision_at)
                    clean = executor.reconcile()
                    flat = not self.store.positions() and not any(
                        i.state in ACTIVE_STATES for i in self.store.intents()
                    )
                    self._event(sid, "RECONCILIATION", clean=clean, flat=flat)
                    if not clean or not flat:
                        raise BrokerBlocked("A6_RESIDUAL_EXPOSURE")
                    result = {
                        "status": "PASS",
                        "session_id": sid,
                        "source": "SIMULATED",
                        "strategy": self.config.strategy.version,
                        "signals": len(decision.signals),
                        "intents": len(self.store.intents()),
                        "flat": True,
                        "reconciled": True,
                        "external_writes": 0,
                        "external_reads": 0,
                        "entries_armed": False,
                        "a7": "NOT_IMPLEMENTED",
                    }
                    self.store.set_meta("a6_result", json.dumps(result, sort_keys=True))
                    self._event(
                        sid,
                        "SESSION_COMPLETE",
                        **{k: v for k, v in result.items() if k != "session_id"},
                    )
                    return result
            except Exception as exc:
                reason = str(exc) if isinstance(exc, BrokerBlocked) else "A6_INTERNAL_ERROR"
                self._event(sid, "SESSION_BLOCKED", reason=reason)
                return {
                    "status": "BLOCKED",
                    "session_id": sid,
                    "reason": reason,
                    "source": "SIMULATED",
                    "external_writes": 0,
                    "external_reads": 0,
                }
