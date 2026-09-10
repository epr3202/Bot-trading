from __future__ import annotations

import argparse
import json
import logging
import os
import secrets
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import uvicorn
from pydantic import ValidationError

from intraday_etoro_lab.api.app import ControlSettings, create_app
from intraday_etoro_lab.brokers.authorization import BrokerBlocked
from intraday_etoro_lab.brokers.etoro_demo import perform_preflight
from intraday_etoro_lab.brokers.transport import Credentials, GuardedTransport
from intraday_etoro_lab.config import AppConfig, Mode, load_config
from intraday_etoro_lab.data.importer import audit_bundle
from intraday_etoro_lab.observability.logging import JsonFormatter
from intraday_etoro_lab.persistence.store import StateStore
from intraday_etoro_lab.service import OperationService, load_bundle, read_report


def emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="bot", description="Laboratorio ORB/RVOL solo virtual")
    sub = root.add_subparsers(dest="command", required=True)
    for name in (
        "doctor",
        "demo-offline",
        "backtest",
        "pause-entries",
        "reconcile",
        "cancel-pending-entries",
    ):
        command = sub.add_parser(name)
        command.add_argument("--config", type=Path, default=Path("configs/offline.yaml"))
    run = sub.add_parser("run")
    run.add_argument("--mode", choices=[m.value for m in Mode], default="offline")
    run.add_argument("--config", type=Path, default=Path("configs/offline.yaml"))
    data = sub.add_parser("data").add_subparsers(dest="data_command", required=True)
    validate = data.add_parser("validate")
    validate.add_argument("--config", type=Path, default=Path("configs/offline.yaml"))
    report = sub.add_parser("report")
    report.add_argument("--run-id", required=True)
    report.add_argument("--config", type=Path, default=Path("configs/offline.yaml"))
    dashboard = sub.add_parser("dashboard")
    dashboard.add_argument("--host", choices=["127.0.0.1"], default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8765)
    dashboard.add_argument("--config", type=Path, default=Path("configs/offline.yaml"))
    etoro = sub.add_parser("etoro").add_subparsers(dest="etoro_command", required=True)
    preflight = etoro.add_parser("preflight")
    preflight.add_argument("--read-only", action="store_true", required=True)
    preflight.add_argument("--config", type=Path, default=Path("configs/offline.yaml"))
    for name in ("arm-demo", "flatten-owned-demo"):
        command = sub.add_parser(name)
        command.add_argument("--confirm", required=True, choices=["DEMO_ONLY"])
        command.add_argument(
            "--budget", help="Presupuesto virtual aceptado; obligatorio para armado"
        )
        command.add_argument("--config", type=Path, default=Path("configs/offline.yaml"))
    backup = sub.add_parser("backup")
    backup.add_argument("--destination", type=Path, required=True)
    backup.add_argument("--config", type=Path, default=Path("configs/offline.yaml"))
    restore = sub.add_parser("restore")
    restore.add_argument("--source", type=Path, required=True)
    restore.add_argument("--destination", type=Path, required=True)
    restore.add_argument("--config", type=Path, default=Path("configs/offline.yaml"))
    return root


def doctor(config: AppConfig) -> dict[str, Any]:
    configured = bool(os.getenv("ETORO_API_KEY") and os.getenv("ETORO_USER_KEY"))
    return {
        "software": "LOCAL_PROCESS_OK",
        "mode": config.mode.value,
        "python": sys.version.split()[0],
        "configuration": "VALID",
        "config_hash": config.config_hash,
        "broker": "BLOCKED" if configured else "NOT_CONFIGURED",
        "entries_armed": False,
        "external_mutations": "DISABLED",
        "close_reconciliation": "BLOCKED",
        "etoro_demo_write": "NOT_TESTED",
        "order_submission_enabled": config.order_submission_enabled,
        "data": "SYNTHETIC_ONLY" if config.data.provider == "fixtures" else "IMPORT_NOT_CHECKED",
        "research": "RESEARCH_BLOCKED_DATA",
        "blockers": [
            {
                "id": "DEMO_PREFLIGHT",
                "solution": "Claves propias Demo y preflight explícito de lectura",
            },
            {
                "id": "OHLCV_SOURCE",
                "solution": "Validar volumen negociado, historia y datos de sesión compatibles",
            },
            {
                "id": "DEMO_SESSION_RUNNER_NOT_VALIDATED",
                "solution": "Completar sesión, elegibilidad, costes, stops y reconciliación",
            },
            {
                "id": "DEMO_NOT_ARMED",
                "solution": "Presupuesto aceptado, gates y autorización temporal; nunca implícita",
            },
        ],
        "network_calls": 0,
    }


