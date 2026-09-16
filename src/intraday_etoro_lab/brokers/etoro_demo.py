"""Thin Demo contract adapter. Its production session wiring is intentionally gated."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from intraday_etoro_lab.brokers.authorization import (
    BrokerBlocked,
    MutationPermit,
    PreflightEvidence,
    RejectedBeforeSend,
)
from intraday_etoro_lab.brokers.market_data import BrokerQuote, EtoroMarketDataProvider
from intraday_etoro_lab.brokers.transport import (
    COSTS,
    ELIGIBILITY,
    LOOKUP,
    ORDERS,
    BrokerHTTPError,
    GuardedTransport,
)
from intraday_etoro_lab.domain.models import Instrument
from intraday_etoro_lab.execution.models import (
    BrokerOrder,
    OrderIntent,
    OrderState,
    Position,
    PreparedSubmission,
)


def perform_preflight(transport: GuardedTransport) -> PreflightEvidence:
    """Explicitly invoked account reads; never called by constructor or offline boot."""
    transport.restrict_to_preflight()
    return transport.observe_demo()


def normalize_costs(document: dict[str, Any], instrument_id: int) -> dict[str, Any]:
    """Normalize documented amount and observed value without inventing fees."""
    try:
        if document.get("instrumentId") != instrument_id:
            raise ValueError
        rows = document["costs"]
        if not isinstance(rows, list) or not rows:
            raise ValueError
        normalized = []
        for row in rows:
            if not isinstance(row, dict) or row.get("currency") != "USD":
                raise ValueError
            if row.get("costType") not in {
                "transactionFee",
                "markup",
                "marketSpread",
                "overnightFee",
                "overWeekendFee",
                "sdrt",
            }:
                raise ValueError
            values = [Decimal(str(row[key])) for key in ("amount", "value") if key in row]
            if not values or any(not value.is_finite() for value in values):
                raise ValueError
            if any(value != values[0] for value in values):
                raise ValueError
            normalized.append({key: value for key, value in row.items() if key != "value"})
            normalized[-1]["amount"] = values[0]
        return {**document, "costs": normalized}
    except (KeyError, TypeError, ValueError, ArithmeticError):
        raise BrokerBlocked("COSTS_UNVERIFIED") from None


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


def _classify_pre_send[T](method: Callable[..., T]) -> Callable[..., T]:
    @wraps(method)
    def guarded(self: "EtoroDemoAdapter", *args: Any, **kwargs: Any) -> T:
        attempted = self.transport.mutation_attempts
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:
            if self.transport.mutation_attempts != attempted:
                raise  # A response error after dispatch is still externally ambiguous.
            reason = str(exc) if isinstance(exc, BrokerBlocked) else "PRE_SEND_PREPARATION_FAILED"
            raise RejectedBeforeSend(reason) from None

    return guarded


class EtoroDemoAdapter:
    def __init__(
        self,
        transport: GuardedTransport,
        *,
        intent_loader: Callable[[str], OrderIntent | None],
        position_loader: Callable[[str], Position | None],
        entry_review: Callable[[OrderIntent], EntryReview] | None = None,
        read_evidence: PreflightEvidence | None = None,
    ) -> None:
        self.transport = transport
        self.intent_loader = intent_loader
        self.position_loader = position_loader
        self.entry_review = entry_review
        self.read_evidence = read_evidence

    def _account_id(self) -> int:
        evidence = self.read_evidence
        if evidence is not None:
            if evidence.credential_fingerprint != self.transport.credentials.fingerprint:
                raise BrokerBlocked("READ_IDENTITY_CREDENTIAL_MISMATCH")
            return evidence.account_id
        # Existing contract fixtures also bind an account through authorization.
        authorization = self.transport.authorization
        if authorization is None or authorization.account_id is None:
            raise BrokerBlocked("ORDER_ACCOUNT_UNVERIFIED")
        return authorization.account_id

    def _persisted(self, intent: OrderIntent) -> None:
        saved = self.intent_loader(intent.intent_id)
        if saved != intent or intent.state != OrderState.SUBMITTING:
            raise BrokerBlocked("PERSISTED_SUBMITTING_INTENT_REQUIRED")
        if intent.mode != "etoro_demo" or intent.session_id != self.transport.session_id:
            raise BrokerBlocked("INTENT_DEMO_SESSION_MISMATCH")

    def _authorization(self, management: bool = False) -> Any:
        self.transport.require_contract_transport()
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
        self.transport.verify_mutation_identity(permit)
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

    @_classify_pre_send
    def submit(self, intent: OrderIntent) -> BrokerOrder:
        self._persisted(intent)
        payload, permit = self._prepare_entry(intent)
        return self._submit_prepared(intent, payload, permit)

    @_classify_pre_send
    def prepare(self, intent: OrderIntent) -> PreparedSubmission:
        if intent.state != OrderState.APPROVED or self.intent_loader(intent.intent_id) != intent:
            raise BrokerBlocked("PERSISTED_PREPARED_INTENT_REQUIRED")
        if intent.mode != "etoro_demo" or intent.session_id != self.transport.session_id:
            raise BrokerBlocked("INTENT_DEMO_SESSION_MISMATCH")
        payload, permit = self._prepare_entry(intent)

        def send(submitting: OrderIntent) -> BrokerOrder:
            if submitting.model_copy(update={"state": OrderState.APPROVED}) != intent:
                raise RejectedBeforeSend("PREPARED_INTENT_CHANGED")
            return self._submit_prepared(submitting, payload, permit)

        return PreparedSubmission(
            send,
            {
                "instrument_id": str(payload["instrumentId"]),
                "units": str(intent.units),
                "direction": "buy",
                "reference_id": intent.intent_id,
                "created_at": intent.created_at.isoformat(),
                "mode": "etoro_demo",
            },
        )

    def _prepare_entry(self, intent: OrderIntent) -> tuple[dict[str, Any], MutationPermit]:
        self.transport.require_contract_transport()
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
        permit = self._authorization()
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
        costs = normalize_costs(costs, asset.broker_id)
        if not review.review(intent, eligibility, costs, quote):
            raise BrokerBlocked("FINAL_RISK_REVALIDATION_FAILED")
        if self.transport.now() - intent.created_at > timedelta(seconds=10):
            raise BrokerBlocked("SIGNAL_EXPIRED_DURING_PREFLIGHT")
        return payload, permit

    @_classify_pre_send
    def _submit_prepared(
        self, intent: OrderIntent, payload: dict[str, Any], permit: MutationPermit
    ) -> BrokerOrder:
        self._persisted(intent)
        if not timedelta(0) <= self.transport.now() - intent.created_at <= timedelta(seconds=10):
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
                document["currency"] not in {"USD", "usd"}
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
            return self._query_close(intent)
        try:
            document = self.transport.request(
                "GET", LOOKUP, params={"referenceId": intent_id}, priority=True
            )
        except BrokerHTTPError as exc:
            if exc.status == 404:
                return None  # Not evidence that a timed-out submission was rejected.
            raise
        if document.get("accountId") != self._account_id():
            raise BrokerBlocked("ORDER_ACCOUNT_UNVERIFIED")
        if intent.broker_order_id and str(document.get("orderId")) != intent.broker_order_id:
            raise BrokerBlocked("ORDER_IDENTITY_MISMATCH")
        try:
            # Lookup v2 serves both actions. Opening data on a close response
            # must never be booked as an entry execution.
            if document["action"] != "open" or type(document["status"]["id"]) is not int:
                raise ValueError
            state = _STATUSES.get(document["status"]["id"], OrderState.UNKNOWN)
            executions = document["positionExecutions"]
            if len(executions) > 1:
                raise BrokerBlocked("MULTI_POSITION_FILL_REQUIRES_RECONCILIATION")
            execution = executions[0] if executions else None
            opening = execution["openingData"] if execution else None
            units = Decimal(str(opening["units"])) if opening else Decimal(0)
            if document["status"]["id"] in {3, 5, 9, 10} and units <= 0:
                raise ValueError  # Execution-bearing terminal states cannot mean zero fills.
            fees = (
                Decimal(str(opening["fees"])) + Decimal(str(opening["taxes"]))
                if opening
                else Decimal(0)
            )
            protection = bool(
                execution and Decimal(str(execution["stopLossRate"])) >= intent.stop_price
            )
            remaining, observed_at = None, None
            if execution and "remainingUnits" in execution:
                remaining = Decimal(str(execution["remainingUnits"]))
                observed_at = datetime.fromisoformat(document["lastUpdate"].replace("Z", "+00:00"))
                if (
                    not remaining.is_finite()
                    or not 0 <= remaining <= units
                    or execution["state"] not in {"open", "closed"}
                    or (execution["state"] == "closed") != (remaining == 0)
                    or observed_at.tzinfo is None
                    or observed_at > self.transport.now()
                    or observed_at < intent.created_at
                ):
                    raise ValueError
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
                remaining_units=remaining,
                observed_at=observed_at,
            )
        except (KeyError, TypeError, ValueError, ArithmeticError):
            raise BrokerBlocked("ORDER_SCHEMA_UNVERIFIED") from None

    def _query_close(self, intent: OrderIntent) -> BrokerOrder | None:
        # No reference lookup guarantee for v1: response lost with no order ID
        # cannot be repaired by ticker/amount/history matching or another sale.
        if intent.broker_order_id is None:
            return None
        if not intent.position_id:
            raise BrokerBlocked("CLOSE_REQUIRES_POSITION")
        position = self.position_loader(intent.position_id)
        if position is None or position.mode != "etoro_demo":
            raise BrokerBlocked("POSITION_OWNERSHIP_UNPROVEN")
        opening = self.intent_loader(position.owner_intent_id)
        if (
            opening is None
            or opening.kind != "entry"
            or opening.mode != "etoro_demo"
            or opening.broker_order_id is None
            or opening.filled_units <= 0
        ):
            raise BrokerBlocked("POSITION_OWNERSHIP_UNPROVEN")
        try:
            document = self.transport.request(
                "GET",
                f"/api/v1/trading/info/demo/close-orders/{intent.broker_order_id}",
                priority=True,
            )
        except BrokerHTTPError as exc:
            if exc.status == 404:
                return None
            raise
        snapshot = self.transport.request(
            "GET",
            LOOKUP,
            params={"orderId": opening.broker_order_id},
            priority=True,
        )
        try:
            if (
                document["CID"] != self._account_id()
                or snapshot["accountId"] != self._account_id()
                or str(document["orderID"]) != intent.broker_order_id
                or str(snapshot["orderId"]) != opening.broker_order_id
                or document["instrumentID"] != snapshot["asset"]["instrumentId"]
                or document.get("referenceID") not in {None, intent.intent_id}
                or type(document["statusID"]) is not int
            ):
                raise ValueError
            executions = snapshot["positionExecutions"]
            if len(executions) != 1 or str(executions[0]["positionId"]) != intent.position_id:
                raise ValueError
            request_at = datetime.fromisoformat(document["requestOccurred"].replace("Z", "+00:00"))
            if (
                request_at.tzinfo is None
                or not intent.created_at <= request_at <= self.transport.now()
            ):
                raise ValueError
            rows = document.get("positions")
            occurred = None
            if rows:
                # No execution IDs or cumulative semantics for repeated position
                # rows are specified. A single documented row can prove quantity;
                # multiple rows require a stronger broker contract.
                if len(rows) != 1 or str(rows[0]["positionID"]) != intent.position_id:
                    raise ValueError
                row = rows[0]
                if row.get("units") is not None and row.get("occurred") is not None:
                    units = Decimal(str(row["units"]))
                    occurred = datetime.fromisoformat(row["occurred"].replace("Z", "+00:00"))
                    if (
                        not units.is_finite()
                        or not 0 < units <= intent.units
                        or occurred.tzinfo is None
                        or not request_at <= occurred <= self.transport.now()
                    ):
                        raise ValueError
                    # Closed units are not a documented cumulative snapshot.
                    # In particular, intent.units may describe a partial close,
                    # not the original position size. Observe remaining exposure
                    # only through the opening lookup's explicit remainingUnits.
            elif rows is not None and not isinstance(rows, list):
                raise ValueError
            # statusID has no documented enum and fees/taxes have no finality
            # contract here. Keep the order UNKNOWN and the cash ledger unchanged.
            return BrokerOrder(
                broker_order_id=intent.broker_order_id,
                intent_id=intent.intent_id,
                state=OrderState.UNKNOWN,
                position_id=intent.position_id,
                filled_units=intent.filled_units,
                average_price=intent.average_price,
                cumulative_cost=intent.cumulative_cost,
                remaining_units=None,
                observed_at=None,
            )
        except (KeyError, TypeError, ValueError, ArithmeticError):
            raise BrokerBlocked("CLOSE_CORRELATION_OR_SCHEMA_UNVERIFIED") from None

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

    @_classify_pre_send
    def close(self, intent: OrderIntent) -> BrokerOrder:
        self._persisted(intent)
        self.transport.require_contract_transport()
        if intent.kind != "close" or intent.position_id is None:
            raise BrokerBlocked("CLOSE_REQUIRES_POSITION")
        position, opening = self._owned(intent.position_id)
        if intent.units > position.units:
            raise BrokerBlocked("CLOSE_EXCEEDS_OWNED_UNITS")
        permit = self._authorization(management=True)
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
        self.transport.require_contract_transport()
        position, opening = self._owned(position_id)
        if not stop_price.is_finite() or stop_price <= 0 or stop_price < position.stop_price:
            raise BrokerBlocked("STOP_CANNOT_BE_WIDENED")
        permit = self._authorization(management=True)
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
