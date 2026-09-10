"""Contract-only evidence; exact mock transport is never evidence of account access."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D

import httpx
import pytest
from test_etoro_adapter import build_adapter, intent, order_response
from test_etoro_transport import HASH, NOW, arm

from intraday_etoro_lab.brokers.authorization import BrokerBlocked, PreflightEvidence
from intraday_etoro_lab.brokers.transport import (
    COSTS,
    ELIGIBILITY,
    LOOKUP,
    ORDERS,
    Credentials,
    GuardedTransport,
    QuotaBudget,
    Route,
)
from intraday_etoro_lab.execution.models import OrderState, Position


def test_different_read_pools_cannot_multiply_shared_quota():
    quota = QuotaBudget(clock=lambda: 0)
    first, second = Route("GET", "/unused1", "one", 60), Route("GET", "/unused2", "two", 60)
    for _ in range(30):
        quota.take(first, False)
    for _ in range(25):
        quota.take(second, False)
    with pytest.raises(BrokerBlocked, match="RESERVED_CAPACITY"):
        quota.take(second, False)
    for _ in range(5):
        quota.take(second, True)
    with pytest.raises(BrokerBlocked, match="RESERVED_CAPACITY"):
        quota.take(first, True)


@pytest.mark.parametrize(
    "method,path,purpose",
    [
        ("POST", ORDERS, "entry"),
        ("DELETE", ORDERS + "/7", "management"),
        ("PATCH", "/api/v2/trading/demo/positions/8", "management"),
        ("POST", "/api/v1/trading/execution/demo/market-close-orders/positions/8", "management"),
        ("POST", COSTS, "entry"),
        ("POST", ELIGIBILITY, "entry"),
    ],
)
def test_network_mutations_blocked_even_with_valid_old_authorization(
    monkeypatch, method, path, purpose
):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("ORDER_SUBMISSION_ENABLED", "true")
    calls = []

    class NetworkSpy(httpx.BaseTransport):
        def handle_request(self, request):
            calls.append(request)
            raise AssertionError("network must not be reached")

    transport = GuardedTransport(
        Credentials("contract-app", "contract-user"),
        mode="etoro_demo",
        session_id="session",
        config_hash=HASH,
        transport=NetworkSpy(),
        now=lambda: NOW,
    )
    authorization = arm(transport)
    with pytest.raises(BrokerBlocked, match="EXTERNAL_MUTATIONS_DISABLED_PHASE2"):
        transport.request(
            method, path, permit=authorization.permit(purpose), request_id=intent().intent_id
        )
    assert calls == []
    transport.close()


def setup_close(rows=None, response_status=None):
    opening = intent(
        state=OrderState.FILLED,
        broker_order_id="7",
        filled_units=D(2),
        average_price=D(100),
        cumulative_cost=D(".2"),
    )
    closing = intent(
        kind="close", position_id="8", broker_order_id="9", state=OrderState.ACKNOWLEDGED
    )
    path = "/api/v1/trading/info/demo/close-orders/9"
    document = {
        "orderID": 9,
        "CID": 42,
        "statusID": 987654,
        "instrumentID": 123,
        "requestOccurred": NOW.isoformat(),
        "referenceID": closing.intent_id,
        "positions": rows
        if rows is not None
        else [{"positionID": 8, "units": 2, "occurred": NOW.isoformat(), "rate": 101}],
    }
    adapter, _, calls, store, positions = build_adapter(
        order_intent=opening, responses={path: response_status or document}
    )
    store[closing.intent_id] = closing
    positions["8"] = Position(
        position_id="8",
        owner_intent_id=opening.intent_id,
        session_id="session",
        symbol="TEST",
        units=D(2),
        average_entry=D(100),
        stop_price=D(99),
        protected=True,
        mode="etoro_demo",
    )
    return adapter, opening, closing, document, calls, store, positions


def test_v1_closed_units_are_evidence_not_final_accounting_or_enum():
    adapter, _, closing, doc, calls, _, _ = setup_close()
    update = adapter.query(closing.intent_id)
    assert update.state == OrderState.UNKNOWN
    assert update.remaining_units == 0 and update.observed_at == NOW
    assert update.filled_units == 0 and update.average_price is None
    assert update.cumulative_cost == 0  # no guessed fee or booked proceeds
    assert all(call.method == "GET" for call in calls)
    doc["positions"][0]["units"] = 1
    assert adapter.query(closing.intent_id).remaining_units == 1


@pytest.mark.parametrize("rows", [[], [{"positionID": 8}], [{"positionID": 8, "units": 2}]])
def test_empty_or_incomplete_close_detail_never_means_flat(rows):
    adapter, _, closing, _, _, _, _ = setup_close(rows)
    update = adapter.query(closing.intent_id)
    assert update.state == OrderState.UNKNOWN and update.remaining_units is None


@pytest.mark.parametrize("status", [404, 401, 403, 429, 500])
def test_close_http_failure_never_releases_exposure(status):
    adapter, _, closing, _, calls, _, _ = setup_close(response_status=status)
    adapter.transport.sleeper = lambda _: None
    if status == 404:
        assert adapter.query(closing.intent_id) is None
    else:
        with pytest.raises(BrokerBlocked):
            adapter.query(closing.intent_id)
    assert all(call.method == "GET" for call in calls)


@pytest.mark.parametrize(
    "change",
    [
        {"CID": 43},
        {"orderID": 10},
        {"instrumentID": 999},
        {"referenceID": "foreign"},
        {"statusID": "3"},
        {"positions": [{"positionID": 88, "units": 2, "occurred": NOW.isoformat()}]},
        {"positions": [{"positionID": 8}, {"positionID": 8}]},
        {"positions": [{"positionID": 8, "units": 3, "occurred": NOW.isoformat()}]},
        {"requestOccurred": (NOW - timedelta(days=1)).isoformat()},
    ],
)
def test_close_identity_and_inconsistent_detail_blocked(change):
    adapter, _, closing, doc, _, _, _ = setup_close()
    doc.update(change)
    with pytest.raises(BrokerBlocked, match="CORRELATION_OR_SCHEMA"):
        adapter.query(closing.intent_id)


def test_close_without_order_id_has_no_undocumented_reference_fallback():
    adapter, _, closing, _, calls, store, _ = setup_close()
    store[closing.intent_id] = closing.model_copy(update={"broker_order_id": None})
    assert adapter.query(closing.intent_id) is None
    assert calls == []


def test_read_only_identity_can_observe_closed_position_without_arming():
    doc = order_response()
    doc["positionExecutions"][0].update({"state": "closed", "remainingUnits": 0})
    doc["lastUpdate"] = NOW.isoformat()
    opening = intent(state=OrderState.FILLED, broker_order_id="7", filled_units=D(2))
    adapter, _, calls, _, _ = build_adapter(opening, {LOOKUP: doc})
    adapter.transport.authorization = None
    adapter.read_evidence = PreflightEvidence(
        42,
        frozenset({"etoro-public:demo:read"}),
        D(10000),
        NOW,
        adapter.transport.credentials.fingerprint,
    )
    update = adapter.query(opening.intent_id)
    assert update.state == OrderState.FILLED and update.remaining_units == 0
    assert update.filled_units == 2  # opening units are not closing fills
    assert adapter.transport.authorization is None
    adapter.read_evidence = replace(adapter.read_evidence, credential_fingerprint="changed")
    with pytest.raises(BrokerBlocked, match="CREDENTIAL_MISMATCH"):
        adapter.query(opening.intent_id)
    assert all(call.method == "GET" for call in calls)


@pytest.mark.parametrize(
    "change",
    [
        {"state": "closed", "remainingUnits": 1},
        {"state": "unknown", "remainingUnits": 0},
        {"state": "open", "remainingUnits": -1},
        {"state": "open", "remainingUnits": 3},
    ],
)
def test_position_state_contradiction_not_used_as_exposure(change):
    doc = order_response()
    doc["positionExecutions"][0].update(change)
    doc["lastUpdate"] = NOW.isoformat()
    adapter, item, _, _, _ = build_adapter(responses={LOOKUP: doc})
    with pytest.raises(BrokerBlocked, match="SCHEMA"):
        adapter.query(item.intent_id)
