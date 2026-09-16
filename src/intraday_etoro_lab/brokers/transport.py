"""One authenticated destination and an exact, reviewed route allowlist."""

import hashlib
import json
import os
import random
import re
import ssl
import time
from collections import defaultdict, deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx

from intraday_etoro_lab.brokers.authorization import (
    BrokerBlocked,
    DemoAuthorization,
    MutationPermit,
    PreflightEvidence,
    utc_now,
)
from intraday_etoro_lab.brokers.identity import portfolio_cash, require_demo

ORIGIN = "https://public-api.etoro.com"
ME = "/api/v1/me"
PORTFOLIO = "/api/v1/trading/info/demo/portfolio"
INSTRUMENTS = "/api/v2/market-data/instruments"
RATES = "/api/v2/market-data/rates"
ORDERS = "/api/v2/trading/execution/demo/orders"
LOOKUP = "/api/v2/trading/info/demo/orders:lookup"
COSTS = "/api/v2/trading/info/demo/costs"
ELIGIBILITY = "/api/v2/trading/info/demo/eligibility"


def create_http_client(*, transport: httpx.BaseTransport | None = None) -> httpx.Client:
    """Use corporate CA/proxy settings only for the actual external network client."""
    if transport is not None:
        # An injected transport must never acquire environment proxy mounts.
        return httpx.Client(
            transport=transport, timeout=10, follow_redirects=False, trust_env=False
        )
    local_ca = Path("certs/epm-root.cer")
    ca_file = str(local_ca) if local_ca.exists() else os.getenv("REQUESTS_CA_BUNDLE")
    try:
        verify = ssl.create_default_context(cafile=ca_file) if ca_file else True
        return httpx.Client(timeout=10, follow_redirects=False, trust_env=True, verify=verify)
    except (OSError, ValueError, ImportError):
        # Do not expose proxy credentials or private paths through exception text.
        raise BrokerBlocked("ETORO_TLS_OR_PROXY_CONFIGURATION_INVALID") from None


@dataclass(frozen=True)
class Credentials:
    api_key: str = field(repr=False)
    user_key: str = field(repr=False)

    def __post_init__(self) -> None:
        if any(not key or any(c.isspace() for c in key) for key in (self.api_key, self.user_key)):
            raise BrokerBlocked("CREDENTIALS_MISSING_OR_INVALID")

    @classmethod
    def from_environment(cls) -> "Credentials":
        return cls(os.getenv("ETORO_API_KEY", ""), os.getenv("ETORO_USER_KEY", ""))

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256((self.api_key + "\0" + self.user_key).encode()).hexdigest()


class BrokerHTTPError(BrokerBlocked):
    def __init__(self, status: int) -> None:
        self.status = status
        super().__init__(f"ETORO_HTTP_{status}")


class SubmissionUnknown(BrokerBlocked):
    """Transport failure: reconciliation required; never replay the mutation."""


@dataclass(frozen=True)
class Route:
    method: str
    pattern: str
    pool: str
    quota: int
    query: frozenset[str] = frozenset()
    mutation: bool = False
    purpose: str = "read"


_ID = r"[1-9][0-9]{0,18}"
ROUTES = (
    Route("GET", ME, "default", 60),
    Route("GET", PORTFOLIO, "portfolio", 60),
    Route(
        "GET",
        INSTRUMENTS,
        "market",
        60,
        frozenset({"instrumentsIds", "symbols", "pageSize", "pageToken", "exchangeId", "type"}),
    ),
    Route("GET", RATES, "market", 60, frozenset({"instrumentIds"})),
    Route(
        "GET",
        rf"/api/v1/market-data/instruments/{_ID}/history/candles/"
        r"(?:asc|desc)/(?:OneMinute|OneDay)/(?:[1-9][0-9]{0,2}|1000)",
        "market",
        60,
    ),
    Route("GET", LOOKUP, "lookup", 60, frozenset({"orderId", "referenceId"})),
    Route("GET", rf"/api/v1/trading/info/demo/close-orders/{_ID}", "lookup", 60),
    Route("POST", COSTS, "costs", 20),
    Route("POST", ELIGIBILITY, "eligibility", 20),
    Route("POST", ORDERS, "execution", 20, mutation=True, purpose="entry"),
    Route("DELETE", rf"{ORDERS}/{_ID}", "execution", 20, mutation=True, purpose="management"),
    Route(
        "PATCH",
        rf"/api/v2/trading/demo/positions/{_ID}",
        "default",
        60,
        mutation=True,
        purpose="management",
    ),
    Route(
        "POST",
        rf"/api/v1/trading/execution/demo/market-close-orders/positions/{_ID}",
        "execution",
        20,
        mutation=True,
        purpose="management",
    ),
)


