"""A5 read-only application service; never constructs an execution adapter."""

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from intraday_etoro_lab.brokers.authorization import BrokerBlocked, utc_now
from intraday_etoro_lab.brokers.etoro_demo import perform_preflight
from intraday_etoro_lab.brokers.market_data import EtoroMarketDataProvider
from intraday_etoro_lab.brokers.transport import ORIGIN, Credentials, GuardedTransport
from intraday_etoro_lab.config import AppConfig
from intraday_etoro_lab.domain.models import Instrument
from intraday_etoro_lab.observability.logging import redact


def strategy_symbol(manifest: Path, config: AppConfig) -> str:
    """Reuse the approved research universe without loading data or running Strategy 1."""
    try:
        document = json.loads(manifest.read_text(encoding="utf-8"))
        if document["schema_version"] != "massive-a2-v1":
            raise ValueError
        symbol = Instrument(symbol=document["symbol"]).symbol
        if symbol in config.strategy.rs_benchmarks:
            raise ValueError
        return symbol
    except (OSError, ValueError, TypeError, KeyError):
        raise BrokerBlocked("PREFLIGHT_STRATEGY_MANIFEST_INVALID") from None


def run_demo_preflight(config: AppConfig, manifest: Path) -> dict[str, Any]:
    """Return only sanitized evidence, also on failure; PASS is never an activation gate."""
    result: dict[str, Any] = {
        "schema_version": "etoro-demo-preflight-a5-v1",
        "timestamp": utc_now().isoformat(),
        "overall": "FAIL",
        "connectivity": "NOT_CHECKED",
        "authentication": "NOT_VERIFIED",
        "account_environment": "UNKNOWN",
        "demo_verification": "FAIL",
        "account_identifier": None,
        "permissions": {"observed": [], "inferred": [], "status": "NOT_VERIFIED"},
        "virtual_cash": {"status": "NOT_CHECKED", "currency": "NOT_PROVIDED"},
        "instrument_check": "NOT_CHECKED",
        "mutation_protection": "PASS",
        "writes": 0,
        "entries_armed": False,
        "external_mutations": "DISABLED",
        "etoro_demo_write": "NOT_TESTED",
        "operational_permission": "BLOCKED",
        "environment": "etoro_demo",
        "origin": ORIGIN,
        "config_hash": config.config_hash,
        "strategy_version": config.strategy.version,
        "operations": [],
        "limitations": [
            "Demo proof combines demoCid, explicit Demo scopes and the Demo portfolio route.",
            "Scopes absent for API keys fail closed; configuration is not permission evidence.",
            "credit is portfolio credit, not reconciled cash available for sizing.",
            "Market metadata is shared; resolution does not verify trading eligibility or RVOL.",
        ],
    }
    transport: GuardedTransport | None = None
    secrets: tuple[str, ...] = ()
    try:
        symbol = strategy_symbol(manifest, config)
        credentials = Credentials.from_environment()
        secrets = (credentials.api_key, credentials.user_key)
        transport = GuardedTransport(
            credentials, mode="shadow", session_id=str(uuid4()), config_hash=config.config_hash
        )
        evidence = perform_preflight(transport)
        # Do not retain CID or a reversible suffix; salt varies with each invocation.
        account_ref = hashlib.sha256(
            f"{transport.session_id}:{evidence.account_id}".encode()
        ).hexdigest()[:16]
        result.update(
            connectivity="PASS",
            authentication="PASS",
            account_environment="DEMO",
            demo_verification="PASS",
            account_identifier=f"demo-{account_ref}",
            permissions={
                "observed": sorted(evidence.scopes),
                "inferred": [],
                "status": "VERIFIED_FROM_ME",
                "effective_writes": "NOT_TESTED",
            },
            virtual_cash={
                "status": "PASS",
                "value": str(evidence.available_cash),
                "field": "clientPortfolio.credit",
                "currency": "NOT_PROVIDED",
            },
        )
        result["instrument_check"] = "FAIL"
        document = EtoroMarketDataProvider(transport).instruments([symbol])
        try:
            rows = document["results"]
            if len(rows) != 1 or document["pagination"]["hasNext"] is not False:
                raise ValueError
            row = rows[0]
            if row["symbol"] != symbol or row["type"] != "Stocks":
                raise ValueError
            for key in ("instrumentId", "exchangeId"):
                if type(row[key]) is not int or row[key] <= 0:
                    raise ValueError
        except (KeyError, TypeError, ValueError):
            raise BrokerBlocked("PREFLIGHT_INSTRUMENT_UNVERIFIED") from None
        result.update(
            instrument_check="PASS",
            instrument={key: row[key] for key in ("symbol", "type", "instrumentId", "exchangeId")},
            overall="PASS",
            broker="DEMO_READ_VERIFIED",
        )
    except BrokerBlocked as exc:
        reason = str(exc)
        result["reason"] = reason
        result["etoro_demo_read"] = (
            "NOT_CONFIGURED" if reason == "CREDENTIALS_MISSING_OR_INVALID" else "BLOCKED"
        )
        if reason.startswith("ETORO_HTTP_"):
            result["connectivity"] = "PASS"
        if reason in {"ETORO_HTTP_401", "ETORO_HTTP_403"}:
            result["authentication"] = "FAIL"
        if reason == "ETORO_READ_UNAVAILABLE":
            result["connectivity"] = "FAIL"
    finally:
        if transport is not None:
            result["operations"] = [f"GET {path}" for path in transport.preflight_reads]
            result["http_statuses"] = transport.preflight_http_statuses
            if transport.preflight_http_statuses:
                result["connectivity"] = "PASS"
            transport.close()
    return dict(redact(result, secrets))
