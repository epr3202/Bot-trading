"""Synthetic audit regressions; these do not represent external market evidence."""

import runpy
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from intraday_etoro_lab.data.calendar import session, sessions

AUDIT = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/audit_etoro_market_data.py")
)
analyze_minutes = AUDIT["analyze_minutes"]
candle_rows = AUDIT["candle_rows"]
stamp = AUDIT["stamp"]


def minute(time, volume=100, high=12, low=9):
    return {
        "instrumentID": 1001,
        "fromDate": time.isoformat(),
        "open": 10,
        "high": high,
        "low": low,
        "close": 11,
        "volume": volume,
    }


def test_partial_window_does_not_become_twenty_sessions_or_final():
    market = session(date(2026, 9, 14))
    rows = [minute(market.open + timedelta(minutes=i)) for i in range(6)]
    rows += [minute(market.open - timedelta(minutes=1), high=1000)]
    report, regular = analyze_minutes(rows, market.open + timedelta(minutes=5, seconds=2))
    assert len(regular) == 5
    assert report["unfinished_regular_minutes"] == 1
    assert report["outside_regular_session"] == 1
    assert report["independent"]["ORH"] == 12
    assert report["independent"]["opening_volume_raw_units"] == 500
    assert report["independent"]["RVOL_arithmetic_only"] is None
    assert report["history"]["complete_prior_sessions"] == 0
    assert report["sessions"][0]["gaps_within_returned_window"] == 0


@pytest.mark.parametrize("defect", ["missing", "duplicate", "revision"])
def test_ambiguous_or_missing_opening_bar_never_produces_range(defect):
    market = session(date(2026, 9, 14))
    rows = [minute(market.open + timedelta(minutes=i)) for i in range(5)]
    if defect == "missing":
        rows.pop(2)
    else:
        rows.append(dict(rows[2], high=20 if defect == "revision" else 12))
    report, _ = analyze_minutes(rows, market.close)
    assert not report["independent"]["opening_complete"]
    assert report["independent"]["ORH"] is None
    assert report["independent"]["RVOL_arithmetic_only"] is None


def test_independent_denominator_excludes_evaluation_and_uses_twenty_windows():
    day = date(2026, 9, 14)
    prior = sessions(day - timedelta(days=60), day - timedelta(days=1))[-20:]
    rows = [minute(session(d).open + timedelta(minutes=i)) for d in prior for i in range(5)]
    rows += [minute(session(day).open + timedelta(minutes=i), volume=300) for i in range(5)]
    report, _ = analyze_minutes(rows, session(day).close)
    assert report["independent"]["historical_mean_raw_units"] == 500
    assert report["independent"]["RVOL_arithmetic_only"] == Decimal(3)
    # Five-minute windows alone still cannot prove full-session liquidity or data semantics.
    assert report["history"]["complete_prior_sessions"] == 0
    assert not report["independent"]["RVOL_strategy_valid"]
    assert not report["volume"]["consolidated_market_volume_verified"]
    rows[0]["volume"] = -1
    with pytest.raises(ValueError, match="INVALID_OHLCV"):
        analyze_minutes(rows, session(day).close)


@pytest.mark.parametrize("field,value", [("volume", "NaN"), ("high", 5), ("low", 15)])
def test_invalid_ohlcv_fails_visibly(field, value):
    market = session(date(2026, 9, 14))
    row = minute(market.open)
    row[field] = value
    with pytest.raises(ValueError):
        analyze_minutes([row], market.close)


def test_timestamp_and_instrument_must_be_explicit():
    with pytest.raises(ValueError, match="ZONE_REQUIRED"):
        stamp("2026-09-14T09:30:00")
    with pytest.raises(ValueError, match="MISMATCH"):
        candle_rows({"interval": "OneDay", "candles": []}, "OneMinute", 1001)


def test_early_close_uses_calendar_not_390_assumption():
    market = session(date(2026, 11, 27))
    rows = [minute(market.open + timedelta(minutes=i)) for i in range(210)]
    report, _ = analyze_minutes(rows, market.close)
    assert report["sessions"][0]["expected_minutes"] == 210
    assert report["sessions"][0]["complete"]
