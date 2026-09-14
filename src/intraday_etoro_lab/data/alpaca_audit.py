"""Historical arithmetic audit, separate from operational signals and execution."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

from intraday_etoro_lab.data.alpaca import AlpacaHistoricalProvider, parse_time, read_document
from intraday_etoro_lab.data.alpaca_http import (
    AlpacaDataError,
    HistoricalRequest,
    save_json,
    sha256,
    software_commit,
)
from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.strategies.orb import ORBStrategy

INSUFFICIENT = "ALPACA_DATA_INSUFFICIENT_FOR_RVOL"
SAFETY = {
    "etoro_demo_read": "DEMO_READ_VERIFIED",
    "entries_armed": False,
    "external_mutations": "DISABLED",
    "order_submission_enabled": False,
    "etoro_demo_write": "NOT_TESTED",
    "shadow": "NOT_STARTED_THIS_PHASE",
    "writes": 0,
}
TOLERANCE = Decimal("0.000000000001")


def independent_metrics(directory: Path, request: HistoricalRequest) -> dict[str, Decimal]:
    """Raw Alpaca keys and Fraction arithmetic; no engine/importer computation reused."""
    capture = read_document(directory / "capture.json")
    values: dict[datetime, dict[str, Any]] = {}
    for page in capture["pages"]:
        for row in read_document(directory / page["file"])["bars"].get(request.symbol, []):
            values.setdefault(parse_time(row["t"]), row)
    totals: list[Fraction] = []
    today: list[dict[str, Any]] = []
    for day in request.days:
        opening = [values[session(day).open + timedelta(minutes=i)] for i in range(5)]
        total = Fraction(0)
        for row in opening:
            total += Fraction(str(row["v"]))
        if total <= 0:
            raise ValueError("ALPACA_ZERO_OPENING_VOLUME")
        totals.append(total)
        if day == request.target:
            today = opening
    mean = Fraction(0)
    for value in totals[:-1]:
        mean += value / 20
    expected = {
        "or_high": max(Fraction(str(row["h"])) for row in today),
        "or_low": min(Fraction(str(row["l"])) for row in today),
        "opening_volume": totals[-1],
        "historical_opening_volume": mean,
        "rvol": totals[-1] / mean,
    }
    return {
        name: Decimal(value.numerator) / Decimal(value.denominator)
        for name, value in expected.items()
    }


def audit_capture(directory: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    provider = AlpacaHistoricalProvider(directory)
    try:
        bundle = provider.load()
    except AlpacaDataError as exc:
        # Parsing stopped: unmeasured counts must not masquerade as zero defects.
        save_json(
            output / "data-quality.json",
            {
                "status": "BLOCKED",
                "reason_codes": [str(exc)],
                "classification": exc.status,
                "counts": None,
                "provider": "alpaca",
                "feed": None,
                "by_symbol": None,
                "aggregate": None,
            },
        )
        raise
    capture = provider.capture
    request = HistoricalRequest(date.fromisoformat(capture["target"]), capture["feed_requested"])
    report: dict[str, Any] = {
        "status": INSUFFICIENT,
        "target": str(request.target),
        **provider.audit,
        **SAFETY,
        "independent": None,
        "engine_metrics": None,
        "metric_comparison": "NOT_RUN",
        "absolute_tolerance": str(TOLERANCE),
        "relative_tolerance": "0",
        "acquisition_class": capture["acquisition_class"],
    }
    engine = ORBStrategy()
    # Historical downloads still go through the unchanged operational availability gate.
    report["engine_decision"] = engine.process_session(bundle, request.target).model_dump(
        mode="json"
    )
    if provider.audit["complete_sessions"] == 21:
        try:
            expected = independent_metrics(directory, request)
            by_time = {bar.event_time: bar for bar in bundle.bars}
            current = [
                by_time[session(request.target).open + timedelta(minutes=i)] for i in range(5)
            ]
            prior = [
                sum(
                    (by_time[session(day).open + timedelta(minutes=i)].volume for i in range(5)),
                    Decimal(0),
                )
                for day in request.days[:-1]
            ]
            actual = engine.opening_metrics(current, prior).model_dump()
            matches = all(abs(actual[name] - expected[name]) <= TOLERANCE for name in expected)
            report.update(
                independent=expected,
                engine_metrics=actual,
                metric_comparison="MATCH" if matches else "MISMATCH",
            )
            if (
                matches
                and request.feed == "sip"
                and provider.audit["data_quality"]["aggregate"]["status"] == "PASS"
            ):
                report["status"] = (
                    "ALPACA_SIP_HISTORICAL_VERIFIED"
                    if not bundle.manifest.synthetic and provider.audit["observed_feed"] == "sip"
                    else "FEED_UNVERIFIED"
                    if not bundle.manifest.synthetic
                    else "ALPACA_CONTRACT_TEST_VERIFIED"
                )
        except (ValueError, KeyError, ArithmeticError):
            report["metric_comparison"] = "INVALID_OPENING_WINDOWS"
    if request.feed == "iex":
        report["status"] = "ALPACA_IEX_INSUFFICIENT_FOR_PRODUCTION_RVOL"
    elif provider.audit["complete_sessions"] != 21:
        report["status"] = "ALPACA_HISTORICAL_INCOMPLETE"
    elif not bundle.manifest.synthetic and provider.audit["observed_feed"] != "sip":
        report["status"] = "FEED_UNVERIFIED"
    save_json(output / "data-quality.json", provider.audit["data_quality"])
    # Share-compatible existing import route, with historical receipts intact.
    csv_path = output / "regular-minutes.csv"
    fields = [
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
    ]
    with csv_path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for bar in bundle.bars:
            writer.writerow(
                {
                    "symbol": bar.instrument.symbol,
                    "exchange": bar.instrument.exchange,
                    "currency": bar.instrument.currency,
                    "asset_class": bar.instrument.asset_class,
                    **{key: getattr(bar, key) for key in fields[4:]},
                }
            )
    manifest = bundle.manifest.model_copy(update={"sha256": sha256(csv_path)})
    save_json(output / "import-manifest.json", manifest.model_dump(mode="json"))
    report["limitations"] = [
        "Historical download does not prove realtime availability or first versions",
        "Missing bars have unknown cause without independent halt evidence; never filled",
        "SIP volume follows Alpaca eligible-trade aggregation, not every reported event",
        "Split-adjusted prices and volume; no point-in-time universe certification",
        "Requested feed is contractual; missing payload echo remains FEED_UNVERIFIED",
        "Numeric engine metrics comparison is not causal signal or execution validation",
    ]
    save_json(output / "audit.json", report)
    portable = {
        "schema_version": "alpaca-audit-v2",
        "status": report["status"],
        "provider": "alpaca",
        "symbol": request.symbol,
        "feed_requested": request.feed,
        "feed_effective": provider.audit["observed_feed"],
        "requested_feed": request.feed,
        "observed_feed": provider.audit["observed_feed"],
        "feed_verification": provider.audit["feed_verification"],
        "feed_identity_basis": capture["feed_identity_basis"],
        "endpoint": capture["origin"] + capture["endpoint"],
        "query": capture["params"],
        "timezone": "America/New_York",
        "timeframe": "1Min",
        "availability_class": "HISTORICAL_DOWNLOAD",
        "acquisition_class": capture["acquisition_class"],
        "started_at": capture["started_at"],
        "finished_at": capture["finished_at"],
        "software_commit": capture.get("software_commit", "UNRECORDED_WORKTREE"),
        "audit_software_commit": software_commit(),
        "instrument_identity": bundle.instruments[0].model_dump(mode="json"),
        "sessions": [
            {key: entry[key] for key in ("date", "expected_minutes", "missing_count", "complete")}
            for entry in provider.audit["sessions"]
        ],
        "bar_count": len(bundle.bars),
        "volume_semantics": provider.audit["volume_semantics"],
        "timestamp_semantics": provider.audit["timestamp_semantics"],
        "raw_sha256": {page["file"]: page["sha256"] for page in capture["pages"]},
        "capture_sha256": sha256(directory / "capture.json"),
        "derived_sha256": {
            name: sha256(output / name)
            for name in (
                "regular-minutes.csv",
                "import-manifest.json",
                "audit.json",
                "data-quality.json",
            )
        },
        "independent": report["independent"],
        "engine_metrics": report["engine_metrics"],
        "metric_comparison": report["metric_comparison"],
        "absolute_tolerance": str(TOLERANCE),
        "limitations": report["limitations"],
        **SAFETY,
    }
    save_json(output / "manifest.json", portable)
    return report
