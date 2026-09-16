"""A6 synthetic demonstration only; never used as a fallback for external data."""

import hashlib
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.data.providers import DataBundle, FixtureProvider
from intraday_etoro_lab.domain import Instrument
from intraday_etoro_lab.execution.session_inputs import (
    DemoContext,
    Eligibility,
    ExecutionQuote,
    SessionInputs,
)
from intraday_etoro_lab.risk import InstrumentRules


def synthetic_session(*, no_signal: bool = False) -> tuple[DataBundle, date, SessionInputs]:
    original = FixtureProvider().load()
    instrument = original.instruments[0]
    stocks = [b for b in original.bars if b.instrument == instrument]
    bars = list(stocks)
    references = tuple(
        Instrument(symbol=s, asset_class="etf", stable_id=f"synthetic:{s}") for s in ("SPY", "QQQ")
    )
    for reference in references:
        for bar in stocks:
            bars.append(
                bar.model_copy(
                    update={
                        "instrument": reference,
                        "open": Decimal(100),
                        "close": Decimal(100),
                        "high": Decimal(101),
                        "low": Decimal(99),
                    }
                )
            )
    bars.sort(key=lambda b: (b.available_at, b.instrument.symbol))
    digest = hashlib.sha256()
    for bar in bars:
        digest.update(bar.model_dump_json().encode())
    manifest = original.manifest.model_copy(
        update={
            "rows": len(bars),
            "sha256": digest.hexdigest(),
            "provenance": "A6 synthetic-v1 plus flat synthetic SPY/QQQ reference bars",
        }
    )
    bundle = replace(
        original, instruments=(instrument, *references), bars=tuple(bars), manifest=manifest
    )
    day = bundle.evaluation_sessions[2 if no_signal else 0]
    market = session(day)

    def quote(event_at: object) -> ExecutionQuote:
        bar = next(b for b in stocks if b.event_time == event_at)
        return ExecutionQuote(
            instrument,
            bar.close - Decimal("0.01"),
            bar.close + Decimal("0.01"),
            bar.available_at,
            bar.available_at + timedelta(milliseconds=500),
            bar.close,
        )

    inputs = SessionInputs(
        DemoContext(
            {"demoCid": 42, "realCid": 99, "scopes": ["etoro-public:demo:read"]},
            {
                "clientPortfolio": {
                    "credit": 10000,
                    "positions": [],
                    "orders": [],
                    "mirrors": [],
                    "ordersForOpen": [],
                    "ordersForClose": [],
                }
            },
            market.open,
            market.close,
            "SIMULATED",
        ),
        {instrument.symbol: Eligibility(instrument, market.open, market.close, InstrumentRules())},
        {instrument.symbol: quote(market.open + timedelta(minutes=5))},
        {instrument.symbol: quote(market.flatten_at - timedelta(minutes=1))},
    )
    return bundle, day, inputs
