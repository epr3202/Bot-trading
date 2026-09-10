from datetime import date, datetime
from decimal import Decimal

import pytest

from intraday_etoro_lab.backtesting import BacktestConfig, run_backtest
from intraday_etoro_lab.backtesting.experiments import walk_forward_windows
from intraday_etoro_lab.backtesting.metrics import portfolio_metrics, session_block_bootstrap
from intraday_etoro_lab.data import FixtureProvider
from intraday_etoro_lab.risk.engine import CostConfig


@pytest.fixture(scope="module")
def bundle():
    return FixtureProvider().load()


def test_replay_reproducible_has_next_open_fills_stop_close_and_no_trade_session(bundle) -> None:
    result = run_backtest(bundle)
    assert result == run_backtest(bundle)
    assert result.label == "SYNTHETIC — NO EVIDENCE OF PROFITABILITY"
    assert len(result.equity) == 3
    assert result.trades
    assert {trade["exit_reason"] for trade in result.trades} >= {
        "SCHEDULED_CLOSE",
        "STOP_CONSERVATIVE",
    }
    for trade in result.trades:
        assert datetime.fromisoformat(trade["entry_at"]) > datetime.fromisoformat(
            trade["submitted_at"]
        )
    assert not result.decisions[-1].signals
    assert result.metrics["open_positions"] == 0
    assert result.metrics["net_return"] != 0


def test_latency_expiry_and_cost_sensitivity(bundle) -> None:
    base = run_backtest(bundle)
    expired = run_backtest(bundle, backtest_config=BacktestConfig(latency_ms=12000))
    assert not expired.trades
    assert {item["reason"] for item in expired.rejections} == {"SIGNAL_EXPIRED"}
    costly = run_backtest(bundle, costs=CostConfig(fixed_per_side=Decimal("1")))
    assert costly.metrics["costs_usd"] > base.metrics["costs_usd"]
    assert costly.metrics["net_return"] < base.metrics["net_return"]


def test_manual_metrics_and_undefined_values() -> None:
    trades = [
        {"net_pnl": "10", "r_multiple": "1", "costs": "1", "turnover": "200"},
        {"net_pnl": "-5", "r_multiple": "-0.5", "costs": "1", "turnover": "200"},
    ]
    metrics = portfolio_metrics(Decimal(100), [Decimal(110), Decimal(105), Decimal(105)], trades)
    assert metrics["net_return"] == pytest.approx(0.05)
    assert metrics["max_drawdown"] == pytest.approx(5 / 110)
    assert metrics["max_drawdown_duration_sessions"] == 2
    assert metrics["expectancy_usd"] == 2.5
    assert metrics["expectancy_r"] == 0.25
    assert metrics["profit_factor"] == 2
    assert metrics["win_rate"] == 0.5
    assert metrics["turnover"] == 4
    empty = portfolio_metrics(Decimal(100), [Decimal(100)], [])
    assert empty["daily_sharpe"] is None
    assert empty["profit_factor"] is None
    assert empty["expectancy_usd"] is None


def test_session_blocks_and_chronological_walkforward() -> None:
    returns = [0.01, -0.02, 0.03, 0]
    assert session_block_bootstrap(returns) == session_block_bootstrap(returns)
    assert session_block_bootstrap([])["reason"] == "INSUFFICIENT_SESSIONS"
    days = tuple(date(2025, 1, value) for value in range(1, 13))
    windows = walk_forward_windows(days, development=4, validation=2, test=2)
    assert len(windows) == 3
    for window in windows:
        assert max(window["development"]) < min(window["validation"])
        assert max(window["validation"]) < min(window["test"])
