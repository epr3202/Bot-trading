import hashlib
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal

from pydantic import Field

from intraday_etoro_lab.data.calendar import session, sessions
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.domain import Bar, Instrument, Signal
from intraday_etoro_lab.domain.models import FrozenModel


class StrategyConfig(FrozenModel):
    version: Literal["ORB_RVOL_v0.1", "ORB_BASE_v0.1"] = "ORB_RVOL_v0.1"
    warmup_sessions: Literal[20] = 20
    opening_range_minutes: Literal[5] = 5
    min_previous_close: Decimal = Field(default=Decimal("10"), ge=0)
    min_average_dollar_volume: Decimal = Field(default=Decimal("50000000"), ge=0)
    min_rvol: Decimal = Field(default=Decimal("2"), gt=0)
    max_selected: int = Field(default=10, ge=1, le=10)
    entry_window_minutes: int = Field(default=60, ge=6, le=60)
    selection_wait_seconds: int = Field(default=2, ge=0, le=10)
    signal_ttl_seconds: int = Field(default=10, ge=1, le=10)
    relative_strength_enabled: Literal[False] = False
    regime_enabled: Literal[False] = False
    vwap_enabled: Literal[False] = False


class Candidate(FrozenModel):
    instrument: Instrument
    rank: int
    rvol: Decimal
    average_dollar_volume: Decimal
    or_high: Decimal
    or_low: Decimal
    or_open: Decimal
    or_close: Decimal
    opening_volume: Decimal
    historical_opening_volume: Decimal


class Rejection(FrozenModel):
    symbol: str
    reason: str
    at: datetime


class SessionDecision(FrozenModel):
    session_date: date
    selection_at: datetime
    evaluable_symbols: tuple[str, ...]
    selection: tuple[Candidate, ...]
    signals: tuple[Signal, ...]
    rejections: tuple[Rejection, ...]


