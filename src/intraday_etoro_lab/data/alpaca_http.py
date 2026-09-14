"""Historical stock bars only: fixed host/path, isolated credentials, no trading API."""

from __future__ import annotations

import hashlib
import json
import os
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Literal

import httpx

from intraday_etoro_lab.data.calendar import session, sessions

ORIGIN = "https://data.alpaca.markets"
BARS_PATH = "/v2/stocks/bars"
Feed = Literal["sip", "iex"]


class AlpacaDataError(RuntimeError):
    """Static public reason; upstream error bodies and credentials are never surfaced."""


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class AlpacaCredentials:
    api_key: str = field(repr=False)
    api_secret: str = field(repr=False)

    def __post_init__(self) -> None:
        if any(
            not value or not value.isascii() or any(c.isspace() for c in value)
            for value in (self.api_key, self.api_secret)
        ):
            raise AlpacaDataError("ALPACA_CREDENTIALS_UNAVAILABLE")

    @classmethod
    def from_environment(cls) -> AlpacaCredentials:
        return cls(os.getenv("ALPACA_API_KEY", ""), os.getenv("ALPACA_API_SECRET", ""))


@dataclass(frozen=True)
class HistoricalRequest:
    target: date
    feed: Feed = "sip"
    symbol: Literal["AAPL"] = "AAPL"

    def __post_init__(self) -> None:
        if self.feed not in {"sip", "iex"} or self.symbol != "AAPL":
            raise AlpacaDataError("ALPACA_REQUEST_NOT_ALLOWED")
        session(self.target)

    @property
    def days(self) -> tuple[date, ...]:
        prior = sessions(self.target - timedelta(days=60), self.target - timedelta(days=1))[-20:]
        if len(prior) != 20:
            raise AlpacaDataError("ALPACA_TWENTY_PRIOR_SESSIONS_REQUIRED")
        return (*prior, self.target)

    def params(self) -> dict[str, str]:
        return {
            "symbols": self.symbol,
            "timeframe": "1Min",
            "feed": self.feed,
            "start": session(self.days[0]).open.isoformat(),
            # API end is inclusive: exclude the first postmarket bar at regular close.
            "end": (session(self.target).close - timedelta(minutes=1)).isoformat(),
            "adjustment": "split",
            "currency": "USD",
            "asof": self.target.isoformat(),
            "limit": "10000",
            "sort": "asc",
        }


