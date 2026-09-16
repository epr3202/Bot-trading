"""Preserve the audited bootstrap contract alongside the approved v1 freeze."""

import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from intraday_etoro_lab.config import load_config
from intraday_etoro_lab.strategies.orb import ORBStrategy, StrategyConfig


def test_existing_configuration_matches_audited_explicit_parameters() -> None:
    audit = json.loads(Path("docs/strategy-1-a3-audit.json").read_text())["historical_audit"]
    raw = yaml.safe_load(Path("configs/offline.yaml").read_text())
    config = load_config("configs/offline.yaml")
    for section in ("strategy", "risk", "costs"):
        model = getattr(config, section)
        assert set(raw[section]) == set(audit["effective"][section])
        assert {key: model.model_dump(mode="json")[key] for key in raw[section]} == audit[
            "effective"
        ][section]
    assert audit["frozen"] is False
    assert audit["status"] == "A3_BLOCKED"
    assert len(audit["blockers"]) == 4


def test_existing_strategy_identity_and_deterministic_loading() -> None:
    first = load_config("configs/offline.yaml")
    second = load_config("configs/offline.yaml")
    assert first == second
    assert first.config_hash == second.config_hash
    strategy = ORBStrategy(first.strategy)
    assert strategy.config.version == "ORB_RVOL_v0.1"
    assert strategy.config.opening_range_minutes == 5
    assert strategy.config.min_rvol == 2
    assert strategy.config.warmup_sessions == 20
    assert strategy.config.entry_window_minutes == 60
    assert strategy.config.version != "ORB_BASE_v0.1"


@pytest.mark.parametrize("field", ["relative_strength_enabled", "regime_enabled", "vwap_enabled"])
def test_undefined_extensions_cannot_be_enabled_by_a_flag(field: str) -> None:
    assert getattr(load_config("configs/offline.yaml").strategy, field) is False
    with pytest.raises(ValidationError):
        StrategyConfig.model_validate({field: True})
