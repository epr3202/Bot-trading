import os
import ssl

import certifi
import httpx
import pytest

from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.transport import create_http_client


@pytest.fixture(autouse=True)
def clean_network_environment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
    ):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    # Also avoid Windows registry proxy discovery in these isolated tests.
    monkeypatch.setattr(
        "httpx._utils.getproxies",
        lambda: {
            key.lower().removesuffix("_proxy"): value
            for key, value in os.environ.items()
            if key in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"}
        },
    )


@pytest.mark.parametrize("bypass", [False, True])
def test_environment_proxy_routing_and_tls(monkeypatch, bypass):
    calls = []

    def factory(**kwargs):
        def handle(request):
            calls.append(kwargs)
            return httpx.Response(200)

        return httpx.MockTransport(handle)

    monkeypatch.setattr("httpx._client.HTTPTransport", factory)
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:8080")
    if bypass:
        monkeypatch.setenv("NO_PROXY", "public-api.etoro.com")
    with create_http_client() as client:
        client.get("https://public-api.etoro.com/")
        assert client.follow_redirects is False
    assert len(calls) == 1
    assert (calls[0].get("proxy") is None) is bypass
    assert calls[0]["verify"] is True


@pytest.mark.parametrize("local", [False, True])
def test_corporate_ca_loaded_with_verification(monkeypatch, tmp_path, local):
    from pathlib import Path

    if local:
        (tmp_path / "certs").mkdir()
        (tmp_path / "certs/epm-root.cer").write_bytes(Path(certifi.where()).read_bytes())
        monkeypatch.setenv("REQUESTS_CA_BUNDLE", "missing-ignored-by-local-ca.pem")
    else:
        monkeypatch.setenv("REQUESTS_CA_BUNDLE", certifi.where())
    with create_http_client() as client:
        context = client._transport._pool._ssl_context
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname
        assert context.cert_store_stats()["x509_ca"] > 0


@pytest.mark.parametrize("invalid", ["missing", "malformed"])
def test_invalid_ca_fails_without_fallback(monkeypatch, tmp_path, invalid):
    ca = tmp_path / "private-ca.pem"
    if invalid == "malformed":
        ca.write_text("not a certificate")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(ca))
    with pytest.raises(BrokerBlocked, match="TLS_OR_PROXY_CONFIGURATION_INVALID") as error:
        create_http_client()
    assert str(tmp_path) not in str(error.value)


def test_injected_transport_ignores_proxy_and_ca(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "unsupported://private-user:private-password@proxy.invalid")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "missing.pem")
    with create_http_client(transport=httpx.MockTransport(lambda r: httpx.Response(200))) as client:
        assert client.get("https://public-api.etoro.com/").status_code == 200


def test_invalid_proxy_is_redacted(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "unsupported://private-user:private-password@proxy.invalid")
    with pytest.raises(BrokerBlocked, match="TLS_OR_PROXY_CONFIGURATION_INVALID") as error:
        create_http_client()
    assert "private-password" not in str(error.value)