def save_json(path: Path, payload: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, default=str, indent=2)
        stream.write("\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AlpacaHistoryClient:
    """No general request method, dynamic URLs, account reads, redirects or feed fallback."""

    def __init__(
        self,
        credentials: AlpacaCredentials,
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
                ca = os.getenv("ALPACA_CA_BUNDLE") or (
                    str(local_ca) if local_ca.exists() else os.getenv("REQUESTS_CA_BUNDLE")
                )
                if ca:
                    verify = ssl.create_default_context(cafile=ca)
            self._client = httpx.Client(
                timeout=20,
                follow_redirects=False,
                trust_env=transport is None,
                transport=transport,
                verify=verify,
            )
        except (OSError, ValueError, ImportError):
            raise AlpacaDataError("ALPACA_TLS_OR_PROXY_CONFIGURATION_INVALID") from None

    def close(self) -> None:
        self._client.close()

    def _wait_seconds(self, response: httpx.Response) -> float:
        retry = response.headers.get("Retry-After")
        reset = response.headers.get("X-RateLimit-Reset")
        try:
            if retry is not None:
                try:
                    delay = float(retry)
                except ValueError:
                    delay = (parsedate_to_datetime(retry) - self.now()).total_seconds()
            elif reset is not None:
                delay = max(0.0, float(reset) - self.now().timestamp())
            else:
                delay = 60.0
            if not 0 <= delay <= 60:
                raise ValueError
            return delay
        except (ValueError, TypeError, OverflowError):
            raise AlpacaDataError("ALPACA_RATE_LIMIT_WAIT_REQUIRED") from None

    def _page(self, params: dict[str, str]) -> tuple[bytes, dict[str, Any], datetime]:
        for attempt in range(3):
            pending = self._not_before - self.now().timestamp()
            if pending > 0:
                self.sleeper(min(pending, 60))
                if self.now().timestamp() < self._not_before:
                    raise AlpacaDataError("ALPACA_RATE_LIMIT_WAIT_REQUIRED")
            started = self.now()
            try:
                response = self._client.get(
                    ORIGIN + BARS_PATH,
                    params=params,
                    headers={
                        "APCA-API-KEY-ID": self.credentials.api_key,
                        "APCA-API-SECRET-KEY": self.credentials.api_secret,
                    },
                )
            except httpx.TransportError:
                self.records.append(
                    {"started_at": started.isoformat(), "status": "TRANSPORT_ERROR"}
                )
                raise AlpacaDataError("ALPACA_HISTORY_UNAVAILABLE") from None
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
                self._not_before = received.timestamp() + self._wait_seconds(response)
                if attempt == 2:
                    raise AlpacaDataError("ALPACA_RATE_LIMIT_EXHAUSTED")
                continue
            if response.status_code == 401:
                raise AlpacaDataError("ALPACA_AUTHENTICATION_FAILED")
            if response.status_code in {403, 422}:
                # A generic 403 can also mean bad authentication, not SIP entitlement.
                if (
                    params["feed"] == "sip"
                    and "subscription does not permit" in response.text.lower()
                ):
                    raise AlpacaDataError("ALPACA_SIP_ENTITLEMENT_REQUIRED")
                raise AlpacaDataError(f"ALPACA_HTTP_{response.status_code}")
            if response.status_code != 200:
                raise AlpacaDataError(f"ALPACA_HTTP_{response.status_code}")
            if response.headers.get("X-RateLimit-Remaining") == "0":
                self._not_before = received.timestamp() + self._wait_seconds(response)
            try:
                document = json.loads(response.content, parse_float=Decimal)
                if not isinstance(document, dict) or not isinstance(document.get("bars"), dict):
                    raise ValueError
                if document.get("feed", params["feed"]) != params["feed"]:
                    raise AlpacaDataError("ALPACA_FEED_IDENTITY_MISMATCH")
            except (ValueError, UnicodeError):
                raise AlpacaDataError("ALPACA_RESPONSE_SCHEMA_INVALID") from None
            return response.content, document, received
        raise AlpacaDataError("ALPACA_RATE_LIMIT_EXHAUSTED")

    def capture(self, request: HistoricalRequest, directory: Path) -> dict[str, Any]:
        if session(request.target).close > self.now() - timedelta(minutes=15):
            raise AlpacaDataError("ALPACA_CLOSED_HISTORICAL_SESSION_REQUIRED")
        directory.mkdir(parents=True, exist_ok=False)
        params = request.params()
        capture: dict[str, Any] = {
            "schema_version": "alpaca-capture-v1",
            "provider": "alpaca",
            "origin": ORIGIN,
            "endpoint": BARS_PATH,
            "method": "GET",
            "feed_requested": request.feed,
            "feed_effective": None,
            "feed_identity_basis": "Explicit HTTPS feed and API contract; no payload echo",
            "acquisition_class": "NETWORK_HTTP" if self.network_observed else "CONTRACT_TEST",
            "availability_class": "HISTORICAL_DOWNLOAD",
            "target": str(request.target),
            "timezone": "America/New_York",
            "params": params,
            "pages": [],
            "status": "INCOMPLETE",
            "started_at": self.now().isoformat(),
        }
        token: str | None = None
        seen: set[str] = set()
        try:
            for index in range(50):
                query = params | ({"page_token": token} if token else {})
                body, doc, received = self._page(query)
                name = f"page-{index:03d}.json"
                with (directory / name).open("xb") as stream:
                    stream.write(body)
                capture["pages"].append(
                    {
                        "file": name,
                        "sha256": sha256(directory / name),
                        "params": query,
                        "received_at": received.isoformat(),
                        "feed_effective": request.feed,
                        "feed_echo": doc.get("feed"),
                    }
                )
                if "next_page_token" not in doc:
                    raise AlpacaDataError("ALPACA_PAGINATION_STATE_MISSING")
                next_token = doc["next_page_token"]
                if next_token is None:
                    capture.update(status="COMPLETE", feed_effective=request.feed)
                    return capture
                if not isinstance(next_token, str) or not next_token or next_token in seen:
                    raise AlpacaDataError("ALPACA_PAGINATION_LOOP_OR_INVALID_TOKEN")
                seen.add(next_token)
                token = next_token
            raise AlpacaDataError("ALPACA_PAGINATION_LIMIT")
        except AlpacaDataError as exc:
            capture["reason"] = str(exc)
            raise
        finally:
            capture["attempts"] = self.records
            capture["finished_at"] = self.now().isoformat()
            save_json(directory / "capture.json", capture)
