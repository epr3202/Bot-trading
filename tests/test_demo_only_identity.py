"""A7 partial delivery: identity defenses, never evidence of external trading."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError
from test_etoro_adapter import build_adapter, identity, intent, order_response, portfolio
from test_etoro_transport import NOW, arm, make_transport
from test_execution_engine import request as entry_request

from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.identity import AccountType, classify_identity
from intraday_etoro_lab.brokers.transport import (
    LOOKUP,
    ME,
    ORDERS,
    PORTFOLIO,
    Credentials,
    allowed_route,
)
from intraday_etoro_lab.config import AppConfig, load_config
from intraday_etoro_lab.execution.engine import Executor
from intraday_etoro_lab.execution.models import OrderState, Position
from intraday_etoro_lab.persistence import StateStore
from intraday_etoro_lab.risk import InstrumentRules, RiskEngine

REAL = {"demoCid": 42, "realCid": 99, "scopes": ["etoro-public:real:write"]}
MUTATIONS = [
    ("POST", ORDERS, "entry"),
    ("DELETE", ORDERS + "/7", "management"),
    ("PATCH", "/api/v2/trading/demo/positions/8", "management"),
    ("POST", "/api/v1/trading/execution/demo/market-close-orders/positions/8", "management"),
]


def mutations(calls):
    return [r for r in calls if allowed_route(r.method, r.url.path, dict(r.url.params)).mutation]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.delenv("CI", raising=False)

    def denied(*args, **kwargs):
        pytest.fail("A7 contracts must never access the network")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", denied)


@pytest.mark.parametrize(
    "document,expected",
    [
        (identity(), AccountType.DEMO),
        (REAL, AccountType.REAL),
        ({"realCid": 99, "scopes": ["etoro-public:real:read"]}, AccountType.REAL),
        ({}, AccountType.UNKNOWN),
        ({**identity(), "demoCid": True}, AccountType.UNKNOWN),
        ({**identity(), "demoCid": "42"}, AccountType.UNKNOWN),
        ({**identity(), "demoCid": 99}, AccountType.UNKNOWN),
        ({**identity(), "realCid": "42"}, AccountType.UNKNOWN),
        ({**identity(), "realCid": True}, AccountType.UNKNOWN),
        ({**identity(), "realCid": -1}, AccountType.UNKNOWN),
        ({**identity(), "scopes": ["etoro-public:demo:*"]}, AccountType.UNKNOWN),
        ({**identity(), "scopes": [42]}, AccountType.UNKNOWN),
        ({**identity(), "scopes": ["etoro-public:user-info:read"]}, AccountType.UNKNOWN),
        ({"isDemo": True, "mode": "demo", "accountType": "virtual"}, AccountType.UNKNOWN),
        ({**identity(), "scopes": identity()["scopes"] + REAL["scopes"]}, AccountType.REAL),
    ],
)
def test_observed_access_classification(document, expected):
    observed = classify_identity(document)
    assert observed.account_type == expected
    assert "Do not retain" not in repr(observed)
    assert "account_id" not in repr(observed)


@pytest.mark.parametrize("operation", ["submit", "cancel", "close", "protect"])
@pytest.mark.parametrize(
    "observed,reason",
    [(REAL, "NON_DEMO_SCOPE"), ({}, "UNVERIFIED"), (403, "ETORO_HTTP_403")],
    ids=["real", "unknown", "identity_error"],
)
def test_adapter_rejects_identity_with_zero_mutations(operation, observed, reason):
    adapter, opening, calls, store, positions = build_adapter(responses={ME: observed})
    positions["8"] = Position(
        position_id="8",
        owner_intent_id=opening.intent_id,
        session_id="session",
        symbol="TEST",
        units=Decimal(2),
        average_entry=Decimal(100),
        stop_price=Decimal(99),
        protected=True,
        mode="etoro_demo",
    )
    closing = intent(kind="close", position_id="8")
    store[closing.intent_id] = closing
    with pytest.raises(BrokerBlocked, match=reason):
        if operation == "protect":
            adapter.protect("8", Decimal(100))
        else:
            getattr(adapter, operation)(closing if operation == "close" else opening)
    assert mutations(calls) == []
    assert all(r.method == "GET" for r in calls)
    assert store[opening.intent_id] == opening and store[closing.intent_id] == closing
    assert adapter.transport.authorization.budget > 0
    with pytest.raises(BrokerBlocked, match="PREFLIGHT_REQUIRED"):
        _ = adapter.transport.authorization.account_id


@pytest.mark.parametrize("method,path,purpose", MUTATIONS)
@pytest.mark.parametrize("observed", [REAL, {}, "timeout"], ids=["real", "unknown", "error"])
def test_direct_transport_cannot_bypass_identity(method, path, purpose, observed):
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path == ME:
            if observed == "timeout":
                raise httpx.ReadTimeout("PRIVATE_BACKEND_DETAIL")
            return httpx.Response(200, json=observed)
        pytest.fail("identity rejection must precede every other request")

    transport = make_transport(handler, sleeper=lambda _: None)
    authorization = arm(transport, identity_reads=False)
    with pytest.raises(BrokerBlocked) as error:
        transport.request(
            method, path, permit=authorization.permit(purpose), request_id=str(uuid4())
        )
    assert mutations(calls) == []
    assert all(r.url.path == ME for r in calls)
    assert "PRIVATE_BACKEND_DETAIL" not in str(error.value)


@pytest.mark.parametrize("method,path,purpose", MUTATIONS)
def test_direct_mutation_requires_authorization_even_with_demo(method, path, purpose):
    calls = []
    transport = make_transport(lambda request: calls.append(request))
    with pytest.raises(BrokerBlocked, match="AUTHORIZATION_REQUIRED"):
        transport.request(method, path, request_id=str(uuid4()))
    assert calls == []


def test_demo_contract_submit_then_reconcile_ack_is_not_fill():
    adapter, item, calls, _, _ = build_adapter()
    result = adapter.submit(item)
    assert result.state == OrderState.ACKNOWLEDGED and result.filled_units == 0
    writes = mutations(calls)
    assert len(writes) == 1 and writes[0].url.path == ORDERS
    assert writes[0].headers["x-request-id"] == item.intent_id
    assert [r.url.path for r in calls[-3:]] == [ME, PORTFOLIO, ORDERS]
    assert len([r for r in calls if r.url.path == ME]) == 2
    reconciled = adapter.query(item.intent_id)
    assert reconciled.state == OrderState.FILLED and reconciled.filled_units == 2


def test_identity_changed_between_adapter_and_transport_blocks_write():
    adapter, item, calls, _, _ = build_adapter()
    mock = adapter.transport._contract_transport
    original = mock.handler
    reads = 0

    def changed(request):
        nonlocal reads
        if request.url.path == ME:
            reads += 1
            if reads == 2:
                calls.append(request)
                return httpx.Response(200, json=REAL)
        return original(request)

    mock.handler = changed
    with pytest.raises(BrokerBlocked, match="NON_DEMO_SCOPE"):
        adapter.submit(item)
    assert reads == 2 and mutations(calls) == []


@pytest.mark.parametrize(
    "case", ["account", "credential", "session", "config", "expiry", "read_only"]
)
def test_identity_refresh_bound_to_current_lease(case):
    calls = []
    clock = [NOW]

    def handler(request):
        calls.append(request)
        if request.url.path == ME:
            doc = identity()
            if case == "account":
                doc["demoCid"] = 43
            if case == "read_only":
                doc["scopes"] = ["etoro-public:demo:read"]
            return httpx.Response(200, json=doc)
        if request.url.path == PORTFOLIO:
            if case == "credential":
                transport.credentials = Credentials("changed-app", "changed-user")
            if case == "session":
                transport.session_id = "changed-session"
            if case == "config":
                transport.config_hash = "b" * 64
            if case == "expiry":
                clock[0] += timedelta(seconds=301)
            return httpx.Response(200, json=portfolio())
        pytest.fail("must not dispatch a mutation")

    transport = make_transport(handler, now=lambda: clock[0])
    authorization = arm(transport, identity_reads=False)
    with pytest.raises(BrokerBlocked):
        transport.request(
            "POST", ORDERS, permit=authorization.permit("entry"), request_id=str(uuid4())
        )
    assert mutations(calls) == []


@pytest.mark.parametrize(
    "status,body",
    [
        (200, b'{"demoCid":42,"demoCid":43,"scopes":["etoro-public:demo:write"]}'),
        (201, b"{}"),
        (200, b"null"),
        (200, b"not-json"),
    ],
)
def test_ambiguous_identity_response_never_authorizes(status, body):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, content=body)

    transport = make_transport(handler)
    authorization = arm(transport, identity_reads=False)
    with pytest.raises(BrokerBlocked):
        transport.request(
            "POST", ORDERS, permit=authorization.permit("entry"), request_id=str(uuid4())
        )
    assert len(calls) == 1 and mutations(calls) == []


@pytest.mark.parametrize("mode", ["real", "live", "production"])
def test_nominal_real_configuration_cannot_enable_trading(mode, monkeypatch):
    with pytest.raises(ValidationError):
        AppConfig(mode=mode, order_submission_enabled=True)
    monkeypatch.setenv("BOT_MODE", mode)
    monkeypatch.setenv("ORDER_SUBMISSION_ENABLED", "true")
    with pytest.raises((ValidationError, ValueError)):
        load_config()


def test_deceptive_demo_environment_and_real_keys_cannot_authorize(monkeypatch):
    monkeypatch.setenv("BOT_MODE", "etoro_demo")
    monkeypatch.setenv("ORDER_SUBMISSION_ENABLED", "true")
    monkeypatch.setenv("ETORO_BASE_URL", "https://example.invalid/real")
    monkeypatch.setenv("ETORO_ACCOUNT_ID", "99")
    adapter, item, calls, _, _ = build_adapter(responses={ME: REAL})
    assert load_config().mode.value == "etoro_demo"
    with pytest.raises(BrokerBlocked, match="NON_DEMO_SCOPE"):
        adapter.submit(item)
    assert mutations(calls) == []
    assert all(r.url.host == "public-api.etoro.com" for r in calls)


def test_real_route_is_never_supported():
    for method, path, _ in MUTATIONS:
        with pytest.raises(BrokerBlocked, match="ROUTE_NOT_ALLOWED"):
            allowed_route(method, path.replace("/demo/", "/real/"))


@pytest.mark.parametrize(
    "observed", [identity(), REAL, {}, 403], ids=["demo", "real", "unknown", "error"]
)
def test_executor_identity_guards_preserve_durable_state(tmp_path, observed):
    """SQLite + Executor/RiskEngine + adapter, exclusively mock HTTP.

    This explicit test wiring does not add a connected runner or arm command.
    Rejected verification releases reservations only on proven pre-send failure.
    """
    ledger = StateStore(tmp_path / "state.sqlite", mode="etoro_demo")
    adapter, _, calls, _, _ = build_adapter(responses={ME: observed})
    adapter.intent_loader = ledger.intent
    adapter.position_loader = ledger.position
    mock = adapter.transport._contract_transport
    original = mock.handler

    def broker(request):
        if request.url.path == ORDERS:
            saved = ledger.intent(request.headers["x-request-id"])
            assert saved.state == OrderState.SUBMITTING
            assert ledger.portfolio("session").reserved_cash > 0
            assert saved.planned_risk > 0 and saved.estimated_cost > 0
            calls.append(request)
            return httpx.Response(200, json={"orderId": 7, "referenceId": saved.intent_id})
        if request.url.path == LOOKUP:
            calls.append(request)
            saved = ledger.intents()[0]
            response = order_response()
            response["positionExecutions"][0]["openingData"]["units"] = int(saved.units)
            return httpx.Response(200, json=response)
        return original(request)

    mock.handler = broker
    request = replace(
        entry_request("TEST"),
        session_id="session",
        now=NOW,
        quote_at=NOW,
        available_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=9),
        entry_price=Decimal("100.01"),
        ask=Decimal("100.01"),
        bid=Decimal(100),
        rules=InstrumentRules(unit_step=Decimal(1)),
    )
    with Executor(ledger, adapter, RiskEngine(), "session") as executor:
        ledger.pause("session", False)  # Test-only activation; no production arming route.
        result = executor.submit_entry(request)
        assert result.decision.approved and result.intent is not None
        if observed == identity():
            assert result.intent.state == OrderState.ACKNOWLEDGED
            assert len(mutations(calls)) == 1 and not ledger.positions()
            assert executor.reconcile()
            assert ledger.intent(result.intent.intent_id).state == OrderState.FILLED
            assert len(ledger.positions()) == 1
        else:
            assert result.intent.state == OrderState.REJECTED and not ledger.positions()
            assert ledger.portfolio("session").reserved_cash == 0
            assert ledger.session("session").entries_paused
            assert executor.reconcile()
            assert any(e["kind"] == "REJECTED_PRE_SEND" for e in ledger.events())
            assert mutations(calls) == []
        before = len(mutations(calls))
        assert executor.submit_entry(request).duplicate
        assert len(mutations(calls)) == before
    ledger.close()
