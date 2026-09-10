"""Offline suite infrastructure. Test artifacts inherit the project's Windows ACL.

Python's Windows mode-0700 temporary directories exclude the restricted execution
token in this environment. Keep per-test, uniquely named, non-secret artifacts under
ignored runtime instead. No existing directory is deleted or permissions changed.
"""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path() -> Path:
    path = Path(__file__).resolve().parent.parent / "runtime" / "test-artifacts" / uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path


@pytest.fixture(autouse=True)
def offline_network_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    original = socket.socket.connect

    def guarded_connect(sock: socket.socket, address: Any) -> Any:
        if not isinstance(address, tuple) or address[0] not in {"127.0.0.1", "::1"}:
            raise AssertionError("Normal tests cannot connect to external services")
        return original(sock, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.delenv("ETORO_API_KEY", raising=False)
    monkeypatch.delenv("ETORO_USER_KEY", raising=False)
    monkeypatch.delenv("BOT_MODE", raising=False)
    monkeypatch.delenv("ORDER_SUBMISSION_ENABLED", raising=False)
