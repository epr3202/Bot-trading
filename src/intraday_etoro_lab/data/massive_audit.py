"""Independent raw/Fraction arithmetic against the unchanged ORB engine/Decimal."""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.data.massive import MassiveHistoricalProvider
from intraday_etoro_lab.data.massive_http import (
    MassiveDataError,
    MassiveHistoricalRequest,
    read_document,
    save_json,
    sha256,
)
from intraday_etoro_lab.strategies.orb import ORBStrategy

SAFETY = {
    "etoro_demo_read": "DEMO_READ_VERIFIED",
    "entries_armed": False,
    "external_mutations": "DISABLED",
    "order_submission_enabled": False,
    "etoro_demo_write": "NOT_TESTED",
    "shadow": "NOT_STARTED",
    "writes": 0,
}


def independent_metrics(directory: Path, request: MassiveHistoricalRequest) -> dict[str, Decimal]:
    """Select raw epoch keys directly; no Bar mapping or engine formula used here."""
    capture = read_document(directory / "capture.json")
    values: dict[int, dict[str, Any]] = {}
    for page in capture["pages"]:
        for row in read_document(directory / page["file"]).get("results", []):
            if row["t"] in values:
                raise MassiveDataError("DUPLICATE_BARS")
            values[row["t"]] = row
    totals: list[Fraction] = []
    target: list[dict[str, Any]] = []
    for day in request.days:
        start = int(session(day).open.timestamp() * 1000)
        opening = [values[start + i * 60000] for i in range(5)]
        total = sum((Fraction(str(row["v"])) for row in opening), Fraction(0))
        if total <= 0:
            raise MassiveDataError("NON_POSITIVE_OPENING_VOLUME")
        totals.append(total)
        if day == request.target:
            target = opening
    mean = sum(totals[:20], Fraction(0)) / 20
    expected = {
        "or_high": max(Fraction(str(row["h"])) for row in target),
        "or_low": min(Fraction(str(row["l"])) for row in target),
        "opening_volume": totals[20],
        "historical_opening_volume": mean,
        "rvol": totals[20] / mean,
    }
    return {key: Decimal(val.numerator) / Decimal(val.denominator) for key, val in expected.items()}


def audit_capture(directory: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    provider = MassiveHistoricalProvider(directory)
    try:
        bundle = provider.load()
    except MassiveDataError as exc:
        save_json(
            output / "data-quality.json",
            {
                "status": "BLOCKED",
                "reason_codes": [str(exc)],
                "counts": None,
            },
        )
        raise
    request = MassiveHistoricalRequest(
        date.fromisoformat(provider.capture["target"]), provider.capture.get("symbol", "AAPL")
    )
    report: dict[str, Any] = {
        "schema_version": "massive-audit-v1",
        "status": "MASSIVE_DATA_INCOMPLETE",
        **provider.audit,
        **SAFETY,
        "target": str(request.target),
        "acquisition_class": provider.capture["acquisition_class"],
        "independent": None,
        "engine_metrics": None,
        "metric_comparison": "NOT_RUN",
        "comparison_rule": "Exact Decimal equality for all five metrics; no tolerance",
        "capture_sha256": sha256(directory / "capture.json"),
        "raw_sha256": {p["file"]: p["sha256"] for p in provider.capture["pages"]},
    }
    engine = ORBStrategy()
    decision = engine.process_session(bundle, request.target)
    report["engine_decision"] = decision.model_dump(mode="json")
    if provider.audit["data_quality"]["status"] == "PASS":
        try:
            expected = independent_metrics(directory, request)
            by_time: dict[datetime, Any] = {bar.event_time: bar for bar in bundle.bars}
            current = [
                by_time[session(request.target).open + timedelta(minutes=i)] for i in range(5)
            ]
            previous = [
                sum(
                    (by_time[session(day).open + timedelta(minutes=i)].volume for i in range(5)),
                    Decimal(0),
                )
                for day in request.days[:-1]
            ]
            actual = engine.opening_metrics(current, previous).model_dump()
            matches = actual == expected
            report.update(
                independent=expected,
                engine_metrics=actual,
                metric_comparison="MATCH" if matches else "MISMATCH",
            )
            if not matches:
                report["reason"] = "ENGINE_METRICS_MISMATCH"
            elif not provider.audit["volume_semantics_verified"]:
                report["status"] = "MASSIVE_VOLUME_SEMANTICS_UNVERIFIED"
                report["reason"] = "VOLUME_SEMANTICS_UNVERIFIED"
            elif bundle.manifest.synthetic:
                report["reason"] = "CONTRACT_TEST_ONLY_NO_EXTERNAL_VERIFICATION"
            elif (
                decision.signals
                or decision.selection
                or not any(
                    item.reason == "OBSERVED_AVAILABILITY_REQUIRED" for item in decision.rejections
                )
            ):
                report["reason"] = "HISTORICAL_AVAILABILITY_GUARD_FAILED"
            else:
                report["status"] = "MASSIVE_HISTORICAL_RVOL_VERIFIED"
        except (ValueError, KeyError, ArithmeticError, MassiveDataError):
            report["reason"] = "INDEPENDENT_OR_ENGINE_ARITHMETIC_INVALID"
    else:
        report["reason"] = "DATA_QUALITY_FAILED"
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
    csv_path = output / "regular-minutes.csv"
    with csv_path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for bar in bundle.bars:
            writer.writerow(
                {
                    **{key: getattr(bar.instrument, key) for key in fields[:4]},
                    **{key: getattr(bar, key) for key in fields[4:]},
                }
            )
    manifest = bundle.manifest.model_copy(update={"sha256": sha256(csv_path)})
    save_json(output / "import-manifest.json", manifest.model_dump(mode="json"))
    save_json(output / "data-quality.json", provider.audit["data_quality"])
    report["csv_sha256"] = sha256(csv_path)
    report["limitations"] = [
        "Plan name is not exposed by this endpoint; HTTP access is recorded separately",
        "Coverage is documented endpoint coverage, not independent trade-by-trade reconciliation",
        "Historical receipt is not realtime latency or contemporaneous availability",
        "Snapshots may contain late corrections and splits; not point-in-time corporate actions",
        "Single AAPL sample; no point-in-time universe, alpha or profitability validation",
        "Calendar version is pinned; extraordinary closures require separate evidence",
    ]
    save_json(output / "audit.json", report)
    return report
