"""Audit saved Market Data responses without network access or strategy changes.

Input: acquisition.json and untouched MCP response bodies. Output must be a new
directory. Historical receipt is never backdated to the candle event timestamp.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.market_data import EtoroMarketDataProvider
from intraday_etoro_lab.brokers.transport import Credentials, GuardedTransport
from intraday_etoro_lab.data.calendar import calendar_version, session, sessions
from intraday_etoro_lab.data.importer import audit_bundle, import_market_data
from intraday_etoro_lab.strategies.orb import ORBStrategy

NY = ZoneInfo("America/New_York")
INSUFFICIENT = "ETORO_MARKET_DATA_INSUFFICIENT_FOR_RVOL"
SAFETY = {
    "entries_armed": False,
    "external_mutations": "DISABLED",
    "order_submission_enabled": False,
    "etoro_demo_write": "NOT_TESTED",
    "writes": 0,
}


def stamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("TIMESTAMP_ZONE_REQUIRED")
    return result.astimezone(UTC)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)


def save_json(path: Path, payload: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, default=str, ensure_ascii=False, indent=2)
        stream.write("\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candle_rows(
    document: dict[str, Any], interval: str, instrument_id: int
) -> list[dict[str, Any]]:
    if document["interval"] != interval or len(document["candles"]) != 1:
        raise ValueError("CANDLE_GROUP_OR_INTERVAL_MISMATCH")
    group = document["candles"][0]
    if group["instrumentId"] != instrument_id:
        raise ValueError("CANDLE_IDENTITY_MISMATCH")
    rows = group["candles"]
    if not rows or any(row["instrumentID"] != instrument_id for row in rows):
        raise ValueError("CANDLE_IDENTITY_OR_EMPTY_RESPONSE")
    return rows


def analyze_minutes(
    rows: list[dict[str, Any]], received_at: datetime
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Independent raw-value arithmetic; no calls to ORBStrategy for the calculation."""
    normalized = []
    for row in rows:
        time = stamp(row["fromDate"])
        values = {key: Decimal(str(row[key])) for key in ("open", "high", "low", "close", "volume")}
        if any(not value.is_finite() for value in values.values()):
            raise ValueError("NONFINITE_OHLCV")
        if min(values[key] for key in ("open", "high", "low", "close")) <= 0:
            raise ValueError("NONPOSITIVE_PRICE")
        if values["volume"] < 0 or values["high"] < max(values["open"], values["close"]):
            raise ValueError("INVALID_OHLCV")
        if values["low"] > min(values["open"], values["close"]) or time.second or time.microsecond:
            raise ValueError("INVALID_OHLC_OR_MINUTE_ALIGNMENT")
        normalized.append({"event_time": time, **values})
    times = [row["event_time"] for row in normalized]
    duplicates = {time for time, count in Counter(times).items() if count > 1}
    regular = []
    outside = 0
    unfinished = 0
    for row in normalized:
        time = row["event_time"]
        try:
            market = session(time.astimezone(NY).date())
        except ValueError:
            outside += 1
            continue
        if not market.open <= time < market.close:
            outside += 1
        elif time + timedelta(minutes=1) > received_at:
            unfinished += 1
        else:
            regular.append(row)
    if not regular:
        raise ValueError("NO_COMPLETED_REGULAR_MINUTES")
    regular.sort(key=lambda row: row["event_time"])
    days = sorted({row["event_time"].astimezone(NY).date() for row in regular})
    by_time = {row["event_time"]: row for row in regular if row["event_time"] not in duplicates}
    session_audits = []
    for day in days:
        market = session(day)
        expected = {market.open + timedelta(minutes=i) for i in range(market.minutes)}
        present = expected & by_time.keys()
        opening = {market.open + timedelta(minutes=i) for i in range(5)}
        elapsed = {time for time in expected if time + timedelta(minutes=1) <= received_at}
        covered = {time for time in elapsed if min(times) <= time <= max(times)}
        session_audits.append(
            {
                "day": str(day),
                "open_utc": market.open,
                "close_utc": market.close,
                "expected_minutes": len(expected),
                "observed_completed_minutes": len(present),
                "missing_minutes": len(expected - present),
                "complete": present == expected,
                "elapsed_minutes_expected": len(elapsed),
                "missing_elapsed_minutes": len(elapsed - present),
                "gaps_within_returned_window": len(covered - present),
                "first_five_complete": opening <= present,
                "first_missing_minutes": sorted(expected - present)[:5],
            }
        )
    day = days[-1]
    market = session(day)
    prior = sessions(day - timedelta(days=60), day - timedelta(days=1))[-20:]
    full_days = {entry["day"] for entry in session_audits if entry["complete"]}
    opening_sums = []
    for previous in prior:
        opening = [session(previous).open + timedelta(minutes=i) for i in range(5)]
        if all(time in by_time for time in opening):
            opening_sums.append(sum((by_time[time]["volume"] for time in opening), Decimal(0)))
    today_times = [market.open + timedelta(minutes=i) for i in range(5)]
    opening_rows = [by_time[time] for time in today_times if time in by_time]
    opening_complete = len(opening_rows) == 5
    numerator = (
        sum((row["volume"] for row in opening_rows), Decimal(0)) if opening_complete else None
    )
    denominator = (
        sum(opening_sums, Decimal(0)) / Decimal(20)
        if len(opening_sums) == 20 and all(value > 0 for value in opening_sums)
        else None
    )
    rvol = numerator / denominator if numerator is not None and denominator is not None else None
    volumes = [row["volume"] for row in normalized]
    report = {
        "rows": len(rows),
        "first_event_utc": min(times),
        "last_event_utc": max(times),
        "ordered_ascending": times == sorted(times),
        "duplicate_timestamps": len(duplicates),
        "outside_regular_session": outside,
        "unfinished_regular_minutes": unfinished,
        "regular_completed_rows": len(regular),
        "sessions": session_audits,
        "volume": {
            "meaning": "unknown",
            "documented_description": "Trading volume during the candle period",
            "consolidated_market_volume_verified": False,
            "min": min(volumes),
            "max": max(volumes),
            "sum": sum(volumes, Decimal(0)),
            "zero_count": sum(value == 0 for value in volumes),
            "noninteger_count": sum(value != value.to_integral_value() for value in volumes),
            "regular_completed_zero_count": sum(row["volume"] == 0 for row in regular),
        },
        "history": {
            "required_prior_sessions": [str(value) for value in prior],
            "complete_prior_sessions": sum(str(value) in full_days for value in prior),
            "prior_first_five_windows": len(opening_sums),
            "required_prior_count": 20,
            "evaluation_day": str(day),
            "evaluation_complete": str(day) in full_days,
            "minimum_full_regular_minutes_for_21_sessions": sum(session(d).minutes for d in prior)
            + market.minutes,
        },
        "independent": {
            "evaluation_day": str(day),
            "opening_complete": opening_complete,
            "opening_rows": opening_rows,
            "ORH": max(row["high"] for row in opening_rows) if opening_complete else None,
            "ORL": min(row["low"] for row in opening_rows) if opening_complete else None,
            "opening_volume_raw_units": numerator,
            "historical_mean_raw_units": denominator,
            "RVOL_arithmetic_only": rvol,
            "RVOL_strategy_valid": False,
            "limitations": [
                "VOLUME_SEMANTICS_UNKNOWN",
                "HISTORICAL_DOWNLOAD_NOT_OBSERVED_AT_OPEN",
                "ADJUSTMENTS_UNKNOWN",
                "NO_FINALITY_GUARANTEE",
            ],
        },
    }
    return report, regular


