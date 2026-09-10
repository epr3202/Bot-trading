from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from intraday_etoro_lab.api.app import Command, ControlSettings, create_app
from intraday_etoro_lab.config import AppConfig, load_config
from intraday_etoro_lab.observability.logging import JsonFormatter, redact


@pytest.mark.parametrize(
    "mode", ["live", "real", "production_trading", "REAL", "production", "paper"]
)
def test_unrecognized_modes_rejected_everywhere(mode: str, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValidationError):
        AppConfig(mode=mode)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        load_config(mode=mode)
    monkeypatch.setenv("BOT_MODE", mode)
    with pytest.raises(ValueError):
        load_config(mode="offline")


def test_config_hash_and_strict_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = load_config("configs/offline.yaml")
    assert config.config_hash == load_config("configs/offline.yaml").config_hash
    changed = config.model_copy(update={"arm_ttl_seconds": 200})
    assert config.config_hash != changed.config_hash
    with pytest.raises(ValidationError):
        AppConfig(order_submission_enabled=True)
    monkeypatch.setenv("ORDER_SUBMISSION_ENABLED", "yes")
    with pytest.raises(ValueError):
        load_config()
    monkeypatch.setenv("ORDER_SUBMISSION_ENABLED", "false")
    bad = tmp_path / "bad.yaml"
    bad.write_text("[wrong, shape]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(bad)
    with pytest.raises(ValidationError):
        AppConfig(data={"provider": "import"})  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        AppConfig(strategy={"vwap_enabled": True})  # type: ignore[arg-type]


class FakeService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def snapshot(self) -> dict[str, Any]:
        return {"mode": "offline", "entries_armed": False}

    def command(self, action: str, confirm: str = "", budget: str | None = None) -> dict[str, Any]:
        self.calls.append(action)
        return self.snapshot()


def client_pair() -> tuple[TestClient, FakeService]:
    service = FakeService()
    return TestClient(create_app(service, "x" * 48), base_url="http://127.0.0.1:8765"), service


def headers() -> dict[str, str]:
    return {"Authorization": "Bearer " + "x" * 48, "Origin": "http://127.0.0.1:8765"}


def test_http_local_boundary_auth_csrf_no_get_mutation() -> None:
    client, service = client_pair()
    assert client.get("/health").status_code == 200
    assert client.get("/api/state").status_code == 401
    assert client.get("/api/state", headers=headers()).json()["mode"] == "offline"
    assert client.get("/api/state?token=no", headers=headers()).status_code == 400
    assert client.get("/api/state", headers={**headers(), "Host": "evil.test"}).status_code == 400
    assert (
        client.get("/api/state", headers={**headers(), "X-Forwarded-For": "127.0.0.1"}).status_code
        == 400
    )
    for origin in ("null", "https://evil.test", "http://localhost:8765"):
        assert (
            client.post(
                "/api/commands",
                json={"action": "pause-entries"},
                headers={**headers(), "Origin": origin},
            ).status_code
            == 403
        )
    assert (
        client.post(
            "/api/commands",
            json={"action": "pause-entries"},
            headers={"Authorization": headers()["Authorization"]},
        ).status_code
        == 403
    )
    assert client.get("/api/commands", headers=headers()).status_code == 405
    assert not service.calls
    assert (
        client.post(
            "/api/commands", json={"action": "pause-entries"}, headers=headers()
        ).status_code
        == 200
    )
    assert service.calls == ["pause-entries"]


def test_ui_mode_rejection_and_demo_confirmation() -> None:
    client, service = client_pair()
    for action in ("live", "real", "production_trading", "open-arbitrary-order"):
        assert (
            client.post("/api/commands", json={"action": action}, headers=headers()).status_code
            == 422
        )
    assert (
        client.post("/api/commands", json={"action": "arm-demo"}, headers=headers()).status_code
        == 400
    )
    assert (
        client.post(
            "/api/commands", json={"action": "flatten-owned-demo"}, headers=headers()
        ).status_code
        == 400
    )
    assert not service.calls
    with pytest.raises(ValidationError):
        Command(action="demo-offline", mode="live")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        ControlSettings(host="0.0.0.0")  # type: ignore[arg-type]


def test_frontend_has_no_embedded_token_and_has_csp() -> None:
    client, _ = client_pair()
    page = client.get("/")
    assert page.status_code == 200
    assert "x" * 48 not in page.text
    assert 'lang="es"' in page.text
    assert "frame-ancestors 'none'" in page.headers["Content-Security-Policy"]
    js = client.get("/assets/app.js").text
    assert "innerHTML" not in js
    assert "localStorage" not in js
    assert "etoro.com" not in js
    assert client.get("/assets/style.css").status_code == 200


def test_recursive_redaction() -> None:
    import logging

    payload = {
        "x-api-key": "hidden",
        "nested": [{"token": "hidden"}],
        "message": "Bearer forbidden",
    }
    result = redact(payload)
    assert "hidden" not in str(result)
    assert "forbidden" not in str(result)
    formatter = JsonFormatter(("private-value",))
    line = formatter.format(logging.LogRecord("test", 20, "", 0, "oops private-value", (), None))
    assert "private-value" not in line
    assert "[REDACTED]" in line
