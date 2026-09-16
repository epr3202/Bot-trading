from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from test_etoro_transport import NOW, arm, make_transport

from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.etoro_demo import EntryReview, EtoroDemoAdapter, perform_preflight
from intraday_etoro_lab.brokers.market_data import EtoroMarketDataProvider
from intraday_etoro_lab.brokers.transport import (
    COSTS,
    ELIGIBILITY,
    INSTRUMENTS,
    LOOKUP,
    ME,
    ORDERS,
    PORTFOLIO,
    RATES,
)
from intraday_etoro_lab.domain import Instrument
from intraday_etoro_lab.execution.models import OrderIntent, OrderState, Position


def identity():
    return {
        "demoCid": 42,
        "realCid": 99,
        "firstName": "Do not retain",
        "scopes": ["etoro-public:demo:write"],
    }


def portfolio():
    return {
        "clientPortfolio": {
            "credit": 10000,
            "positions": [],
            "orders": [],
            "mirrors": [],
            "ordersForOpen": [],
            "ordersForClose": [],
        }
    }


def intent(**changes):
    return OrderIntent(
        intent_id=str(uuid4()),
        session_id="session",
        signal_id="synthetic-test",
        symbol="TEST",
        units=Decimal(2),
        entry_price=Decimal(100),
        stop_price=Decimal(99),
        state=OrderState.SUBMITTING,
        created_at=NOW,
        mode="etoro_demo",
    ).model_copy(update=changes)


def eligibility():
    return {
        "currency": "USD",
        "eligibilities": [
            {
                "instrumentId": 123,
                "allowOpenPosition": True,
                "allowClosePosition": True,
                "allowedOrderQuantityType": "all",
                "tradeUnitType": "units",
                "maxUnitsPerOrder": 1000,
                "minPositionExposure": 10,
                "leverageConfigs": [
                    {
                        "settlementType": "real",
                        "direction": "long",
                        "leverageValues": [1],
                        "isPotential": False,
                        "allowStopLossTakeProfit": True,
                        "minPositionAmount": 10,
                        "minStopLossPercentage": 0,
                        "maxStopLossPercentage": 50,
                    }
                ],
            }
        ],
    }


def quote_rows():
    return {
        "results": [
            {
                "instrumentId": 123,
                "bid": 100,
                "ask": 100.01,
                "date": NOW.isoformat(),
                "quoteType": "realtime",
            }
        ]
    }


def order_response(status=3, protected=True):
    return {
        "accountId": 42,
        "orderId": 7,
        "action": "open",
        "status": {"id": status},
        "asset": {"instrumentId": 123, "settlementType": "real", "leverage": 1, "side": "long"},
        "positionExecutions": [
            {
                "positionId": 8,
                "stopLossRate": 99 if protected else 0,
                "openingData": {"units": 2, "fees": 0.2, "taxes": 0, "avgPrice": 100.01},
            }
        ],
    }


def build_adapter(order_intent=None, responses=None, with_review=True):
    item = order_intent or intent()
    responses = responses or {}
    calls = []

    def handler(request):
        calls.append(request)
        path = request.url.path
        if path in responses:
            response = responses[path]
            if isinstance(response, int):
                return httpx.Response(response)
            return httpx.Response(200, json=response)
        defaults = {
            ME: identity(),
            PORTFOLIO: portfolio(),
            ELIGIBILITY: eligibility(),
            RATES: quote_rows(),
            COSTS: {
                "instrumentId": 123,
                "costs": [{"costType": "transactionFee", "amount": 0.2, "currency": "USD"}],
            },
            LOOKUP: order_response(),
            ORDERS: {"orderId": 7, "referenceId": item.intent_id},
        }
        return httpx.Response(200, json=defaults.get(path, {}))

    transport = make_transport(handler)
    arm(transport, identity_reads=False)
    asset = Instrument(symbol="TEST", broker_id=123, stable_id="synthetic-test-only")
    store = {item.intent_id: item}
    positions = {}
    adapter = EtoroDemoAdapter(
        transport,
        intent_loader=store.get,
        position_loader=positions.get,
        entry_review=(lambda unused: EntryReview(asset, lambda *args: True))
        if with_review
        else None,
    )
    return adapter, item, calls, store, positions


