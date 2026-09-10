import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.domain import Bar, DataManifest, Instrument

REQUIRED_COLUMNS = {
    "symbol",
    "exchange",
    "currency",
    "asset_class",
    "event_time",
    "received_at",
    "available_at",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "source",
    "final",
}


def quality_issues(bars: tuple[Bar, ...]) -> tuple[str, ...]:
    issues: set[str] = set()
    seen: set[tuple[str, datetime]] = set()
    grouped: dict[tuple[str, date], set[datetime]] = {}
    latest: dict[str, datetime] = {}
    for bar in bars:
        symbol = bar.instrument.symbol
        key = (symbol, bar.event_time)
        if key in seen:
            issues.add("DUPLICATE_OR_REVISION")
        seen.add(key)
        if symbol in latest and bar.event_time < latest[symbol]:
            issues.add("OUT_OF_ORDER")
        latest[symbol] = bar.event_time
        if bar.revision:
            issues.add("LATE_REVISION")
        if not bar.final:
            issues.add("INCOMPLETE_BAR")
        try:
            market = session(bar.session_date)
        except ValueError:
            issues.add("NON_SESSION_DATA")
            continue
        if not market.open <= bar.event_time < market.close:
            issues.add("OUTSIDE_REGULAR_SESSION")
            continue
        grouped.setdefault((symbol, bar.session_date), set()).add(bar.event_time)
    for (_symbol, day), timestamps in grouped.items():
        if len(timestamps) != session(day).minutes:
            issues.add("SESSION_GAPS")
    return tuple(sorted(issues))


def import_market_data(path: Path, manifest_path: Path) -> DataBundle:
    """Read-only import. Manifest checksum pins the raw bytes; no filling or rewriting."""
    metadata: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = DataManifest.model_validate(metadata)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if manifest.sha256 != digest:
        raise ValueError("CHECKSUM_MISMATCH: raw import differs from manifest")
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    elif path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
    else:
        raise ValueError("Only .csv and .parquet imports are supported")
    if missing := REQUIRED_COLUMNS - set(frame.columns):
        raise ValueError(f"SCHEMA_MISSING_COLUMNS: {sorted(missing)}")
    instruments: dict[str, Instrument] = {}
    bars: list[Bar] = []
    for record in frame.to_dict(orient="records"):
        raw = {str(key): value for key, value in record.items()}
        instrument = Instrument.model_validate(
            {key: raw[key] for key in ("symbol", "exchange", "currency", "asset_class")}
        )
        if instrument.symbol in instruments and instruments[instrument.symbol] != instrument:
            raise ValueError("AMBIGUOUS_INSTRUMENT: symbol maps to multiple instruments")
        instruments[instrument.symbol] = instrument
        values = {
            key: raw[key]
            for key in (
                "event_time",
                "received_at",
                "available_at",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "source",
                "final",
            )
        }
        values["instrument"] = instrument
        values["revision"] = raw.get("revision", 0)
        bars.append(Bar.model_validate(values))
    if len(bars) != manifest.rows or not bars:
        raise ValueError("MANIFEST_ROW_COUNT_MISMATCH")
    if any(bar.source != manifest.source for bar in bars):
        raise ValueError("MANIFEST_SOURCE_MISMATCH")
    if (
        min(bar.event_time for bar in bars) != manifest.coverage_start
        or max(bar.end_time for bar in bars) != manifest.coverage_end
    ):
        raise ValueError("MANIFEST_COVERAGE_MISMATCH")
    issues = quality_issues(tuple(bars))
    manifest = manifest.model_copy(
        update={"quality": tuple(sorted(set(manifest.quality + issues)))}
    )
    days = sorted({bar.session_date for bar in bars})
    return DataBundle(tuple(instruments.values()), tuple(bars), manifest, tuple(days[20:]))