class ORBStrategy:
    """Point-in-time selection; decisions use first finalized arrival, never revisions."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()

    def process_session(self, bundle: DataBundle, day: date) -> SessionDecision:
        config = self.config
        market = session(day)
        cutoff = market.open + timedelta(minutes=5, seconds=config.selection_wait_seconds)
        end_entries = market.open + timedelta(minutes=config.entry_window_minutes)
        grouped: dict[tuple[str, date], dict[datetime, Bar]] = defaultdict(dict)
        # Sorting by arrival explicitly retains the original decision history.
        for bar in sorted(bundle.bars, key=lambda item: (item.available_at, item.revision)):
            if bar.final and bar.revision == 0:
                grouped[(bar.instrument.symbol, bar.session_date)].setdefault(bar.event_time, bar)
        previous_days = sessions(day - timedelta(days=60), day - timedelta(days=1))[-20:]
        rejects: list[Rejection] = []
        evaluable: list[str] = []
        candidates: list[Candidate] = []

        def reject(symbol: str, reason: str, at: datetime = cutoff) -> None:
            rejects.append(Rejection(symbol=symbol, reason=reason, at=at))

        usable_volume = bundle.manifest.volume_kind in ("synthetic_shares", "consolidated_shares")
        for instrument in sorted(bundle.instruments, key=lambda item: item.symbol):
            symbol = instrument.symbol
            if not bundle.manifest.synthetic and bundle.manifest.availability_kind != "observed":
                reject(symbol, "OBSERVED_AVAILABILITY_REQUIRED")
                continue
            if (
                instrument.asset_class != "common_stock"
                or instrument.currency != "USD"
                or instrument.exchange not in ("XNYS", "XNAS")
                or symbol in ("SPY", "QQQ")
            ):
                reject(symbol, "UNIVERSE_INELIGIBLE")
                continue
            if not usable_volume or bundle.manifest.adjustments == "unknown":
                reject(symbol, "VOLUME_OR_ADJUSTMENTS_UNVERIFIED")
                continue
            daily: list[list[Bar]] = []
            for previous in previous_days:
                previous_market = session(previous)
                available = grouped.get((symbol, previous), {})
                expected = [
                    previous_market.open + timedelta(minutes=i)
                    for i in range(previous_market.minutes)
                ]
                if all(
                    stamp in available and available[stamp].available_at <= cutoff
                    for stamp in expected
                ):
                    daily.append([available[stamp] for stamp in expected])
            if len(daily) != config.warmup_sessions:
                reject(symbol, "INSUFFICIENT_VALID_WARMUP_20")
                continue
            # Approximation explicitly defined as sum(minute close * minute share volume).
            liquidity = sum(
                (sum((bar.close * bar.volume for bar in bars), Decimal(0)) for bars in daily),
                Decimal(0),
            ) / Decimal(20)
            if daily[-1][-1].close <= config.min_previous_close:
                reject(symbol, "PREVIOUS_CLOSE_TOO_LOW")
                continue
            if liquidity <= config.min_average_dollar_volume:
                reject(symbol, "DOLLAR_LIQUIDITY_TOO_LOW")
                continue
            opening_means = [sum((bar.volume for bar in bars[:5]), Decimal(0)) for bars in daily]
            if any(volume <= 0 for volume in opening_means):
                reject(symbol, "INVALID_HISTORICAL_OPENING_VOLUME")
                continue
            denominator = sum(opening_means, Decimal(0)) / Decimal(20)
            today = grouped.get((symbol, day), {})
            opening_times = [market.open + timedelta(minutes=i) for i in range(5)]
            if not all(
                stamp in today and today[stamp].available_at <= cutoff for stamp in opening_times
            ):
                reject(symbol, "OPENING_RANGE_MISSING_OR_LATE")
                continue
            opening = [today[stamp] for stamp in opening_times]
            current_volume = sum((bar.volume for bar in opening), Decimal(0))
            if current_volume <= 0:
                reject(symbol, "INVALID_OPENING_VOLUME")
                continue
            evaluable.append(symbol)
            rvol = current_volume / denominator
            if config.version == "ORB_RVOL_v0.1" and rvol < config.min_rvol:
                reject(symbol, "RVOL_BELOW_THRESHOLD")
                continue
            candidates.append(
                Candidate(
                    instrument=instrument,
                    rank=1,
                    rvol=rvol,
                    average_dollar_volume=liquidity,
                    or_high=max(bar.high for bar in opening),
                    or_low=min(bar.low for bar in opening),
                    or_open=opening[0].open,
                    or_close=opening[-1].close,
                    opening_volume=current_volume,
                    historical_opening_volume=denominator,
                )
            )
        # Base comparison ranks by the same liquidity universe without RVOL selection.
        candidates.sort(
            key=lambda item: (
                -item.rvol if config.version == "ORB_RVOL_v0.1" else Decimal(0),
                -item.average_dollar_volume,
                item.instrument.symbol,
            )
        )
        selected = tuple(
            candidate.model_copy(update={"rank": rank})
            for rank, candidate in enumerate(candidates[: config.max_selected], 1)
        )
        signals: list[Signal] = []
        for candidate in selected:
            symbol = candidate.instrument.symbol
            if candidate.or_close <= candidate.or_open:
                reject(symbol, "OPENING_RANGE_NOT_BULLISH")
                continue
            today_bars = sorted(
                grouped.get((symbol, day), {}).values(),
                key=lambda item: (item.available_at, item.event_time),
            )
            for bar in today_bars:
                if bar.event_time < market.open + timedelta(minutes=5):
                    continue
                if not cutoff <= bar.available_at < end_entries:
                    continue
                if bar.close <= candidate.or_high:
                    continue
                # Signal expires against original availability, even if an event loop is late.
                signal_id = hashlib.sha256(f"{config.version}|{day}|{symbol}".encode()).hexdigest()[
                    :24
                ]
                signals.append(
                    Signal(
                        signal_id=signal_id,
                        session_date=day,
                        instrument=candidate.instrument,
                        available_at=bar.available_at,
                        expires_at=bar.available_at + timedelta(seconds=config.signal_ttl_seconds),
                        reference_price=bar.close,
                        stop_price=candidate.or_low,
                        rank=candidate.rank,
                        rvol=candidate.rvol,
                        strategy_version=config.version,
                    )
                )
                break
        signals.sort(key=lambda item: (item.available_at, item.rank, item.instrument.symbol))
        return SessionDecision(
            session_date=day,
            selection_at=cutoff,
            evaluable_symbols=tuple(evaluable),
            selection=selected,
            signals=tuple(signals),
            rejections=tuple(rejects),
        )
