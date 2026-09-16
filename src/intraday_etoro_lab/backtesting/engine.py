import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import Field

from intraday_etoro_lab.backtesting.metrics import portfolio_metrics, session_block_bootstrap
from intraday_etoro_lab.backtesting.replay import ReplayAsOf
from intraday_etoro_lab.data.calendar import calendar_version, session
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.domain import Bar, Signal
from intraday_etoro_lab.domain.models import FrozenModel
from intraday_etoro_lab.risk.engine import (
    CostConfig,
    EntryRequest,
    RiskConfig,
    RiskDecision,
    RiskEngine,
    RiskPortfolio,
)
from intraday_etoro_lab.strategies.orb import ORBStrategy, SessionDecision, StrategyConfig

ZERO = Decimal(0)
BPS = Decimal(10000)


class BacktestConfig(FrozenModel):
    starting_capital: Decimal = Field(default=Decimal("10000"), gt=0)
    latency_ms: int = Field(default=250, ge=1, le=120000)
    spread_bps: Decimal = Field(default=Decimal("2"), ge=0, le=1000)
    slippage_bps: Decimal = Field(default=Decimal("1"), ge=0, le=1000)
    seed: int = 42
    bootstrap_samples: int = Field(default=200, ge=10, le=10000)
    bootstrap_block_sessions: int = Field(default=2, ge=1, le=20)


class BacktestResult(FrozenModel):
    run_id: str
    mode: str = "backtest"
    label: str
    research_status: str
    data_manifest: dict[str, Any]
    config_hash: str
    calendar_version: str
    execution_model: str = "minute-next-open-v1"
    commit: str = "UNRECORDED_WORKTREE"
    seed: int
    decisions: tuple[SessionDecision, ...]
    signals: tuple[Signal, ...]
    trades: tuple[dict[str, Any], ...]
    equity: tuple[dict[str, Any], ...]
    rejections: tuple[dict[str, Any], ...]
    incidents: tuple[dict[str, Any], ...]
    metrics: dict[str, Any]
    bootstrap: dict[str, Any]
    assumptions: tuple[str, ...]
    run_metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class Pending:
    signal: Signal
    sent_at: datetime
    decision: RiskDecision


@dataclass
class Position:
    pending: Pending
    filled_at: datetime
    entry: Decimal
    entry_fee: Decimal
    mark: Decimal
    friction: Decimal


