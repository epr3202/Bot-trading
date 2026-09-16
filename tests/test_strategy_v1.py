"""Frozen hypothesis and causal RS contract, using synthetic unit-test bars only."""

import csv
import hashlib
import json
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from intraday_etoro_lab.config import AppConfig, load_config
from intraday_etoro_lab.data import FixtureProvider
from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.domain import Instrument
from intraday_etoro_lab.service import load_bundle
from intraday_etoro_lab.strategies.orb import ORBStrategy, StrategyConfig

D = Decimal


@pytest.fixture(scope="module")
def base():
    original = FixtureProvider().load()
    return replace(
        original,
        instruments=(original.instruments[0],),
        bars=tuple(b for b in original.bars if b.instrument.symbol == "SIMA"),
    )


def scenario(base, stock="1.2", spy="0.5", qqq="0.8"):
    day = base.evaluation_sessions[0]
    opening = session(day).open
    bars = []
    for bar in base.bars:
        if bar.session_date == day and bar.event_time < opening + timedelta(minutes=5):
            bar = bar.model_copy(
                update={"open": D(100), "close": D("100.05"), "high": D("100.1"), "low": D("99.8")}
            )
        elif bar.event_time == opening + timedelta(minutes=5):
            price = D(100) + D(stock)
            bar = bar.model_copy(
                update={
                    "open": D(100),
                    "close": price,
                    "high": max(price, D(101)),
                    "low": D("99.8"),
                }
            )
        bars.append(bar)
    first = next(b for b in bars if b.event_time == opening)
    current = next(b for b in bars if b.event_time == opening + timedelta(minutes=5))
    instruments = list(base.instruments)
    for symbol, change in (("SPY", spy), ("QQQ", qqq)):
        instrument = Instrument(
            symbol=symbol, asset_class="etf", exchange="ARCX" if symbol == "SPY" else "XNAS"
        )
        instruments.append(instrument)
        for template, close in ((first, D(100)), (current, D(100) + D(change))):
            bars.append(
                template.model_copy(
                    update={
                        "instrument": instrument,
                        "open": D(100),
                        "close": close,
                        "high": max(D(101), close),
                        "low": min(D(99), close),
                    }
                )
            )
    return replace(base, bars=tuple(bars), instruments=tuple(instruments))


def decision(bundle):
    return ORBStrategy(load_config("configs/strategy-1-v1.yaml").strategy).process_session(
        bundle, bundle.evaluation_sessions[0]
    )


def test_frozen_config_snapshot_and_sources():
    snapshot = json.loads(Path("docs/strategy-1-a3-audit.json").read_text())
    config = load_config("configs/strategy-1-v1.yaml")
    raw = yaml.safe_load(Path("configs/strategy-1-v1.yaml").read_text())
    assert snapshot["frozen"] is True
    assert snapshot["version"] == config.strategy.version == "ORB_RVOL_v1.0"
    assert snapshot["strategy_hash"] == config.strategy_hash
    for section in ("strategy", "risk", "costs"):
        actual = getattr(config, section)
        assert set(raw[section]) == set(type(actual).model_fields)
        assert actual.model_dump(mode="json") == snapshot["effective"][section]
    for path, expected in snapshot["source_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
    assert config == load_config("configs/strategy-1-v1.yaml")
    assert config.strategy_hash != load_config("configs/offline.yaml").strategy_hash
    assert config.strategy.opening_range_minutes == 5
    assert config.strategy.min_rvol == 2
    assert config.strategy.warmup_sessions == 20
    assert config.strategy.entry_window_minutes == 60
    assert config.strategy.rs_benchmarks == ("SPY", "QQQ")
    assert config.strategy.rs_margin == 0
    assert not config.strategy.regime_enabled and not config.strategy.vwap_enabled
    assert not config.strategy.etf_tradable and config.strategy.benchmarks_reference_only


@pytest.mark.parametrize(
    "section,key,value",
    [
        ("strategy", "min_rvol", "2.1"),
        ("strategy", "entry_window_minutes", 59),
        ("strategy", "relative_strength_enabled", False),
        ("strategy", "rs_margin", "0.001"),
        ("strategy", "rs_benchmarks", ["SPY"]),
        ("strategy", "etf_tradable", True),
        ("strategy", "regime_enabled", True),
        ("strategy", "vwap_enabled", True),
        ("risk", "risk_fraction", "0.0005"),
        ("risk", "max_positions", 1),
        ("risk", "max_position_fraction", "0.5"),
        ("costs", "slippage_per_unit", "0.03"),
    ],
)
def test_v1_rejects_parameter_drift(section, key, value):
    raw = load_config("configs/strategy-1-v1.yaml").model_dump()
    raw[section][key] = value
    with pytest.raises(ValidationError):
        AppConfig.model_validate(raw)


def test_strategy_boundary_revalidates_copied_config():
    config = load_config("configs/strategy-1-v1.yaml").strategy
    with pytest.raises(ValidationError):
        ORBStrategy(config.model_copy(update={"min_rvol": D(1)}))
    with pytest.raises(ValidationError):
        StrategyConfig(relative_strength_enabled=True)


@pytest.mark.parametrize(
    "stock,spy,qqq,passes",
    [
        ("1.2", "0.5", "0.8", True),
        ("0.4", "0.5", "0.3", False),
        ("0.7", "0.4", "0.8", False),
        ("0.5", "0.5", "0.3", False),
        ("0.8", "0.3", "0.8", False),
        ("0.8000001", "0.8", "0.8", True),
    ],
)
def test_strict_long_rs(base, stock, spy, qqq, passes):
    result = decision(scenario(base, stock, spy, qqq))
    assert bool(result.signals) == passes
    assert result.selection[0].rvol == 3
    if not passes:
        assert any(r.reason == "RS_NOT_STRONGER_THAN_BOTH" for r in result.rejections)


@pytest.mark.parametrize("symbol", ["SPY", "QQQ"])
@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "opening",
        "future",
        "stale",
        "late",
        "unfinished",
        "revision",
        "zero_volume",
        "identity",
    ],
)
def test_benchmark_invalid_fails_closed(base, symbol, defect):
    bundle = scenario(base)
    opening = session(bundle.evaluation_sessions[0]).open
    changed = []
    for bar in bundle.bars:
        if bar.instrument.symbol == symbol:
            if defect == "missing" or (defect == "opening" and bar.event_time == opening):
                continue
            if bar.event_time != opening:
                updates = {
                    "future": {
                        "event_time": bar.event_time + timedelta(minutes=1),
                        "received_at": bar.received_at + timedelta(minutes=1),
                        "available_at": bar.available_at + timedelta(minutes=1),
                    },
                    "stale": {"event_time": bar.event_time - timedelta(minutes=1)},
                    "late": {"available_at": bar.available_at + timedelta(microseconds=1)},
                    "unfinished": {"final": False},
                    "revision": {"revision": 1},
                    "zero_volume": {"volume": D(0)},
                    "identity": {
                        "instrument": bar.instrument.model_copy(update={"currency": "EUR"})
                    },
                }
                if defect in updates:
                    bar = bar.model_copy(update=updates[defect])
        changed.append(bar)
    result = decision(replace(bundle, bars=tuple(changed)))
    assert not result.signals
    assert any(r.reason.startswith("RS_") for r in result.rejections)