def control(
    config: AppConfig, action: str, confirm: str = "", budget: str | None = None
) -> dict[str, Any]:
    endpoint = config.runtime_dir / "control.json"
    if endpoint.is_file():
        info = json.loads(endpoint.read_text(encoding="utf-8"))
        settings = ControlSettings.model_validate(info["settings"])
        if info["config_hash"] != config.config_hash:
            raise RuntimeError("BLOCKED: configuración distinta del ejecutor activo")
        token = (config.runtime_dir / "control-token").read_text(encoding="utf-8").strip()
        with httpx.Client(timeout=120, follow_redirects=False, trust_env=False) as client:
            try:
                response = client.post(
                    settings.origin + "/api/commands",
                    headers={"Authorization": f"Bearer {token}", "Origin": settings.origin},
                    json={"action": action, "confirm": confirm, "budget": budget},
                )
            except httpx.HTTPError:
                raise RuntimeError(
                    "BLOCKED: ejecutor local inaccesible; reinicie dashboard y reconcilie"
                ) from None
        if response.status_code != 200:
            raise RuntimeError(f"BLOCKED: comando local HTTP {response.status_code}")
        result: dict[str, Any] = response.json()
        return result
    if action in {
        "arm-demo",
        "flatten-owned-demo",
        "pause-entries",
        "reconcile",
        "cancel-pending-entries",
    }:
        raise RuntimeError("BLOCKED: inicie dashboard; los controles se dirigen al ejecutor único")
    service = OperationService(config)
    try:
        return service.command(action, confirm, budget)
    finally:
        service.close()


