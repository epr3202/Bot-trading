"""Provider-observed access classification; configuration is never evidence."""

import re
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any

from intraday_etoro_lab.brokers.authorization import BrokerBlocked


class AccountType(StrEnum):
    DEMO = "DEMO"
    REAL = "REAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ObservedIdentity:
    account_type: AccountType
    reason: str
    account_id: int | None = field(default=None, repr=False)
    scopes: frozenset[str] = frozenset()


def classify_identity(identity: dict[str, Any]) -> ObservedIdentity:
    """Classify granted access, not the human (who may have both account IDs).

    DEMO here still requires a successful validated Demo portfolio read before
    it becomes preflight evidence. Mixed, malformed or wildcard access is denied.
    """
    account = identity.get("demoCid")
    scopes = identity.get("scopes")
    reason = ""
    if type(account) is not int or account <= 0 or not isinstance(scopes, list):
        reason = "DEMO_IDENTITY_OR_SCOPES_UNVERIFIED"
    elif identity.get("realCid") == account:
        reason = "DEMO_IDENTITY_AMBIGUOUS"
    elif "realCid" in identity and (
        type(identity["realCid"]) is not int or identity["realCid"] < 0
    ):
        reason = "DEMO_IDENTITY_AMBIGUOUS"
    elif not scopes or any(not isinstance(scope, str) for scope in scopes):
        reason = "DEMO_SCOPE_UNVERIFIED_FOR_KEYS"
    elif any("real" in scope.lower() or "*" in scope for scope in scopes):
        reason = "NON_DEMO_SCOPE_DETECTED"
    elif any(not re.fullmatch(r"etoro-public:[a-z.-]+:(?:read|write)", s) for s in scopes):
        reason = "DEMO_SCOPE_UNVERIFIED_FOR_KEYS"
    elif not set(scopes) & {
        "etoro-public:demo:read",
        "etoro-public:demo:write",
        "etoro-public:trade.demo:read",
        "etoro-public:trade.demo:write",
    }:
        reason = "DEMO_SCOPE_INSUFFICIENT"
    if not reason:
        assert isinstance(scopes, list)
        return ObservedIdentity(
            AccountType.DEMO, "DEMO_ACCESS_OBSERVED", account, frozenset(scopes)
        )
    real_scopes = {
        "etoro-public:real:read",
        "etoro-public:real:write",
        "etoro-public:trade.real:read",
        "etoro-public:trade.real:write",
    }
    # Explicit valid Real grants identify forbidden access even when Demo also exists.
    real = (
        type(identity.get("realCid")) is int
        and identity["realCid"] > 0
        and isinstance(scopes, list)
        and all(isinstance(s, str) for s in scopes)
        and bool(set(scopes) & real_scopes)
        and reason != "DEMO_IDENTITY_AMBIGUOUS"
    )
    return ObservedIdentity(AccountType.REAL if real else AccountType.UNKNOWN, reason)


def require_demo(identity: dict[str, Any]) -> ObservedIdentity:
    observed = classify_identity(identity)
    if observed.account_type != AccountType.DEMO:
        raise BrokerBlocked(observed.reason)
    return observed


def portfolio_cash(portfolio: dict[str, Any], account: int) -> Decimal:
    """Validate the existing Demo portfolio contract; cash is not sizing approval."""
    try:
        client = portfolio["clientPortfolio"]
        if not isinstance(client, dict) or isinstance(client.get("credit"), bool):
            raise ValueError
        if "CID" in client and (type(client["CID"]) is not int or client["CID"] != account):
            raise ValueError
        cash = Decimal(str(client["credit"]))
        if not cash.is_finite() or cash < 0:
            raise ValueError
        for name in ("positions", "orders", "mirrors", "ordersForOpen", "ordersForClose"):
            if not isinstance(client[name], list):
                raise ValueError
            for row in client[name]:
                if not isinstance(row, dict):
                    raise ValueError
                if "CID" in row and (type(row["CID"]) is not int or row["CID"] != account):
                    raise ValueError
    except (KeyError, TypeError, ValueError, ArithmeticError):
        raise BrokerBlocked("DEMO_PORTFOLIO_UNVERIFIED") from None
    return cash
