"""Prespecified, small comparisons; no search over rule combinations."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from intraday_etoro_lab.backtesting.engine import BacktestConfig, BacktestResult, run_backtest
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.risk.engine import CostConfig, RiskConfig
from intraday_etoro_lab.strategies.orb import StrategyConfig


def walk_forward_windows(
    days: tuple[date, ...],
    *,
    development: int,
    validation: int,
    test: int,
) -> tuple[dict[str, tuple[date, ...]], ...]:
    if min(development, validation, test) < 1 or tuple(sorted(set(days))) != days:
        raise ValueError("positive sizes and unique ordered sessions required")
    windows = []
    width = development + validation + test
    for start in range(0, len(days) - width + 1, test):
        windows.append(
            {
                "development": days[start : start + development],
                "validation": days[start + development : start + development + validation],
                "test": days[start + development + validation : start + width],
            }
        )
    return tuple(windows)


def controlled_comparison(
    bundle: DataBundle,
    strategy: StrategyConfig,
    config: BacktestConfig,
    risk: RiskConfig,
    costs: CostConfig,
) -> dict[str, BacktestResult]:
    cost_values = costs.model_dump()
    for key, value in tuple(cost_values.items()):
        if isinstance(value, Decimal):
            cost_values[key] = value * 2
    doubled_costs = CostConfig.model_validate(cost_values)
    return {
        "orb_base": run_backtest(
            bundle, strategy.model_copy(update={"version": "ORB_BASE_v0.1"}), config, risk, costs
        ),
        "orb_rvol": run_backtest(bundle, strategy, config, risk, costs),
        "costs_x2": run_backtest(
            bundle,
            strategy,
            config.model_copy(
                update={
                    "spread_bps": config.spread_bps * 2,
                    "slippage_bps": config.slippage_bps * 2,
                }
            ),
            risk,
            doubled_costs,
        ),
        "latency_2s": run_backtest(
            bundle, strategy, config.model_copy(update={"latency_ms": 2000}), risk, costs
        ),
        "latency_12s_expired": run_backtest(
            bundle, strategy, config.model_copy(update={"latency_ms": 12000}), risk, costs
        ),
    }


def append_experiment(path: Path, result: BacktestResult, hypothesis: str) -> None:
    """Append-only local registry; callers may store under ignored state/reports."""
    import json

    record: dict[str, Any] = {
        "run_id": result.run_id,
        "hypothesis": hypothesis,
        "config_hash": result.config_hash,
        "data_sha256": result.data_manifest["sha256"],
        "commit": result.commit,
        "research_status": result.research_status,
        "label": result.label,
        "metrics": result.metrics,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