def audit(raw: Path, output: Path) -> dict[str, Any]:
    acquisition = read_json(raw / "acquisition.json")
    hashes = {path.name: digest(path) for path in sorted(raw.glob("*.json"))}
    records = {item["name"]: item for item in acquisition["records"]}
    if any(item["status_code"] != 200 or item["body_truncated"] for item in records.values()):
        raise ValueError("INCOMPLETE_OR_FAILED_ACQUISITION")
    instruments = read_json(raw / "instruments.json")["results"]
    if len(instruments) != 1 or instruments[0]["symbol"] != "AAPL":
        raise ValueError("EXPECTED_UNAMBIGUOUS_AAPL_SAMPLE")
    instrument = instruments[0]
    instrument_id = instrument["instrumentId"]
    asc = read_json(raw / "candles-asc.json")
    rows = candle_rows(asc, "OneMinute", instrument_id)
    received = stamp(records["candles-asc"]["received_at"])
    report, regular = analyze_minutes(rows, received)
    report["volume"]["group_total"] = asc["candles"][0]["volume"]
    report["volume"]["group_equals_sum_of_minutes"] = (
        asc["candles"][0]["volume"] == report["volume"]["sum"]
    )
    desc = candle_rows(read_json(raw / "candles-desc.json"), "OneMinute", instrument_id)
    repeats = candle_rows(read_json(raw / "recent-repeat.json"), "OneMinute", instrument_id)
    primary = {row["fromDate"]: row for row in rows}
    report["direction_comparison"] = {
        "same_timestamp_set": set(primary) == {row["fromDate"] for row in desc},
        "descending_order": [row["fromDate"] for row in desc]
        == sorted((row["fromDate"] for row in desc), reverse=True),
        "same_values": all(primary.get(row["fromDate"]) == row for row in desc),
        "conclusion": "direction sorts results; no historical cursor documented",
    }
    report["repeat_observation"] = {
        "overlapping_rows": sum(row["fromDate"] in primary for row in repeats),
        "changed_rows": [
            row["fromDate"]
            for row in repeats
            if row["fromDate"] in primary and primary[row["fromDate"]] != row
        ],
        "finality": "unknown; elapsed interval does not certify immutable final version",
    }
    daily = candle_rows(read_json(raw / "daily.json"), "OneDay", instrument_id)
    report["daily_history"] = {
        "rows": len(daily),
        "first_label": min(row["fromDate"] for row in daily),
        "last_label": max(row["fromDate"] for row in daily),
        "substitutes_for_first_five_minutes": False,
    }
    quote_doc = read_json(raw / "quote.json")
    quote = quote_doc["results"][0]
    if quote["instrumentId"] != instrument_id:
        raise ValueError("QUOTE_IDENTITY_MISMATCH")
    quote_time = datetime.fromisoformat(quote["date"])
    no_zone = quote_time.tzinfo is None
    # The rates contract explicitly states UTC; preserve the missing offset as a defect.
    quote_time = quote_time.replace(tzinfo=UTC) if no_zone else quote_time.astimezone(UTC)
    report["quote"] = {
        **quote,
        "interpreted_event_utc": quote_time,
        "missing_explicit_offset": no_zone,
        "interpretation_basis": "getRates schema documents date as UTC; raw text preserved",
        "received_at": records["quote"]["received_at"],
        "age_seconds_at_tool_return": (
            stamp(records["quote"]["received_at"]) - quote_time
        ).total_seconds(),
        "bid_ask_valid": Decimal(0) < quote["bid"] <= quote["ask"],
    }
    output.mkdir(parents=True, exist_ok=False)
    csv_path = output / "regular-minutes.csv"
    with csv_path.open("x", encoding="utf-8", newline="") as stream:
        names = [
            "symbol",
            "exchange",
            "currency",
            "asset_class",
            "broker_id",
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
        ]
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader()
        for row in regular:
            writer.writerow(
                {
                    **row,
                    "symbol": "AAPL",
                    "exchange": "XNAS",
                    "currency": "USD",
                    "asset_class": "common_stock",
                    "broker_id": instrument_id,
                    "received_at": received.isoformat(),
                    "available_at": received.isoformat(),
                    "source": "etoro",
                    "final": False,
                }
            )
    manifest = {
        "source": "etoro",
        "synthetic": False,
        "volume_kind": "unknown",
        "adjustments": "unknown",
        "license": "User-authorized private audit; redistribution unverified",
        "provenance": (
            "eToro MCP Market Data responses; acquisition.json records routes and receipts"
        ),
        "sha256": digest(csv_path),
        "coverage_start": regular[0]["event_time"],
        "coverage_end": regular[-1]["event_time"] + timedelta(minutes=1),
        "rows": len(regular),
        "calendar": calendar_version(),
        "point_in_time_universe": False,
        "availability_evidence": (
            "Tool completion receipt; no original publication or first-version evidence"
        ),
        "availability_kind": "historical_download",
        "acquired_at": received,
        "feed_id": "etoro-candles-feed-coverage-unknown",
        "quality": ["FINALITY_UNVERIFIED"],
    }
    save_json(output / "import-manifest.json", manifest)
    bundle = import_market_data(csv_path, output / "import-manifest.json")
    decision = ORBStrategy().process_session(
        bundle, regular[-1]["event_time"].astimezone(NY).date()
    )
    report["engine_comparison"] = {
        "decision": decision.model_dump(mode="json"),
        "import_audit": audit_bundle(bundle),
        "numeric_ORH_ORL_RVOL_comparison": (
            "BLOCKED: existing engine correctly rejects unqualified data"
        ),
        "strategy_modified": False,
        "availability_or_volume_overrides": False,
    }
    # Replay actual saved payload through the parser only; never a new external read.
    transport = GuardedTransport(
        Credentials("local-parser-placeholder", "local-parser-placeholder"),
        mode="shadow",
        session_id="parser-audit",
        config_hash="a" * 64,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=(raw / "quote.json").read_bytes())
        ),
    )
    try:
        EtoroMarketDataProvider(transport).quotes([instrument_id])
        report["quote_parser"] = "ACCEPTED_LOCAL_REPLAY"
    except BrokerBlocked as exc:
        report["quote_parser"] = str(exc)
    finally:
        transport.close()
    report.update(
        {
            "market_data": "BLOCKED",
            "market_data_access": "VERIFIED_VIA_MCP",
            "reason": INSUFFICIENT,
            "shadow": "NOT_STARTED_DATA_QUALITY_BLOCKED",
            **SAFETY,
            "instrument": instrument,
            "exchange": read_json(raw / "exchanges.json"),
            "timezone": "America/New_York",
            "granularity_seconds": 60,
            "acquisition": acquisition,
            "raw_file_hashes": hashes,
            "raw_files_unchanged": hashes
            == {path.name: digest(path) for path in sorted(raw.glob("*.json"))},
        }
    )
    save_json(output / "audit.json", report)
    save_json(
        output / "manifest.json",
        {
            "source": "eToro Public API",
            "instrument": instrument,
            "timezone": "America/New_York",
            "granularity": "OneMinute",
            "volume_kind": "unknown",
            "acquisition": acquisition,
            "raw_directory": str(raw),
            "raw_sha256": hashes,
            "derived_sha256": {
                name: digest(output / name)
                for name in ("regular-minutes.csv", "import-manifest.json", "audit.json")
            },
            "limitations": report["independent"]["limitations"] + ["INSUFFICIENT_MINUTE_HISTORY"],
            **SAFETY,
        },
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.input, args.output)
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("market_data", "reason", "history", "independent", "shadow")
            },
            default=str,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
