from __future__ import annotations

import hashlib
import json
import os
from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from intraday_etoro_lab.backtesting.engine import BacktestConfig
from intraday_etoro_lab.risk import CostConfig, RiskConfig
from intraday_etoro_lab.strategies.orb import StrategyConfig

V1_RISK_VALUES = {
    "allocated_capital": "10000",
    "risk_fraction": "0.001",
    "daily_loss_fraction": "0.005",
    "max_positions": 2,
    "max_gross_fraction": "1",
    "max_position_fraction": "0.60",
    "max_spread_fraction": "0.003",
    "max_price_deviation": "0.005",
    "max_source_divergence": "0.005",
    "max_quote_age_seconds": 3,
    "signal_ttl_seconds": 10,
}
V1_COST_VALUES = {
    "known": True,
    "fixed_per_side": "0",
    "minimum_per_side": "0",
    "per_unit_per_side": "0.005",
    "notional_rate_per_side": "0",
    "slippage_per_unit": "0.02",
    "quadratic_impact": "0",
}


class Mode(StrEnum):
    OFFLINE = "offline"
    BACKTEST = "backtest"
    SHADOW = "shadow"
    ETORO_DEMO = "etoro_demo"


class DataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    provider: Literal["fixtures", "import", "massive"] = "fixtures"
    path: Path | None = None
    manifest: Path | None = None

    @model_validator(mode="after")
    def validate_provider_paths(self) -> Self:
        if self.provider == "import" and (self.path is None or self.manifest is None):
            raise ValueError("Importación requiere path y manifest explícitos")
        if self.provider == "massive":
            if self.path is None:
                raise ValueError("Massive requiere path explícito al directorio de captura")
            if not self.path.is_dir():
                raise ValueError("Massive requiere un directorio de captura existente")
            if self.manifest is not None:
                raise ValueError("Massive usa capture.json dentro de path, no manifest externo")
        return self


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mode: Mode = Mode.OFFLINE
    order_submission_enabled: bool = Field(default=False, strict=True)
    runtime_dir: Path = Path("runtime")
    reports_dir: Path = Path("reports/runs")
    arm_ttl_seconds: int = Field(default=300, gt=0, le=900)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    costs: CostConfig = Field(default_factory=CostConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    data: DataConfig = Field(default_factory=DataConfig)

    @model_validator(mode="after")
    def safe_modes(self) -> Self:
        if self.strategy.version == "ORB_RVOL_v1.0":
            if self.risk != RiskConfig.model_validate(V1_RISK_VALUES):
                raise ValueError("STRATEGY_V1_FROZEN_RISK")
            if self.costs != CostConfig.model_validate(V1_COST_VALUES):
                raise ValueError("STRATEGY_V1_FROZEN_COSTS")
        if self.order_submission_enabled and self.mode != Mode.ETORO_DEMO:
            raise ValueError("ORDER_SUBMISSION_ENABLED solo es válido en etoro_demo")
        if self.risk.allocated_capital != self.backtest.starting_capital:
            raise ValueError("El capital de backtest debe coincidir con el presupuesto de riesgo")
        if self.risk.signal_ttl_seconds != self.strategy.signal_ttl_seconds:
            raise ValueError("La caducidad de señal debe coincidir entre estrategia y riesgo")
        return self

    @property
    def config_hash(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def strategy_hash(self) -> str:
        """Strategy, risk and sizing costs only; excludes future replay parameters."""
        payload = {
            key: getattr(self, key).model_dump(mode="json") for key in ("strategy", "risk", "costs")
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def load_config(path: Path | str | None = None, mode: str | None = None) -> AppConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) if path else {}
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("La configuración YAML debe ser un mapa")
    env_mode = os.environ.get("BOT_MODE")
    if env_mode is not None:
        # Reject invalid environment even if a valid CLI override was supplied.
        raw["mode"] = Mode(env_mode)
    if mode is not None:
        raw["mode"] = Mode(mode)
    enabled = os.environ.get("ORDER_SUBMISSION_ENABLED")
    if enabled is not None:
        if enabled not in {"true", "false"}:
            raise ValueError("ORDER_SUBMISSION_ENABLED debe ser exactamente true o false")
        raw["order_submission_enabled"] = enabled == "true"
    return AppConfig.model_validate(raw)
