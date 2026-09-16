"""Massive historical AAPL/SPY/QQQ aggregates only. No account capabilities."""

from __future__ import annotations

import hashlib
import json
import os
import re
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit
from zoneinfo import ZoneInfo

import httpx

from intraday_etoro_lab.data.calendar import session, sessions

ORIGIN = "https://api.massive.com"
PREFIX = "/v2/aggs/ticker/AAPL/range/1/minute/"
SEMANTICS_VERSION = "massive-consolidated-eligible-split-v1"
SOURCES = (
    "https://massive.com/docs/rest/stocks/aggregates/custom-bars",
    "https://massive.com/blog/understanding-trade-eligibility",
    "https://massive.com/stocks",
    "https://massive.com/knowledge-base/article/"
    "why-does-volume-return-as-a-decimal-value-from-the-aggregates-endpoint",
)
VOLUME_SEMANTICS = (
    "Split-adjusted shares from volume-eligible trades across the consolidated US market; "
    "CTA/UTP consolidated update rules apply separately to volume and OHLC. "
    "Trades with a condition excluding volume do not contribute; price-ineligible trades "
    "can contribute volume. Not a count of trades, quotes, ticks or every reported event."
)


class MassiveDataError(RuntimeError):
    """Only static reasons, never upstream text, URLs or credential values."""

    @property
    def status(self) -> str:
        reason = str(self)
        if reason in {"AUTH_MISSING_OR_INVALID", "HTTP_401", "HTTP_403", "AUTH_PAYLOAD_DENIED"}:
            return "MASSIVE_AUTHENTICATION_FAILED"
        if reason.startswith("RATE_LIMIT"):
            return "MASSIVE_RATE_LIMITED"
        if reason == "VOLUME_SEMANTICS_UNVERIFIED":
            return "MASSIVE_VOLUME_SEMANTICS_UNVERIFIED"
        return "MASSIVE_DATA_INCOMPLETE"


def utc_now() -> datetime:
    return datetime.now(UTC)


