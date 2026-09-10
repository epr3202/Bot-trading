import hashlib
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Protocol

from intraday_etoro_lab.data.calendar import session, sessions
from intraday_etoro_lab.domain import Bar, DataManifest, Instrument


@dataclass(frozen=True)
class DataBundle:
    instruments: tuple[Instrument, ...]
    bars: tuple[Bar, ...]
    manifest: DataManifest
    evaluation_sessions: tuple[date, ...]


class MarketDataProvider(Protocol):
    def load(self) -> DataBundle: ...


class FixtureProvider:
    """Versioned algorithmic fixture: twenty warmups plus three evaluation days."""

    def load(self) -> DataBundle:
        days = sessions(date(2025, 10, 23), date(2025, 11, 26))[:23]
        instruments = tuple(
            Instrument(symbol=symbol, stable_id=f"synthetic:{symbol}")
            for symbol in ("SIMA", "SIMB", "SIMC")
        )
        bars: list[Bar] = []
        digest = hashlib.sha256()
        for day_index, day in enumerate(days):
            market = session(day)
            for instrument_index, instrument in enumerate(instruments):
                base = Decimal(100 + 20 * instrument_index)
                for minute in range(market.minutes):
                    offset = Decimal(min(minute, 4)) / Decimal(10)
                    opening = base + offset
                    closing = opening + Decimal("0.10")
                    low = opening - Decimal("0.20")
                    high = closing + Decimal("0.20")
                    volume = Decimal(2500)
                    if day_index >= 20 and minute < 5:
                        # Third day is an explicit no-selection session.
                        multiplier = (3, 2, 1)[instrument_index] if day_index < 22 else 1
                        volume *= multiplier
                    if day_index >= 20 and minute >= 5:
                        opening = base + Decimal("0.85")
                        closing = base + Decimal("0.90")
                        high = closing + Decimal("0.10")
                        low = opening - Decimal("0.05")
                        if instrument_index == 1 and minute >= 15:
                            opening = base - Decimal("0.30")
                            closing = base - Decimal("0.25")
                            high, low = closing + Decimal("0.10"), opening - Decimal("0.10")
                        elif minute >= 30:
                            opening = base + Decimal("1.50")
                            closing = base + Decimal("1.55")
                            high, low = closing + Decimal("0.10"), opening - Decimal("0.10")
                    event_time = market.open + timedelta(minutes=minute)
                    received = event_time + timedelta(minutes=1, milliseconds=200)
                    bar = Bar(
                        instrument=instrument,
                        event_time=event_time,
                        received_at=received,
                        available_at=received,
                        open=opening,
                        high=high,
                        low=low,
                        close=closing,
                        volume=volume,
                        source="synthetic-v1",
                    )
                    bars.append(bar)
                    digest.update(bar.model_dump_json().encode())
        bars.sort(key=lambda bar: (bar.available_at, bar.instrument.symbol, bar.revision))
        manifest = DataManifest(
            source="synthetic-v1",
            synthetic=True,
            volume_kind="synthetic_shares",
            adjustments="unadjusted",
            license="Generated locally; no market data license required",
            provenance="FixtureProvider v1: deterministic arithmetic; no actual securities",
            sha256=digest.hexdigest(),
            coverage_start=min(bar.event_time for bar in bars),
            coverage_end=max(bar.end_time for bar in bars),
            rows=len(bars),
            availability_evidence="Synthetic final bars become available 200ms after close",
            quality=("SYNTHETIC — NO EVIDENCE OF PROFITABILITY", "NO_POINT_IN_TIME_UNIVERSE"),
        )
        return DataBundle(instruments, tuple(bars), manifest, days[20:])