def run_backtest(
    bundle: DataBundle,
    strategy_config: StrategyConfig | None = None,
    backtest_config: BacktestConfig | None = None,
    risk_policy: RiskConfig | None = None,
    costs: CostConfig | None = None,
    *,
    commit: str = "UNRECORDED_WORKTREE",
    replay: ReplayAsOf | None = None,
    code_hash: str | None = None,
) -> BacktestResult:
    strategy_config = strategy_config or StrategyConfig()
    config = backtest_config or BacktestConfig()
    risk_policy = risk_policy or RiskConfig(allocated_capital=config.starting_capital)
    costs = costs or CostConfig()
    if replay is not None and replay.original is not bundle:
        raise ValueError("REPLAY_DATASET_IDENTITY_MISMATCH")
    if config.starting_capital != risk_policy.allocated_capital:
        raise ValueError("BACKTEST_CAPITAL_MUST_MATCH_RISK_ALLOCATION")
    if not costs.known:
        raise ValueError("RESEARCH_BLOCKED_COSTS_UNKNOWN")
    if not bundle.evaluation_sessions:
        raise ValueError("RESEARCH_BLOCKED_DATA: at least 20 warmups and one evaluation session")
    engine = RiskEngine(risk_policy, costs)
    strategy = ORBStrategy(strategy_config)
    config_payload = [
        model.model_dump(mode="json") for model in (strategy_config, config, risk_policy, costs)
    ]
    config_hash = hashlib.sha256(json.dumps(config_payload, sort_keys=True).encode()).hexdigest()
    identity = f"{bundle.manifest.sha256}|{config_hash}|{calendar_version()}|{commit}"
    if replay is not None:
        identity += "|" + json.dumps(replay.metadata(), sort_keys=True) + "|" + str(code_hash)
    run_id = hashlib.sha256(identity.encode()).hexdigest()[:20]
    decisions = tuple(
        replay.process_session(strategy, day) if replay else strategy.process_session(bundle, day)
        for day in bundle.evaluation_sessions
    )
    signals = tuple(signal for decision in decisions for signal in decision.signals)
    cash = config.starting_capital
    pending: dict[str, Pending] = {}
    positions: dict[str, Position] = {}
    seen_intents: set[str] = set()
    trades: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []
    incidents: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []
    exposure_integral = ZERO
    held_seconds = 0.0
    total_session_seconds = 0.0

    def fee(units: Decimal, price: Decimal) -> Decimal:
        return (
            costs.fixed_per_side
            + max(
                costs.minimum_per_side,
                units * costs.per_unit_per_side + units * price * costs.notional_rate_per_side,
            )
            + costs.quadratic_impact * units * units / 2
        )

    def executable(price: Decimal, direction: int) -> Decimal:
        return (
            price * (1 + direction * (config.spread_bps / 2 + config.slippage_bps) / BPS)
            + direction * costs.slippage_per_unit / 2
        )

    def close(symbol: str, price: Decimal, at: datetime, reason: str) -> None:
        nonlocal cash, held_seconds
        position = positions.pop(symbol)
        units = position.pending.decision.units
        exit_price = executable(price, -1)
        exit_fee = fee(units, exit_price)
        cash += units * exit_price - exit_fee
        net = units * (exit_price - position.entry) - position.entry_fee - exit_fee
        held_seconds += (at - position.filled_at).total_seconds()
        friction = position.friction + units * (price - exit_price)
        trades.append(
            {
                "signal_id": position.pending.signal.signal_id,
                "symbol": symbol,
                "session": str(position.pending.signal.session_date),
                "submitted_at": position.pending.sent_at.isoformat(),
                "entry_at": position.filled_at.isoformat(),
                "exit_at": at.isoformat(),
                "units": str(units),
                "entry_price": str(position.entry),
                "exit_price": str(exit_price),
                "stop_price": str(position.pending.signal.stop_price),
                "exit_reason": reason,
                "net_pnl": str(net),
                "planned_risk": str(position.pending.decision.planned_risk),
                "r_multiple": str(net / position.pending.decision.planned_risk),
                "costs": str(position.entry_fee + exit_fee + friction),
                "fees": str(position.entry_fee + exit_fee),
                "spread_slippage": str(friction),
                "turnover": str(units * (position.entry + exit_price)),
            }
        )

    for day, decision in zip(bundle.evaluation_sessions, decisions, strict=True):
        market = session(day)
        total_session_seconds += (market.close - market.open).total_seconds()
        reference = cash + sum(
            (p.mark * p.pending.decision.units for p in positions.values()), ZERO
        )
        realized_start = sum((Decimal(trade["net_pnl"]) for trade in trades), ZERO)
        events: list[tuple[datetime, int, int, str, Any]] = []
        first_bars: dict[tuple[str, datetime], Bar] = {}
        for bar in sorted(bundle.bars, key=lambda item: (item.available_at, item.revision)):
            if bar.session_date == day and bar.final and bar.revision == 0:
                first_bars.setdefault((bar.instrument.symbol, bar.event_time), bar)
        for bar in first_bars.values():
            events.append((bar.event_time, 1, 0, bar.instrument.symbol, ("open", bar)))
            closed_at = replay.available_at(bar) if replay else bar.end_time
            if not replay or closed_at <= market.close:
                events.append((closed_at, 0, 0, bar.instrument.symbol, ("close", bar)))
        for signal in decision.signals:
            submitted = signal.available_at + timedelta(milliseconds=config.latency_ms)
            events.append((submitted, 2, signal.rank, signal.instrument.symbol, ("signal", signal)))
        events.sort(key=lambda event: event[:4])
        last_event_at = market.open
        for at, _, _rank, symbol, (kind, value) in events:
            seconds = max(0.0, (at - last_event_at).total_seconds())
            exposure_integral += Decimal(str(seconds)) * sum(
                (
                    position.mark * position.pending.decision.units
                    for position in positions.values()
                ),
                ZERO,
            )
            last_event_at = at
            if kind == "signal":
                signal = value
                if signal.signal_id in seen_intents:
                    continue
                seen_intents.add(signal.signal_id)
                ask = executable(signal.reference_price, 1)
                bid = executable(signal.reference_price, -1)
                gross = sum((p.mark * p.pending.decision.units for p in positions.values()), ZERO)
                realized = sum((Decimal(t["net_pnl"]) for t in trades), ZERO) - realized_start
                request = EntryRequest(
                    signal_id=signal.signal_id,
                    session_id=str(day),
                    symbol=symbol,
                    available_at=signal.available_at,
                    expires_at=signal.expires_at,
                    now=at,
                    entry_price=ask,
                    stop_price=signal.stop_price,
                    bid=bid,
                    ask=ask,
                    quote_at=signal.available_at,
                    reference_price=signal.reference_price,
                    entry_window_open=at
                    < market.open + timedelta(minutes=strategy_config.entry_window_minutes),
                )
                portfolio = RiskPortfolio(
                    reference_capital=min(reference, risk_policy.allocated_capital),
                    equity=cash + gross,
                    cash=cash,
                    gross_exposure=gross,
                    reserved_cash=sum(
                        (p.decision.notional + p.decision.estimated_cost for p in pending.values()),
                        ZERO,
                    ),
                    reserved_risk=sum((p.decision.planned_risk for p in pending.values()), ZERO)
                    + sum((p.pending.decision.planned_risk for p in positions.values()), ZERO),
                    potential_positions=len(pending) + len(positions),
                    realized_pnl=realized,
                    unrealized_pnl=sum(
                        (
                            (p.mark - p.entry) * p.pending.decision.units - p.entry_fee
                            for p in positions.values()
                        ),
                        ZERO,
                    ),
                    entries_paused=any(
                        p.pending.signal.session_date != day for p in positions.values()
                    ),
                )
                risk = engine.assess(request, portfolio)
                if not risk.approved:
                    rejects.append({"symbol": symbol, "at": at.isoformat(), "reason": risk.reason})
                else:
                    pending[symbol] = Pending(signal, at, risk)
            elif kind == "open":
                bar = value
                if (
                    symbol in positions
                    and at >= session(positions[symbol].pending.signal.session_date).flatten_at
                ):
                    close(symbol, bar.open, at, "SCHEDULED_CLOSE")
                if symbol in pending and at > pending[symbol].sent_at:
                    order = pending.pop(symbol)
                    if at >= market.open + timedelta(minutes=strategy_config.entry_window_minutes):
                        rejects.append(
                            {
                                "symbol": symbol,
                                "at": at.isoformat(),
                                "reason": "PENDING_ENTRY_WINDOW_CLOSED",
                            }
                        )
                        continue
                    price = executable(bar.open, 1)
                    entry_fee = fee(order.decision.units, price)
                    cash -= order.decision.units * price + entry_fee
                    positions[symbol] = Position(
                        order,
                        at,
                        price,
                        entry_fee,
                        bar.open,
                        order.decision.units * (price - bar.open),
                    )
                    actual_risk, incident = engine.post_fill_risk(
                        order.decision.units,
                        price,
                        order.signal.stop_price,
                        order.decision.planned_risk,
                        protected=True,
                    )
                    if incident:
                        incidents.append(
                            {
                                "symbol": symbol,
                                "at": at.isoformat(),
                                "reason": incident,
                                "risk": str(actual_risk),
                            }
                        )
                        close(symbol, bar.open, at, "POST_FILL_RISK_EXIT")
            elif kind == "close" and symbol in positions:
                bar = value
                position = positions[symbol]
                # At a shared timestamp the prior bar cannot stop a just-opened position.
                if bar.event_time < position.filled_at:
                    continue
                position.mark = bar.close
                if bar.low <= position.pending.signal.stop_price:
                    price = min(bar.open, position.pending.signal.stop_price)
                    close(symbol, price, at, "STOP_CONSERVATIVE")
        for symbol, order in tuple(pending.items()):
            rejects.append(
                {
                    "symbol": symbol,
                    "at": market.close.isoformat(),
                    "reason": "UNFILLED_NO_EXECUTABLE_BAR",
                    "signal_id": order.signal.signal_id,
                }
            )
            del pending[symbol]
        if positions:
            incidents.append(
                {
                    "at": market.close.isoformat(),
                    "reason": "UNRESOLVED_EXPOSURE_NO_EXIT_BAR",
                    "symbols": sorted(positions),
                }
            )
        equity = cash + sum((p.mark * p.pending.decision.units for p in positions.values()), ZERO)
        equity_curve.append(
            {
                "session": str(day),
                "equity": str(equity),
                "cash": str(cash),
                "open_positions": len(positions),
            }
        )
    metrics = portfolio_metrics(
        config.starting_capital, [Decimal(point["equity"]) for point in equity_curve], trades
    )
    metrics["average_gross_exposure_fraction"] = (
        float(exposure_integral / Decimal(str(total_session_seconds)) / config.starting_capital)
        if total_session_seconds
        else None
    )
    metrics["position_time_fraction"] = (
        held_seconds / total_session_seconds if total_session_seconds else None
    )
    metrics["pnl_by_instrument"] = {
        symbol: str(
            sum((Decimal(trade["net_pnl"]) for trade in trades if trade["symbol"] == symbol), ZERO)
        )
        for symbol in sorted({str(trade["symbol"]) for trade in trades})
    }
    metrics["open_positions"] = len(positions)
    metrics["limitations"] = [
        "No point-in-time universe"
        if not bundle.manifest.point_in_time_universe
        else "Universe provenance declared; not independently certified",
        "Minute execution approximates queues, halts and intrabar paths",
    ]
    label = (
        "SYNTHETIC — NO EVIDENCE OF PROFITABILITY"
        if bundle.manifest.synthetic
        else "IMPORTED HISTORICAL — EXPLORATORY, NOT VALIDATED"
    )
    return BacktestResult(
        run_id=run_id,
        label=label,
        research_status=(
            "EXPLORATORY_REPLAY_AS_OF"
            if replay
            else "RESEARCH_BLOCKED_DATA"
            if bundle.manifest.synthetic or bundle.manifest.availability_kind != "observed"
            else "EXPLORATORY"
        ),
        data_manifest=bundle.manifest.model_dump(mode="json"),
        config_hash=config_hash,
        calendar_version=calendar_version(),
        commit=commit,
        seed=config.seed,
        run_metadata=replay.metadata() if replay else {},
        decisions=decisions,
        signals=signals,
        trades=tuple(trades),
        equity=tuple(equity_curve),
        rejections=tuple(rejects),
        incidents=tuple(incidents),
        metrics=metrics,
        bootstrap=session_block_bootstrap(
            metrics["daily_returns"],
            seed=config.seed,
            samples=config.bootstrap_samples,
            block_size=config.bootstrap_block_sessions,
        ),
        assumptions=(
            "Selection uses finalized bars received by open+5m+configured wait",
            "Research quote proxy = last available bar close plus explicit spread/slippage",
            "TTL limits submission; accepted orders fill at first strictly later minute open",
            "Same-bar stop touch assumes stop hit, gaps use worse open; no tick precision",
            "Scheduled closing requests use first available open at/after close minus 5 minutes",
            "Fees and execution friction are distinct; no external flows in this portfolio",
        ),
    )
