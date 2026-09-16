from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from intraday_etoro_lab.brokers.authorization import (
    ActivationGates,
    BrokerBlocked,
    DemoAuthorization,
    PreflightEvidence,
)
from intraday_etoro_lab.brokers.transport import (
    COSTS,
    ME,
    ORDERS,
    PORTFOLIO,
    RATES,
    ROUTES,
    BrokerHTTPError,
    Credentials,
    GuardedTransport,
    QuotaBudget,
    SubmissionUnknown,
    _json_bytes,
    allowed_route,
)

NOW = datetime(2026, 9, 10, 14, 0, tzinfo=UTC)
HASH = "a" * 64


def make_transport(handler, mode="etoro_demo", now=lambda: NOW, **kwargs):
    return GuardedTransport(
        Credentials("test-app-placeholder", "test-user-placeholder"),
        mode=mode,
        session_id="session",
        config_hash=HASH,
        transport=httpx.MockTransport(handler),
        now=now,
        **kwargs,
    )


def arm(transport, *, identity_reads=True):
    # Existing lease tests now also need explicit provider identity responses.
    # Adapter/security tests supply their own responses and disable this fixture.
    mock = transport._contract_transport
    if identity_reads and type(mock) is httpx.MockTransport:
        original = mock.handler

        def observed(request):
            if request.method == "GET" and request.url.path == ME:
                return httpx.Response(
                    200, json={"demoCid": 42, "realCid": 99, "scopes": ["etoro-public:demo:write"]}
                )
            if request.method == "GET" and request.url.path == PORTFOLIO:
                return httpx.Response(
                    200,
                    json={
                        "clientPortfolio": {
                            "credit": 10000,
                            "positions": [],
                            "orders": [],
                            "mirrors": [],
                            "ordersForOpen": [],
                            "ordersForClose": [],
                        }
                    },
                )
            return original(request)

        mock.handler = observed
    authorization = DemoAuthorization("session", HASH)
    evidence = PreflightEvidence(
        42,
        frozenset({"etoro-public:demo:write"}),
        Decimal(10000),
        NOW,
        transport.credentials.fingerprint,
    )
    authorization.activate(
        evidence,
        ActivationGates(*([True] * 7)),
        accepted_budget=Decimal(1000),
        explicit_confirmation=True,
        submission_enabled=True,
        now=NOW,
        entry_seconds=300,
    )
    transport.authorization = authorization
    return authorization


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "https://evil.invalid/api/v1/me"),
        ("GET", "//public-api.etoro.com/api/v1/me"),
        ("GET", "/api/v1/trading/info/real/portfolio"),
        ("POST", "/api/v1/trading/orders"),
        ("GET", "/api/v1/me/"),
        ("GET", "/api/v1//me"),
        ("GET", "/api/v1/./me"),
        ("GET", "/api/v1/x/../me"),
        ("GET", "/api/v1/%6de"),
        ("GET", "/api/v1/me?x=1"),
        ("GET", "/api/v1/me#fragment"),
        ("GET", "/api/v1\\me"),
        ("get", "/api/v1/me"),
        ("POST", ME),
        ("DELETE", f"{ORDERS}/01"),
        ("GET", ME + "\n"),
        ("GET", "/api/v1/market-data/instruments/1/history/candles/asc/OneMinute/1001"),
        ("POST", "/api/v3/trading/execution/demo/orders"),
    ],
)
def test_unapproved_destination_never_reaches_network(method, path):
    calls = []
    transport = make_transport(lambda request: calls.append(request))
    with pytest.raises(BrokerBlocked):
        transport.request(method, path)
    assert not calls


