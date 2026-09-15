"""Explicit historical Massive capture or offline audit. No shadow or order activation."""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from intraday_etoro_lab.data.calendar import sessions
from intraday_etoro_lab.data.massive_audit import SAFETY, audit_capture
from intraday_etoro_lab.data.massive_http import (
    VOLUME_SEMANTICS,
    MassiveCredentials,
    MassiveDataError,
    MassiveHistoricalRequest,
    MassiveHistoryClient,
    read_document,
    save_json,
    utc_now,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--capture", action="store_true")
    group.add_argument("--input", type=Path)
    parser.add_argument("--target", type=date.fromisoformat)
    args = parser.parse_args()
    if args.input and args.target:
        parser.error("--target only applies to --capture; offline target comes from the capture")
    run_id = utc_now().strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8]
    evidence = Path("runtime/massive-audits") / run_id
    evidence.mkdir(parents=True, exist_ok=False)
    raw = args.input or Path("data/raw/massive") / run_id
    client = None
    result = {
        "schema_version": "massive-attempt-v1",
        "status": "MASSIVE_DATA_INCOMPLETE",
        "provider": "massive",
        "symbol": "AAPL",
        "timeframe": "1m",
        "availability_class": "HISTORICAL_DOWNLOAD",
        "latency": None,
        "coverage": None,
        "plan_observed": None,
        "access_observed": "NOT_OBSERVED",
        "sessions_requested": 21,
        "sessions_valid": None,
        "bar_count": None,
        "independent": None,
        "metric_comparison": "NOT_RUN",
        "raw_sha256": {},
        "volume_semantics": VOLUME_SEMANTICS,
        **SAFETY,
    }
    try:
        today = utc_now().astimezone(ZoneInfo("America/New_York")).date()
        target = args.target or sessions(today - timedelta(days=60), today - timedelta(days=1))[-1]
        if args.input:
            target = date.fromisoformat(read_document(raw / "capture.json")["target"])
        request = MassiveHistoricalRequest(target)
        result.update(
            target=str(target),
            endpoint=request.endpoint,
            sessions=[str(day) for day in request.days],
        )
        if args.capture:
            client = MassiveHistoryClient(MassiveCredentials.from_environment())
            client.capture(request, raw)
        result = audit_capture(raw, evidence / "analysis")
    except MassiveDataError as exc:
        result.update(status=exc.status, reason=str(exc))
    except (OSError, ValueError, TypeError, KeyError):
        result.update(status="MASSIVE_DATA_INCOMPLETE", reason="LOCAL_INPUT_OR_STORAGE_INVALID")
    finally:
        if client is not None:
            result["http_attempts"] = client.records
            client.close()
    result.update(raw_directory=raw.as_posix(), evidence_directory=evidence.as_posix())
    save_json(evidence / "result.json", result)
    print(
        json.dumps(
            {
                key: result.get(key)
                for key in (
                    "status",
                    "reason",
                    "target",
                    "sessions_valid",
                    "bar_count",
                    "coverage",
                    "independent",
                    "metric_comparison",
                )
            },
            indent=2,
            default=str,
        )
    )
    print(f"Evidence: {evidence.as_posix()}")
    return 0 if result["status"] == "MASSIVE_HISTORICAL_RVOL_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
