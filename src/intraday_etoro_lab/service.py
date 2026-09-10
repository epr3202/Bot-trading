from __future__ import annotations

import hashlib
import html
import json
import os
import re
import subprocess
import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from intraday_etoro_lab.backtesting.engine import BacktestResult, run_backtest
from intraday_etoro_lab.backtesting.experiments import append_experiment
from intraday_etoro_lab.brokers.simulator import SimulatorBroker
from intraday_etoro_lab.config import AppConfig, Mode
from intraday_etoro_lab.data import FixtureProvider
from intraday_etoro_lab.data.importer import import_market_data
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.execution.engine import Executor
from intraday_etoro_lab.persistence.store import ExecutorLock, StateStore
from intraday_etoro_lab.risk import EntryRequest, RiskEngine
from intraday_etoro_lab.strategies.orb import ORBStrategy


def load_bundle(config: AppConfig) -> DataBundle:
    if config.data.provider == "fixtures":
        return FixtureProvider().load()
    if config.data.path is None or config.data.manifest is None:
        raise ValueError("Importación requiere archivo y manifiesto")
    return import_market_data(config.data.path, config.data.manifest)


def source_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    revision = result.stdout.strip() if result.returncode == 0 else "UNCOMMITTED"
    digest = hashlib.sha256()
    root = Path(__file__).parent
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in {".py", ".html", ".js", ".css"}:
            digest.update(str(path.relative_to(root)).replace("\\", "/").encode())
            digest.update(path.read_bytes())
    return f"{revision}+source.{digest.hexdigest()[:16]}"


