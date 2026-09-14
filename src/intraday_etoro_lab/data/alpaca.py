"""Offline Alpaca capture -> existing MarketDataProvider contract; no broker dependency."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from intraday_etoro_lab.data.alpaca_http import (
    BARS_PATH,
    ORIGIN,
    AlpacaDataError,
    HistoricalRequest,
    sha256,
)
from intraday_etoro_lab.data.calendar import calendar_version, session
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.domain import Bar, DataManifest, Instrument


def read_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_bytes(), parse_float=Decimal)
        if not isinstance(document, dict):
            raise ValueError
        return document
    except (ValueError, UnicodeError):
        raise AlpacaDataError("ALPACA_CAPTURE_JSON_INVALID") from None


def parse_time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("ALPACA_TIMESTAMP_ZONE_REQUIRED")
    return result.astimezone(UTC)


class AlpacaHistoricalProvider:
    """load() is offline. Acquisition and audit are explicit separate actions."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.capture: dict[str, Any] = {}
        self.audit: dict[str, Any] = {}

    def load(self) -> DataBundle:
        try:
            return self._load()
        except AlpacaDataError:
            raise
        except (ValueError, TypeError, KeyError, ArithmeticError, OSError):
            raise AlpacaDataError("ALPACA_CAPTURE_OR_BAR_INVALID") from None

    def _load(self) -> DataBundle:
        capture = read_document(self.directory / "capture.json")
        self.capture = capture
        if (
            capture["schema_version"] != "alpaca-capture-v1"
            or capture["status"] != "COMPLETE"
            or capture["origin"] != ORIGIN
            or capture["endpoint"] != BARS_PATH
            or capture["method"] != "GET"
            or capture["provider"] != "alpaca"
        ):
            raise AlpacaDataError("ALPACA_CAPTURE_INCOMPLETE_OR_WRONG_SOURCE")
        feed = capture["feed_requested"]
        if feed not in {"sip", "iex"} or capture["feed_effective"] not in {None, feed}:
            raise AlpacaDataError("ALPACA_FEED_IDENTITY_MISMATCH")
        request = HistoricalRequest(datetime.fromisoformat(capture["target"]).date(), feed)
        if capture["params"] != request.params():
            raise AlpacaDataError("ALPACA_QUERY_CONTRACT_MISMATCH")
        if capture["availability_class"] != "HISTORICAL_DOWNLOAD":
            raise AlpacaDataError("ALPACA_HISTORICAL_AVAILABILITY_REQUIRED")
        if capture["acquisition_class"] not in {"NETWORK_HTTP", "CONTRACT_TEST"}:
            raise AlpacaDataError("ALPACA_ACQUISITION_UNKNOWN")
        pages = capture["pages"]
        if not pages:
            raise AlpacaDataError("ALPACA_NO_PAGES")
        instrument = Instrument(
            symbol="AAPL", exchange="XNAS", currency="USD", asset_class="common_stock"
        )
        bars: dict[datetime, Bar] = {}
        originals: dict[datetime, dict[str, Any]] = {}
        received_times = []
        feed_observed = True
        outside = duplicates = raw_count = 0
        duplicate_times: set[datetime] = set()
        counts: list[int] = []
        vwaps: list[Decimal] = []
        token: str | None = None
        token_history: set[str] = set()
        last_time: datetime | None = None
        start = parse_time(request.params()["start"])
        end = parse_time(request.params()["end"])
        for index, page in enumerate(pages):
            if not re.fullmatch(r"page-[0-9]{3}\.json", page["file"]):
                raise AlpacaDataError("ALPACA_PAGE_PATH_INVALID")
            if page["file"] != f"page-{index:03d}.json":
                raise AlpacaDataError("ALPACA_PAGE_SEQUENCE_INVALID")
            expected = request.params() | ({"page_token": token} if token else {})
            if page["params"] != expected or page["feed_effective"] != feed:
                raise AlpacaDataError("ALPACA_PAGE_FEED_OR_QUERY_MISMATCH")
            path = self.directory / page["file"]
            if sha256(path) != page["sha256"]:
                raise AlpacaDataError("ALPACA_RAW_CHECKSUM_MISMATCH")
            doc = read_document(path)
            if doc.get("feed", feed) != feed or page["feed_echo"] not in {None, feed}:
                raise AlpacaDataError("ALPACA_FEED_IDENTITY_MISMATCH")
            # A query parameter is a contractual request, not a server observation.
            feed_observed &= doc.get("feed") == feed and page["feed_echo"] == feed
            token = doc["next_page_token"]
            if index < len(pages) - 1:
                if not isinstance(token, str) or not token or token in token_history:
                    raise AlpacaDataError("ALPACA_PAGINATION_INVALID")
                token_history.add(token)
            elif token is not None:
                raise AlpacaDataError("ALPACA_PAGINATION_INCOMPLETE")
            by_symbol = doc["bars"]
            if not isinstance(by_symbol, dict) or set(by_symbol) - {request.symbol}:
                raise AlpacaDataError("ALPACA_SYMBOL_MISMATCH")
            received = parse_time(page["received_at"])
            received_times.append(received)
            rows = by_symbol.get(request.symbol, [])
            if not isinstance(rows, list):
                raise AlpacaDataError("ALPACA_BARS_INVALID")
            for row in rows:
                raw_count += 1
                event = parse_time(row["t"])
                if not start <= event <= end:
                    raise AlpacaDataError("ALPACA_BAR_OUTSIDE_REQUEST")
                if last_time is not None and event < last_time:
                    raise AlpacaDataError("ALPACA_BARS_OUT_OF_ORDER")
                if event in originals:
                    if originals[event] != row:
                        raise AlpacaDataError("ALPACA_CONFLICTING_DUPLICATE")
                    duplicates += 1
                    duplicate_times.add(event)
                    continue
                last_time = event
                originals[event] = row
                bar = Bar(
                    instrument=instrument,
                    event_time=event,
                    received_at=received,
                    available_at=received,
                    source="alpaca",
                    final=True,
                    open=Decimal(str(row["o"])),
                    high=Decimal(str(row["h"])),
                    low=Decimal(str(row["l"])),
                    close=Decimal(str(row["c"])),
                    volume=Decimal(str(row["v"])),
                )
                if row.get("n") is not None:
                    if type(row["n"]) is not int or row["n"] < 0:
                        raise AlpacaDataError("ALPACA_TRADE_COUNT_INVALID")
                    counts.append(row["n"])
                if row.get("vw") is not None:
                    vwap = Decimal(str(row["vw"]))
                    if not vwap.is_finite() or vwap <= 0:
                        raise AlpacaDataError("ALPACA_VWAP_INVALID")
                    vwaps.append(vwap)
                try:
                    market = session(bar.session_date)
                except ValueError:
                    outside += 1
                    continue
                if not market.open <= event < market.close:
                    outside += 1
                    continue
                bars[event] = bar
        if not bars:
            raise AlpacaDataError("ALPACA_NO_REGULAR_BARS")
        ordered = tuple(bars[time] for time in sorted(bars))
        coverage: list[dict[str, Any]] = []
        for day in request.days:
            market = session(day)
            expected_times = {market.open + timedelta(minutes=i) for i in range(market.minutes)}
            missing = sorted(expected_times - bars.keys())
            session_reasons = []
            if missing:
                session_reasons.append("SESSION_GAPS")
            if expected_times & duplicate_times:
                session_reasons.append("DUPLICATE_BARS")
            if any(bars[t].volume == 0 for t in expected_times & bars.keys()):
                session_reasons.append("ZERO_VOLUME_BARS")
            coverage.append(
                {
                    "date": str(day),
                    "expected_minutes": market.minutes,
                    "early_close": market.minutes < 390,
                    "open": market.open.isoformat(),
                    "close": market.close.isoformat(),
                    "missing_count": len(missing),
                    "missing_timestamps": [value.isoformat() for value in missing],
                    "complete": not missing,
                    "valid": not session_reasons,
                    "reason_codes": session_reasons,
                    "gap_cause": "UNKNOWN_NO_HALT_EVIDENCE" if missing else None,
                    "first_five_complete": all(
                        market.open + timedelta(minutes=i) in bars for i in range(5)
                    ),
                }
            )
        synthetic = capture["acquisition_class"] == "CONTRACT_TEST"
        complete = sum(item["complete"] for item in coverage)
        zero_volume = sum(bar.volume == 0 for bar in ordered)
        reasons = []
        if complete != 21:
            reasons.append("SESSION_GAPS")
        if duplicates:
            reasons.append("DUPLICATE_BARS")
        if zero_volume:
            reasons.append("ZERO_VOLUME_BARS")
        if not synthetic and not feed_observed:
            reasons.append("FEED_UNVERIFIED")
        quality = {
            "status": "PASS" if not reasons else "BLOCKED",
            "reason_codes": reasons,
            "sessions_requested": len(request.days),
            "sessions_valid": sum(item["valid"] for item in coverage),
            "sessions_invalid": sum(not item["valid"] for item in coverage),
            "opening_windows_complete": sum(item["first_five_complete"] for item in coverage),
            "missing_bars": sum(item["missing_count"] for item in coverage),
            "duplicate_bars": duplicates,
            "out_of_session_bars": outside,
            "exclusions": [{"reason_code": "OUTSIDE_REGULAR_SESSION", "count": outside}]
            if outside
            else [],
            # These zeros are only emitted after every raw row passed the parser.
            "non_positive_prices": 0,
            "negative_volume": 0,
            "zero_volume_bars": zero_volume,
            "feed_mismatch": 0,
            "timezone_errors": 0,
            "hash": sha256(self.directory / "capture.json"),
            "provider": "alpaca",
            "feed": feed if feed_observed else None,
        }
        manifest = DataManifest(
            source="alpaca",
            synthetic=synthetic,
            volume_kind="synthetic_shares"
            if synthetic
            else "unknown"
            if not feed_observed
            else "consolidated_shares"
            if feed == "sip"
            else "venue_shares",
            adjustments="split_adjusted",
            license="Private audit only; redistribution not authorized",
            provenance="Alpaca bars; explicit feed on every request; capture/page SHA-256",
            sha256=sha256(self.directory / "capture.json"),
            coverage_start=ordered[0].event_time,
            coverage_end=ordered[-1].end_time,
            rows=len(ordered),
            calendar=calendar_version(),
            point_in_time_universe=False,
            availability_evidence="HTTP receipt per page; no contemporaneous observation",
            availability_kind="historical_download",
            acquired_at=min(received_times),
            feed_id=f"alpaca:{feed if feed_observed else 'unverified'}:1Min:split",
            quality=tuple(reasons),
        )
        self.audit = {
            "provider": "alpaca",
            "feed_requested": feed,
            "feed_effective": feed if feed_observed else None,
            "requested_feed": feed,
            "observed_feed": feed if feed_observed else None,
            "feed_verification": "PAYLOAD_ECHO_OBSERVED" if feed_observed else "FEED_UNVERIFIED",
            "feed_identity_basis": capture["feed_identity_basis"],
            "raw_bar_count": raw_count,
            "regular_bar_count": len(ordered),
            "exact_duplicates_removed": duplicates,
            "outside_regular_session": outside,
            "sessions": coverage,
            "complete_sessions": sum(item["complete"] for item in coverage),
            "data_quality": {"by_symbol": {request.symbol: quality}, "aggregate": quality},
            "trade_count_present": len(counts),
            "vwap_present": len(vwaps),
            "volume_semantics": "SIP eligible trade sizes in split-adjusted shares"
            if feed == "sip"
            else "IEX-only eligible trade sizes in split-adjusted shares",
            "timestamp_semantics": "UTC interval start; [t,t+1 minute)",
            "availability_class": "HISTORICAL_DOWNLOAD",
            "operationally_observed": False,
            "final_semantics": "Closed historical interval snapshot; corrections remain possible",
        }
        return DataBundle((instrument,), ordered, manifest, (request.target,))
