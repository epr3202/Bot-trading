from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from intraday_etoro_lab.data import FixtureProvider
from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.strategies import ORBStrategy


@pytest.fixture(scope="module")
def bundle():
    return FixtureProvider().load()


def test_rvol_uses_twenty_prior_five_minute_volumes(bundle) -> None:
    day = bundle.evaluation_sessions[0]
    result = ORBStrategy().process_session(bundle, day)
    assert [(item.instrument.symbol, item.rvol) for item in result.selection] == [
        ("SIMA", Decimal(3)),
        ("SIMB", Decimal(2)),
    ]
    assert result.selection[0].historical_opening_volume == Decimal(12500)
    assert result.selection[0].opening_volume == Decimal(37500)
    assert result.selection[0].or_high == Decimal("100.7")
    assert result.selection[0].or_low == Decimal("99.8")
    assert [signal.rank for signal in result.signals] == [1, 2]
    assert result.signals[0].available_at == session(day).open + timedelta(
        minutes=6, milliseconds=200
    )
    assert result.signals[0].expires_at - result.signals[0].available_at == timedelta(seconds=10)


def test_later_prices_and_volumes_cannot_change_selection_or_earlier_signal(bundle) -> None:
    day = bundle.evaluation_sessions[0]
    cutoff = session(day).open + timedelta(minutes=10)
    mutated = replace(
        bundle,
        bars=tuple(
            bar.model_copy(update={"volume": Decimal("999999999"), "high": bar.high + 100})
            if bar.event_time > cutoff
            else bar
            for bar in bundle.bars
        ),
    )
    assert ORBStrategy().process_session(bundle, day) == ORBStrategy().process_session(mutated, day)


def test_late_opening_bar_excluded_and_revisions_never_rewrite(bundle) -> None:
    day = bundle.evaluation_sessions[0]
    stamp = session(day).open + timedelta(minutes=4)
    original = next(
        bar for bar in bundle.bars if bar.instrument.symbol == "SIMA" and bar.event_time == stamp
    )
    late = original.model_copy(
        update={"available_at": original.available_at + timedelta(seconds=3)}
    )
    revised = original.model_copy(
        update={
            "revision": 1,
            "volume": Decimal("999999"),
            "available_at": original.available_at + timedelta(hours=1),
        }
    )
    altered = replace(bundle, bars=tuple(late if bar == original else bar for bar in bundle.bars))
    result = ORBStrategy().process_session(altered, day)
    assert "SIMA" not in result.evaluable_symbols
    assert any(item.reason == "OPENING_RANGE_MISSING_OR_LATE" for item in result.rejections)
    baseline = ORBStrategy().process_session(bundle, day)
    assert baseline == ORBStrategy().process_session(
        replace(bundle, bars=(*bundle.bars, revised)), day
    )


def test_zero_or_unknown_volume_never_fallback(bundle) -> None:
    day = bundle.evaluation_sessions[0]
    unknown = replace(
        bundle, manifest=bundle.manifest.model_copy(update={"volume_kind": "unknown"})
    )
    assert not ORBStrategy().process_session(unknown, day).signals
    opening = session(day).open
    bars = tuple(
        bar.model_copy(update={"volume": Decimal(0)})
        if bar.session_date < day
        and bar.event_time < session(bar.session_date).open + timedelta(minutes=5)
        else bar
        for bar in bundle.bars
    )
    result = ORBStrategy().process_session(replace(bundle, bars=bars), day)
    assert not result.selection
    assert all(item.reason == "INVALID_HISTORICAL_OPENING_VOLUME" for item in result.rejections)
    assert opening < result.selection_at


def test_missing_warmup_no_signal_and_one_intent_per_session(bundle) -> None:
    day = bundle.evaluation_sessions[0]
    cut = min(bar.session_date for bar in bundle.bars)
    missing = replace(bundle, bars=tuple(bar for bar in bundle.bars if bar.session_date != cut))
    assert not ORBStrategy().process_session(missing, day).signals
    decision = ORBStrategy().process_session(bundle, day)
    assert len({signal.signal_id for signal in decision.signals}) == len(decision.signals)
    assert not ORBStrategy().process_session(bundle, bundle.evaluation_sessions[-1]).selection
