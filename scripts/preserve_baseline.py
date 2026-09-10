"""Preserve reviewed index/worktree bytes without Git identity or private runtime data."""

import hashlib
import json
import platform
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from scan_secrets import PATTERNS


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def main() -> None:
    root = Path.cwd().resolve()
    destination = root / "runtime" / "phase2-baseline"
    destination.mkdir(exist_ok=False)
    names = sorted(git("ls-files", "-z").decode().strip("\0").split("\0"))
    records = []
    content = {}
    for name in names:
        if re.search(r"(^|/)(runtime|\.env|\.venv|\.git|control-token)(/|$)", name):
            raise RuntimeError("SENSITIVE_INDEX_PATH; no values printed")
        if Path(name).suffix in {".db", ".sqlite", ".key", ".pem", ".log"}:
            raise RuntimeError("SENSITIVE_INDEX_PATH; no values printed")
        index = git("show", f":{name}")
        working = (root / name).read_bytes()
        for data in (index, working):
            if any(p.search(data.decode("utf-8", errors="replace")) for p in PATTERNS):
                raise RuntimeError(f"SECRET_PATTERN: {name}; values redacted")
        records.append(
            {
                "path": name,
                "index_sha256": hashlib.sha256(index).hexdigest(),
                "worktree_sha256": hashlib.sha256(working).hexdigest(),
            }
        )
        content[f"index/{name}"] = index
        content[f"worktree/{name}"] = working
    with zipfile.ZipFile(destination / "reviewed-source.zip", "x", zipfile.ZIP_DEFLATED) as archive:
        for name, data in content.items():
            archive.writestr(name, data)
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    result = {
        "preserved_at_utc": datetime.now(UTC).isoformat(),
        "branch": git("branch", "--show-current").decode().strip(),
        "git_identity": "CONFIGURED"
        if all(
            subprocess.run(
                ["git", "config", "--get", field], capture_output=True, check=False
            ).stdout.strip()
            for field in ("user.name", "user.email")
        )
        else "GIT_IDENTITY_BLOCKED",
        "head": subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], capture_output=True, check=False
        )
        .stdout.decode()
        .strip()
        or None,
        "python": platform.python_version(),
        "git": git("--version").decode().strip(),
        "file_count": len(records),
        "manifest_payload_sha256": hashlib.sha256(canonical).hexdigest(),
        "archive_sha256": hashlib.sha256(
            (destination / "reviewed-source.zip").read_bytes()
        ).hexdigest(),
        "exclusions": "private runtime, secrets, caches, datasets; manifest does not hash itself",
        "files": records,
    }
    Path("docs/phase2-baseline.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for name in (
        "verification.json",
        "coverage.json",
        "test-results.xml",
        "package-evidence.json",
        "browser-evidence.json",
    ):
        source = root / "runtime" / name
        if source.exists():
            (destination / f"prior-{name}").write_bytes(source.read_bytes())
    print(
        json.dumps(
            {key: result[key] for key in ("file_count", "manifest_payload_sha256", "git_identity")}
        )
    )


if __name__ == "__main__":
    main()
