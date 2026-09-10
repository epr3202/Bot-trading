"""Collect exact local gate results with account credentials removed from child processes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    root = Path.cwd()
    (root / "runtime").mkdir(exist_ok=True)
    uv = shutil.which("uv") or str(root / ".tools" / "bin" / "uv.exe")
    env = os.environ.copy()
    env.update(
        {
            "CI": "true",
            "BOT_MODE": "offline",
            "ORDER_SUBMISSION_ENABLED": "false",
            "ETORO_API_KEY": "",
            "ETORO_USER_KEY": "",
            "PYTHONUTF8": "1",
            "UV_CACHE_DIR": str(root / ".uv-cache"),
            "UV_PYTHON_INSTALL_DIR": str(root / ".python"),
        }
    )
    checks: list[tuple[list[str], int]] = [
        ([uv, "sync", "--frozen", "--offline"], 0),
        ([sys.executable, "-m", "ruff", "check", "."], 0),
        ([sys.executable, "-m", "ruff", "format", "--check", "."], 0),
        ([sys.executable, "-m", "mypy", "src"], 0),
        (
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--cov=intraday_etoro_lab",
                "--cov-branch",
                "--cov-report=json:runtime/coverage.json",
                "--junitxml=runtime/test-results.xml",
            ],
            0,
        ),
        ([sys.executable, "scripts/check_coverage.py"], 0),
        ([sys.executable, "scripts/scan_secrets.py"], 0),
        ([sys.executable, "-m", "intraday_etoro_lab.cli", "doctor"], 0),
        ([sys.executable, "-m", "intraday_etoro_lab.cli", "data", "validate"], 0),
        ([sys.executable, "-m", "intraday_etoro_lab.cli", "demo-offline"], 0),
        ([sys.executable, "-m", "intraday_etoro_lab.cli", "backtest"], 0),
        ([sys.executable, "-m", "intraday_etoro_lab.cli", "etoro", "preflight", "--read-only"], 2),
        ([sys.executable, "-m", "intraday_etoro_lab.cli", "run", "--mode", "etoro_demo"], 2),
        ([sys.executable, "-m", "intraday_etoro_lab.cli", "run", "--mode", "live"], 2),
        ([uv, "build", "--offline"], 0),
        (["node", "--check", "src/intraday_etoro_lab/ui/app.js"], 0),
    ]
    results = []
    for command, expected in checks:
        process = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        passed = process.returncode == expected
        results.append(
            {
                "command": command,
                "exit_code": process.returncode,
                "expected_exit_code": expected,
                "passed": passed,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }
        )
        print(
            f"{'PASS' if passed else 'FAIL'} {' '.join(command[1:])}: {process.returncode}",
            flush=True,
        )
    data = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "CI_environment": True,
        "account_credentials": "removed",
        "results": results,
    }
    (root / "runtime" / "verification.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    return int(any(not item["passed"] for item in results))


if __name__ == "__main__":
    raise SystemExit(main())
