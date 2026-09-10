"""Conservative monotone sizing with complete, explicit cost assumptions."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_FLOOR, Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

D = Decimal
ZERO = D("0")


class RiskConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    allocated_capital: Decimal = Field(default=D("10000"), gt=0, allow_inf_nan=False)
    risk_fraction: Decimal = Field(default=D("0.001"), gt=0, le=D("0.001"))
    daily_loss_fraction: Decimal = Field(default=D("0.005"), gt=0, le=D("0.005"))
    max_positions: int = Field(default=2, ge=1, le=2)
    max_gross_fraction: Decimal = Field(default=D("1"), gt=0, le=1)
    max_position_fraction: Decimal = Field(default=D("0.60"), gt=0, le=1)
    max_spread_fraction: Decimal = Field(default=D("0.003"), gt=0, le=D("0.05"))
    max_price_deviation: Decimal = Field(default=D("0.005"), gt=0, le=D("0.05"))
    max_source_divergence: Decimal = Field(default=D("0.005"), gt=0, le=D("0.05"))
    max_quote_age_seconds: int = Field(default=3, ge=0, le=10)
    signal_ttl_seconds: int = Field(default=10, ge=1, le=10)


class CostConfig(BaseModel):
    """USD round-trip reserve; price spread is already present in executable ask/bid."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    known: bool = True
    fixed_per_side: Decimal = Field(default=D("0"), ge=0, allow_inf_nan=False)
    minimum_per_side: Decimal = Field(default=D("0"), ge=0, allow_inf_nan=False)
    per_unit_per_side: Decimal = Field(default=D("0.005"), ge=0, allow_inf_nan=False)
    notional_rate_per_side: Decimal = Field(default=D("0"), ge=0, allow_inf_nan=False)
    slippage_per_unit: Decimal = Field(default=D("0.02"), ge=0, allow_inf_nan=False)
    quadratic_impact: Decimal = Field(default=D("0"), ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def finite_costs(self) -> "CostConfig":
        return self

    def estimate(self, units: Decimal, entry_price: Decimal) -> Decimal:
        if units == 0:
            return ZERO
        commission = max(
            self.minimum_per_side,
            units * self.per_unit_per_side + units * entry_price * self.notional_rate_per_side,
        )
        return (
            2 * (self.fixed_per_side + commission)
            + units * self.slippage_per_unit
            + self.quadratic_impact * units * units
        )


@dataclass(frozen=True)
class InstrumentRules:
    unit_step: Decimal = D("0.001")
    minimum_units: Decimal = D("0.001")
    maximum_units: Decimal = D("1000000")
    minimum_notional: Decimal = D("1")
    maximum_notional: Decimal = D("1000000")
    currency: str = "USD"
    effective_product: str = "common_stock"
    eligibility_verified: bool = True
    native_stop_supported: bool = True


@dataclass(frozen=True)
class EntryRequest:
    signal_id: str
    session_id: str
    symbol: str
    available_at: datetime
    expires_at: datetime
    now: datetime
    entry_price: Decimal
    stop_price: Decimal
    bid: Decimal
    ask: Decimal
    quote_at: datetime
    reference_price: Decimal | None = None
    source_price: Decimal | None = None
    entry_window_open: bool = True
    rules: InstrumentRules = field(default_factory=InstrumentRules)
    strategy: str = "ORB_RVOL"
    version: str = "0.1"


@dataclass(frozen=True)
class RiskPortfolio:
    reference_capital: Decimal = D("10000")
    equity: Decimal = D("10000")
    cash: Decimal = D("10000")
    gross_exposure: Decimal = ZERO
    reserved_cash: Decimal = ZERO
    reserved_risk: Decimal = ZERO
    potential_positions: int = 0
    realized_pnl: Decimal = ZERO
    unrealized_pnl: Decimal = ZERO
    entries_paused: bool = False
    reconciliation_ok: bool = True


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    units: Decimal = ZERO
    planned_risk: Decimal = ZERO
    notional: Decimal = ZERO
    estimated_cost: Decimal = ZERO
    cost_to_r: Decimal = ZERO


def finite_decimal(value: object) -> bool:
    return isinstance(value, Decimal) and value.is_finite()


class RiskEngine:
    def __init__(self, config: RiskConfig | None = None, costs: CostConfig | None = None):
        self.config = config or RiskConfig()
        self.costs = costs or CostConfig()

    def assess(self, request: EntryRequest, portfolio: RiskPortfolio) -> RiskDecision:
        reason = self._reject_reason(request, portfolio)
        if reason:
            return RiskDecision(False, reason)
        config, rule = self.config, request.rules
        capital = min(config.allocated_capital, portfolio.reference_capital, portfolio.equity)
        loss_headroom = (
            portfolio.reference_capital * config.daily_loss_fraction
            + min(ZERO, portfolio.realized_pnl + portfolio.unrealized_pnl)
            - portfolio.reserved_risk
        )
        risk_budget = min(capital * config.risk_fraction, loss_headroom)
        cash_budget = min(
            portfolio.cash - portfolio.reserved_cash,
            capital * config.max_gross_fraction
            - portfolio.gross_exposure
            - portfolio.reserved_cash,
            capital * config.max_position_fraction,
        )
        if risk_budget <= 0 or cash_budget <= 0:
            return RiskDecision(False, "BUDGET_EXHAUSTED")
        distance = request.entry_price - request.stop_price
        maximum = min(
            rule.maximum_units,
            rule.maximum_notional / request.entry_price,
            risk_budget / distance,
            cash_budget / request.entry_price,
        )
        high = int((maximum / rule.unit_step).to_integral_value(rounding=ROUND_FLOOR))
        low = 0
        # All accepted CostConfig terms are nonnegative, so feasibility is monotone.
        while low < high:
            middle = (low + high + 1) // 2
            units = rule.unit_step * middle
            costs = self.costs.estimate(units, request.entry_price)
            if units * distance + costs <= risk_budget and (
                units * request.entry_price + costs <= cash_budget
            ):
                low = middle
            else:
                high = middle - 1
        units = rule.unit_step * low
        notional = units * request.entry_price
        if units <= 0 or units < rule.minimum_units or notional < rule.minimum_notional:
            return RiskDecision(False, "MINIMUM_INCOMPATIBLE")
        cost = self.costs.estimate(units, request.entry_price)
        risk = units * distance + cost
        return RiskDecision(True, "APPROVED", units, risk, notional, cost, cost / risk)

    def _reject_reason(self, r: EntryRequest, p: RiskPortfolio) -> str | None:
        amounts = [r.entry_price, r.stop_price, r.bid, r.ask]
        amounts += [value for value in (r.reference_price, r.source_price) if value is not None]
        amounts += [
            p.reference_capital,
            p.equity,
            p.cash,
            p.gross_exposure,
            p.reserved_cash,
            p.reserved_risk,
            p.realized_pnl,
            p.unrealized_pnl,
        ]
        rule = r.rules
        amounts += [
            rule.unit_step,
            rule.minimum_units,
            rule.maximum_units,
            rule.minimum_notional,
            rule.maximum_notional,
        ]
        if not all(finite_decimal(value) for value in amounts):
            return "INVALID_DECIMAL"
        if (
            any(
                value < 0
                for value in (
                    p.cash,
                    p.gross_exposure,
                    p.reserved_cash,
                    p.reserved_risk,
                )
            )
            or p.reference_capital <= 0
            or p.equity <= 0
            or p.potential_positions < 0
        ):
            return "INVALID_PORTFOLIO"
        if not r.signal_id or not r.session_id or not r.symbol:
            return "INVALID_IDENTITY"
        if p.entries_paused:
            return "ENTRIES_PAUSED"
        if not p.reconciliation_ok:
            return "RECONCILIATION_REQUIRED"
        if p.realized_pnl + p.unrealized_pnl <= -(
            p.reference_capital * self.config.daily_loss_fraction
        ):
            return "DAILY_LOSS_LIMIT"
        if p.potential_positions >= self.config.max_positions:
            return "POSITION_LIMIT"
        if not self.costs.known:
            return "COSTS_UNKNOWN"
        if rule.currency != "USD" or rule.effective_product != "common_stock":
            return "PRODUCT_INELIGIBLE"
        if not rule.eligibility_verified:
            return "ELIGIBILITY_UNVERIFIED"
        if not rule.native_stop_supported:
            return "NATIVE_STOP_REQUIRED"
        if (
            rule.unit_step <= 0
            or rule.minimum_units < 0
            or rule.maximum_units <= 0
            or rule.minimum_notional < 0
            or rule.maximum_notional <= 0
            or rule.minimum_units > rule.maximum_units
            or rule.minimum_notional > rule.maximum_notional
        ):
            return "INVALID_INSTRUMENT_RULES"
        if r.stop_price <= 0 or r.entry_price <= r.stop_price:
            return "INVALID_STOP_DISTANCE"
        if r.bid <= 0 or r.ask < r.bid or r.entry_price < r.ask:
            return "INVALID_EXECUTABLE_QUOTE"
        times = [r.now, r.quote_at, r.available_at, r.expires_at]
        if any(t.tzinfo is None or t.utcoffset() is None for t in times):
            return "NAIVE_TIMESTAMP"
        if r.now < r.available_at or r.quote_at > r.now:
            return "FUTURE_DATA"
        if not r.entry_window_open:
            return "ENTRY_WINDOW_CLOSED"
        if (
            r.now >= r.expires_at
            or (r.now - r.available_at).total_seconds() > self.config.signal_ttl_seconds
        ):
            return "SIGNAL_EXPIRED"
        if (r.now - r.quote_at).total_seconds() > self.config.max_quote_age_seconds:
            return "STALE_QUOTE"
        if (r.ask - r.bid) / r.ask > self.config.max_spread_fraction:
            return "SPREAD_LIMIT"
        for price, limit, reason in (
            (r.reference_price, self.config.max_price_deviation, "PRICE_DEVIATION"),
            (r.source_price, self.config.max_source_divergence, "SOURCE_DIVERGENCE"),
        ):
            if price is not None and (price <= 0 or abs(r.entry_price - price) / price > limit):
                return reason
        return None

    def post_fill_risk(
        self,
        units: Decimal,
        fill_price: Decimal,
        stop_price: Decimal,
        planned_risk: Decimal,
        protected: bool,
    ) -> tuple[Decimal, str | None]:
        risk = max(ZERO, units * (fill_price - stop_price)) + self.costs.estimate(units, fill_price)
        if not protected:
            return risk, "MISSING_PROTECTION"
        if risk > planned_risk:
            return risk, "POST_FILL_RISK_EXCEEDED"
        return risk, None
