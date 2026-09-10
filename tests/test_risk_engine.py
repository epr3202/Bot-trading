from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from intraday_etoro_lab.risk import (
    CostConfig,
    EntryRequest,
    InstrumentRules,
    RiskConfig,
    RiskEngine,
    RiskPortfolio,
)

D = Decimal
NOW = datetime(2026, 9, 9, 13, 36, 1, tzinfo=UTC)


def request(**changes: object) -> EntryRequest:
    base = EntryRequest(
        signal_id="s1",
        session_id="2026-09-09",
        symbol="SYNTH",
        available_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=9),
        now=NOW,
        entry_price=D("100"),
        stop_price=D("99"),
        bid=D("99.99"),
        ask=D("100"),
        quote_at=NOW,
    )
    return replace(base, **changes)


def test_manually_calculated_sizing_and_costs() -> None:
    result = RiskEngine().assess(request(), RiskPortfolio())
    assert result.approved
    assert result.units == D("9.708")  # 10 / (1 + .01 commission + .02 slippage)
    assert result.planned_risk == D("9.99924")
    assert result.estimated_cost == D("0.29124")
    assert result.notional == D("970.800")
    assert result.cost_to_r == result.estimated_cost / result.planned_risk


def test_nonlinear_cost_binary_search_finds_largest_feasible_step() -> None:
    costs = CostConfig(fixed_per_side=D("1"), quadratic_impact=D("0.05"))
    engine = RiskEngine(costs=costs)
    result = engine.assess(request(), RiskPortfolio())
    assert result.approved
    assert result.planned_risk <= D("10")
    next_units = result.units + D(".001")
    assert next_units + costs.estimate(next_units, D("100")) > D("10")
    assert result.units < RiskEngine().assess(request(), RiskPortfolio()).units


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"entry_price": D("NaN")}, "INVALID_DECIMAL"),
        ({"entry_price": 100.0}, "INVALID_DECIMAL"),
        ({"signal_id": ""}, "INVALID_IDENTITY"),
        ({"stop_price": D("100")}, "INVALID_STOP_DISTANCE"),
        ({"stop_price": D("0")}, "INVALID_STOP_DISTANCE"),
        ({"bid": D("101")}, "INVALID_EXECUTABLE_QUOTE"),
        ({"ask": D("100.01")}, "INVALID_EXECUTABLE_QUOTE"),
        ({"now": NOW.replace(tzinfo=None)}, "NAIVE_TIMESTAMP"),
        ({"quote_at": NOW + timedelta(seconds=1)}, "FUTURE_DATA"),
        ({"available_at": NOW + timedelta(seconds=1)}, "FUTURE_DATA"),
        ({"entry_window_open": False}, "ENTRY_WINDOW_CLOSED"),
        ({"expires_at": NOW}, "SIGNAL_EXPIRED"),
        ({"available_at": NOW - timedelta(seconds=11)}, "SIGNAL_EXPIRED"),
        ({"quote_at": NOW - timedelta(seconds=4)}, "STALE_QUOTE"),
        ({"bid": D("99")}, "SPREAD_LIMIT"),
        ({"reference_price": D("98")}, "PRICE_DEVIATION"),
        ({"reference_price": D("0")}, "PRICE_DEVIATION"),
        ({"source_price": D("98")}, "SOURCE_DIVERGENCE"),
    ],
)
def test_request_guards(changes: dict[str, object], reason: str) -> None:
    result = RiskEngine().assess(request(**changes), RiskPortfolio())
    assert not result.approved and result.reason == reason


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"cash": D("-1")}, "INVALID_PORTFOLIO"),
        ({"reference_capital": D("0")}, "INVALID_PORTFOLIO"),
        ({"equity": D("0")}, "INVALID_PORTFOLIO"),
        ({"potential_positions": -1}, "INVALID_PORTFOLIO"),
        ({"entries_paused": True}, "ENTRIES_PAUSED"),
        ({"reconciliation_ok": False}, "RECONCILIATION_REQUIRED"),
        ({"realized_pnl": D("-49"), "unrealized_pnl": D("-1")}, "DAILY_LOSS_LIMIT"),
        ({"potential_positions": 2}, "POSITION_LIMIT"),
        ({"reserved_cash": D("10000")}, "BUDGET_EXHAUSTED"),
        ({"reserved_risk": D("50")}, "BUDGET_EXHAUSTED"),
    ],
)
def test_portfolio_guards(changes: dict[str, object], reason: str) -> None:
    result = RiskEngine().assess(request(), replace(RiskPortfolio(), **changes))
    assert not result.approved and result.reason == reason


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"currency": "EUR"}, "PRODUCT_INELIGIBLE"),
        ({"effective_product": "CFD"}, "PRODUCT_INELIGIBLE"),
        ({"eligibility_verified": False}, "ELIGIBILITY_UNVERIFIED"),
        ({"native_stop_supported": False}, "NATIVE_STOP_REQUIRED"),
        ({"unit_step": D("0")}, "INVALID_INSTRUMENT_RULES"),
        ({"maximum_units": D("0")}, "INVALID_INSTRUMENT_RULES"),
        ({"minimum_notional": D("-1")}, "INVALID_INSTRUMENT_RULES"),
        ({"minimum_units": D("1000001")}, "INVALID_INSTRUMENT_RULES"),
        ({"minimum_notional": D("1000001")}, "INVALID_INSTRUMENT_RULES"),
        ({"minimum_units": D("10")}, "MINIMUM_INCOMPATIBLE"),
        ({"minimum_notional": D("1000")}, "MINIMUM_INCOMPATIBLE"),
    ],
)
def test_instrument_guards(changes: dict[str, object], reason: str) -> None:
    rule = replace(InstrumentRules(), **changes)
    result = RiskEngine().assess(request(rules=rule), RiskPortfolio())
    assert not result.approved and result.reason == reason