def test_preflight_retains_minimum_identity():
    adapter, _, calls, _, _ = build_adapter()
    evidence = perform_preflight(adapter.transport)
    assert evidence.account_id == 42 and evidence.available_cash == Decimal(10000)
    assert "Do not retain" not in repr(evidence) and "realCid" not in repr(evidence)
    assert [request.url.path for request in calls] == [ME, PORTFOLIO]


@pytest.mark.parametrize(
    "payload,reason",
    [
        ({}, "IDENTITY"),
        ({"demoCid": 0, "scopes": []}, "IDENTITY"),
        ({"demoCid": 42, "scopes": []}, "SCOPE_UNVERIFIED"),
        ({"demoCid": 42, "scopes": [5]}, "SCOPE_UNVERIFIED"),
        ({"demoCid": 42, "scopes": ["etoro-public:real:write"]}, "NON_DEMO"),
        ({"demoCid": 42, "scopes": ["*"]}, "NON_DEMO"),
        ({"demoCid": 42, "scopes": ["etoro-public:market-data:read"]}, "INSUFFICIENT"),
    ],
)
def test_preflight_fails_before_portfolio_for_unverified_identity(payload, reason):
    adapter, _, calls, _, _ = build_adapter(responses={ME: payload})
    with pytest.raises(BrokerBlocked, match=reason):
        perform_preflight(adapter.transport)
    assert len(calls) == 1


@pytest.mark.parametrize("case", ["missing", "credit", "position_cid", "wrong_list"])
def test_preflight_invalid_demo_portfolio(case):
    data = portfolio()
    if case == "missing":
        data = {}
    if case == "credit":
        data["clientPortfolio"]["credit"] = -1
    if case == "position_cid":
        data["clientPortfolio"]["positions"] = [{"CID": 99}]
    if case == "wrong_list":
        data["clientPortfolio"]["orders"] = {}
    adapter, _, _, _, _ = build_adapter(responses={PORTFOLIO: data})
    with pytest.raises(BrokerBlocked, match="PORTFOLIO"):
        perform_preflight(adapter.transport)


def test_default_runner_is_blocked():
    adapter, item, calls, _, _ = build_adapter(with_review=False)
    with pytest.raises(BrokerBlocked, match="RUNNER_NOT_VALIDATED"):
        adapter.submit(item)
    assert not calls


def test_mock_submit_is_acknowledgment_not_fill(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    adapter, item, calls, _, _ = build_adapter()
    order = adapter.submit(item)
    assert order.state == OrderState.ACKNOWLEDGED and order.filled_units == 0
    request = calls[-1]
    assert request.url.path == ORDERS
    assert b'"settlementType":"real"' in request.content  # Security type, inside Demo route only.
    assert b'"stopLossRate":99' in request.content and b'"leverage":1' in request.content
    assert b'"transaction":"buy"' in request.content
    assert request.headers["x-request-id"] == item.intent_id


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"state": OrderState.CREATED}, "PERSISTED"),
        ({"mode": "shadow"}, "DEMO_SESSION"),
        ({"session_id": "other"}, "DEMO_SESSION"),
        ({"kind": "close"}, "ENTRY_INTENT"),
        ({"created_at": NOW - timedelta(seconds=11)}, "EXPIRED"),
        ({"units": Decimal("1.5")}, "FRACTIONAL"),
    ],
)
def test_invalid_entry_never_submits(changes, reason):
    item = intent(**changes)
    adapter, _, calls, _, _ = build_adapter(order_intent=item)
    with pytest.raises(BrokerBlocked, match=reason):
        adapter.submit(item)
    assert not calls


@pytest.mark.parametrize(
    "case", ["cfd", "no_stop", "potential", "min_size", "min_stop", "allow_open"]
)
def test_eligibility_blocks_incompatible_entries(case):
    doc = eligibility()
    row = doc["eligibilities"][0]
    config = row["leverageConfigs"][0]
    if case == "cfd":
        config["settlementType"] = "cfd"
    if case == "no_stop":
        config["allowStopLossTakeProfit"] = False
    if case == "potential":
        config["isPotential"] = True
    if case == "min_size":
        row["minPositionExposure"] = 1000
    if case == "min_stop":
        config["minStopLossPercentage"] = 30
    if case == "allow_open":
        row["allowOpenPosition"] = False
    adapter, item, calls, _, _ = build_adapter(responses={ELIGIBILITY: doc})
    with pytest.raises(BrokerBlocked, match="ELIGIBILITY"):
        adapter.submit(item)
    assert all(request.url.path != ORDERS for request in calls)


