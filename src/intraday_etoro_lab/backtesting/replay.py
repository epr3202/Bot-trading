"""Logical-time views for historical research; never a market-data provider."""

import hashlib
import json
from bisect import bisect_right
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.domain import Bar
from intraday_etoro_lab.strategies.orb import ORBStrategy, SessionDecision

POLICY = "replay_as_of_v1"
BAR_CLOSE_SEMANTICS = "unix_ms_interval_start_plus_60s"


@dataclass(frozen=True)
class ReplayRecord:
    original: Bar
    available_at: datetime
    availability_basis: str


class ReplayAsOf:
    """Expose only immutable prefixes; original receipts and provenance stay intact.

    An explicit publication map, when supplied, is authoritative for its keys.
    Missing keys require documented bar-close semantics; HTTP download receipt is
    not a publication timestamp. Equal-time arrivals become visible atomically.
    """

    def __init__(
        self,
        bundle: DataBundle,
        *,
        bar_close_semantics: str | None = None,
        publication_times: dict[tuple[str, datetime], datetime] | None = None,
    ) -> None:
        if bundle.manifest.synthetic or bundle.manifest.availability_kind != "historical_download":
            raise ValueError("REPLAY_REQUIRES_HISTORICAL_PROVENANCE")
        if bar_close_semantics not in (None, BAR_CLOSE_SEMANTICS):
            raise ValueError("REPLAY_TEMPORAL_SEMANTICS_UNSUPPORTED")
        if bundle.evaluation_sessions != tuple(sorted(set(bundle.evaluation_sessions))):
            raise ValueError("REPLAY_SESSION_ORDER_INVALID")
        instruments = {item.symbol: item for item in bundle.instruments}
        if len(instruments) != len(bundle.instruments) or not bundle.bars:
            raise ValueError("REPLAY_AMBIGUOUS_OR_EMPTY_DATA")
        explicit = publication_times or {}
        seen: set[tuple[str, datetime]] = set()
        records = []
        for original in bundle.bars:
            bar = Bar.model_validate(original.model_dump())
            key = (bar.instrument.symbol, bar.event_time)
            if key in seen or bar.revision != 0 or not bar.final:
                raise ValueError("REPLAY_DUPLICATE_OR_REVISION_UNSUPPORTED")
            if instruments.get(key[0]) != bar.instrument:
                raise ValueError("REPLAY_INSTRUMENT_IDENTITY_MISMATCH")
            seen.add(key)
            if key in explicit:
                available = explicit[key]
                if available.tzinfo is None or available.utcoffset() is None:
                    raise ValueError("REPLAY_PUBLICATION_TIMEZONE_REQUIRED")
                available = available.astimezone(UTC)
                basis = "explicit_publication_timestamp"
            elif bar_close_semantics == BAR_CLOSE_SEMANTICS:
                available = bar.end_time
                basis = "documented_bar_close"
            else:
                raise ValueError("REPLAY_AVAILABILITY_CONTRACT_MISSING")
            if available < bar.end_time:
                raise ValueError("REPLAY_PUBLICATION_BEFORE_BAR_CLOSE")
            records.append(ReplayRecord(bar, available, basis))
        if set(explicit) - seen:
            raise ValueError("REPLAY_UNKNOWN_PUBLICATION_RECORD")
        self.original = bundle
        self.records = tuple(
            sorted(
                records,
                key=lambda r: (r.available_at, r.original.event_time, r.original.instrument.symbol),
            )
        )
        self._times = tuple(record.available_at for record in self.records)
        self._projected: list[Bar] = []
        self._clock: datetime | None = None
        self._availability = {
            (record.original.instrument.symbol, record.original.event_time): record.available_at
            for record in self.records
        }

    def available_at(self, bar: Bar) -> datetime:
        return self._availability[(bar.instrument.symbol, bar.event_time)]

    def metadata(self) -> dict[str, Any]:
        return {
            "availability_policy": POLICY,
            "dataset_provenance": "historical_download",
            "dataset_manifest": self.original.manifest.model_dump(mode="json"),
            "available_at_semantics": {
                "priority": ["explicit_publication_timestamp", "documented_bar_close"],
                "bar_close": BAR_CLOSE_SEMANTICS,
                "basis_counts": {
                    basis: sum(r.availability_basis == basis for r in self.records)
                    for basis in sorted({r.availability_basis for r in self.records})
                },
                "observed_means": "visible in logical replay; not contemporaneous HTTP receipt",
                "received_at_in_view": (
                    "logical delivery at available_at; original receipt retained in record"
                ),
            },
            "timezone": "UTC",
            "session_timezone": "America/New_York",
            "ordering": ["available_at", "event_time", "symbol"],
            "availability_schedule_sha256": hashlib.sha256(
                json.dumps(
                    [
                        [
                            r.original.instrument.symbol,
                            r.original.event_time.isoformat(),
                            r.available_at.isoformat(),
                            r.availability_basis,
                        ]
                        for r in self.records
                    ],
                    separators=(",", ":"),
                ).encode()
            ).hexdigest(),
        }

    def view(self, replay_clock: datetime) -> DataBundle:
        if replay_clock.tzinfo is None or replay_clock.utcoffset() is None:
            raise ValueError("REPLAY_CLOCK_TIMEZONE_REQUIRED")
        replay_clock = replay_clock.astimezone(UTC)
        if self._clock is not None and replay_clock < self._clock:
            raise ValueError("REPLAY_CLOCK_CANNOT_REWIND")
        self._clock = replay_clock
        count = bisect_right(self._times, replay_clock)
        for record in self.records[len(self._projected) : count]:
            # Only now is an observed projection constructed. Never mutate raw bars.
            fields = record.original.model_dump()
            fields.update(received_at=record.available_at, available_at=record.available_at)
            self._projected.append(Bar.model_validate(fields))
        manifest = self.original.manifest.model_copy(
            update={
                "availability_kind": "observed",
                "provenance": "historical_download; " + self.original.manifest.provenance,
                "availability_evidence": (
                    f"{POLICY}; visible iff available_at <= {replay_clock.isoformat()}"
                ),
            }
        )
        return DataBundle(
            tuple(sorted(self.original.instruments, key=lambda item: item.symbol)),
            tuple(self._projected),
            manifest,
            self.original.evaluation_sessions,
        )

    def process_session(self, strategy: ORBStrategy, day: date) -> SessionDecision:
        market = session(day)
        cutoff = market.open + timedelta(minutes=5, seconds=strategy.config.selection_wait_seconds)
        end = market.open + timedelta(minutes=strategy.config.entry_window_minutes)
        initial = strategy.process_session(self.view(cutoff), day)
        signals = {signal.instrument.symbol: signal for signal in initial.signals}
        rejections = list(initial.rejections)
        terminal = set(signals) | {r.symbol for r in rejections}
        selected = {item.instrument.symbol for item in initial.selection}
        for clock in sorted({at for at in self._times if cutoff < at < end}):
            if selected <= terminal:
                break
            decision = strategy.process_session(self.view(clock), day)
            if (
                decision.selection != initial.selection
                or decision.evaluable_symbols != initial.evaluable_symbols
            ):
                raise ValueError("REPLAY_SELECTION_CHANGED_AFTER_CUTOFF")
            for signal in decision.signals:
                symbol = signal.instrument.symbol
                if symbol not in terminal:
                    if signal.available_at != clock:
                        raise ValueError("REPLAY_RETROACTIVE_SIGNAL_BLOCKED")
                    signals[symbol] = signal
                    terminal.add(symbol)
            for rejection in decision.rejections:
                if rejection.symbol not in terminal:
                    rejections.append(rejection)
                    terminal.add(rejection.symbol)
        return initial.model_copy(
            update={
                "signals": tuple(
                    sorted(
                        signals.values(),
                        key=lambda s: (s.available_at, s.rank, s.instrument.symbol),
                    )
                ),
                "rejections": tuple(rejections),
            }
        )