def test_explicit_unknown_cost_is_never_zero() -> None:
    result = RiskEngine(costs=CostConfig(known=False)).assess(request(), RiskPortfolio())
    assert result.reason == "COSTS_UNKNOWN"
    assert CostConfig().estimate(D("0"), D("100")) == 0


def test_cash_equity_concentration_and_instrument_maxima() -> None:
    config = RiskConfig(max_position_fraction=D(".005"))
    engine = RiskEngine(config)
    result = engine.assess(request(), RiskPortfolio(cash=D("40")))
    assert result.notional + result.estimated_cost <= D("40")
    assert result.units == D(".399")
    constrained = request(rules=InstrumentRules(maximum_units=D(".1")))
    assert RiskEngine().assess(constrained, RiskPortfolio()).units == D(".100")
    constrained = request(rules=InstrumentRules(maximum_notional=D("10")))
    assert RiskEngine().assess(constrained, RiskPortfolio()).units == D(".100")
    tiny = RiskEngine().assess(request(), RiskPortfolio(cash=D(".01")))
    assert tiny.reason == "MINIMUM_INCOMPATIBLE"
    equity = RiskEngine().assess(request(), RiskPortfolio(equity=D("1000")))
    assert equity.planned_risk <= D("1")


@given(st.decimals(min_value=".001", max_value="1000", places=3, allow_nan=False))
def test_step_and_budget_invariant(distance: Decimal) -> None:
    entry = distance + D("100")
    r = request(entry_price=entry, stop_price=D("100"), bid=entry, ask=entry)
    result = RiskEngine().assess(r, RiskPortfolio())
    if result.approved:
        assert result.units % r.rules.unit_step == 0
        assert result.planned_risk <= D("10")
        assert result.notional + result.estimated_cost <= D("6000")


def test_post_fill_guard_and_config_reject_unsafe_values() -> None:
    engine = RiskEngine()
    assert engine.post_fill_risk(D("5"), D("100"), D("99"), D("10"), True)[1] is None
    assert engine.post_fill_risk(D("5"), D("100"), D("99"), D("10"), False)[1] == (
        "MISSING_PROTECTION"
    )
    assert engine.post_fill_risk(D("5"), D("110"), D("99"), D("10"), True)[1] == (
        "POST_FILL_RISK_EXCEEDED"
    )
    with pytest.raises(ValidationError):
        RiskConfig(max_positions=3)
    with pytest.raises(ValidationError):
        CostConfig(quadratic_impact=D("-1"))
