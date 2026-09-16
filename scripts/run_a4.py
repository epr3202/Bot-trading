"""Explicit offline A4 run/compare; no download, broker or fixture fallback."""

import argparse
import json
from pathlib import Path

from intraday_etoro_lab.backtesting.a4 import compare_runs, persist_run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--output", required=True, type=Path)
    compare = commands.add_parser("compare")
    compare.add_argument("first", type=Path)
    compare.add_argument("second", type=Path)
    compare.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "run":
            print(
                json.dumps(
                    {"status": "PASS", "artifact": str(persist_run(Path.cwd(), args.output))}
                )
            )
            return 0
        result = compare_runs(args.first, args.second, args.output)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "PASS" else 2
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
