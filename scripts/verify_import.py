"""Generate, import, validate and replay 20 warmups + one evaluation; SYNTHETIC ONLY."""

import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import yaml

from intraday_etoro_lab.data import FixtureProvider
from intraday_etoro_lab.data.importer import audit_bundle, import_market_data
from intraday_etoro_lab.strategies.orb import ORBStrategy


def main() -> None:
    root = Path.cwd()
    directory = root / "runtime" / "import-checks" / uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    source = FixtureProvider().load()
    day = source.evaluation_sessions[0]
    bars = [
        bar for bar in source.bars if bar.instrument.symbol == "SIMA" and bar.session_date <= day
    ]
    rows = []
    for bar in bars:
        row = bar.model_dump(mode="json")
        row.update(row.pop("instrument"))
        row.pop("broker_id")
        rows.append(row)
    raw = directory / "synthetic.csv"
    with raw.open("x", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    manifest = source.manifest.model_copy(
        update={
            "sha256": digest,
            "rows": len(rows),
            "coverage_end": max(b.end_time for b in bars),
        }
    )
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    bundle = import_market_data(raw, manifest_path)
    decision = ORBStrategy().process_session(bundle, day)
    # Independent calculation from raw CSV and wall-clock opening window. No
    # feature, calendar or strategy helper computes this reference arithmetic.
    groups: dict[str, list[dict[str, str]]] = {}
    with raw.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            stamp = datetime.fromisoformat(row["event_time"])
            # Selected November sample uses 14:30 UTC (EST); October uses 13:30.
            opening_hour = 14 if stamp.date().month == 11 else 13
            if stamp.hour == opening_hour and 30 <= stamp.minute < 35:
                groups.setdefault(stamp.date().isoformat(), []).append(row)
    previous = sorted(groups)[:-1]
    assert len(previous) == 20 and all(len(rows) == 5 for rows in groups.values())
    denominator = sum(sum(Decimal(r["volume"]) for r in groups[d]) for d in previous) / 20
    today = groups[day.isoformat()]
    numerator = sum(Decimal(r["volume"]) for r in today)
    independent = {
        "or_high": max(Decimal(r["high"]) for r in today),
        "or_low": min(Decimal(r["low"]) for r in today),
        "rvol": numerator / denominator,
    }
    candidate = decision.selection[0]
    assert candidate.or_high == independent["or_high"] == Decimal("100.70")
    assert candidate.or_low == independent["or_low"] == Decimal("99.80")
    assert candidate.rvol == independent["rvol"] == 3
    cutoff = decision.selection_at + timedelta(hours=2)
    future = tuple(
        bar.model_copy(update={"volume": bar.volume * 500}) if bar.event_time > cutoff else bar
        for bar in bundle.bars
    )
    from dataclasses import replace

    assert ORBStrategy().process_session(replace(bundle, bars=future), day) == decision
    config = yaml.safe_load(Path("configs/offline.yaml").read_text(encoding="utf-8"))
    config.update(
        {
            "mode": "backtest",
            "runtime_dir": str(directory / "state"),
            "reports_dir": str(root / "reports" / "runs" / "synthetic-import" / directory.name),
            "data": {"provider": "import", "path": str(raw), "manifest": str(manifest_path)},
        }
    )
    config_path = directory / "replay.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PYTHONUTF8": "1",
            "BOT_MODE": "backtest",
            "ORDER_SUBMISSION_ENABLED": "false",
            "ETORO_API_KEY": "",
            "ETORO_USER_KEY": "",
        }
    )
    checks = []
    for operation in (["data", "validate"], ["backtest"]):
        command = [
            sys.executable,
            "-m",
            "intraday_etoro_lab.cli",
            *operation,
            "--config",
            str(config_path),
        ]
        completed = subprocess.run(
            command, env=env, capture_output=True, encoding="utf-8", check=False
        )
        checks.append(
            {
                "command": command,
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "at_utc": datetime.now(UTC).isoformat(),
            }
        )
    evidence = {
        "kind": "SYNTHETIC_IMPORT_REPLAY",
        "source_sha256": digest,
        "audit": audit_bundle(bundle),
        "independent_arithmetic": independent,
        "future_perturbation": "PASS",
        "raw_unchanged": hashlib.sha256(raw.read_bytes()).hexdigest() == digest,
        "configuration": str(config_path),
        "checks": checks,
        "real_sample": "NOT_AVAILABLE",
    }
    Path("runtime/import-evidence.json").write_text(
        json.dumps(evidence, indent=2, default=str), encoding="utf-8"
    )
    assert all(item["exit_code"] == 0 for item in checks), "IMPORT_REPLAY_FAILED"
    assert evidence["raw_unchanged"]
    print(
        json.dumps(
            {
                "rows": len(rows),
                "sessions": 21,
                "independent_arithmetic": independent,
                "configuration": str(config_path),
                "status": "PASS_SYNTHETIC_ONLY",
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()