def allowed_route(method: str, path: str, params: Mapping[str, Any] | None = None) -> Route:
    # Validate the original string BEFORE httpx performs URL normalization.
    if not path.startswith("/api/") or any(ch in path for ch in ("%", "\\", "?", "#")):
        raise BrokerBlocked("ROUTE_NOT_ALLOWED")
    if "//" in path or any(part in {".", ".."} for part in path.split("/")):
        raise BrokerBlocked("AMBIGUOUS_PATH")
    for route in ROUTES:
        if method == route.method and re.fullmatch(route.pattern, path):
            if set(params or {}) - route.query:
                raise BrokerBlocked("UNDOCUMENTED_QUERY_PARAMETER")
            if path == LOOKUP:
                query = params or {}
                if len(query) != 1 or next(iter(query.values()), None) in (None, ""):
                    raise BrokerBlocked("LOOKUP_REQUIRES_EXACTLY_ONE_IDENTIFIER")
            return route
    raise BrokerBlocked("ROUTE_NOT_ALLOWED")


class QuotaBudget:
    """Rolling shared pools with five slots reserved for reconciliation/management."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self._uses: dict[str, deque[float]] = defaultdict(deque)
        self.blocked_until = 0.0

    def take(self, route: Route, priority: bool) -> None:
        now = self.clock()
        if now < self.blocked_until:
            raise BrokerBlocked("RATE_LIMIT_RETRY_AFTER_PENDING")
        # Conservatively cap all authenticated reads together as well as each
        # documented dedicated group. Different pool names cannot multiply quota.
        budgets = ((self._uses["_all"], 60), (self._uses[route.pool], route.quota))
        for uses, maximum in budgets:
            while uses and uses[0] <= now - 60:
                uses.popleft()
            limit = maximum if priority else maximum - 5
            if len(uses) >= limit:
                raise BrokerBlocked("RATE_LIMIT_RESERVED_CAPACITY")
        for uses, _ in budgets:
            uses.append(now)


def _json_bytes(value: Any) -> bytes:
    """Decimal remains a JSON number; finite values only, never binary rounding up."""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise BrokerBlocked("NONFINITE_PAYLOAD")
        return format(value, "f").encode()
    if isinstance(value, dict):
        return (
            b"{"
            + b",".join(
                json.dumps(str(k)).encode() + b":" + _json_bytes(v) for k, v in value.items()
            )
            + b"}"
        )
    if isinstance(value, (list, tuple)):
        return b"[" + b",".join(_json_bytes(v) for v in value) + b"]"
    return json.dumps(value, allow_nan=False).encode()


def _unambiguous_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


class GuardedTransport:
    def __init__(
        self,
        credentials: Credentials,
        *,
        mode: str,
        session_id: str,
        config_hash: str,
        authorization: DemoAuthorization | None = None,
        transport: httpx.BaseTransport | None = None,
        now: Callable[[], datetime] = utc_now,
        sleeper: Callable[[float], None] = time.sleep,
        quota: QuotaBudget | None = None,
    ) -> None:
        if mode not in {"shadow", "etoro_demo"}:
            raise BrokerBlocked("CONNECTED_MODE_REQUIRED")
        self.credentials = credentials
        self.mode = mode
        self.session_id = session_id
        self.config_hash = config_hash
        self.authorization = authorization
        self.now = now
        self.sleeper = sleeper
        self.quota = quota or QuotaBudget()
        self._preflight_only = False
        self.preflight_reads: list[str] = []
        self.preflight_http_statuses: list[int] = []
        self.mutation_attempts = 0
        self.response_received_at: datetime | None = None
        # Phase 2 is read-only on every network transport. Only the exact in-memory
        # httpx mock used by contract tests may exercise the existing mutation guards.
        # No configuration, environment variable or old authorization bypasses this.
        self._contract_transport = transport if type(transport) is httpx.MockTransport else None
        self._client = create_http_client(transport=transport)

    def close(self) -> None:
        self._client.close()

    def restrict_to_preflight(self) -> None:
        """One-way restriction, including contract mocks and previously armed sessions."""
        self._preflight_only = True

    def observe_demo(self) -> PreflightEvidence:
        """Read identity and Demo portfolio with the exact credentials in use."""
        fingerprint = self.credentials.fingerprint
        observed = require_demo(self.request("GET", ME, priority=True))
        assert observed.account_id is not None
        cash = portfolio_cash(self.request("GET", PORTFOLIO, priority=True), observed.account_id)
        if fingerprint != self.credentials.fingerprint:
            raise BrokerBlocked("CREDENTIALS_CHANGED")
        return PreflightEvidence(
            observed.account_id, observed.scopes, cash, self.now(), fingerprint
        )

    def verify_mutation_identity(self, permit: MutationPermit) -> None:
        """Fresh provider evidence plus existing lease; no caller-supplied identity."""
        self.require_contract_transport()
        authorization = self.authorization
        if authorization is None:
            raise BrokerBlocked("MUTATION_AUTHORIZATION_REQUIRED")
        binding = (self.session_id, self.config_hash, self.credentials.fingerprint)
        try:
            authorization.check(
                permit,
                session_id=binding[0],
                config_hash=binding[1],
                credential_fingerprint=binding[2],
                now=self.now(),
            )
            evidence = self.observe_demo()
            if (
                self.authorization is not authorization
                or binding != (self.session_id, self.config_hash, self.credentials.fingerprint)
                or evidence.account_id != authorization.account_id
            ):
                raise BrokerBlocked("DEMO_IDENTITY_BINDING_CHANGED")
            if not evidence.scopes & {"etoro-public:demo:write", "etoro-public:trade.demo:write"}:
                raise BrokerBlocked("DEMO_WRITE_SCOPE_UNVERIFIED")
            # Reads can consume the remainder of an expiring authorization.
            authorization.check(
                permit,
                session_id=self.session_id,
                config_hash=self.config_hash,
                credential_fingerprint=self.credentials.fingerprint,
                now=self.now(),
            )
        except BrokerBlocked:
            authorization.invalidate()
            raise

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        permit: MutationPermit | None = None,
        request_id: str | None = None,
        priority: bool = False,
        demo_preview: bool = False,
    ) -> dict[str, Any]:
        self.response_received_at = None
        if self._preflight_only and (method != "GET" or path not in {ME, PORTFOLIO, INSTRUMENTS}):
            raise BrokerBlocked("PREFLIGHT_READ_ONLY_ROUTE_REQUIRED")
        route = allowed_route(method, path, params)
        if demo_preview:
            if method != "POST" or path not in {COSTS, ELIGIBILITY}:
                raise BrokerBlocked("DEMO_PREVIEW_ROUTE_REQUIRED")
            self.observe_demo()
        if method == "GET" and body is not None:
            raise BrokerBlocked("GET_BODY_FORBIDDEN")
        if route.mutation:
            self.require_contract_transport()
            if self.mode != "etoro_demo" or os.getenv("CI", "").lower() in {"1", "true", "yes"}:
                raise BrokerBlocked("MUTATION_DISABLED_IN_THIS_MODE")
            if self.authorization is None or permit is None or permit.purpose != route.purpose:
                raise BrokerBlocked("MUTATION_AUTHORIZATION_REQUIRED")
            self.authorization.check(
                permit,
                session_id=self.session_id,
                config_hash=self.config_hash,
                credential_fingerprint=self.credentials.fingerprint,
                now=self.now(),
            )
            if request_id is None:
                raise BrokerBlocked("PERSISTED_REQUEST_ID_REQUIRED")
        reference = request_id or str(uuid4())
        try:
            UUID(reference)
        except (ValueError, AttributeError):
            raise BrokerBlocked("REQUEST_ID_MUST_BE_UUID") from None
        payload = _json_bytes(dict(body)) if body is not None else None
        if route.mutation:
            assert permit is not None
            self.verify_mutation_identity(permit)
        if method == "POST" and not route.mutation and not demo_preview:
            # Cost/eligibility are documented read semantics, but this phase has
            # authorized only GET diagnostics on the actual account.
            self.require_contract_transport()
        for attempt in range(1 if route.mutation else 3):
            self.quota.take(
                route, priority or (permit is not None and permit.purpose == "management")
            )
            if self._preflight_only:
                self.preflight_reads.append(path)
            try:
                headers = {
                    "x-api-key": self.credentials.api_key,
                    "x-user-key": self.credentials.user_key,
                    "x-request-id": reference,
                    "Content-Type": "application/json",
                }
                if route.mutation or (method == "POST" and not demo_preview):
                    # Dispatch directly to the pinned mock, never through mounts,
                    # proxies or a replaceable network client.
                    assert self._contract_transport is not None
                    request = httpx.Request(
                        method, ORIGIN + path, params=params, content=payload, headers=headers
                    )
                    if route.mutation:
                        self.mutation_attempts += 1
                    response = self._contract_transport.handle_request(request)
                    response.read()
                else:
                    response = self._client.request(
                        method,
                        ORIGIN + path,
                        params=params,
                        content=payload,
                        headers=headers,
                        follow_redirects=False,
                    )
            except httpx.TransportError:
                if route.mutation:
                    raise SubmissionUnknown("SUBMISSION_UNKNOWN_RECONCILE_NO_RETRY") from None
                if attempt == 2:
                    raise BrokerBlocked("ETORO_READ_UNAVAILABLE") from None
                self.sleeper(0.25 * 2**attempt + random.uniform(0, 0.1))
                continue
            self.response_received_at = self.now()
            if self._preflight_only:
                self.preflight_http_statuses.append(response.status_code)
            if 300 <= response.status_code < 400:
                raise BrokerBlocked("AUTHENTICATED_REDIRECT_BLOCKED")
            if response.status_code == 429:
                delay = self._retry_after(response)
                self.quota.blocked_until = max(self.quota.blocked_until, self.quota.clock() + delay)
                if not route.mutation and delay <= 10 and attempt < 2:
                    self.sleeper(delay)
                    continue
            elif response.status_code >= 500 and not route.mutation and attempt < 2:
                self.sleeper(0.25 * 2**attempt + random.uniform(0, 0.1))
                continue
            if response.status_code >= 400:
                raise BrokerHTTPError(response.status_code)
            if (self._preflight_only or path in {ME, PORTFOLIO}) and response.status_code != 200:
                raise BrokerBlocked("PREFLIGHT_UNEXPECTED_HTTP_STATUS")
            try:
                document = json.loads(
                    response.content,
                    parse_float=Decimal,
                    object_pairs_hook=_unambiguous_object,
                )
            except (ValueError, UnicodeError):
                raise BrokerBlocked("INVALID_ETORO_RESPONSE") from None
            if not isinstance(document, dict):
                raise BrokerBlocked("INVALID_ETORO_RESPONSE")
            return document
        raise BrokerBlocked("ETORO_READ_UNAVAILABLE")

    def require_contract_transport(self) -> None:
        if type(self._contract_transport) is not httpx.MockTransport:
            raise BrokerBlocked("EXTERNAL_MUTATIONS_DISABLED_PHASE2")

    def _retry_after(self, response: httpx.Response) -> float:
        value = response.headers.get("Retry-After", "60")
        try:
            result = float(value)
        except ValueError:
            try:
                result = (parsedate_to_datetime(value) - self.now()).total_seconds()
            except (TypeError, ValueError, OverflowError):
                result = 60
        if not 0 <= result < float("inf"):
            return 60
        return result
