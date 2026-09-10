import hashlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest
from pydantic import ValidationError

from intraday_etoro_lab.data import FixtureProvider
from intraday_etoro_lab.data.importer import audit_bundle, import_market_data
from intraday_etoro_lab.domain.models import DataManifest
from intraday_etoro_lab.strategies.orb import ORBStrategy


@pytest.fixture(scope="module")
def bundle():
    return FixtureProvider().load()


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"synthetic": False}, "SYNTHETIC_VOLUME_LABEL_MISMATCH"),
        ({"license": ""}, "at least 1"),
        ({"provenance": ""}, "at least 1"),
        ({"availability_evidence": ""}, "at least 1"),
        ({"coverage_start": "2026-01-01T00:00:00"}, "TIMEZONE"),
        ({"coverage_end": "2000-01-01T00:00:00Z"}, "COVERAGE"),
        ({"availability_kind": "historical_download"}, "DOWNLOAD_TIME"),
        ({"synthetic": False, "volume_kind": "consolidated_shares"}, "SYNTHETIC_AVAILABILITY"),
    ],
)
def test_manifest_cannot_certify_synthetic_or_impossible_availability(bundle, changes, reason):
    with pytest.raises(ValidationError, match=reason):
        DataManifest.model_validate(bundle.manifest.model_dump() | changes)


@pytest.mark.parametrize("availability", ["unknown", "historical_download"])
def test_real_historical_declaration_is_not_a_live_observation(bundle, availability):
    declared = DataManifest.model_validate(
        bundle.manifest.model_dump()
        | {
            "synthetic": False,
            "volume_kind": "consolidated_shares",
            "availability_kind": availability,
            "acquired_at": datetime.now(UTC),
        }
    )
    sample = replace(bundle, manifest=declared)
    result = ORBStrategy().process_session(sample, bundle.evaluation_sessions[0])
    assert not result.signals
    assert all(r.reason == "OBSERVED_AVAILABILITY_REQUIRED" for r in result.rejections)
    assert audit_bundle(sample)["market_data"] == "BLOCKED"
    assert audit_bundle(sample)["research"] == "NOT_VALIDATED"


def test_import_preserves_identity_and_refuses_backdated_download(tmp_path, bundle):
    bar = bundle.bars[0]
    row = bar.model_dump(mode="json")
    row.update(row.pop("instrument"))
    row.pop("broker_id")
    raw = tmp_path / "bars.csv"
    pd.DataFrame([row]).to_csv(raw, index=False)
    checksum = hashlib.sha256(raw.read_bytes()).hexdigest()
    metadata = bundle.manifest.model_dump() | {
        "sha256": checksum,
        "rows": 1,
        "coverage_start": bar.event_time,
        "coverage_end": bar.end_time,
        "availability_kind": "historical_download",
        "acquired_at": bar.received_at,
    }
    path = tmp_path / "manifest.json"
    path.write_text(DataManifest.model_validate(metadata).model_dump_json(), encoding="utf-8")
    assert import_market_data(raw, path).instruments[0].stable_id == bar.instrument.stable_id
    metadata["acquired_at"] = bar.received_at + timedelta(days=1)
    path.write_text(DataManifest.model_validate(metadata).model_dump_json(), encoding="utf-8")
    with pytest.raises(ValueError, match="AVAILABILITY_BACKDATED"):
        import_market_data(raw, path)
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == checksum


def test_synthetic_quality_not_mistaken_for_market_evidence(bundle):
    audit = audit_bundle(bundle)
    assert audit["availability_delay_seconds"] == {"min": 0.2, "max": 0.2}
    assert audit["sessions"] == 23 and audit["market_data"] == "SYNTHETIC_ONLY"
    assert audit["external_mutations"] == "DISABLED"
    assert "BLOCKED_EXTERNAL_DATA" in audit["blockers"]


def test_reports_cannot_mix_synthetic_and_real_declarations(tmp_path, bundle):
    from intraday_etoro_lab.backtesting.engine import run_backtest
    from intraday_etoro_lab.service import save_report

    report = run_backtest(bundle)
    save_report(report, tmp_path)
    declared_real = report.model_copy(
        update={
            "run_id": "a" * 20,
            "data_manifest": report.data_manifest | {"synthetic": False},
        }
    )
    with pytest.raises(RuntimeError, match="SOURCE_MIXING_BLOCKED"):
        save_report(declared_real, tmp_path)
    assert not (tmp_path / ("a" * 20 + ".json")).exists()
