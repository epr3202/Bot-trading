"""Explicit synthetic evidence for A6; none of these records authorize a broker write."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx

from intraday_etoro_lab.brokers.authorization import BrokerBlocked, PreflightEvidence
from intraday_etoro_lab.brokers.etoro_demo import perform_preflight
from intraday_etoro_lab.brokers.transport import ME, PORTFOLIO, Credentials, GuardedTransport
from intraday_etoro_lab.domain import Instrument, Signal
from intraday_etoro_lab.risk import EntryRequest, InstrumentRules


def within(start: datetime, end: datetime, at: datetime) -> bool:
    return all(t.tzinfo is not None for t in (start, end, at)) and start <= at < end


@dataclass(frozen=True)
class DemoContext:
    identity: dict[str, Any]
    portfolio: dict[str, Any]
    observed_at: datetime
    expires_at: datetime
    source: str

    def verify(self, at: datetime) -> PreflightEvidence:
        if self.source != "SIMULATED" or not within(self.observed_at, self.expires_at, at):
            raise BrokerBlocked("A6_DEMO_CONTEXT_INVALID_OR_STALE")
        documents = {ME: self.identity, PORTFOLIO: self.portfolio}
        transport = GuardedTransport(
            Credentials("a6-synthetic-app", "a6-synthetic-user"),
            mode="shadow",
            session_id="a6-synthetic",
            config_hash="0" * 64,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=documents[request.url.path])
            ),
            now=lambda: at,
        )
        try:
            return perform_preflight(transport)
        finally:
            transport.close()


@dataclass(frozen=True)
class Eligibility:
    instrument: Instrument
    observed_at: datetime
    expires_at: datetime
    rules: InstrumentRules

    def reason(self, instrument: Instrument, at: datetime) -> str | None:
        if self.instrument != instrument or not instrument.stable_id:
            return "INSTRUMENT_IDENTITY_UNVERIFIED"
        if not within(self.observed_at, self.expires_at, at):
            return "ELIGIBILITY_STALE"
        if not self.rules.eligibility_verified:
            return "ELIGIBILITY_UNVERIFIED"
        # Financial rule validation remains in RiskEngine.
        return None


@dataclass(frozen=True)
class ExecutionQuote:
    instrument: Instrument
    bid: Decimal
    ask: Decimal
    observed_at: datetime
    decision_at: datetime
    source_price: Decimal

    def entry(
        self, signal: Signal, session_id: str, rules: InstrumentRules, window_end: datetime
    ) -> EntryRequest:
        if self.instrument != signal.instrument:
            raise BrokerBlocked("A6_QUOTE_IDENTITY_MISMATCH")
        return EntryRequest(
            signal_id=signal.signal_id,
            session_id=session_id,
            symbol=signal.instrument.symbol,
            available_at=signal.available_at,
            expires_at=signal.expires_at,
            now=self.decision_at,
            entry_price=self.ask,
            stop_price=signal.stop_price,
            bid=self.bid,
            ask=self.ask,
            quote_at=self.observed_at,
            reference_price=signal.reference_price,
            source_price=self.source_price,
            entry_window_open=self.decision_at < window_end,
            rules=rules,
            version=signal.strategy_version,
        )


@dataclass(frozen=True)
class SessionInputs:
    demo: DemoContext
    eligibility: dict[str, Eligibility]
    quotes: dict[str, ExecutionQuote]
    closing_quotes: dict[str, ExecutionQuote]
