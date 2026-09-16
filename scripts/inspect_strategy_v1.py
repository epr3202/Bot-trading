"""Verify and inspect frozen A3 configuration and source hashes; no data or replay."""

import hashlib
import json
from pathlib import Path

from intraday_etoro_lab.config import load_config


def main() -> int:
    snapshot = json.loads(Path("docs/strategy-1-a3-audit.json").read_text(encoding="utf-8"))
    config = load_config(snapshot["configuration"])
    effective = {
        key: getattr(config, key).model_dump(mode="json") for key in ("strategy", "risk", "costs")
    }
    matches = (
        effective == snapshot["effective"] and config.strategy_hash == snapshot["strategy_hash"]
    )
    hashes = all(
        hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
        for path, expected in snapshot["source_sha256"].items()
    )
    passed = (
        matches and hashes and snapshot["frozen"] and config.strategy.version == "ORB_RVOL_v1.0"
    )
    print(
        json.dumps(
            {
                "status": "PASS" if passed else "FAIL",
                "strategy_id": snapshot["strategy_id"],
                "version": config.strategy.version,
                "strategy_hash": config.strategy_hash,
                "effective": effective,
                "source_hashes_match": hashes,
            },
            indent=2,
        )
    )
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
