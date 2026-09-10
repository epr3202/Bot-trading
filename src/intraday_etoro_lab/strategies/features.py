"""Research features only; StrategyConfig forbids their activation in v0.1."""

from decimal import Decimal

from intraday_etoro_lab.domain import Bar


def relative_strength(
    stock_open: Decimal, stock_now: Decimal, benchmark_open: Decimal, benchmark_now: Decimal
) -> Decimal:
    if stock_open <= 0 or benchmark_open <= 0:
        raise ValueError("opening prices must be positive")
    return stock_now / stock_open - benchmark_now / benchmark_open


def session_vwap(bars: tuple[Bar, ...], *, volume_verified: bool) -> Decimal:
    if not volume_verified or not bars:
        raise ValueError("verified share volume and complete bars required")
    if len({bar.session_date for bar in bars}) != 1 or not all(bar.final for bar in bars):
        raise ValueError("VWAP must reset each session and use complete bars")
    volume = sum((bar.volume for bar in bars), Decimal(0))
    if volume <= 0:
        raise ValueError("positive volume required")
    return (
        sum(
            (((bar.high + bar.low + bar.close) / Decimal(3)) * bar.volume for bar in bars),
            Decimal(0),
        )
        / volume
    )
