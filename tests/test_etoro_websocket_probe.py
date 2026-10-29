"""Read-only spike contracts; fabricated messages are not provider observations."""

import importlib.util
import json
import ssl
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("ws_probe", "scripts/probe_etoro_websocket.py")
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
NOW = datetime(2026, 9, 16, 19, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def isolated_proxy(monkeypatch):
    for name in ("HOST", "PORT", "USER", "PASSWORD"):
        monkeypatch.delenv(f"ETORO_PROXY_{name}", raising=False)


def configure_proxy(monkeypatch):
    for name, value in {
        "HOST": "proxy.epm.com.co",
        "PORT": "8080",
        "USER": "example-domain\\example-user",
        "PASSWORD": "example:p@ss#word",
    }.items():
        monkeypatch.setenv(f"ETORO_PROXY_{name}", value)


def test_proxy_auth_separate_from_destination_and_no_bypass(monkeypatch):
    configure_proxy(monkeypatch)
    monkeypatch.setenv("NO_PROXY", "*")
    options = probe.proxy_options()
    assert options["http_proxy_auth"] == ("example-domain\\example-user", "example:p@ss#word")
    assert options["http_proxy_host"] == "proxy.epm.com.co"
    assert options["http_proxy_port"] == 8080
    assert options["http_no_proxy"] == ["localhost", "127.0.0.1"]
    assert options["proxy_type"] == "http"


@pytest.mark.parametrize("name", ["HOST", "PORT", "USER", "PASSWORD"])
def test_partial_proxy_configuration_fails_closed(monkeypatch, name):
    configure_proxy(monkeypatch)
    monkeypatch.delenv(f"ETORO_PROXY_{name}")
    with pytest.raises(ValueError, match="PROXY_"):
        probe.proxy_options()


def test_unconfigured_proxy_keeps_existing_environment_behavior():
    assert probe.proxy_options() == {}


def test_proxy_secrets_redacted_in_all_supported_forms(monkeypatch):
    configure_proxy(monkeypatch)
    user, password = probe.proxy_options()["http_proxy_auth"]
    encoded = probe.base64.b64encode(f"{user}:{password}".encode()).decode()
    escaped = probe.quote(password, safe="")
    assert probe.redact(f"{user} {password} {encoded} {escaped}") == " ".join(["[REDACTED]"] * 4)


@pytest.mark.parametrize("encoding", ["PEM", "DER"])
def test_tls_loads_ca_independent_of_cwd_and_preserves_public_trust(
    monkeypatch, tmp_path, encoding
):
    public = Path(probe.certifi.where()).read_text()
    start = public.index("-----BEGIN CERTIFICATE-----")
    end = public.index("-----END CERTIFICATE-----", start) + len("-----END CERTIFICATE-----")
    pem = public[start:end]
    data = pem.encode() if encoding == "PEM" else ssl.PEM_cert_to_DER_cert(pem)
    (tmp_path / "certs").mkdir()
    (tmp_path / "certs" / "epm-root.cer").write_bytes(data)
    monkeypatch.setattr(probe, "PROJECT_ROOT", tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    context, report = probe.tls_context()
    public_context = ssl.create_default_context(cafile=probe.certifi.where())
    assert set(public_context.get_ca_certs(binary_form=True)) <= set(
        context.get_ca_certs(binary_form=True)
    )
    assert context.check_hostname
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert report["certificate_loaded"]


def test_missing_corporate_ca_never_silently_falls_back(monkeypatch, tmp_path):
    monkeypatch.setattr(probe, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", probe.certifi.where())
    with pytest.raises(ValueError, match="PROXY_CA_MISSING"):
        probe.tls_context()


def test_invalid_corporate_ca_rejected(monkeypatch, tmp_path):
    (tmp_path / "certs").mkdir()
    (tmp_path / "certs" / "epm-root.cer").write_bytes(b"invalid certificate")
    monkeypatch.setattr(probe, "PROJECT_ROOT", tmp_path)
    with pytest.raises(ssl.SSLError):
        probe.tls_context()


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
            assert kwargs["http_proxy_auth"] == (
                "example-domain\\example-user",
                "example:p@ss#word",
            )
            assert kwargs["sslopt"]["context"].check_hostname
            return socket

    socket = Socket()
    configure_proxy(monkeypatch)
    monkeypatch.setattr(probe, "tls_context", lambda: (ssl.create_default_context(), {}))
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
