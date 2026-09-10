"""Run a bounded local UI verification and shut down the server cleanly."""

from __future__ import annotations

import secrets
import subprocess
import sys
import threading
import time

import uvicorn

from intraday_etoro_lab.api.app import create_app
from intraday_etoro_lab.config import load_config
from intraday_etoro_lab.service import OperationService


def main() -> None:
    if len(sys.argv) != 2:
        raise ValueError("Pass the installed Chromium executable path")
    config = load_config("configs/offline.yaml")
    service = OperationService(config)
    token = secrets.token_urlsafe(36)
    path = config.runtime_dir / "control-token"
    path.write_text(token, encoding="utf-8")
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(service, token),
            host="127.0.0.1",
            port=8765,
            access_log=False,
            proxy_headers=False,
            log_level="warning",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    try:
        thread.start()
        deadline = time.monotonic() + 15
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.1)
        if not server.started:
            raise RuntimeError("Local server failed to start")
        subprocess.run(["node", "scripts/check_dashboard.mjs", sys.argv[1]], check=True)
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        if thread.is_alive():
            raise RuntimeError("Local server did not stop cleanly")
        path.unlink(missing_ok=True)
        # A previous killed CLI may have left discovery metadata. We own the OS lock.
        (config.runtime_dir / "control.json").unlink(missing_ok=True)
        service.close()


if __name__ == "__main__":
    main()
