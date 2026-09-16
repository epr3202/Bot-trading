"""Ephemeral authorization: a restart cannot carry an armed entry lease."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal
from uuid import uuid4


class BrokerBlocked(RuntimeError):
    """Public error containing only a static reason, never broker response text."""


class RejectedBeforeSend(BrokerBlocked):
    """The adapter proved that this invocation never attempted a trading mutation."""


@dataclass(frozen=True)
class PreflightEvidence:
    account_id: int = field(repr=False)
    scopes: frozenset[str]
    available_cash: Decimal
    verified_at: datetime
    credential_fingerprint: str


@dataclass(frozen=True)
class ActivationGates:
    data_verified: bool = False
    calendar_verified: bool = False
    risk_verified: bool = False
    reconciliation_verified: bool = False
    native_stop_verified: bool = False
    eligibility_verified: bool = False
    persistence_verified: bool = False

    def ready(self) -> bool:
        return all(vars(self).values())


@dataclass(frozen=True)
class MutationPermit:
    nonce: str
    purpose: Literal["entry", "management"]


class DemoAuthorization:
    def __init__(self, session_id: str, config_hash: str) -> None:
        if not session_id or len(config_hash) != 64:
            raise BrokerBlocked("INVALID_SESSION_OR_CONFIG_HASH")
        self.session_id = session_id
        self.config_hash = config_hash
        self._nonce = str(uuid4())
        self._evidence: PreflightEvidence | None = None
        self._entry_expiry: datetime | None = None
        self._management_expiry: datetime | None = None
        self._budget = Decimal(0)

    def activate(
        self,
        evidence: PreflightEvidence,
        gates: ActivationGates,
        *,
        accepted_budget: Decimal,
        explicit_confirmation: bool,
        submission_enabled: bool,
        now: datetime,
        entry_seconds: int = 300,
        management_seconds: int = 3600,
    ) -> None:
        self.pause_entries()
        if not explicit_confirmation or not submission_enabled or not gates.ready():
            raise BrokerBlocked("DEMO_ACTIVATION_GATES_INCOMPLETE")
        if not 1 <= entry_seconds <= 900 or not entry_seconds <= management_seconds <= 86400:
            raise BrokerBlocked("INVALID_AUTHORIZATION_DURATION")
        if now.tzinfo is None or evidence.verified_at.tzinfo is None:
            raise BrokerBlocked("TIMEZONE_REQUIRED")
        if not timedelta(0) <= now - evidence.verified_at <= timedelta(seconds=60):
            raise BrokerBlocked("PREFLIGHT_STALE")
        if not evidence.account_id > 0 or not evidence.scopes & {
            "etoro-public:demo:write",
            "etoro-public:trade.demo:write",
        }:
            raise BrokerBlocked("DEMO_WRITE_SCOPE_UNVERIFIED")
        if any("real" in scope or scope.endswith(":*") for scope in evidence.scopes):
            raise BrokerBlocked("NON_DEMO_SCOPE_DETECTED")
        if not accepted_budget.is_finite() or not 0 < accepted_budget <= evidence.available_cash:
            raise BrokerBlocked("VIRTUAL_BUDGET_INVALID")
        self._evidence = evidence
        self._budget = accepted_budget
        self._entry_expiry = now + timedelta(seconds=entry_seconds)
        self._management_expiry = now + timedelta(seconds=management_seconds)
        self._nonce = str(uuid4())

    def pause_entries(self) -> None:
        self._entry_expiry = None

    def invalidate(self) -> None:
        self.pause_entries()
        self._management_expiry = None
        self._evidence = None
        self._nonce = str(uuid4())

    def permit(self, purpose: Literal["entry", "management"]) -> MutationPermit:
        return MutationPermit(self._nonce, purpose)

    def check(
        self,
        permit: MutationPermit,
        *,
        session_id: str,
        config_hash: str,
        credential_fingerprint: str,
        now: datetime,
    ) -> None:
        if session_id != self.session_id:
            self.pause_entries()
            raise BrokerBlocked("AUTHORIZATION_BINDING_CHANGED")
        if config_hash != self.config_hash:
            self.pause_entries()
            if permit.purpose == "entry":
                raise BrokerBlocked("AUTHORIZATION_BINDING_CHANGED")
        if self._evidence is None or permit.nonce != self._nonce:
            raise BrokerBlocked("DEMO_NOT_ARMED")
        if credential_fingerprint != self._evidence.credential_fingerprint:
            self.invalidate()
            raise BrokerBlocked("CREDENTIALS_CHANGED")
        expiry = self._entry_expiry if permit.purpose == "entry" else self._management_expiry
        if now.tzinfo is None or expiry is None or now >= expiry:
            raise BrokerBlocked("DEMO_AUTHORIZATION_EXPIRED_OR_PAUSED")

    @property
    def account_id(self) -> int:
        if self._evidence is None:
            raise BrokerBlocked("PREFLIGHT_REQUIRED")
        return self._evidence.account_id

    @property
    def budget(self) -> Decimal:
        return self._budget


def utc_now() -> datetime:
    return datetime.now(UTC)