def test_credentials_headers_origin_and_redaction(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://evil.invalid")
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"ok": True})

    transport = make_transport(handler)
    assert transport.request("GET", ME) == {"ok": True}
    request = calls[0]
    assert str(request.url) == "https://public-api.etoro.com/api/v1/me"
    assert request.headers["x-api-key"] == "test-app-placeholder"
    assert request.headers["x-user-key"] == "test-user-placeholder"
    assert "authorization" not in request.headers
    assert "placeholder" not in repr(transport.credentials)
    transport.close()


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirect_not_followed(status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, headers={"Location": "https://evil.invalid/"})

    with pytest.raises(BrokerBlocked, match="REDIRECT"):
        make_transport(handler).request("GET", ME)
    assert len(calls) == 1


@pytest.mark.parametrize("mode", ["offline", "backtest", "live", "real", "production_trading"])
def test_transport_rejects_nonconnected_modes(mode):
    with pytest.raises(BrokerBlocked):
        make_transport(lambda request: httpx.Response(200, json={}), mode=mode)


@pytest.mark.parametrize("api,user", [("", "x"), ("x", ""), ("x\n", "y"), ("x", "y y")])
def test_missing_credentials(api, user):
    with pytest.raises(BrokerBlocked):
        Credentials(api, user)


def test_credentials_environment(monkeypatch):
    monkeypatch.setenv("ETORO_API_KEY", "demo-placeholder-app")
    monkeypatch.setenv("ETORO_USER_KEY", "demo-placeholder-user")
    assert Credentials.from_environment().api_key == "demo-placeholder-app"
    monkeypatch.delenv("ETORO_API_KEY")
    with pytest.raises(BrokerBlocked):
        Credentials.from_environment()


def test_undocumented_query_and_get_body():
    transport = make_transport(lambda request: pytest.fail("network reached"))
    with pytest.raises(BrokerBlocked, match="QUERY"):
        transport.request("GET", RATES, params={"url": "https://evil.invalid"})
    with pytest.raises(BrokerBlocked, match="GET_BODY"):
        transport.request("GET", ME, body={})


@pytest.mark.parametrize("mode,ci", [("shadow", ""), ("etoro_demo", "true")])
def test_shadow_and_ci_cannot_mutate(mode, ci, monkeypatch):
    monkeypatch.setenv("CI", ci)
    transport = make_transport(lambda request: pytest.fail("network reached"), mode=mode)
    authorization = arm(transport)
    with pytest.raises(BrokerBlocked, match="MUTATION_DISABLED"):
        transport.request(
            "POST", ORDERS, body={}, request_id=str(uuid4()), permit=authorization.permit("entry")
        )
    # Semantic read POST remains permitted in shadow.
    shadow = make_transport(lambda request: httpx.Response(200, json={"costs": []}), mode="shadow")
    assert shadow.request("POST", COSTS, body={}) == {"costs": []}


