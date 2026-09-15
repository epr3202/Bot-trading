"""Offline Massive capture reader implementing MarketDataProvider.load()."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from intraday_etoro_lab.data.calendar import calendar_version, session
from intraday_etoro_lab.data.massive_http import (
    SEMANTICS_VERSION,
    SOURCES,
    VOLUME_SEMANTICS,
    MassiveDataError,
    MassiveHistoricalRequest,
    parse_time,
    read_document,
    sha256,
    validate_page,
)
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.domain import Bar, DataManifest, Instrument


def event_time(value: Any) -> datetime:
    if type(value) is not int or value % 60000:
        raise MassiveDataError("TIMESTAMP_NOT_INTEGER_MINUTE_MILLISECONDS")
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=value)


class MassiveHistoricalProvider:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.capture: dict[str, Any] = {}
        self.audit: dict[str, Any] = {}

    def load(self) -> DataBundle:
        try:
            return self._load()
        except MassiveDataError:
            raise
        except (ValueError, TypeError, KeyError, ArithmeticError, OSError):
            raise MassiveDataError("CAPTURE_OR_OHLCV_INVALID") from None

    def _load(self) -> DataBundle:
        capture = read_document(self.directory / "capture.json")
        self.capture = capture
        request = MassiveHistoricalRequest(date.fromisoformat(capture["target"]))
        if (
            capture["schema_version"] != "massive-capture-v1"
            or capture["provider"] != "massive"
            or capture["method"] != "GET"
            or capture["status"] != "COMPLETE"
            or capture["endpoint"] != request.endpoint
            or capture["initial_url"] != request.url
            or capture["timeframe"] != "1m"
            or capture["timezone"] != "America/New_York"
            or capture["availability_class"] != "HISTORICAL_DOWNLOAD"
            or capture["latency"] is not None
            or capture["acquisition_class"] not in {"NETWORK_HTTP", "CONTRACT_TEST"}
            or not capture["pages"]
        ):
            raise MassiveDataError("CAPTURE_CONTRACT_INVALID_OR_INCOMPLETE")
        semantics = capture.get("semantics_version") == SEMANTICS_VERSION and capture.get(
            "sources"
        ) == list(SOURCES)
        instrument = Instrument(
            symbol="AAPL", exchange="XNAS", currency="USD", asset_class="common_stock"
        )
        bars: dict[datetime, Bar] = {}
        duplicates: set[datetime] = set()
        raw_count = duplicate_count = outside = 0
        seen: set[datetime] = set()
        previous: datetime | None = None
        receipts: list[datetime] = []
        expected_url: str | None = request.url
        seen_urls: set[str] = set()
        start, end = request.bounds
        for index, page in enumerate(capture["pages"]):
            if page["file"] != f"page-{index:03d}.json":
                raise MassiveDataError("PAGE_PATH_OR_SEQUENCE_INVALID")
            if page["url"] != expected_url or expected_url in seen_urls or expected_url is None:
                raise MassiveDataError("PAGINATION_CHAIN_INVALID")
            request.validate_url(expected_url)
            seen_urls.add(expected_url)
            path = self.directory / page["file"]
            if sha256(path) != page["sha256"]:
                raise MassiveDataError("RAW_CHECKSUM_MISMATCH")
            doc = read_document(path)
            validate_page(doc)
            expected_url = doc.get("next_url")
            if expected_url is not None:
                request.validate_url(expected_url)
            received = parse_time(page["received_at"])
            if (
                request.target >= received.astimezone(ZoneInfo("America/New_York")).date()
                or (receipts and received < receipts[-1])
                or received < parse_time(capture["started_at"])
                or received > parse_time(capture["finished_at"])
            ):
                raise MassiveDataError("HISTORICAL_RECEIPT_INVALID")
            receipts.append(received)
            for row in doc.get("results", []):
                raw_count += 1
                event = event_time(row["t"])
                if not start <= row["t"] <= end:
                    raise MassiveDataError("BAR_OUTSIDE_REQUEST")
                if previous is not None and event < previous:
                    raise MassiveDataError("TIMESTAMPS_OUT_OF_ORDER")
                previous = event
                # Validate even duplicate/out-of-session rows; never hide malformed OHLCV.
                bar = Bar(
                    instrument=instrument,
                    event_time=event,
                    received_at=received,
                    available_at=received,
                    source="massive",
                    final=True,
                    open=Decimal(str(row["o"])),
                    high=Decimal(str(row["h"])),
                    low=Decimal(str(row["l"])),
                    close=Decimal(str(row["c"])),
                    volume=Decimal(str(row["v"])),
                )
                if event in seen:
                    duplicate_count += 1
                    duplicates.add(event)
                    continue
                seen.add(event)
                try:
                    market = session(bar.session_date)
                except ValueError:
                    outside += 1
                    continue
                if not market.open <= event < market.close:
                    outside += 1
                    continue
                bars[event] = bar
        if expected_url is not None:
            raise MassiveDataError("PAGINATION_INCOMPLETE")
        if not bars:
            raise MassiveDataError("NO_REGULAR_BARS")
        coverage: list[dict[str, Any]] = []
        for day in request.days:
            market = session(day)
            expected = {market.open + timedelta(minutes=i) for i in range(market.minutes)}
            missing = sorted(expected - bars.keys())
            reasons = []
            if missing:
                reasons.append("SESSION_GAPS")
            if expected & duplicates:
                reasons.append("DUPLICATE_BARS")
            if any(bars[t].volume == 0 for t in expected & bars.keys()):
                reasons.append("ZERO_VOLUME_BARS")
            coverage.append(
                {
                    "date": str(day),
                    "open": market.open.isoformat(),
                    "close": market.close.isoformat(),
                    "early_close": market.minutes < 390,
                    "expected_minutes": market.minutes,
                    "missing_count": len(missing),
                    "missing_timestamps": [t.isoformat() for t in missing],
                    "gap_cause": "UNKNOWN_NO_HALT_EVIDENCE" if missing else None,
                    "opening_complete": all(
                        market.open + timedelta(minutes=i) in bars for i in range(5)
                    ),
                    "valid": not reasons,
                    "reason_codes": reasons,
                }
            )
        reasons = sorted({r for item in coverage for r in item["reason_codes"]})
        if duplicate_count and "DUPLICATE_BARS" not in reasons:
            reasons.append("DUPLICATE_BARS")
        synthetic = capture["acquisition_class"] == "CONTRACT_TEST"
        ordered = tuple(bars.values())
        quality = {
            "status": "PASS" if not reasons else "BLOCKED",
            "reason_codes": reasons,
            "sessions_requested": 21,
            "sessions_valid": sum(item["valid"] for item in coverage),
            "missing_bars": sum(item["missing_count"] for item in coverage),
            "duplicate_bars": duplicate_count,
            "outside_regular_session": outside,
            "non_positive_prices": 0,
            "negative_volume": 0,
            "timezone_errors": 0,
            "out_of_order": 0,
            "zero_volume_bars": sum(bar.volume == 0 for bar in ordered),
        }
        self.audit = {
            "provider": "massive",
            "endpoint": request.endpoint,
            "symbol": "AAPL",
            "plan_observed": None,
            "access_observed": "CONTRACT_TEST" if synthetic else "HISTORICAL_AGGREGATES_HTTP_200",
            "coverage": "100_percent_market" if semantics and not synthetic else None,
            "coverage_basis": "Documented consolidated EOD endpoint; not tick reconciliation",
            "timeframe": "1m",
            "timezone": "America/New_York",
            "sessions": coverage,
            "sessions_requested": 21,
            "sessions_valid": quality["sessions_valid"],
            "raw_bar_count": raw_count,
            "bar_count": len(ordered),
            "data_quality": quality,
            "volume_semantics": VOLUME_SEMANTICS,
            "volume_semantics_verified": semantics,
            "availability_class": "HISTORICAL_DOWNLOAD",
            "latency": None,
            "timestamp_semantics": "Unix ms interval start, [t,t+1m); UTC -> America/New_York",
        }
        manifest = DataManifest(
            source="massive",
            synthetic=synthetic,
            volume_kind="synthetic_shares"
            if synthetic
            else "consolidated_shares"
            if semantics
            else "unknown",
            adjustments="split_adjusted",
            license="Private research; redistribution not authorized",
            provenance="Massive consolidated historical aggregates; hashed immutable capture/pages",
            sha256=sha256(self.directory / "capture.json"),
            coverage_start=ordered[0].event_time,
            coverage_end=ordered[-1].end_time,
            rows=len(ordered),
            calendar=calendar_version(),
            point_in_time_universe=False,
            availability_kind="historical_download",
            availability_evidence="Page HTTP receipt; historical snapshot, revisions possible",
            acquired_at=min(receipts),
            feed_id="massive:consolidated:1m:split" if semantics else "massive:unverified:1m:split",
            quality=tuple(reasons + ([] if semantics else ["VOLUME_SEMANTICS_UNVERIFIED"])),
        )
        return DataBundle((instrument,), ordered, manifest, (request.target,))
