import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from intraday_etoro_lab.data import FixtureProvider
from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.data.importer import import_market_data, quality_issues
from intraday_etoro_lab.domain import Bar


def test_calendar_dst_holiday_early_close() -> None:
    assert session(date(2025, 3, 7)).open.hour == 14
    assert session(date(2025, 3, 10)).open.hour == 13
    assert session(date(2025, 11, 28)).minutes == 210
    assert session(date(2025, 11, 28)).flatten_at.hour == 17
    assert session(date(2025, 11, 28)).flatten_at.minute == 55
    with pytest.raises(ValueError, match="NOT_TRADING_SESSION"):
        session(date(2025, 12, 25))


@pytest.fixture(scope="module")
def bundle():
    return FixtureProvider().load()


def test_fixture_is_reproducible_and_complete(bundle) -> None:
    assert len(bundle.bars) == 23 * 3 * 390
    assert len(bundle.evaluation_sessions) == 3
    assert bundle.manifest.synthetic
    assert bundle.manifest.sha256 == FixtureProvider().load().manifest.sha256
    assert quality_issues(bundle.bars) == ()


@pytest.mark.parametrize(
    "change",
    [
        {"volume": "-1"},
        {"close": "NaN"},
        {"high": "1"},
        {"event_time": "2025-10-23T13:30:00"},
    ],
)
def test_invalid_bar_rejected(bundle, change) -> None:
    values = bundle.bars[0].model_dump()
    values.update(change)
    with pytest.raises(ValidationError):
        Bar.model_validate(values)


def test_completed_bar_cannot_arrive_before_close(bundle) -> None:
    values = bundle.bars[0].model_dump()
    values["received_at"] = bundle.bars[0].event_time
    with pytest.raises(ValidationError, match="before interval end"):
        Bar.model_validate(values)


def test_gaps_duplicates_late_revisions_marked(bundle) -> None:
    first = bundle.bars[0]
    later = first.model_copy(
        update={"revision": 1, "available_at": first.available_at + timedelta(hours=1)}
    )
    issues = quality_issues((bundle.bars[3], first, first, later))
    assert {"SESSION_GAPS", "DUPLICATE_OR_REVISION", "LATE_REVISION", "OUT_OF_ORDER"} <= set(issues)


@pytest.mark.parametrize("suffix", ["csv", "parquet"])
def test_import_checksum_schema_and_raw_immutability(tmp_path: Path, bundle, suffix: str) -> None:
    bars = bundle.bars[:9]
    rows = []
    for bar in bars:
        record = bar.model_dump(mode="json")
        instrument = record.pop("instrument")
        record.update(
            {key: instrument[key] for key in ("symbol", "exchange", "currency", "asset_class")}
        )
        rows.append(record)
    path = tmp_path / f"bars.{suffix}"
    frame = pd.DataFrame(rows)
    if suffix == "csv":
        frame.to_csv(path, index=False)
    else:
        frame.to_parquet(path, index=False)
    original = path.read_bytes()
    manifest = bundle.manifest.model_copy(
        update={
            "sha256": hashlib.sha256(original).hexdigest(),
            "rows": len(bars),
            "coverage_start": min(bar.event_time for bar in bars),
            "coverage_end": max(bar.end_time for bar in bars),
        }
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(manifest.model_dump_json(), encoding="utf-8")
    imported = import_market_data(path, manifest_path)
    assert len(imported.bars) == 9
    assert "SESSION_GAPS" in imported.manifest.quality
    assert path.read_bytes() == original
    altered = json.loads(manifest_path.read_text())
    altered["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(altered), encoding="utf-8")
    with pytest.raises(ValueError, match="CHECKSUM_MISMATCH"):
        import_market_data(path, manifest_path)
