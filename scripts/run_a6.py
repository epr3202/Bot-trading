"""Reproducible A6 local-only session; no account credentials are read."""

import argparse
import json
from pathlib import Path

from intraday_etoro_lab.config import load_config
from intraday_etoro_lab.execution.session import DemoSessionRunner
from intraday_etoro_lab.execution.session_fixture import synthetic_session
from intraday_etoro_lab.persistence import StateStore


def main() -> int:
    parser = argparse.ArgumentParser(description="A6 SIMULATED Demo session; no external writes")
    parser.add_argument("--config", type=Path, default=Path("configs/strategy-1-v1.yaml"))
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--scenario", choices=("accepted", "no-signal"), default="accepted")
    args = parser.parse_args()
    config = load_config(args.config)
    bundle, day, inputs = synthetic_session(no_signal=args.scenario == "no-signal")
    store = StateStore(args.database, mode="offline")
    try:
        result = DemoSessionRunner(config, store).run(bundle, day, inputs)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as output:
            json.dump(
                {
                    "result": result,
                    "events": store.events(),
                    "orders": [i.model_dump(mode="json") for i in store.intents()],
                },
                output,
                indent=2,
            )
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "PASS" else 2
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
