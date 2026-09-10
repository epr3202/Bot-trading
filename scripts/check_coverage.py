"""Enforce the critical-module line and branch coverage gate from pytest-cov JSON."""

import json
from pathlib import Path

CRITICAL = (
    "risk/engine.py",
    "brokers/transport.py",
    "brokers/authorization.py",
    "execution/engine.py",
    "execution/models.py",
    "persistence/store.py",
)


def main() -> int:
    payload = json.loads(Path("runtime/coverage.json").read_text(encoding="utf-8"))
    files = {name.replace("\\", "/"): data for name, data in payload["files"].items()}
    failed = False
    for module in CRITICAL:
        found = [data["summary"] for name, data in files.items() if name.endswith("/" + module)]
        if len(found) != 1:
            print(f"FAIL {module}: coverage evidence missing")
            failed = True
            continue
        summary = found[0]
        percentage = summary["percent_covered"]
        print(f"{module}: {percentage:.2f}% (lines + branches)")
        failed |= percentage < 90
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