def test_regular_open_and_no_future_rewrite(base):
    bundle = scenario(base)
    original = decision(bundle)
    opening = session(bundle.evaluation_sessions[0]).open
    benchmark_open = next(
        b for b in bundle.bars if b.instrument.symbol == "SPY" and b.event_time == opening
    )
    premarket = benchmark_open.model_copy(
        update={"event_time": opening - timedelta(minutes=1), "open": D(1)}
    )
    future = benchmark_open.model_copy(
        update={
            "event_time": opening + timedelta(minutes=10),
            "received_at": opening + timedelta(minutes=11),
            "available_at": opening + timedelta(minutes=11),
            "close": D(999),
        }
    )
    assert decision(replace(bundle, bars=(*bundle.bars, premarket, future))) == original
    missing_open = tuple(b for b in bundle.bars if b != benchmark_open)
    assert not decision(replace(bundle, bars=(*missing_open, premarket))).signals
    assert original.signals[0].available_at == opening + timedelta(minutes=6, milliseconds=200)


def test_references_and_generic_etf_never_rank_or_emit_intents(base):
    bundle = scenario(base)
    generic = Instrument(symbol="FUND", asset_class="etf")
    etf_bars = tuple(
        b.model_copy(update={"instrument": generic, "volume": b.volume * 100}) for b in base.bars
    )
    result = decision(
        replace(bundle, instruments=(*bundle.instruments, generic), bars=(*bundle.bars, *etf_bars))
    )
    assert result.evaluable_symbols == ("SIMA",)
    assert [c.instrument.symbol for c in result.selection] == ["SIMA"]
    assert [s.instrument.symbol for s in result.signals] == ["SIMA"]
    assert result.selection[0].rank == 1
    assert {r.symbol for r in result.rejections if r.reason == "UNIVERSE_INELIGIBLE"} == {
        "SPY",
        "QQQ",
        "FUND",
    }
    # No signal/intent reaches downstream sizing/reservations for any reference.
    assert not ({s.instrument.symbol for s in result.signals} & {"SPY", "QQQ", "FUND"})


def test_existing_import_loader_preserves_reference_only_data(base, tmp_path):
    bundle = scenario(base)
    csv_path = tmp_path / "bars.csv"
    fields = [
        "symbol",
        "exchange",
        "currency",
        "asset_class",
        "event_time",
        "received_at",
        "available_at",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "source",
        "final",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for bar in bundle.bars:
            writer.writerow(
                {
                    **{k: getattr(bar.instrument, k) for k in fields[:4]},
                    **{k: getattr(bar, k) for k in fields[4:]},
                }
            )
    manifest = bundle.manifest.model_copy(
        update={
            "sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            "rows": len(bundle.bars),
        }
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(manifest.model_dump_json())
    raw = load_config("configs/strategy-1-v1.yaml").model_dump()
    raw["data"] = {"provider": "import", "path": csv_path, "manifest": manifest_path}
    config = AppConfig.model_validate(raw)
    loaded = load_bundle(config)
    assert {i.symbol for i in loaded.instruments} == {"SIMA", "SPY", "QQQ"}
    assert [s.model_dump(exclude={"instrument"}) for s in decision(loaded).signals] == [
        s.model_dump(exclude={"instrument"}) for s in decision(bundle).signals
    ]
    assert config.strategy_hash == load_config("configs/strategy-1-v1.yaml").strategy_hash


def test_real_historical_availability_guard_is_preserved(base):
    bundle = scenario(base)
    historical = bundle.manifest.model_copy(
        update={"synthetic": False, "availability_kind": "historical_download"}
    )
    result = decision(replace(bundle, manifest=historical))
    assert not result.signals and not result.selection
    assert any(r.reason == "OBSERVED_AVAILABILITY_REQUIRED" for r in result.rejections)
