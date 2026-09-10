"""Deterministic, durable local broker. No network and no claimed market realism."""

from decimal import Decimal

from intraday_etoro_lab.execution.models import BrokerOrder, LifecycleError, OrderIntent, OrderState
from intraday_etoro_lab.persistence import StateStore
from intraday_etoro_lab.risk import CostConfig

D = Decimal
ONE = D("1")


class SimulatorBroker:
    def __init__(
        self,
        store: StateStore,
        costs: CostConfig | None = None,
        fill_fraction: Decimal = ONE,
        timeout_after_accept: bool = False,
        native_protection: bool = True,
    ):
        if store.mode not in {"offline", "backtest"}:
            raise ValueError("Simulator state must use offline or backtest mode")
        if not fill_fraction.is_finite() or not 0 <= fill_fraction <= 1:
            raise ValueError("Invalid fill fraction")
        self.store = store
        self.costs = costs or CostConfig()
        self.fill_fraction = fill_fraction
        self.timeout_after_accept = timeout_after_accept
        self.native_protection = native_protection
        self.submit_calls = 0
        self.close_calls = 0

    def _fill(self, intent: OrderIntent) -> BrokerOrder:
        existing = self.query(intent.intent_id)
        if existing is not None:
            return existing
        units = intent.units * self.fill_fraction
        state = (
            OrderState.FILLED
            if units == intent.units
            else OrderState.PARTIALLY_FILLED
            if units
            else OrderState.ACKNOWLEDGED
        )
        # Commission charged per side; slippage/impact are sizing reserves, not cash fees.
        cost = (
            D("0")
            if not units
            else self.costs.fixed_per_side
            + max(
                self.costs.minimum_per_side,
                units * self.costs.per_unit_per_side
                + units * intent.entry_price * self.costs.notional_rate_per_side,
            )
        )
        result = BrokerOrder(
            broker_order_id=f"sim-order-{intent.intent_id}",
            intent_id=intent.intent_id,
            state=state,
            filled_units=units,
            average_price=intent.entry_price if units else None,
            position_id=intent.position_id or f"sim-position-{intent.intent_id}",
            protected=self.native_protection,
            cumulative_cost=cost,
        )
        self.store.simulator_save(result)
        if self.timeout_after_accept:
            raise TimeoutError("Synthetic response lost after durable acceptance")
        return result

    def submit(self, intent: OrderIntent) -> BrokerOrder:
        if intent.kind != "entry" or intent.mode != self.store.mode:
            raise LifecycleError("INVALID_SIMULATOR_ENTRY")
        self.submit_calls += 1
        return self._fill(intent)

    def close(self, intent: OrderIntent) -> BrokerOrder:
        if intent.kind != "close" or intent.position_id is None or intent.mode != self.store.mode:
            raise LifecycleError("INVALID_SIMULATOR_CLOSE")
        position = self.store.position(intent.position_id)
        if intent.units > position.units:
            raise LifecycleError("CLOSE_WOULD_OPEN_SHORT")
        self.close_calls += 1
        return self._fill(intent)

    def query(self, intent_id: str) -> BrokerOrder | None:
        return self.store.simulator_get(intent_id)

    def cancel(self, intent: OrderIntent) -> BrokerOrder:
        result = self.query(intent.intent_id)
        if result is None:
            raise LifecycleError("SIMULATOR_ORDER_NOT_FOUND")
        if result.state != OrderState.FILLED:
            result = result.model_copy(update={"state": OrderState.CANCELLED})
            self.store.simulator_save(result)
        return result

    def protect(self, position_id: str, stop_price: Decimal) -> bool:
        position = self.store.position(position_id)
        if stop_price < position.stop_price:
            raise LifecycleError("STOP_WIDENING_BLOCKED")
        return self.native_protection

    def set_order(self, order: BrokerOrder) -> None:
        """Explicit scenario control for offline tests, including cancel/fill races."""
        if self.query(order.intent_id) is None:
            raise LifecycleError("Cannot inject an unsubmitted simulated order")
        self.store.simulator_save(order)
