"""Read-only spike contracts; fabricated messages are not provider observations."""

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("ws_probe", "scripts/probe_etoro_websocket.py")
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
NOW = datetime(2026, 9, 16, 19, 0, tzinfo=UTC)


def message(**changes):
    content = {"Bid": "100.01", "Ask": "100.02", "Date": NOW.isoformat(), "PriceRateID": "123"}
    content.update(changes)
    return {
        "topic": "instrument:1001",
        "type": "Trading.Instrument.Rate",
        "content": json.dumps(content),
    }


@pytest.mark.parametrize("age,fresh", [(0, True), (3, True), (3.000001, False), (-0.000001, False)])
def test_event_age_exact_gate(age, fresh):
    checked = NOW + timedelta(seconds=age)
    result = probe.rate(message(), checked, checked)
    assert result["fresh"] is fresh
    assert result["quote_age"] == age
    assert result["event_time"] == NOW.isoformat()


def test_prices_and_provider_stamp_preserved():
    stamp = "2026-09-16T14:00:00.1234567-05:00"
    result = probe.rate(message(Date=stamp), NOW + timedelta(seconds=1), NOW + timedelta(seconds=2))
    assert result["provider_timestamp"] == stamp
    assert result["bid"] == "100.01"
    assert result["ask"] == "100.02"
    assert result["price_rate_id"] == "123"
    assert result["received_at"] != result["event_time"]


@pytest.mark.parametrize(
    "changes",
    [
        {"Date": None},
        {"Date": "2026-09-16T19:00:00"},
        {"Date": "invalid"},
        {"Bid": None},
        {"Ask": None},
        {"Bid": "NaN"},
        {"Ask": "Infinity"},
        {"Bid": "0"},
        {"Bid": "101"},
        {"PriceRateID": "not-an-id"},
    ],
)
def test_invalid_quote_rejected(changes):
    with pytest.raises((ValueError, ArithmeticError)):
        probe.rate(message(**changes), NOW, NOW)


@pytest.mark.parametrize("field", ["Bid", "Ask", "Date"])
def test_required_fields(field):
    row = message()
    content = json.loads(row["content"])
    del content[field]
    row["content"] = json.dumps(content)
    with pytest.raises(KeyError):
        probe.rate(row, NOW, NOW)


def test_wrong_topic_or_private_message_blocked():
    row = message()
    row["topic"] = "private"
    with pytest.raises(ValueError):
        probe.rate(row, NOW, NOW)


def test_ambiguous_json_blocked():
    with pytest.raises(ValueError):
        probe.decode('{"success":true,"success":false}')


@pytest.mark.parametrize("success", [True, False])
def test_auth_ack_and_no_trading(monkeypatch, tmp_path, success):
    class Socket:
        def __init__(self):
            self.sent = []

        def getstatus(self):
            return 101

        def send(self, raw):
            self.sent.append(json.loads(raw))

        def recv(self):
            last = self.sent[-1]
            return json.dumps(
                {"id": last["id"], "operation": last["operation"], "success": success}
            )

        def close(self):
            pass

    class Library:
        @staticmethod
        def create_connection(url, **kwargs):
            assert url == "wss://ws.etoro.com/ws"
            assert kwargs["redirect_limit"] == 0
            return socket

    socket = Socket()
    ticks = iter([0, 121])
    monkeypatch.setattr(probe, "time", SimpleNamespace(monotonic=lambda: next(ticks)))
    monkeypatch.setattr(probe, "importlib", SimpleNamespace(import_module=lambda _: Library))
    monkeypatch.setenv("ETORO_API_KEY", "test-app-only")
    monkeypatch.setenv("ETORO_USER_KEY", "test-user-only")
    destination = tmp_path / "evidence"
    monkeypatch.setattr("sys.argv", ["probe", "--output", str(destination)])
    probe.main()
    report = json.loads((destination / "summary.json").read_text())
    assert report["authenticated"] is success
    assert report["state"] == "DISCONNECTED"
    assert report["mutations"] == 0
    assert [m["operation"] for m in socket.sent] == (
        ["Authenticate", "Subscribe"] if success else ["Authenticate"]
    )
    assert "test-app-only" not in (destination / "summary.json").read_text()
    assert report["events"] == 0


def test_no_production_integration():
    source = Path("scripts/probe_etoro_websocket.py").read_text()
    assert "EtoroDemoAdapter" not in source
    assert "RATES" not in source
    assert '"migration"] = "NOT_INTEGRATED"' in source
