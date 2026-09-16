"""Local order identifiers and lifecycle are independent of broker enums."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class OrderState(StrEnum):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    SUBMITTING = "SUBMITTING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


ACTIVE_STATES = {
    OrderState.CREATED,
    OrderState.APPROVED,
    OrderState.SUBMITTING,
    OrderState.ACKNOWLEDGED,
    OrderState.PARTIALLY_FILLED,
    OrderState.CANCEL_PENDING,
    OrderState.UNKNOWN,
}
TERMINAL_STATES = {OrderState.FILLED, OrderState.CANCELLED, OrderState.REJECTED, OrderState.EXPIRED}
TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.CREATED: {OrderState.APPROVED, OrderState.REJECTED, OrderState.EXPIRED},
    OrderState.APPROVED: {
        OrderState.SUBMITTING,
        OrderState.EXPIRED,
        OrderState.CANCELLED,
        OrderState.REJECTED,
    },
    OrderState.SUBMITTING: {
        OrderState.ACKNOWLEDGED,
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.REJECTED,
        OrderState.UNKNOWN,
        OrderState.CANCEL_PENDING,
    },
    OrderState.ACKNOWLEDGED: {
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCEL_PENDING,
        OrderState.CANCELLED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
        OrderState.UNKNOWN,
    },
    OrderState.PARTIALLY_FILLED: {
        OrderState.FILLED,
        OrderState.CANCEL_PENDING,
        OrderState.CANCELLED,
        OrderState.EXPIRED,
        OrderState.UNKNOWN,
    },
    OrderState.CANCEL_PENDING: {
        OrderState.CANCELLED,
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.UNKNOWN,
        OrderState.ACKNOWLEDGED,
    },
    OrderState.UNKNOWN: {
        OrderState.ACKNOWLEDGED,
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCEL_PENDING,
        OrderState.CANCELLED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
    },
    # A late, cumulative broker fill can cross an authoritative cancellation.
    OrderState.CANCELLED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED},
    OrderState.EXPIRED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED},
    OrderState.REJECTED: set(),
    OrderState.FILLED: set(),
}


class LifecycleError(RuntimeError):
    pass


def validate_transition(old: OrderState, new: OrderState) -> None:
    if new != old and new not in TRANSITIONS[old]:
        raise LifecycleError(f"Invalid order transition {old} -> {new}")


class OrderIntent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    intent_id: str
    session_id: str
    signal_id: str
    symbol: str
    units: Decimal = Field(gt=0, allow_inf_nan=False)
    entry_price: Decimal = Field(gt=0, allow_inf_nan=False)
    stop_price: Decimal = Field(gt=0, allow_inf_nan=False)
    state: OrderState = OrderState.CREATED
    kind: Literal["entry", "close"] = "entry"
    position_id: str | None = None
    strategy: str = "ORB_RVOL"
    version: str = "0.1"
    mode: Literal["offline", "backtest", "shadow", "etoro_demo"] = "offline"
    created_at: datetime
    planned_risk: Decimal = Decimal("0")
    estimated_cost: Decimal = Decimal("0")
    broker_order_id: str | None = None
    filled_units: Decimal = Decimal("0")
    average_price: Decimal | None = None
    cumulative_cost: Decimal = Field(default=Decimal("0"), ge=0, allow_inf_nan=False)


class BrokerOrder(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    broker_order_id: str
    intent_id: str
    state: OrderState
    filled_units: Decimal = Field(default=Decimal("0"), ge=0, allow_inf_nan=False)
    average_price: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    position_id: str | None = None
    protected: bool = False
    cumulative_cost: Decimal = Field(default=Decimal("0"), ge=0, allow_inf_nan=False)
    remaining_units: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    observed_at: datetime | None = None


class Fill(BaseModel):
    fill_id: str
    intent_id: str
    broker_order_id: str
    position_id: str
    units: Decimal
    price: Decimal
    cost: Decimal
    timestamp: datetime


class Position(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    position_id: str
    owner_intent_id: str
    session_id: str
    symbol: str
    units: Decimal
    average_entry: Decimal
    stop_price: Decimal
    protected: bool
    realized_pnl: Decimal = Decimal("0")
    mark_price: Decimal | None = None
    planned_risk: Decimal = Decimal("0")
    mode: Literal["offline", "backtest", "shadow", "etoro_demo"]
    observed_units: Decimal | None = None
    observed_at: datetime | None = None
    accounting_complete: bool = True


class AuditEvent(BaseModel):
    event_id: int
    timestamp: datetime
    kind: str
    intent_id: str | None
    details: str
    mode: str


class TradingSession(BaseModel):
    session_id: str
    reference_capital: Decimal
    realized_pnl: Decimal = Decimal("0")
    entries_paused: bool = True


class ExecutionBroker(Protocol):
    def submit(self, intent: OrderIntent) -> BrokerOrder: ...
    def query(self, intent_id: str) -> BrokerOrder | None: ...
    def cancel(self, intent: OrderIntent) -> BrokerOrder: ...
    def close(self, intent: OrderIntent) -> BrokerOrder: ...
    def protect(self, position_id: str, stop_price: Decimal) -> bool: ...


@dataclass(frozen=True)
class PreparedSubmission:
    """Ephemeral send capability plus safe durable correlation metadata."""

    send: Callable[[OrderIntent], BrokerOrder]
    metadata: dict[str, str]


@runtime_checkable
class PreparingBroker(Protocol):
    def prepare(self, intent: OrderIntent) -> PreparedSubmission: ...