def save_report(report: BacktestResult, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for existing in directory.glob("[0-9a-f]" * 20 + ".json"):
        previous = json.loads(existing.read_text(encoding="utf-8"))
        if previous["data_manifest"]["synthetic"] != report.data_manifest["synthetic"]:
            raise RuntimeError("REPORT_SOURCE_MIXING_BLOCKED: use a separate reports_dir")
    target = directory / f"{report.run_id}.json"
    payload = report.model_dump_json(indent=2)
    if target.exists():
        if target.read_text(encoding="utf-8") != payload:
            raise RuntimeError("REPORT_COLLISION: un run_id no puede sobrescribir otro resultado")
    else:
        with target.open("x", encoding="utf-8") as handle:
            handle.write(payload)
    exported = directory / f"{report.run_id}.html"
    if not exported.exists():
        data = report.model_dump(mode="json")
        rows = "".join(
            f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>"
            for key, value in data["metrics"].items()
        )
        with exported.open("x", encoding="utf-8") as handle:
            handle.write(
                '<!doctype html><html lang="es"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                f"<title>Informe {report.run_id}</title><style>"
                "body{max-width:960px;margin:40px auto;padding:20px;font:15px system-ui;"
                "color:#243b35}td{padding:10px;border-bottom:1px solid #ddd}"
                "pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px}"
                "</style><h1>Informe de investigación</h1>"
                f"<p><strong>{html.escape(report.label)}</strong></p>"
                f"<p>{html.escape(report.research_status)}</p><table>{rows}</table>"
                f"<h2>Manifiesto y resultados</h2><pre>{html.escape(payload)}</pre></html>"
            )
    return target


def read_report(run_id: str, directory: Path) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{20}", run_id):
        raise ValueError("run_id inválido")
    path = directory / f"{run_id}.json"
    if not path.is_file():
        raise ValueError("Informe inexistente")
    result: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return result


class OperationService:
    """One local command owner, serialized requests, separate state for every mode."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.mutex = threading.RLock()
        self.owner = ExecutorLock(config.runtime_dir / "operation-owner.lock")
        self.owner.acquire()
        self.db_path = config.runtime_dir / f"{config.mode.value}.sqlite"
        self.bundle: DataBundle | None = None
        self.session_id = "local-fixture-v1"
        try:
            store = self._store()
            try:
                store.ensure_session(self.session_id, config.risk.allocated_capital)
                store.pause(self.session_id)
                store.audit("CONTROL_START_DISARMED", details=config.config_hash)
            finally:
                store.close()
        except BaseException:
            self.owner.release()
            raise

    def _store(self) -> StateStore:
        return StateStore(self.db_path, mode=self.config.mode.value)

    def close(self) -> None:
        self.owner.release()

    def _bundle(self) -> DataBundle:
        if self.bundle is None:
            self.bundle = load_bundle(self.config)
        return self.bundle

    def _run_research(self, store: StateStore) -> None:
        report = run_backtest(
            self._bundle(),
            self.config.strategy,
            self.config.backtest,
            self.config.risk,
            self.config.costs,
            commit=source_revision(),
        )
        save_report(report, self.config.reports_dir)
        append_experiment(
            self.config.reports_dir / "experiments.jsonl",
            report,
            "ORB/RVOL v0.1: ejecución de reglas fijadas, sin selección por resultado",
        )
        store.set_meta("data_manifest", self._bundle().manifest.model_dump_json())
        store.set_meta("latest_report", report.run_id)
        store.audit("RESEARCH_RUN", details=f"{report.run_id} {report.label}")

    def _fixture_start(self, store: StateStore, executor: Executor) -> None:
        bundle = self._bundle()
        if not bundle.manifest.synthetic:
            raise RuntimeError("FIXTURE_REQUIRES_SYNTHETIC_DATA")
        decision = ORBStrategy(self.config.strategy).process_session(
            bundle,
            bundle.evaluation_sessions[0],
        )
        store.set_meta("selection", decision.model_dump_json())
        store.set_meta("data_manifest", bundle.manifest.model_dump_json())
        executor.arm_offline()
        for signal in sorted(decision.signals, key=lambda s: (s.available_at, s.rank)):
            # Explicit synthetic executable quotes for lifecycle testing. These are not
            # historical minute fills; the separate backtest uses the next minute open.
            quote_at = signal.available_at + timedelta(milliseconds=250)
            decision_at = quote_at + timedelta(milliseconds=250)
            ask = signal.reference_price + Decimal("0.01")
            request = EntryRequest(
                signal_id=signal.signal_id,
                session_id=self.session_id,
                symbol=signal.instrument.symbol,
                available_at=signal.available_at,
                expires_at=signal.expires_at,
                now=decision_at,
                entry_price=ask,
                stop_price=signal.stop_price,
                bid=signal.reference_price - Decimal("0.01"),
                ask=ask,
                quote_at=quote_at,
                reference_price=signal.reference_price,
                source_price=signal.reference_price,
                version=signal.strategy_version,
            )
            result = executor.submit_entry(request)
            store.audit("FIXTURE_SIGNAL", signal.signal_id, result.decision.reason)

    def _fixture_close(self, store: StateStore, executor: Executor) -> None:
        for position in store.positions():
            # Independent deterministic quote scenario for the lifecycle demonstration.
            exit_price = position.average_entry + Decimal("0.20")
            executor.close_owned(position.position_id, price=exit_price)
        executor.reconcile()

    def command(self, action: str, confirm: str = "", budget: str | None = None) -> dict[str, Any]:
        with self.mutex:
            store = self._store()
            try:
                store.audit("CONTROL_COMMAND", details=action)
                if action in {"arm-demo", "flatten-owned-demo"}:
                    if confirm != "DEMO_ONLY":
                        raise ValueError("Confirmación DEMO_ONLY requerida")
                    if action == "arm-demo" and budget != str(self.config.risk.allocated_capital):
                        raise ValueError(
                            "Debe aceptar exactamente el presupuesto virtual configurado"
                        )
                    raise RuntimeError(
                        "BLOCKED: DEMO_SESSION_RUNNER_NOT_VALIDATED; faltan preflight propio, "
                        "datos compatibles, elegibilidad y protección verificadas. Sin escrituras."
                    )
                if self.config.mode not in {Mode.OFFLINE, Mode.BACKTEST}:
                    raise RuntimeError(
                        "BLOCKED: modo conectado sin sesión validada; no se usan fixtures"
                    )
                if action == "backtest":
                    self._run_research(store)
                else:
                    with Executor(
                        store,
                        SimulatorBroker(store, costs=self.config.costs),
                        RiskEngine(self.config.risk, self.config.costs),
                        self.session_id,
                    ) as executor:
                        if action in {"demo-offline", "fixture-start"}:
                            self._fixture_start(store, executor)
                        if action in {"demo-offline", "fixture-close"}:
                            self._fixture_close(store, executor)
                            self._run_research(store)
                        elif action == "pause-entries":
                            executor.pause_entries()
                        elif action == "reconcile":
                            executor.reconcile()
                        elif action == "cancel-pending-entries":
                            executor.cancel_pending_entries()
                        elif action != "fixture-start":
                            raise ValueError("Comando desconocido")
                store.audit("CONTROL_DONE", details=action)
            except (RuntimeError, ValueError):
                store.audit("CONTROL_BLOCKED", details=action)
                raise
            finally:
                store.close()
            return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self.mutex:
            store = self._store()
            try:
                raw = store.snapshot(self.session_id)
                selection = json.loads(store.get_meta("selection") or "{}")
                run_id = store.get_meta("latest_report")
                report = read_report(run_id, self.config.reports_dir) if run_id else None
                manifest = json.loads(store.get_meta("data_manifest") or "{}")
                paid_costs = sum(
                    (
                        Decimal(row[0])
                        for row in store.connection.execute("SELECT total FROM broker_costs")
                    ),
                    Decimal(0),
                )
            finally:
                store.close()
        now = datetime.now(UTC)
        portfolio = raw["portfolio"]
        positions = [{**p, "entry_price": p["average_entry"]} for p in raw["positions"]]
        candidates = [
            {
                "symbol": c["instrument"]["symbol"],
                "rank": c["rank"],
                "rvol": c["rvol"],
                "orh": c["or_high"],
                "orl": c["or_low"],
                "reason": "Seleccionada",
            }
            for c in selection.get("selection", [])
        ]
        candidates.extend(
            {"symbol": r["symbol"], "reason": r["reason"]} for r in selection.get("rejections", [])
        )
        metrics = report["metrics"] if report else {}
        return {
            "mode": self.config.mode.value,
            "config_hash": self.config.config_hash,
            "budget": str(self.config.risk.allocated_capital),
            "cash": str(
                max(
                    Decimal(0),
                    min(
                        Decimal(portfolio["cash"]) - Decimal(portfolio["reserved_cash"]),
                        self.config.risk.allocated_capital
                        - Decimal(portfolio["gross_exposure"])
                        - Decimal(portfolio["reserved_cash"]),
                    ),
                )
            ),
            "realized_pnl": portfolio["realized_pnl"],
            "unrealized_pnl": portfolio["unrealized_pnl"],
            "exposure": portfolio["gross_exposure"],
            "reserved_cash": portfolio["reserved_cash"],
            "daily_loss_limit": str(
                self.config.risk.allocated_capital * self.config.risk.daily_loss_fraction
            ),
            "costs": str(paid_costs),
            "costs_note": "Comisiones acumuladas del simulador, ya descontadas en PnL",
            "entries_armed": False,
            "external_mutations": "DISABLED",
            "etoro_demo_write": "NOT_TESTED",
            "close_reconciliation": "BLOCKED: contrato externo incompleto",
            "etoro_demo_read": "BLOCKED"
            if os.getenv("ETORO_API_KEY") and os.getenv("ETORO_USER_KEY")
            else "NOT_CONFIGURED",
            "entries_paused": raw["session"]["entries_paused"],
            "broker_status": "NOT_CONFIGURED",
            "readiness": "BLOCKED: Demo sin verificar",
            "data_status": (
                "SYNTHETIC_ONLY"
                if self.config.data.provider == "fixtures" or manifest.get("synthetic")
                else "IMPORT_SCHEMA_VALID"
                if manifest
                else "IMPORT_NOT_CHECKED"
            ),
            "research_status": report["research_status"] if report else "RESEARCH_BLOCKED_DATA",
            "time_new_york": now.astimezone(ZoneInfo("America/New_York")).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            ),
            "time_bogota": now.astimezone(ZoneInfo("America/Bogota")).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            ),
            "session": selection.get("session_date", "Sin fixture ejecutado"),
            "data_freshness": (
                f"{manifest.get('source', 'Sin datos cargados')} · reloj reproducido, "
                "sin cotizaciones actuales"
            ),
            "selection": candidates,
            "orders": raw["orders"],
            "positions": positions,
            "incidents": [f"{e['kind']} · {e['details']}" for e in raw["events"][-15:]],
            "report": report,
            "chart": (
                [{"session": "Inicio", "equity": str(self.config.backtest.starting_capital)}]
                + report["equity"]
            )
            if report
            else [],
            "summary_metrics": {
                "Operaciones backtest": metrics.get("trade_count"),
                "Sesiones": metrics.get("sessions"),
                "Costes backtest USD": f"{metrics['costs_usd']:.2f}" if report else None,
                "Drawdown al cierre": f"{metrics['max_drawdown'] * 100:.3f}%" if report else None,
            },
        }