def test_mutation_requires_bound_permit_and_uuid(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    transport = make_transport(lambda request: httpx.Response(200, json={}))
    with pytest.raises(BrokerBlocked, match="AUTHORIZATION_REQUIRED"):
        transport.request("POST", ORDERS)
    authorization = arm(transport)
    with pytest.raises(BrokerBlocked, match="AUTHORIZATION_REQUIRED"):
        transport.request("POST", ORDERS, permit=authorization.permit("management"))
    with pytest.raises(BrokerBlocked, match="PERSISTED_REQUEST"):
        transport.request("POST", ORDERS, permit=authorization.permit("entry"))
    with pytest.raises(BrokerBlocked, match="UUID"):
        transport.request("POST", ORDERS, permit=authorization.permit("entry"), request_id="foo")
    assert (
        transport.request(
            "POST",
            ORDERS,
            permit=authorization.permit("entry"),
            request_id=str(uuid4()),
            body={"units": Decimal("0.123456789")},
        )
        == {}
    )


def test_pause_preserves_management_and_expiration(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    clock = [NOW]
    transport = make_transport(lambda request: httpx.Response(200, json={}), now=lambda: clock[0])
    authorization = arm(transport)
    clock[0] += timedelta(seconds=301)
    with pytest.raises(BrokerBlocked, match="EXPIRED"):
        transport.request(
            "POST", ORDERS, permit=authorization.permit("entry"), request_id=str(uuid4())
        )
    authorization.pause_entries()
    assert (
        transport.request(
            "DELETE",
            ORDERS + "/1",
            permit=authorization.permit("management"),
            request_id=str(uuid4()),
        )
        == {}
    )
    clock[0] += timedelta(seconds=3600)
    with pytest.raises(BrokerBlocked, match="EXPIRED"):
        transport.request(
            "DELETE",
            ORDERS + "/1",
            permit=authorization.permit("management"),
            request_id=str(uuid4()),
        )


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("session_id", "other", "BINDING"),
        ("config_hash", "b" * 64, "BINDING"),
        ("credentials", Credentials("other", "key"), "CREDENTIALS"),
    ],
)
def test_changes_disarm(field, value, reason, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    transport = make_transport(lambda request: pytest.fail("network reached"))
    authorization = arm(transport)
    setattr(transport, field, value)
    with pytest.raises(BrokerBlocked, match=reason):
        transport.request(
            "POST", ORDERS, permit=authorization.permit("entry"), request_id=str(uuid4())
        )


def test_restart_and_forged_permit_are_disarmed():
    old = make_transport(lambda request: httpx.Response(200, json={}))
    authorization = arm(old)
    new = DemoAuthorization("session", HASH)
    with pytest.raises(BrokerBlocked, match="NOT_ARMED"):
        new.check(
            authorization.permit("entry"),
            session_id="session",
            config_hash=HASH,
            credential_fingerprint=old.credentials.fingerprint,
            now=NOW,
        )
    with pytest.raises(BrokerBlocked, match="PREFLIGHT_REQUIRED"):
        _ = new.account_id
    assert authorization.account_id == 42
    assert authorization.budget == Decimal(1000)


@pytest.mark.parametrize(
    "case",
    [
        "confirmation",
        "enabled",
        "gates",
        "duration",
        "management",
        "timezone",
        "stale",
        "scope",
        "real_scope",
        "budget",
        "nan",
    ],
)
def test_activation_fails_closed(case):
    transport = make_transport(lambda request: httpx.Response(200, json={}))
    authorization = DemoAuthorization("session", HASH)
    evidence = PreflightEvidence(
        42,
        frozenset({"etoro-public:demo:write"}),
        Decimal(10000),
        NOW,
        transport.credentials.fingerprint,
    )
    kwargs = dict(
        accepted_budget=Decimal(1000),
        explicit_confirmation=True,
        submission_enabled=True,
        now=NOW,
        entry_seconds=300,
        management_seconds=3600,
    )
    gates = ActivationGates(*([True] * 7))
    if case == "confirmation":
        kwargs["explicit_confirmation"] = False
    if case == "enabled":
        kwargs["submission_enabled"] = False
    if case == "gates":
        gates = ActivationGates()
    if case == "duration":
        kwargs["entry_seconds"] = 1000
    if case == "management":
        kwargs["management_seconds"] = 1
    if case == "timezone":
        kwargs["now"] = NOW.replace(tzinfo=None)
    if case == "stale":
        kwargs["now"] = NOW + timedelta(minutes=2)
    if case == "scope":
        evidence = PreflightEvidence(42, frozenset(), Decimal(10000), NOW, "x")
    if case == "real_scope":
        evidence = PreflightEvidence(
            42,
            frozenset({"etoro-public:demo:write", "etoro-public:real:write"}),
            Decimal(10000),
            NOW,
            "x",
        )
    if case == "budget":
        kwargs["accepted_budget"] = Decimal(10001)
    if case == "nan":
        kwargs["accepted_budget"] = Decimal("NaN")
    with pytest.raises(BrokerBlocked):
        authorization.activate(evidence, gates, **kwargs)


def test_invalid_session_hash():
    with pytest.raises(BrokerBlocked):
        DemoAuthorization("", "a")


def test_write_timeout_never_retried(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("sensitive backend detail must not surface")

    transport = make_transport(handler)
    authorization = arm(transport)
    with pytest.raises(SubmissionUnknown, match="UNKNOWN_RECONCILE") as error:
        transport.request(
            "POST", ORDERS, permit=authorization.permit("entry"), request_id=str(uuid4())
        )
    assert len(calls) == 1
    assert "sensitive" not in str(error.value)


@pytest.mark.parametrize("failure", ["timeout", "500"])
def test_reads_bounded_retries(failure):
    calls, sleeps = [], []

    def handler(request):
        calls.append(request)
        if failure == "timeout":
            raise httpx.ConnectError("private error")
        return httpx.Response(500)

    with pytest.raises(BrokerBlocked):
        make_transport(handler, sleeper=sleeps.append).request("GET", ME)
    assert len(calls) == 3 and len(sleeps) == 2


@pytest.mark.parametrize("status", [401, 403, 404, 422])
def test_no_retry_auth_permission_client_errors(status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"errorMessage": "sensitive"})

    with pytest.raises(BrokerHTTPError) as error:
        make_transport(handler).request("GET", ME)
    assert error.value.status == status and "sensitive" not in str(error.value)
    assert len(calls) == 1


@pytest.mark.parametrize("content", [b"not json", b"[]", b"\xff"])
def test_invalid_responses(content):
    with pytest.raises(BrokerBlocked, match="INVALID_ETORO"):
        make_transport(lambda request: httpx.Response(200, content=content)).request("GET", ME)


def test_shared_quota_reserves_management_capacity():
    clock = [0.0]
    quota = QuotaBudget(lambda: clock[0])
    market = next(route for route in ROUTES if route.pattern == RATES)
    for _ in range(55):
        quota.take(market, False)
    with pytest.raises(BrokerBlocked, match="RESERVED_CAPACITY"):
        quota.take(market, False)
    for _ in range(5):
        quota.take(market, True)
    with pytest.raises(BrokerBlocked):
        quota.take(market, True)
    clock[0] = 60
    quota.take(market, False)
    assert allowed_route("GET", PORTFOLIO).pool == "portfolio"


def test_retry_after_enforced_and_shared():
    clock = [0.0]
    calls = []
    quota = QuotaBudget(lambda: clock[0])

    def sleep(delay):
        clock[0] += delay

    def handler(request):
        calls.append(request)
        return (
            httpx.Response(429, headers={"Retry-After": "2"})
            if len(calls) == 1
            else httpx.Response(200, json={})
        )

    transport = make_transport(handler, sleeper=sleep, quota=quota)
    assert transport.request("GET", ME) == {}
    assert len(calls) == 2 and clock[0] == 2
    transport = make_transport(
        lambda request: httpx.Response(429, headers={"Retry-After": "90"}), quota=quota
    )
    with pytest.raises(BrokerHTTPError):
        transport.request("GET", ME)
    with pytest.raises(BrokerBlocked, match="RETRY_AFTER_PENDING"):
        transport.request("GET", RATES)


@pytest.mark.parametrize(
    "header,expected", [("bad", 60), ("-1", 60), ("nan", 60), ("Thu, 10 Sep 2026 14:00:05 GMT", 5)]
)
def test_retry_after_parsing(header, expected):
    transport = make_transport(lambda request: httpx.Response(200, json={}))
    assert transport._retry_after(httpx.Response(429, headers={"Retry-After": header})) == expected


def test_decimal_wire_values_are_exact():
    assert (
        _json_bytes({"units": Decimal("0.123456789123456789"), "nested": [True, None]})
        == b'{"units":0.123456789123456789,"nested":[true,null]}'
    )
    with pytest.raises(BrokerBlocked):
        _json_bytes(Decimal("NaN"))