def save_json(path: Path, payload: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, default=str, ensure_ascii=False)
        stream.write("\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_document(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_bytes(), parse_float=Decimal)
    if not isinstance(result, dict):
        raise MassiveDataError("DOCUMENT_INVALID")
    return result


def parse_time(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise MassiveDataError("TIMESTAMP_ZONE_REQUIRED")
    return result.astimezone(UTC)


@dataclass(frozen=True)
class MassiveCredentials:
    api_key: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.api_key or not re.fullmatch(r"[A-Za-z0-9_-]+", self.api_key):
            raise MassiveDataError("AUTH_MISSING_OR_INVALID")

    @classmethod
    def from_environment(cls) -> MassiveCredentials:
        return cls(os.getenv("MASSIVE_API_KEY", ""))


@dataclass(frozen=True)
class MassiveHistoricalRequest:
    target: date
    symbol: str = "AAPL"

    def __post_init__(self) -> None:
        if self.symbol not in {"AAPL", "SPY", "QQQ"}:
            raise MassiveDataError("SYMBOL_NOT_ALLOWED")
        session(self.target)

    @property
    def prefix(self) -> str:
        return f"/v2/aggs/ticker/{self.symbol}/range/1/minute/"

    @property
    def days(self) -> tuple[date, ...]:
        prior = sessions(self.target - timedelta(days=60), self.target - timedelta(days=1))[-20:]
        if len(prior) != 20:
            raise MassiveDataError("TWENTY_PREVIOUS_SESSIONS_REQUIRED")
        return (*prior, self.target)

    @property
    def bounds(self) -> tuple[int, int]:
        return (
            int(session(self.days[0]).open.timestamp() * 1000),
            int((session(self.target).close - timedelta(minutes=1)).timestamp() * 1000),
        )

    @property
    def endpoint(self) -> str:
        start, end = self.bounds
        return f"{ORIGIN}{self.prefix}{start}/{end}"

    @property
    def url(self) -> str:
        return self.endpoint + "?adjusted=true&sort=asc&limit=50000"

    def validate_url(self, value: str) -> str:
        """Pagination may advance start; cannot change host, ticker, interval or final bound."""
        if not isinstance(value, str) or len(value) > 8192 or not value.isascii():
            raise MassiveDataError("PAGINATION_URL_NOT_ALLOWED")
        parsed = urlsplit(value)
        match = re.fullmatch(re.escape(self.prefix) + r"([0-9]{13})/([0-9]{13})", parsed.path)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "api.massive.com"
            or parsed.fragment
            or not match
        ):
            raise MassiveDataError("PAGINATION_URL_NOT_ALLOWED")
        start, end = self.bounds
        if not start <= int(match[1]) <= end or int(match[2]) != end:
            raise MassiveDataError("PAGINATION_RANGE_NOT_ALLOWED")
        pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
        query = dict(pairs)
        allowed = {"adjusted": "true", "sort": "asc", "limit": "50000"}
        if len(pairs) != len(query) or set(query) - {*allowed, "cursor"}:
            raise MassiveDataError("PAGINATION_QUERY_NOT_ALLOWED")
        if any(query[key] != val for key, val in allowed.items() if key in query):
            raise MassiveDataError("PAGINATION_QUERY_NOT_ALLOWED")
        if "cursor" in query and not re.fullmatch(r"[A-Za-z0-9_+/=-]{1,4096}", query["cursor"]):
            raise MassiveDataError("PAGINATION_CURSOR_INVALID")
        if value != self.url and "cursor" not in query:
            raise MassiveDataError("PAGINATION_CURSOR_REQUIRED")
        return value


def validate_page(doc: dict[str, Any], symbol: str = "AAPL") -> None:
    if doc.get("status") in {"NOT_AUTHORIZED", "AUTH_ERROR"}:
        raise MassiveDataError("AUTH_PAYLOAD_DENIED")
    rows = doc.get("results", [])
    if (
        doc.get("status") != "OK"
        or doc.get("ticker") != symbol
        or doc.get("adjusted") is not True
        or not isinstance(rows, list)
        or type(doc.get("resultsCount")) is not int
        or doc["resultsCount"] != len(rows)
    ):
        raise MassiveDataError("RESPONSE_SCHEMA_OR_IDENTITY_INVALID")


class MassiveHistoryClient:
    def __init__(
        self,
        credentials: MassiveCredentials,
        *,
        transport: httpx.BaseTransport | None = None,
        now: Callable[[], datetime] = utc_now,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.credentials = credentials
        self.now = now
        self.sleeper = sleeper
        self.network_observed = transport is None
        self.records: list[dict[str, Any]] = []
        self._not_before = 0.0
        try:
            verify: ssl.SSLContext | bool = True
            if transport is None:
                local_ca = Path("certs/epm-root.cer")
                ca = str(local_ca) if local_ca.exists() else os.getenv("REQUESTS_CA_BUNDLE")
                if ca:
                    verify = ssl.create_default_context(cafile=ca)
            self._client = httpx.Client(
                timeout=20,
                follow_redirects=False,
                trust_env=transport is None,
                verify=verify,
                transport=transport,
            )
        except (OSError, ValueError, ImportError):
            raise MassiveDataError("TLS_OR_PROXY_CONFIGURATION_INVALID") from None

    def close(self) -> None:
        self._client.close()

    def _delay(self, response: httpx.Response) -> float:
        try:
            retry = response.headers.get("Retry-After")
            reset = response.headers.get("X-RateLimit-Reset")
            if retry is not None:
                try:
                    delay = float(retry)
                except ValueError:
                    delay = (parsedate_to_datetime(retry) - self.now()).total_seconds()
            elif reset is not None:
                delay = max(0.0, float(reset) - self.now().timestamp())
            else:
                raise ValueError
            if not 0 <= delay <= 60:
                raise ValueError
            return delay
        except (ValueError, TypeError, OverflowError):
            raise MassiveDataError("RATE_LIMIT_WAIT_REQUIRED") from None

    def _page(
        self,
        request: MassiveHistoricalRequest,
        url: str,
    ) -> tuple[bytes, dict[str, Any], datetime]:
        request.validate_url(url)
        for attempt in range(3):
            pending = self._not_before - self.now().timestamp()
            if pending > 0:
                self.sleeper(min(pending, 60))
                if self.now().timestamp() < self._not_before:
                    raise MassiveDataError("RATE_LIMIT_WAIT_REQUIRED")
            started = self.now()
            try:
                response = self._client.get(
                    url, headers={"Authorization": "Bearer " + self.credentials.api_key}
                )
            except httpx.TransportError:
                self.records.append({"status": "TRANSPORT_ERROR"})
                raise MassiveDataError("CONNECTIVITY_FAILED") from None
            received = self.now()
            self.records.append(
                {
                    "started_at": started.isoformat(),
                    "received_at": received.isoformat(),
                    "status_code": response.status_code,
                    "attempt": attempt + 1,
                }
            )
            if response.status_code == 429:
                self._not_before = received.timestamp() + self._delay(response)
                if attempt == 2:
                    raise MassiveDataError("RATE_LIMIT_EXHAUSTED")
                continue
            if response.status_code != 200:
                raise MassiveDataError(f"HTTP_{response.status_code}")
            # Do not persist an upstream response that reflects authentication material.
            if self.credentials.api_key.encode() in response.content:
                raise MassiveDataError("RESPONSE_CONTAINS_CREDENTIAL")
            try:
                doc = json.loads(response.content, parse_float=Decimal)
                if not isinstance(doc, dict):
                    raise ValueError
                validate_page(doc, request.symbol)
                if doc.get("next_url") is not None:
                    request.validate_url(doc["next_url"])
            except (ValueError, TypeError, UnicodeError):
                raise MassiveDataError("RESPONSE_SCHEMA_INVALID") from None
            # 13 seconds between requests stays below the documented free 5/min quota.
            self._not_before = received.timestamp() + 13
            if response.headers.get("X-RateLimit-Remaining") == "0" and doc.get("next_url"):
                self._not_before = received.timestamp() + max(13, self._delay(response))
            return response.content, doc, received
        raise MassiveDataError("RATE_LIMIT_EXHAUSTED")

    def capture(self, request: MassiveHistoricalRequest, directory: Path) -> dict[str, Any]:
        # Previous NY date only: an EOD historical snapshot, never today's delayed/realtime data.
        if request.target >= self.now().astimezone(ZoneInfo("America/New_York")).date():
            raise MassiveDataError("PREVIOUS_DATE_HISTORICAL_SESSION_REQUIRED")
        directory.mkdir(parents=True, exist_ok=False)
        capture: dict[str, Any] = {
            "schema_version": "massive-capture-v1",
            "provider": "massive",
            "method": "GET",
            "endpoint": request.endpoint,
            "initial_url": request.url,
            "target": str(request.target),
            "symbol": request.symbol,
            "timeframe": "1m",
            "timezone": "America/New_York",
            "availability_class": "HISTORICAL_DOWNLOAD",
            "latency": None,
            "acquisition_class": "NETWORK_HTTP" if self.network_observed else "CONTRACT_TEST",
            "semantics_version": SEMANTICS_VERSION,
            "sources": SOURCES,
            "plan_observed": None,
            "access_observed": "NOT_OBSERVED",
            "pages": [],
            "status": "INCOMPLETE",
            "started_at": self.now().isoformat(),
        }
        url = request.url
        seen: set[str] = set()
        try:
            for index in range(50):
                if url in seen:
                    raise MassiveDataError("PAGINATION_LOOP")
                seen.add(url)
                body, doc, received = self._page(request, url)
                name = f"page-{index:03d}.json"
                with (directory / name).open("xb") as stream:
                    stream.write(body)
                capture["pages"].append(
                    {
                        "file": name,
                        "sha256": sha256(directory / name),
                        "url": url,
                        "received_at": received.isoformat(),
                    }
                )
                capture["access_observed"] = (
                    "HISTORICAL_AGGREGATES_HTTP_200" if self.network_observed else "CONTRACT_TEST"
                )
                next_url = doc.get("next_url")
                if next_url is None:
                    capture["status"] = "COMPLETE"
                    return capture
                url = next_url
            raise MassiveDataError("PAGINATION_LIMIT")
        except MassiveDataError as exc:
            capture["reason"] = str(exc)
            raise
        finally:
            capture["attempts"] = self.records
            capture["finished_at"] = self.now().isoformat()
            save_json(directory / "capture.json", capture)
