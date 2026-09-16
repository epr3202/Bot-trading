"""Validate cached AAPL/SPY/QQQ; explicitly capture only missing benchmarks."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from uuid import uuid4

from intraday_etoro_lab.data.massive_a2 import validate_a2
from intraday_etoro_lab.data.massive_http import (
    MassiveCredentials,
    MassiveDataError,
    MassiveHistoricalRequest,
    MassiveHistoryClient,
    save_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=date.fromisoformat, required=True)
    parser.add_argument("--aapl", type=Path, required=True)
    parser.add_argument("--spy", type=Path)
    parser.add_argument("--qqq", type=Path)
    parser.add_argument("--capture-missing", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be new; existing evidence is immutable")
    paths = {s: p for s in ("AAPL", "SPY", "QQQ") if (p := getattr(args, s.lower()))}
    failures = {}
    client = None
    try:
        for symbol in ("SPY", "QQQ"):
            if symbol in paths or not args.capture_missing:
                continue
            try:
                if client is None:
                    client = MassiveHistoryClient(MassiveCredentials.from_environment())
                paths[symbol] = Path("data/raw/massive") / f"a2-{symbol}-{uuid4().hex[:12]}"
                client.capture(MassiveHistoricalRequest(args.target, symbol), paths[symbol])
            except MassiveDataError as exc:
                failures[symbol] = str(exc)
    finally:
        if client is not None:
            client.close()
    result = validate_a2(paths, args.target)
    result["capture_failures"] = failures
    result["http_attempts"] = client.records if client else []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_json(args.output, result)
    print(json.dumps({k: result[k] for k in ("status", "criteria", "errors", "capture_failures")}))
    print(f"Evidence: {args.output.as_posix()}")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
