"""Documented eToro reads. Candle volume/finality are not research-validated."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, NoReturn

from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.transport import INSTRUMENTS, RATES, GuardedTransport


@dataclass(frozen=True)
class BrokerQuote:
    instrument_id: int
    bid: Decimal
    ask: Decimal
    event_time: datetime
    received_at: datetime
    quote_type: str
    source: str = "etoro"


class EtoroMarketDataProvider:
    def __init__(self, transport: GuardedTransport) -> None:
        self.transport = transport

    def instruments(self, symbols: list[str], page_token: str | None = None) -> dict[str, Any]:
        if not symbols or len(symbols) > 100:
            raise BrokerBlocked("INSTRUMENT_BATCH_INVALID")
        params: dict[str, Any] = {"symbols": ",".join(symbols), "type": "Stocks", "pageSize": 100}
        if page_token is not None:
            params["pageToken"] = page_token
        document = self.transport.request("GET", INSTRUMENTS, params=params)
        if not isinstance(document.get("results"), list) or "pagination" not in document:
            raise BrokerBlocked("INSTRUMENT_SCHEMA_INVALID")
        # Exchange/currency/common-stock/ADR verification is a separate identity gate.
        return document

    def quotes(self, instrument_ids: list[int]) -> tuple[BrokerQuote, ...]:
        if not instrument_ids or len(instrument_ids) > 1000 or any(i <= 0 for i in instrument_ids):
            raise BrokerBlocked("QUOTE_BATCH_INVALID")
        document = self.transport.request(
            "GET", RATES, params={"instrumentIds": ",".join(map(str, instrument_ids))}
        )
        now = self.transport.response_received_at
        if now is None or now.tzinfo is None or now.utcoffset() is None:
            raise BrokerBlocked("QUOTE_RECEPTION_TIME_INVALID")
        now = now.astimezone(UTC)
        result: list[BrokerQuote] = []
        try:
            for row in document["results"]:
                bid, ask = Decimal(str(row["bid"])), Decimal(str(row["ask"]))
                stamp = row["date"]
                if not isinstance(stamp, str) or "T" not in stamp:
                    raise ValueError
                event_time = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                # getRates specifies UTC; the provider also emits UTC without a suffix.
                # Preserve the event time, never substitute reception time for freshness.
                if event_time.tzinfo is None:
                    event_time = event_time.replace(tzinfo=UTC)
                event_time = event_time.astimezone(UTC)
                if not bid.is_finite() or not ask.is_finite() or not 0 < bid <= ask:
                    raise ValueError
                if row["quoteType"] not in {"realtime", "delayed"} or event_time.tzinfo is None:
                    raise ValueError
                result.append(
                    BrokerQuote(row["instrumentId"], bid, ask, event_time, now, row["quoteType"])
                )
        except (KeyError, TypeError, ValueError, ArithmeticError):
            raise BrokerBlocked("QUOTE_SCHEMA_INVALID") from None
        if {quote.instrument_id for quote in result} != set(instrument_ids):
            raise BrokerBlocked("QUOTE_PARTIAL_OR_IDENTITY_MISMATCH")
        if len(result) != len(set(instrument_ids)):
            raise BrokerBlocked("QUOTE_DUPLICATES")
        return tuple(result)

    def recent_candles(self, instrument_id: int, count: int = 1000) -> dict[str, Any]:
        if instrument_id <= 0 or not 1 <= count <= 1000:
            raise BrokerBlocked("CANDLE_REQUEST_INVALID")
        path = (
            f"/api/v1/market-data/instruments/{instrument_id}/history/candles/asc/OneMinute/{count}"
        )
        response = self.transport.request("GET", path)
        try:
            if response["interval"] != "OneMinute":
                raise ValueError
            groups = response["candles"]
            if len(groups) != 1 or groups[0]["instrumentId"] != instrument_id:
                raise ValueError
            for candle in groups[0]["candles"]:
                if candle["instrumentID"] != instrument_id:
                    raise ValueError
                for name in ("fromDate", "open", "high", "low", "close", "volume"):
                    if name not in candle:
                        raise ValueError
        except (KeyError, TypeError, ValueError):
            raise BrokerBlocked("CANDLE_SCHEMA_INVALID") from None
        return {
            "data": response,
            "received_at": self.transport.now().isoformat(),
            "source": "etoro",
            "volume_kind": "unknown",
            "finality": "unverified",
            "research_usable": False,
        }

    def load(self) -> NoReturn:
        raise BrokerBlocked("RVOL_VOLUME_UNVERIFIED_AND_HISTORY_INSUFFICIENT")