def run_dashboard(config: AppConfig, host: str, port: int) -> None:
    settings = ControlSettings(host=host, port=port)  # type: ignore[arg-type]
    service = OperationService(config)
    token = secrets.token_urlsafe(36)
    token_path = config.runtime_dir / "control-token"
    endpoint = config.runtime_dir / "control.json"
    try:
        token_path.write_text(token, encoding="utf-8")
        if os.name != "nt":
            token_path.chmod(0o600)
        endpoint.write_text(
            json.dumps({"settings": settings.model_dump(), "config_hash": config.config_hash}),
            encoding="utf-8",
        )
        emit(
            {
                "dashboard": settings.origin,
                "mode": config.mode.value,
                "control_token_file": str(token_path),
                "entries_armed": False,
            }
        )
        uvicorn.run(
            create_app(service, token, settings),
            host=host,
            port=port,
            access_log=False,
            proxy_headers=False,
        )
    finally:
        endpoint.unlink(missing_ok=True)
        token_path.unlink(missing_ok=True)
        service.close()


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    handler = logging.StreamHandler()
    handler.setFormatter(
        JsonFormatter(
            tuple(filter(None, (os.getenv("ETORO_API_KEY"), os.getenv("ETORO_USER_KEY"))))
        )
    )
    logging.getLogger("intraday_etoro_lab").addHandler(handler)
    try:
        config = load_config(args.config, getattr(args, "mode", None))
        if args.command == "doctor":
            emit(doctor(config))
        elif args.command == "data":
            bundle = load_bundle(config)
            emit(bundle.manifest.model_dump(mode="json") | {"audit": audit_bundle(bundle)})
        elif args.command == "report":
            emit(read_report(args.run_id, config.reports_dir))
        elif args.command == "dashboard":
            run_dashboard(config, args.host, args.port)
        elif args.command == "etoro":
            transport = GuardedTransport(
                Credentials.from_environment(),
                mode="shadow",
                session_id=str(uuid4()),
                config_hash=config.config_hash,
            )
            try:
                evidence = perform_preflight(transport)
                # No CID, personal profile or complete portfolio is printed or saved.
                emit(
                    {
                        "broker": "DEMO_READ_VERIFIED",
                        "verified_at": evidence.verified_at,
                        "entries_armed": False,
                        "scope_count": len(evidence.scopes),
                        "writes": 0,
                        "external_mutations": "DISABLED",
                        "connectivity": "VERIFIED",
                        "authentication": "VERIFIED",
                        "demo_identity": "VERIFIED",
                        "market_data": "NOT_CHECKED",
                        "etoro_demo_write": "NOT_TESTED",
                        "operational_permission": "BLOCKED",
                        "scope": "Identidad mínima y lectura de portafolio virtual",
                    }
                )
            finally:
                transport.close()
        elif args.command == "run" and config.mode in {Mode.SHADOW, Mode.ETORO_DEMO}:
            raise BrokerBlocked(
                "DEMO_SESSION_RUNNER_NOT_VALIDATED: no se sustituye conexión por fixtures"
            )
        elif args.command == "backup":
            store = StateStore(
                config.runtime_dir / f"{config.mode.value}.sqlite", mode=config.mode.value
            )
            try:
                emit({"backup": str(store.backup(args.destination))})
            finally:
                store.close()
        elif args.command == "restore":
            emit(
                {
                    "restored_copy": str(StateStore.restore(args.source, args.destination)),
                    "entries_armed": False,
                }
            )
        else:
            action = "demo-offline" if args.command == "run" else args.command
            state = control(
                config, action, getattr(args, "confirm", ""), getattr(args, "budget", None)
            )
            report = state.get("report")
            emit(
                {
                    "mode": state["mode"],
                    "orders": len(state["orders"]),
                    "open_positions": len(state["positions"]),
                    "realized_simulator_pnl": state["realized_pnl"],
                    "report_run_id": report["run_id"] if report else None,
                    "research_status": state["research_status"],
                    "broker": state["broker_status"],
                    "label": report["label"]
                    if report
                    else "SYNTHETIC — NO EVIDENCE OF PROFITABILITY",
                }
            )
        return 0
    except (ValidationError, ValueError, RuntimeError, OSError) as exc:
        # Exception details from untrusted broker/data responses are never interpolated.
        if isinstance(exc, ValidationError):
            reason = "CONFIGURATION_INVALID: " + ", ".join(
                ".".join(str(p) for p in e["loc"]) for e in exc.errors()
            )
        elif isinstance(exc, OSError):
            reason = f"LOCAL_IO_ERROR:{type(exc).__name__}"
        else:
            reason = str(exc)
        result = {
            "status": "BLOCKED",
            "reason": reason,
            "entries_armed": False,
            "external_mutations": "DISABLED",
            "etoro_demo_write": "NOT_TESTED",
        }
        if args.command == "etoro":
            missing = reason == "CREDENTIALS_MISSING_OR_INVALID"
            http_reached = reason.startswith("ETORO_HTTP_")
            result.update(
                {
                    "etoro_demo_read": "NOT_CONFIGURED" if missing else "BLOCKED",
                    "connectivity": "VERIFIED" if http_reached else "NOT_CHECKED",
                    "authentication": "FAILED" if reason == "ETORO_HTTP_401" else "NOT_VERIFIED",
                    "demo_identity": "NOT_VERIFIED",
                    "market_data": "NOT_CHECKED",
                    "operational_permission": "BLOCKED",
                }
            )
        emit(result)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
