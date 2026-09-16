"""Fabricated A5 contracts; real integration is an explicit CLI invocation."""

import json
from pathlib import Path

import httpx
import pytest

from intraday_etoro_lab.brokers import preflight
from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.transport import (
    COSTS,
    INSTRUMENTS,
    ME,
    ORDERS,
    PORTFOLIO,
    RATES,
    Credentials,
    GuardedTransport,
)
from intraday_etoro_lab.cli import main
from intraday_etoro_lab.config import load_config

MANIFEST = Path("docs/massive-a2-manifest.json")
CONFIG = load_config("configs/strategy-1-v1.yaml")
APP = "synthetic-app-placeholder"
USER = "synthetic-user-placeholder"


def responses():
    return {
        ME: {
            "demoCid": 42,
            "realCid": 99,
            "scopes": ["etoro-public:demo:read"],
            "firstName": "PRIVATE_PROFILE",
        },
        PORTFOLIO: {
            "clientPortfolio": {
                "credit": 10000,
                "positions": [],
                "orders": [],
                "mirrors": [],
                "ordersForOpen": [],
                "ordersForClose": [],
            }
        },
        INSTRUMENTS: {
            "results": [
                {"symbol": "AAPL", "type": "Stocks", "instrumentId": 1001, "exchangeId": 4}
            ],
            "pagination": {"hasNext": False},
        },
    }


def setup(monkeypatch, payloads=None, error=None):
    payloads = responses() if payloads is None else payloads
    calls = []

    def handler(request):
        calls.append(request)
        if error is not None:
            if isinstance(error, Exception):
                raise error
            return error
        return httpx.Response(200, json=payloads[request.url.path])

    monkeypatch.setenv("ETORO_API_KEY", APP)
    monkeypatch.setenv("ETORO_USER_KEY", USER)

    def factory(credentials, **kwargs):
        return GuardedTransport(
            credentials, **kwargs, transport=httpx.MockTransport(handler), sleeper=lambda _: None
        )

    monkeypatch.setattr(preflight, "GuardedTransport", factory)
    return calls


def test_success_and_sanitization(monkeypatch):
    calls = setup(monkeypatch)
    result = preflight.run_demo_preflight(CONFIG, MANIFEST)
    assert result["overall"] == "PASS"
    assert result["account_environment"] == "DEMO"
    assert result["permissions"]["observed"] == ["etoro-public:demo:read"]
    assert result["virtual_cash"]["value"] == "10000"
    assert result["instrument"]["symbol"] == "AAPL"
    assert [r.url.path for r in calls] == [ME, PORTFOLIO, INSTRUMENTS]
    assert all(r.method == "GET" for r in calls)
    assert result["writes"] == 0 and result["entries_armed"] is False
    for secret in (APP, USER, "PRIVATE_PROFILE", '"realCid"', '"demoCid"'):
        assert secret not in json.dumps(result)
    assert result["account_identifier"].startswith("demo-")


@pytest.mark.parametrize(
    "identity",
    [
        {},
        {"realCid": 99, "scopes": ["etoro-public:real:read"]},
        {"demoCid": "unknown", "scopes": ["etoro-public:demo:read"]},
        {"demoCid": True, "scopes": ["etoro-public:demo:read"]},
        {"demoCid": 42, "realCid": 42, "scopes": ["etoro-public:demo:read"]},
        {"demoCid": 42, "scopes": ["etoro-public:demo:read", "etoro-public:real:read"]},
        {"demoCid": 42, "scopes": []},
        {"demoCid": 42, "scopes": ["etoro-public:demo:read", "*"]},
        {"demoCid": 42, "scopes": ["etoro-public:demo:read", USER]},
        {"demoCid": 42},
    ],
)
def test_real_unknown_missing_ambiguous_fail_before_portfolio(monkeypatch, identity):
    payloads = responses()
    payloads[ME] = identity
    calls = setup(monkeypatch, payloads)
    result = preflight.run_demo_preflight(CONFIG, MANIFEST)
    assert result["overall"] == "FAIL"
    assert result["demo_verification"] == "FAIL"
    assert result["account_environment"] != "DEMO"
    assert [r.url.path for r in calls] == [ME]
    assert USER not in json.dumps(result)


@pytest.mark.parametrize("credit", [None, True, "NaN", "Infinity", -1, {}, []])
def test_invalid_cash(monkeypatch, credit):
    payloads = responses()
    payloads[PORTFOLIO]["clientPortfolio"]["credit"] = credit
    calls = setup(monkeypatch, payloads)
    result = preflight.run_demo_preflight(CONFIG, MANIFEST)
    assert result["reason"] == "DEMO_PORTFOLIO_UNVERIFIED"
    assert len(calls) == 2


