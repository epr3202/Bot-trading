"""Thin Demo contract adapter. Its production session wiring is intentionally gated."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from intraday_etoro_lab.brokers.authorization import BrokerBlocked, PreflightEvidence
from intraday_etoro_lab.brokers.market_data import BrokerQuote, EtoroMarketDataProvider
from intraday_etoro_lab.brokers.transport import (
    COSTS,
    ELIGIBILITY,
    LOOKUP,
    ME,
    ORDERS,
    PORTFOLIO,
    BrokerHTTPError,
    GuardedTransport,
)
from intraday_etoro_lab.domain.models import Instrument
from intraday_etoro_lab.execution.models import BrokerOrder, OrderIntent, OrderState, Position


def perform_preflight(transport: GuardedTransport) -> PreflightEvidence:
    """Explicitly invoked account reads; never called by constructor or offline boot."""
    identity = transport.request("GET", ME, priority=True)
    account = identity.get("demoCid")
    scopes = identity.get("scopes")
    if type(account) is not int or account <= 0 or not isinstance(scopes, list):
        raise BrokerBlocked("DEMO_IDENTITY_OR_SCOPES_UNVERIFIED")
    if not scopes or any(not isinstance(scope, str) for scope in scopes):
        raise BrokerBlocked("DEMO_SCOPE_UNVERIFIED_FOR_KEYS")
    if any("real" in scope.lower() or "*" in scope for scope in scopes):
        raise BrokerBlocked("NON_DEMO_SCOPE_DETECTED")
    if not set(scopes) & {
        "etoro-public:demo:read",
        "etoro-public:demo:write",
        "etoro-public:trade.demo:read",
        "etoro-public:trade.demo:write",
    }:
        raise BrokerBlocked("DEMO_SCOPE_INSUFFICIENT")
    portfolio = transport.request("GET", PORTFOLIO, priority=True)
    try:
        client = portfolio["clientPortfolio"]
        cash = Decimal(str(client["credit"]))
        if not cash.is_finite() or cash < 0:
            raise ValueError
        # Successful access to the Demo-specific route plus matching IDs when
        # present proves this read's environment. An empty portfolio has no CID.
        for name in ("positions", "orders", "mirrors", "ordersForOpen", "ordersForClose"):
            if not isinstance(client[name], list):
                raise ValueError
            for row in client[name]:
                if "CID" in row and row["CID"] != account:
                    raise ValueError
    except (KeyError, TypeError, ValueError, ArithmeticError):
        raise BrokerBlocked("DEMO_PORTFOLIO_UNVERIFIED") from None
    return PreflightEvidence(
        account, frozenset(scopes), cash, transport.now(), transport.credentials.fingerprint
    )


@dataclass(frozen=True)
class EntryReview:
    """The session orchestrator must resolve identity and rerun RiskEngine."""

    instrument: Instrument
    review: Callable[[OrderIntent, dict[str, Any], dict[str, Any], BrokerQuote], bool]


_STATUSES = {
    1: OrderState.ACKNOWLEDGED,
    2: OrderState.ACKNOWLEDGED,
    3: OrderState.FILLED,
    4: OrderState.REJECTED,
    5: OrderState.PARTIALLY_FILLED,
    6: OrderState.CANCEL_PENDING,
    7: OrderState.CANCELLED,
    8: OrderState.EXPIRED,
    9: OrderState.CANCELLED,
    10: OrderState.CANCELLED,
    11: OrderState.ACKNOWLEDGED,
    12: OrderState.ACKNOWLEDGED,
}


class EtoroDemoAdapter:
    def __init__(
        self,
        transport: GuardedTransport,
        *,
        intent_loader: Callable[[str], OrderIntent | None],
        position_loader: Callable[[str], Position | None],
        entry_review: Callable[[OrderIntent], EntryReview] | None = None,
    ) -> None:
        self.transport = transport
        self.intent_loader = intent_loader
        self.position_loader = position_loader
        self.entry_review = entry_review

    def _persisted(self, intent: OrderIntent) -> None:
        saved = self.intent_loader(intent.intent_id)
        if saved != intent or intent.state != OrderState.SUBMITTING:
            raise BrokerBlocked("PERSISTED_SUBMITTING_INTENT_REQUIRED")
        if intent.mode != "etoro_demo" or intent.session_id != self.transport.session_id:
            raise BrokerBlocked("INTENT_DEMO_SESSION_MISMATCH")

    def _authorization(self, management: bool = False) -> Any:
        authorization = self.transport.authorization
        if authorization is None:
            raise BrokerBlocked("DEMO_NOT_ARMED")
        permit = authorization.permit("management" if management else "entry")
        authorization.check(
            permit,
            session_id=self.transport.session_id,
            config_hash=self.transport.config_hash,
            credential_fingerprint=self.transport.credentials.fingerprint,
            now=self.transport.now(),
        )
        return permit

    def _owned(self, position_id: str) -> tuple[Position, OrderIntent]:
        position = self.position_loader(position_id)
        if position is None or position.mode != "etoro_demo":
            raise BrokerBlocked("POSITION_OWNERSHIP_UNPROVEN")
        opening = self.intent_loader(position.owner_intent_id)
        if opening is None or opening.kind != "entry" or opening.mode != "etoro_demo":
            raise BrokerBlocked("POSITION_OWNERSHIP_UNPROVEN")
        # Broker-side lookup ties persisted opening intent to actual Demo position.
        order = self.query(opening.intent_id)
        if order is None or order.position_id != position_id:
            raise BrokerBlocked("POSITION_BROKER_OWNERSHIP_UNPROVEN")
        return position, opening

    def submit(self, intent: OrderIntent) -> BrokerOrder:
        self._persisted(intent)
        permit = self._authorization()
        if self.entry_review is None:
            raise BrokerBlocked("DEMO_SESSION_RUNNER_NOT_VALIDATED")
        if intent.kind != "entry" or intent.position_id is not None:
            raise BrokerBlocked("ENTRY_INTENT_REQUIRED")
        now = self.transport.now()
        if intent.created_at.tzinfo is None or not timedelta(
            0
        ) <= now - intent.created_at <= timedelta(seconds=10):
            raise BrokerBlocked("SIGNAL_EXPIRED")
        review = self.entry_review(intent)
        asset = review.instrument
        if (
            asset.broker_id is None
            or asset.symbol != intent.symbol
            or asset.currency != "USD"
            or asset.asset_class != "common_stock"
            or asset.stable_id is None
        ):
            raise BrokerBlocked("COMMON_STOCK_IDENTITY_UNVERIFIED")
        if intent.units != intent.units.to_integral_value():
            raise BrokerBlocked("FRACTIONAL_PRECISION_UNVERIFIED")
        payload: dict[str, Any] = {
            "action": "open",
            "transaction": "buy",
            "instrumentId": asset.broker_id,
            "settlementType": "real",
            "orderType": "mkt",
            "leverage": 1,
            "units": intent.units,
            "orderCurrency": "usd",
            "stopLossRate": intent.stop_price,
            "stopLossType": "fixed",
        }
        eligibility = self.transport.request(
            "POST", ELIGIBILITY, body={"instrumentIds": [asset.broker_id], "currency": "USD"}
        )
        costs = self.transport.request("POST", COSTS, body=payload)
        quote = EtoroMarketDataProvider(self.transport).quotes([asset.broker_id])[0]
        if (
            quote.quote_type != "realtime"
            or quote.event_time > self.transport.now()
            or self.transport.now() - quote.event_time > timedelta(seconds=3)
        ):
            raise BrokerBlocked("QUOTE_STALE_OR_DELAYED")
        self._check_eligibility(eligibility, intent, asset.broker_id, quote)
        # Costs, sizing/reservations, session calendar, source discrepancy and all
        # risk checks are rerun by the reviewed orchestrator callback.
        if costs.get("instrumentId") != asset.broker_id or not isinstance(costs.get("costs"), list):
            raise BrokerBlocked("COSTS_UNVERIFIED")
        if not review.review(intent, eligibility, costs, quote):
            raise BrokerBlocked("FINAL_RISK_REVALIDATION_FAILED")
        if self.transport.now() - intent.created_at > timedelta(seconds=10):
            raise BrokerBlocked("SIGNAL_EXPIRED_DURING_PREFLIGHT")
        response = self.transport.request(
            "POST", ORDERS, body=payload, permit=permit, request_id=intent.intent_id
        )
        if (
            response.get("referenceId") != intent.intent_id
            or type(response.get("orderId")) is not int
        ):
            raise BrokerBlocked("SUBMISSION_RESPONSE_UNVERIFIED_RECONCILE")
        return BrokerOrder(
            broker_order_id=str(response["orderId"]),
            intent_id=intent.intent_id,
            state=OrderState.ACKNOWLEDGED,
        )

    @staticmethod
    def _check_eligibility(
        document: dict[str, Any], intent: OrderIntent, instrument_id: int, quote: BrokerQuote
    ) -> None:
        try:
            rows = document["eligibilities"]
            row = next(item for item in rows if item["instrumentId"] == instrument_id)
            configs = [
                item
                for item in row["leverageConfigs"]
                if item["settlementType"] == "real"
                and item["direction"] == "long"
                and 1 in item["leverageValues"]
                and item["isPotential"] is False
                and item["allowStopLossTakeProfit"] is True
            ]
            if (
                document["currency"] != "USD"
                or not row["allowOpenPosition"]
                or not configs
                or row["allowedOrderQuantityType"] not in {"all", "unitsOnly"}
                or row["tradeUnitType"] != "units"
                or not row["allowClosePosition"]
                or intent.units > Decimal(str(row["maxUnitsPerOrder"]))
                or intent.units * quote.ask < Decimal(str(row["minPositionExposure"]))
                or not 0 < intent.stop_price < quote.bid
            ):
                raise ValueError
            config = configs[0]
            stop_percent = (quote.ask - intent.stop_price) / quote.ask * 100
            if intent.units * quote.ask < Decimal(str(config["minPositionAmount"])) or not Decimal(
                str(config["minStopLossPercentage"])
            ) <= stop_percent <= Decimal(str(config["maxStopLossPercentage"])):
                raise ValueError
        except (KeyError, StopIteration, TypeError, ValueError, ArithmeticError):
            raise BrokerBlocked("ELIGIBILITY_OR_NATIVE_STOP_INCOMPATIBLE") from None

    def query(self, intent_id: str) -> BrokerOrder | None:
        intent = self.intent_loader(intent_id)
        if intent is None or intent.mode != "etoro_demo":
            raise BrokerBlocked("ORDER_OWNERSHIP_UNPROVEN")
        if intent.kind == "close":
            # The selected v1 close contract does not promise v2 reference lookup
            # or describe the meaning of its statusID values. Preserve UNKNOWN;
            # never reuse openingData units as units closed, or invent status enums.
            if intent.broker_order_id is not None:
                self.transport.request(
                    "GET",
                    f"/api/v1/trading/info/demo/close-orders/{intent.broker_order_id}",
                    priority=True,
                )
            return None
        try:
            document = self.transport.request(
                "GET", LOOKUP, params={"referenceId": intent_id}, priority=True
            )
        except BrokerHTTPError as exc:
            if exc.status == 404:
                return None  # Not evidence that a timed-out submission was rejected.
            raise
        authorization = self.transport.authorization
        if authorization is None or document.get("accountId") != authorization.account_id:
            raise BrokerBlocked("ORDER_ACCOUNT_UNVERIFIED")
        try:
            state = _STATUSES.get(document["status"]["id"], OrderState.UNKNOWN)
            executions = document["positionExecutions"]
            if len(executions) > 1:
                raise BrokerBlocked("MULTI_POSITION_FILL_REQUIRES_RECONCILIATION")
            execution = executions[0] if executions else None
            opening = execution["openingData"] if execution else None
            units = Decimal(str(opening["units"])) if opening else Decimal(0)
            fees = (
                Decimal(str(opening["fees"])) + Decimal(str(opening["taxes"]))
                if opening
                else Decimal(0)
            )
            protection = bool(
                execution and Decimal(str(execution["stopLossRate"])) >= intent.stop_price
            )
            if units and (
                document["asset"]["settlementType"] != "real"
                or document["asset"]["leverage"] != 1
                or document["asset"]["side"] != "long"
            ):
                raise BrokerBlocked("UNEXPECTED_PRODUCT_INCIDENT")
            return BrokerOrder(
                broker_order_id=str(document["orderId"]),
                intent_id=intent_id,
                state=state,
                filled_units=units,
                average_price=Decimal(str(opening["avgPrice"])) if opening else None,
                position_id=str(execution["positionId"]) if execution else None,
                protected=protection,
                cumulative_cost=fees,
            )
        except (KeyError, TypeError, ValueError, ArithmeticError):
            raise BrokerBlocked("ORDER_SCHEMA_UNVERIFIED") from None

    def cancel(self, intent: OrderIntent) -> BrokerOrder:
        permit = self._authorization(management=True)
        order = self.query(intent.intent_id)
        if order is None:
            raise BrokerBlocked("UNKNOWN_ORDER_CANNOT_CANCEL_BY_GUESS")
        reference = str(uuid5(NAMESPACE_URL, f"cancel:{intent.intent_id}"))
        self.transport.request(
            "DELETE",
            f"{ORDERS}/{order.broker_order_id}",
            permit=permit,
            request_id=reference,
            priority=True,
        )
        return order.model_copy(update={"state": OrderState.CANCEL_PENDING})

    def close(self, intent: OrderIntent) -> BrokerOrder:
        self._persisted(intent)
        permit = self._authorization(management=True)
        if intent.kind != "close" or intent.position_id is None:
            raise BrokerBlocked("CLOSE_REQUIRES_POSITION")
        position, opening = self._owned(intent.position_id)
        if intent.units > position.units:
            raise BrokerBlocked("CLOSE_EXCEEDS_OWNED_UNITS")
        snapshot = self.transport.request(
            "GET", LOOKUP, params={"referenceId": opening.intent_id}, priority=True
        )
        path = (
            f"/api/v1/trading/execution/demo/market-close-orders/positions/{position.position_id}"
        )
        response = self.transport.request(
            "POST",
            path,
            permit=permit,
            request_id=intent.intent_id,
            priority=True,
            body={"InstrumentID": snapshot["asset"]["instrumentId"], "UnitsToDeduct": intent.units},
        )
        try:
            result = response["orderForClose"]
            if result["positionID"] != int(position.position_id):
                raise ValueError
            return BrokerOrder(
                broker_order_id=str(result["orderID"]),
                intent_id=intent.intent_id,
                state=OrderState.ACKNOWLEDGED,
                position_id=position.position_id,
            )
        except (KeyError, TypeError, ValueError):
            raise BrokerBlocked("CLOSE_RESPONSE_UNKNOWN_RECONCILE") from None

    def protect(self, position_id: str, stop_price: Decimal) -> bool:
        permit = self._authorization(management=True)
        position, opening = self._owned(position_id)
        if not stop_price.is_finite() or stop_price <= 0 or stop_price < position.stop_price:
            raise BrokerBlocked("STOP_CANNOT_BE_WIDENED")
        reference = str(uuid5(NAMESPACE_URL, f"protect:{position_id}:{stop_price}"))
        self.transport.request(
            "PATCH",
            f"/api/v2/trading/demo/positions/{position_id}",
            body={"stopLossRate": stop_price, "stopLossType": "fixed"},
            permit=permit,
            request_id=reference,
            priority=True,
        )
        order = self.query(opening.intent_id)
        # An asynchronous edit acknowledgment is never proof of protection.
        if order is None:
            return False
        document = self.transport.request(
            "GET", LOOKUP, params={"referenceId": opening.intent_id}, priority=True
        )
        return any(
            str(row.get("positionId")) == position_id
            and row.get("stopLossRate") is not None
            and Decimal(str(row["stopLossRate"])) >= stop_price
            for row in document.get("positionExecutions", [])
        )