@pytest.mark.parametrize(
    "status,state",
    [
        (1, OrderState.ACKNOWLEDGED),
        (2, OrderState.ACKNOWLEDGED),
        (3, OrderState.FILLED),
        (4, OrderState.REJECTED),
        (5, OrderState.PARTIALLY_FILLED),
        (6, OrderState.CANCEL_PENDING),
        (7, OrderState.CANCELLED),
        (8, OrderState.EXPIRED),
        (9, OrderState.CANCELLED),
        (10, OrderState.CANCELLED),
        (11, OrderState.ACKNOWLEDGED),
        (12, OrderState.ACKNOWLEDGED),
        (999, OrderState.UNKNOWN),
    ],
)
def test_documented_lookup_statuses(status, state):
    adapter, item, _, _, _ = build_adapter(responses={LOOKUP: order_response(status)})
    result = adapter.query(item.intent_id)
    assert result.state == state
    assert result.filled_units == 2 and result.cumulative_cost == Decimal("0.2")


def test_unknown_not_found_keeps_intent_unresolved():
    adapter, item, _, _, _ = build_adapter(responses={LOOKUP: 404})
    assert adapter.query(item.intent_id) is None
    with pytest.raises(BrokerBlocked, match="OWNERSHIP"):
        adapter.query("unowned")


def test_missing_stop_and_multi_position_fill_are_visible():
    doc = order_response(protected=False)
    adapter, item, _, _, _ = build_adapter(responses={LOOKUP: doc})
    assert not adapter.query(item.intent_id).protected
    doc["positionExecutions"] *= 2
    with pytest.raises(BrokerBlocked, match="MULTI_POSITION"):
        adapter.query(item.intent_id)


def test_account_and_effective_settlement_checked():
    doc = order_response()
    doc["accountId"] = 999
    adapter, item, _, _, _ = build_adapter(responses={LOOKUP: doc})
    with pytest.raises(BrokerBlocked, match="ACCOUNT"):
        adapter.query(item.intent_id)
    doc["accountId"] = 42
    doc["asset"]["settlementType"] = "cfd"
    with pytest.raises(BrokerBlocked, match="PRODUCT_INCIDENT"):
        adapter.query(item.intent_id)


