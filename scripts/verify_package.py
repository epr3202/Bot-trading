"""Install a fresh source distribution offline; never overwrite a previous check."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from uuid import uuid4


def main() -> None:
    root = Path.cwd().resolve()
    archive = next((root / "dist").glob("*.tar.gz"))
    wheel = next((root / "dist").glob("*.whl"))
    destination = root / "runtime" / "package-checks" / uuid4().hex
    destination.mkdir(parents=True, exist_ok=False)
    forbidden = {".git", ".venv", ".tools", ".uv-cache", ".python", "runtime", ".env"}
    with tarfile.open(archive) as source:
        members = source.getmembers()
        for member in members:
            if not (destination / member.name).resolve().is_relative_to(destination):
                raise ValueError("Archive path escapes isolated package check")
            if forbidden.intersection(Path(member.name).parts):
                raise ValueError("Sensitive runtime directory in source distribution")
        source.extractall(destination, filter="data")
    with zipfile.ZipFile(wheel) as built:
        for asset in ("index.html", "app.js", "style.css"):
            if f"intraday_etoro_lab/ui/{asset}" not in built.namelist():
                raise ValueError("Wheel is missing a dashboard asset")
    project = next(path for path in destination.iterdir() if path.is_dir())
    uv = shutil.which("uv") or str(root / ".tools" / "bin" / "uv.exe")
    environment = os.environ.copy()
    environment["UV_CACHE_DIR"] = str(root / ".uv-cache")
    environment["UV_PYTHON_INSTALL_DIR"] = str(root / ".python")
    environment["PYTHONUTF8"] = "1"
    environment.pop("VIRTUAL_ENV", None)
    for command in (
        [uv, "sync", "--frozen", "--offline"],
        [uv, "run", "--offline", "bot", "demo-offline"],
    ):
        subprocess.run(command, cwd=project, env=environment, check=True)
    evidence = {
        "source": archive.name,
        "wheel": wheel.name,
        "fresh_install": "PASS",
        "offline_roundtrip": "PASS",
        "project": str(project),
        "network": "offline",
    }
    (root / "runtime" / "package-evidence.json").write_text(
        json.dumps(evidence, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
