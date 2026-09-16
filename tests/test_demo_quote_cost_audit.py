"""Regression of actual A7 UTC timestamps and observed cost wire format."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from test_etoro_adapter import build_adapter, quote_rows

from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.etoro_demo import normalize_costs
from intraday_etoro_lab.brokers.market_data import EtoroMarketDataProvider
from intraday_etoro_lab.brokers.transport import COSTS, RATES


@pytest.mark.parametrize("suffix", ["Z", "", "+00:00"])
def test_observed_utc_age_is_81_point_588043_seconds(suffix):
    rows = quote_rows()
    rows["results"][0]["date"] = "2026-09-16T14:37:59.810" + suffix
    adapter, _, calls, _, _ = build_adapter(responses={RATES: rows})
    received = datetime(2026, 9, 16, 14, 39, 21, 398043, tzinfo=UTC)
    adapter.transport.now = lambda: received
    quote = EtoroMarketDataProvider(adapter.transport).quotes([123])[0]
    assert quote.received_at == received
    assert quote.event_time.utcoffset() == timedelta(0)
    assert (quote.received_at - quote.event_time).total_seconds() == 81.588043
    assert calls[-1].url.path == RATES


def test_quote_reception_is_before_json_decode_and_every_call_uses_http(monkeypatch):
    adapter, _, calls, _, _ = build_adapter()
    clock = [datetime(2026, 9, 16, 15, tzinfo=UTC)]
    adapter.transport.now = lambda: clock[0]
    original = json.loads

    def slow_decode(*args, **kwargs):
        clock[0] += timedelta(seconds=20)
        return original(*args, **kwargs)

    monkeypatch.setattr(json, "loads", slow_decode)
    market = EtoroMarketDataProvider(adapter.transport)
    first = market.quotes([123])[0]
    second = market.quotes([123])[0]
    assert first.received_at == datetime(2026, 9, 16, 15, tzinfo=UTC)
    assert second.received_at == first.received_at + timedelta(seconds=20)
    assert sum(call.url.path == RATES for call in calls) == 2


@pytest.mark.parametrize(
    "seconds,accepted", [(0, True), (3, True), (3.001, False), (81.588043, False), (-1, False)]
)
def test_pre_send_freshness_threshold_unchanged(seconds, accepted, monkeypatch):
    from test_etoro_transport import NOW

    monkeypatch.delenv("CI", raising=False)  # Only the pinned in-memory contract transport.
    rows = quote_rows()
    rows["results"][0]["date"] = (NOW - timedelta(seconds=seconds)).isoformat()
    adapter, intent, calls, _, _ = build_adapter(responses={RATES: rows})
    if accepted:
        adapter.submit(intent)
    else:
        with pytest.raises(BrokerBlocked, match="QUOTE_STALE_OR_DELAYED"):
            adapter.submit(intent)
        assert adapter.transport.mutation_attempts == 0


def observed_costs():
    return json.loads(Path("tests/fixtures/etoro_a7_costs_observed.json").read_text())


def test_real_cost_fixture_normalizes_without_changing_raw_document(monkeypatch):
    monkeypatch.delenv("CI", raising=False)  # Only the pinned in-memory contract transport.
    raw = observed_costs()
    normalized = normalize_costs(raw, 1001)
    assert normalized["costs"][0]["amount"] == Decimal("1.0")
    assert all("amount" in row and "value" not in row for row in normalized["costs"])
    assert "value" in raw["costs"][0]
    raw = {**raw, "instrumentId": 123}  # Bind the wire fixture to the existing mock asset.
    adapter, intent, _, _, _ = build_adapter(responses={COSTS: raw})
    adapter.submit(intent)


@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"value": "invalid"},
        {"value": None},
        {"value": True},
        {"amount": "NaN"},
        {"value": "Infinity"},
        {"amount": 1, "value": 2},
    ],
)
def test_invalid_cost_fails_before_mutation(fields):
    raw = observed_costs()
    raw["costs"][0].pop("value")
    raw["costs"][0].update(fields)
    raw = {**raw, "instrumentId": 123}
    adapter, intent, _, _, _ = build_adapter(responses={COSTS: raw})
    with pytest.raises(BrokerBlocked, match="COSTS_UNVERIFIED"):
        adapter.submit(intent)
    assert adapter.transport.mutation_attempts == 0


@pytest.mark.parametrize("fields", [{"amount": "1.0"}, {"amount": 1, "value": "1.0"}])
def test_documented_amount_and_matching_dual_fields(fields):
    raw = observed_costs()
    raw["costs"][0].pop("value")
    raw["costs"][0].update(fields)
    assert normalize_costs(raw, 1001)["costs"][0]["amount"] == Decimal(1)