@pytest.mark.parametrize(
    "client",
    [
        {},
        None,
        [],
        {"credit": 10},
        {**responses()[PORTFOLIO]["clientPortfolio"], "positions": [None]},
        {**responses()[PORTFOLIO]["clientPortfolio"], "positions": [{"CID": 99}]},
        {**responses()[PORTFOLIO]["clientPortfolio"], "CID": 99},
    ],
)
def test_malformed_portfolio(monkeypatch, client):
    payloads = responses()
    payloads[PORTFOLIO] = {"clientPortfolio": client}
    setup(monkeypatch, payloads)
    assert preflight.run_demo_preflight(CONFIG, MANIFEST)["overall"] == "FAIL"


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"results": None},
        {"results": [], "pagination": {"hasNext": False}},
        {"results": [None], "pagination": {"hasNext": False}},
        {**responses()[INSTRUMENTS], "pagination": {"hasNext": True}},
        {**responses()[INSTRUMENTS], "pagination": None},
        {**responses()[INSTRUMENTS], "results": responses()[INSTRUMENTS]["results"] * 2},
        *[
            {
                "results": [{**responses()[INSTRUMENTS]["results"][0], key: value}],
                "pagination": {"hasNext": False},
            }
            for key, value in [
                ("symbol", "QQQ"),
                ("type", "ETF"),
                ("instrumentId", True),
                ("exchangeId", 0),
            ]
        ],
    ],
)
def test_instrument_failure_retains_demo_evidence(monkeypatch, document):
    payloads = responses()
    payloads[INSTRUMENTS] = document
    setup(monkeypatch, payloads)
    result = preflight.run_demo_preflight(CONFIG, MANIFEST)
    assert result["overall"] == "FAIL"
    assert result["demo_verification"] == "PASS"
    assert result["instrument_check"] == "FAIL"


@pytest.mark.parametrize(
    "error,reason,attempts",
    [
        (httpx.Response(401, text=USER), "ETORO_HTTP_401", 1),
        (httpx.Response(403, text=USER), "ETORO_HTTP_403", 1),
        (httpx.Response(429, headers={"Retry-After": "60"}), "ETORO_HTTP_429", 1),
        (httpx.ReadTimeout(USER), "ETORO_READ_UNAVAILABLE", 3),
        (httpx.ConnectError(APP), "ETORO_READ_UNAVAILABLE", 3),
        (httpx.Response(200, text=USER), "INVALID_ETORO_RESPONSE", 1),
        (httpx.Response(200, json=[]), "INVALID_ETORO_RESPONSE", 1),
        (httpx.Response(200, text='{"demoCid":99,"demoCid":42}'), "INVALID_ETORO_RESPONSE", 1),
        (httpx.Response(202, json=responses()[ME]), "PREFLIGHT_UNEXPECTED_HTTP_STATUS", 1),
        (
            httpx.Response(302, headers={"Location": "https://invalid.example"}),
            "AUTHENTICATED_REDIRECT_BLOCKED",
            1,
        ),
    ],
)
def test_api_errors_redacted(monkeypatch, caplog, error, reason, attempts):
    calls = setup(monkeypatch, error=error)
    result = preflight.run_demo_preflight(CONFIG, MANIFEST)
    assert result["reason"] == reason
    assert result["overall"] == "FAIL"
    assert len(calls) == attempts
    for secret in (APP, USER):
        assert secret not in json.dumps(result) + caplog.text


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", ORDERS),
        ("PUT", ME),
        ("PATCH", "/api/v2/trading/demo/positions/1"),
        ("DELETE", ORDERS + "/1"),
        ("POST", COSTS),
        ("HEAD", ME),
        ("GET", RATES),
        ("GET", "/api/v1/trading/info/real/portfolio"),
    ],
)
def test_preflight_boundary_blocks_even_mock_mutations(method, path):
    calls = []
    transport = GuardedTransport(
        Credentials(APP, USER),
        mode="etoro_demo",
        session_id="test",
        config_hash="a" * 64,
        transport=httpx.MockTransport(lambda request: calls.append(request)),
    )
    try:
        transport.restrict_to_preflight()
        with pytest.raises(BrokerBlocked, match="PREFLIGHT_READ_ONLY_ROUTE_REQUIRED"):
            transport.request(method, path)
        assert not calls
    finally:
        transport.close()


def test_cli_evidence_and_no_overwrite(monkeypatch, tmp_path, capsys):
    calls = setup(monkeypatch)
    destination = tmp_path / "evidence.json"
    args = [
        "etoro",
        "preflight",
        "--read-only",
        "--config",
        "configs/strategy-1-v1.yaml",
        "--evidence",
        str(destination),
    ]
    assert main(args) == 0
    evidence = destination.read_bytes()
    assert json.loads(evidence)["overall"] == "PASS"
    assert main(args) == 2
    assert destination.read_bytes() == evidence
    assert all(r.method == "GET" for r in calls)
    output = capsys.readouterr().out
    assert APP not in output and USER not in output


def test_missing_credentials_produces_failure_evidence(tmp_path):
    destination = tmp_path / "missing.json"
    assert main(["etoro", "preflight", "--read-only", "--evidence", str(destination)]) == 2
    result = json.loads(destination.read_text())
    assert result["reason"] == "CREDENTIALS_MISSING_OR_INVALID"
    assert result["operations"] == []
    assert result["overall"] == "FAIL"


@pytest.mark.parametrize(
    "document",
    [
        None,
        {},
        {"schema_version": "other"},
        {"schema_version": "massive-a2-v1", "symbol": "QQQ"},
        {"schema_version": "massive-a2-v1", "symbol": "bad symbol"},
    ],
)
def test_invalid_manifest_before_network(monkeypatch, tmp_path, document):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(document))
    calls = setup(monkeypatch)
    result = preflight.run_demo_preflight(CONFIG, path)
    assert result["reason"] == "PREFLIGHT_STRATEGY_MANIFEST_INVALID"
    assert not calls
