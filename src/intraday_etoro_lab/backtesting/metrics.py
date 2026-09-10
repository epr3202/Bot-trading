import math
import random
from decimal import Decimal
from typing import Any


def portfolio_metrics(
    initial: Decimal,
    daily_equity: list[Decimal],
    trades: list[dict[str, Any]],
) -> dict[str, Any]:
    equity = [initial, *daily_equity]
    returns = [
        float(after / before - 1) for before, after in zip(equity[:-1], equity[1:], strict=True)
    ]
    peak = initial
    maximum_drawdown = Decimal(0)
    duration = max_duration = 0
    for value in daily_equity:
        if value >= peak:
            peak, duration = value, 0
        else:
            duration += 1
            max_duration = max(max_duration, duration)
            maximum_drawdown = max(maximum_drawdown, (peak - value) / peak)
    pnl = [Decimal(str(trade["net_pnl"])) for trade in trades]
    gains = sum((value for value in pnl if value > 0), Decimal(0))
    losses = -sum((value for value in pnl if value < 0), Decimal(0))
    sharpe = None
    if len(returns) > 1:
        mean = sum(returns) / len(returns)
        variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
        if variance > 0:
            sharpe = mean / math.sqrt(variance) * math.sqrt(252)
    return {
        "net_return": float(equity[-1] / initial - 1),
        "max_drawdown": float(maximum_drawdown),
        "max_drawdown_duration_sessions": max_duration,
        "daily_sharpe": sharpe,
        "daily_sharpe_note": "N/A for <2 sessions or zero variance; 252 daily periods/year",
        "trade_count": len(trades),
        "expectancy_usd": float(sum(pnl, Decimal(0)) / len(pnl)) if pnl else None,
        "expectancy_r": sum(float(trade["r_multiple"]) for trade in trades) / len(trades)
        if trades
        else None,
        "profit_factor": float(gains / losses) if losses else ("infinity" if gains else None),
        "profit_factor_note": "Infinity means no observed losses; undefined with no gains/losses",
        "win_rate": len([value for value in pnl if value > 0]) / len(pnl) if pnl else None,
        "costs_usd": float(sum((Decimal(str(trade["costs"])) for trade in trades), Decimal(0))),
        "turnover": float(
            sum((Decimal(str(trade["turnover"])) for trade in trades), Decimal(0)) / initial
        ),
        "sessions": len(daily_equity),
        "daily_returns": returns,
        "drawdown_sampling": "session close; intraday drawdown may be larger",
    }


def session_block_bootstrap(
    daily_returns: list[float],
    *,
    seed: int = 42,
    samples: int = 200,
    block_size: int = 2,
) -> dict[str, Any]:
    if not daily_returns or samples < 1 or block_size < 1:
        return {"lower": None, "median": None, "upper": None, "reason": "INSUFFICIENT_SESSIONS"}
    generator = random.Random(seed)
    outcomes: list[float] = []
    for _ in range(samples):
        draw: list[float] = []
        while len(draw) < len(daily_returns):
            start = generator.randrange(len(daily_returns))
            draw.extend(
                daily_returns[(start + offset) % len(daily_returns)] for offset in range(block_size)
            )
        outcomes.append(math.prod(1 + value for value in draw[: len(daily_returns)]) - 1)
    outcomes.sort()
    return {
        "lower": outcomes[int((samples - 1) * 0.025)],
        "median": outcomes[int((samples - 1) * 0.5)],
        "upper": outcomes[int((samples - 1) * 0.975)],
        "samples": samples,
        "block_sessions": block_size,
        "seed": seed,
        "note": "Descriptive circular session-block bootstrap; no significance claim",
    }