def test_cancel_acceptance_not_final_after_pausing(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    adapter, item, calls, _, _ = build_adapter()
    adapter.transport.authorization.pause_entries()
    result = adapter.cancel(item)
    assert result.state == OrderState.CANCEL_PENDING
    assert calls[-1].method == "DELETE" and calls[-1].url.path == ORDERS + "/7"


def test_foreign_positions_cannot_close_or_protect():
    adapter, item, calls, store, _ = build_adapter()
    closing = intent(kind="close", position_id="999")
    store[closing.intent_id] = closing
    with pytest.raises(BrokerBlocked, match="OWNERSHIP"):
        adapter.close(closing)
    with pytest.raises(BrokerBlocked, match="OWNERSHIP"):
        adapter.protect("999", Decimal(100))
    assert not calls


def test_native_protection_updates_require_broker_confirmation(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    adapter, item, calls, _, positions = build_adapter()
    positions["8"] = Position(
        position_id="8",
        owner_intent_id=item.intent_id,
        session_id="session",
        symbol="TEST",
        units=Decimal(2),
        average_entry=Decimal(100),
        stop_price=Decimal(99),
        protected=True,
        mode="etoro_demo",
    )
    with pytest.raises(BrokerBlocked, match="WIDENED"):
        adapter.protect("8", Decimal(98))
    adapter.transport.authorization.pause_entries()
    assert adapter.protect("8", Decimal(100)) is False
    assert any(request.method == "PATCH" for request in calls)


def test_legacy_close_status_never_guessed():
    closing = intent(kind="close", position_id="8", broker_order_id="9")
    adapter, _, calls, _, _ = build_adapter(order_intent=closing)
    with pytest.raises(BrokerBlocked, match="OWNERSHIP_UNPROVEN"):
        adapter.query(closing.intent_id)
    assert not calls  # Phase 2 verifies persisted ownership even before close reads.


@pytest.mark.parametrize("malformed", [False, True])
def test_documented_demo_close_payload_ack_and_bad_response(monkeypatch, malformed):
    import json

    monkeypatch.delenv("CI", raising=False)
    path = "/api/v1/trading/execution/demo/market-close-orders/positions/8"
    response = {"orderForClose": {"positionID": 9 if malformed else 8, "orderID": 22}}
    adapter, opening, calls, store, positions = build_adapter(responses={path: response})
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
    adapter.transport.authorization.pause_entries()
    if malformed:
        with pytest.raises(BrokerBlocked, match="CLOSE_RESPONSE_UNKNOWN"):
            adapter.close(closing)
    else:
        result = adapter.close(closing)
        assert result.state == OrderState.ACKNOWLEDGED and result.filled_units == 0
        assert result.position_id == "8"
    writes = [r for r in calls if r.method == "POST"]
    assert len(writes) == 1
    assert writes[0].url.path == path
    assert json.loads(writes[0].content) == {"InstrumentID": 123, "UnitsToDeduct": 2}
    assert writes[0].headers["x-request-id"] == closing.intent_id


def test_close_exceeding_owned_quantity_is_blocked_before_write():
    adapter, opening, calls, store, positions = build_adapter()
    positions["8"] = Position(
        position_id="8",
        owner_intent_id=opening.intent_id,
        session_id="session",
        symbol="TEST",
        units=Decimal(1),
        average_entry=Decimal(100),
        stop_price=Decimal(99),
        protected=True,
        mode="etoro_demo",
    )
    closing = intent(kind="close", position_id="8")
    store[closing.intent_id] = closing
    with pytest.raises(BrokerBlocked, match="EXCEEDS_OWNED"):
        adapter.close(closing)
    assert all(r.method == "GET" for r in calls)


def test_market_quotes_are_decimal_and_delayed_preserved():
    doc = quote_rows()
    doc["results"][0]["quoteType"] = "delayed"
    adapter, _, _, _, _ = build_adapter(responses={RATES: doc})
    quote = EtoroMarketDataProvider(adapter.transport).quotes([123])[0]
    assert quote.ask == Decimal("100.01") and quote.quote_type == "delayed"
    with pytest.raises(BrokerBlocked, match="RVOL_VOLUME_UNVERIFIED"):
        EtoroMarketDataProvider(adapter.transport).load()


@pytest.mark.parametrize("case", ["partial", "none", "negative", "date", "duplicate"])
def test_market_quotes_reject_bad_or_incomplete(case):
    doc = quote_rows()
    if case == "partial":
        doc["results"] = []
    if case == "none":
        doc["results"][0]["bid"] = None
    if case == "negative":
        doc["results"][0]["ask"] = -1
    if case == "date":
        doc["results"][0]["date"] = "2026-09-10"
    if case == "duplicate":
        doc["results"] *= 2
    adapter, _, _, _, _ = build_adapter(responses={RATES: doc})
    with pytest.raises(BrokerBlocked):
        EtoroMarketDataProvider(adapter.transport).quotes([123])


def test_candle_history_has_no_invented_pagination_or_share_volume():
    path = "/api/v1/market-data/instruments/123/history/candles/asc/OneMinute/1000"
    doc = {
        "interval": "OneMinute",
        "candles": [
            {
                "instrumentId": 123,
                "candles": [
                    {
                        "instrumentID": 123,
                        "fromDate": NOW.isoformat(),
                        "open": 100,
                        "high": 101,
                        "low": 99,
                        "close": 100,
                        "volume": 0,
                    }
                ],
            }
        ],
    }
    adapter, _, calls, _, _ = build_adapter(responses={path: doc})
    data = EtoroMarketDataProvider(adapter.transport).recent_candles(123)
    assert data["volume_kind"] == "unknown" and data["research_usable"] is False
    assert not calls[0].url.query
    with pytest.raises(BrokerBlocked):
        EtoroMarketDataProvider(adapter.transport).recent_candles(123, 1001)


def test_instrument_cursor_is_documented_only_for_instruments():
    adapter, _, calls, _, _ = build_adapter(
        responses={INSTRUMENTS: {"results": [], "pagination": {"hasNext": False}}}
    )
    EtoroMarketDataProvider(adapter.transport).instruments(["TEST"], page_token="opaque-cursor")
    assert calls[0].url.params["pageToken"] == "opaque-cursor"
