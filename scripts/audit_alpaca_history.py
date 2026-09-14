"""Explicit SIP historical acquisition, or offline re-audit; never trading or shadow."""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

from intraday_etoro_lab.data.alpaca_audit import INSUFFICIENT, SAFETY, audit_capture
from intraday_etoro_lab.data.alpaca_http import (
    AlpacaCredentials,
    AlpacaDataError,
    AlpacaHistoryClient,
    HistoricalRequest,
    save_json,
    utc_now,
)
from intraday_etoro_lab.data.calendar import session, sessions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--capture", action="store_true", help="GET historical bars using dedicated credentials"
    )
    group.add_argument("--input", type=Path, help="Offline existing capture directory")
    parser.add_argument("--target", type=date.fromisoformat)
    parser.add_argument("--feed", choices=["sip", "iex"], default="sip")
    args = parser.parse_args()
    run_id = utc_now().strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8]
    evidence = Path("runtime/alpaca-audits") / run_id
    evidence.mkdir(parents=True)
    raw = args.input or Path("data/raw/alpaca") / run_id
    client = None
    now = utc_now()
    days = sessions(now.date() - timedelta(days=60), now.date())
    target = args.target or next(
        day for day in reversed(days) if session(day).close <= now - timedelta(minutes=15)
    )
    request = HistoricalRequest(target, args.feed)
    result = {
        "status": INSUFFICIENT,
        "provider": "alpaca",
        "feed_requested": request.feed,
        "feed_effective": None,
        "target": str(target),
        "query": request.params(),
        "sessions_recovered": 0,
        "independent": None,
        "metric_comparison": "NOT_RUN",
        "availability_class": "HISTORICAL_DOWNLOAD",
        **SAFETY,
    }
    try:
        if args.capture:
            client = AlpacaHistoryClient(AlpacaCredentials.from_environment())
            client.capture(request, raw)
        result = audit_capture(raw, evidence / "analysis")
    except AlpacaDataError as exc:
        reason = str(exc)
        result["reason"] = reason
        if reason == "ALPACA_SIP_ENTITLEMENT_REQUIRED":
            result["status"] = reason
        result["entitlement_verified"] = reason == "ALPACA_SIP_ENTITLEMENT_REQUIRED"
    except (OSError, ValueError, TypeError, KeyError):
        result["reason"] = "ALPACA_LOCAL_INPUT_OR_STORAGE_INVALID"
    finally:
        if client is not None:
            client.close()
    result["raw_directory"] = raw.as_posix()
    result["evidence_directory"] = evidence.as_posix()
    save_json(evidence / "result.json", result)
    print(
        json.dumps(
            {
                key: result.get(key)
                for key in (
                    "status",
                    "reason",
                    "feed_requested",
                    "feed_effective",
                    "complete_sessions",
                    "independent",
                    "metric_comparison",
                )
            },
            indent=2,
            default=str,
        )
    )
    print(f"Evidence: {evidence.as_posix()}")
    return 0 if result["status"] == "ALPACA_SIP_HISTORICAL_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
