"""Scan Git candidate text; no network, no secret values printed on failure."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?:ghp_|github_pat_|sk-proj-)[A-Za-z0-9_]{20,}"),
    re.compile(r"(?im)^[ \t]*(?:ETORO_API_KEY|ETORO_USER_KEY)[ \t]*=[ \t]*[^\s#]{12,}[ \t]*$"),
)


def scan() -> int:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    failures: list[str] = []
    paths = sorted(set(result.stdout.decode().split("\0")) - {""})
    for name in paths:
        path = Path(name)
        if not path.is_file():
            continue
        if name.endswith((".key", ".pem", ".db", ".sqlite")) or path.name == ".env":
            failures.append(f"{name}: archivo sensible")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in PATTERNS:
            if pattern.search(content):
                failures.append(f"{name}: patrón de secreto detectado (valor redactado)")
                break
    for item in failures:
        print(item)
    print(f"Secret scan: {len(paths)} candidate files, {len(failures)} findings")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(scan())
