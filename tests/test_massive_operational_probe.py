"""Diagnostic-only timestamp and evidence tests; no trading imports or live access."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("probe", Path("scripts/probe_massive_operational.py"))
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
STAMP = 1789570800_123456789


@pytest.mark.parametrize(
    "assignment", ["example-test-key", "'example-test-key'", '"example-test-key" # comment']
)
def test_dotenv_key_overrides_inherited_environment(tmp_path, monkeypatch, assignment):
    monkeypatch.setenv("MASSIVE_API_KEY", "inherited-test-key")
    path = tmp_path / ".env"
    path.write_text("MASSIVE_API_KEY=" + assignment + "\n", encoding="utf-8")
    assert probe.dotenv_credential(path) == "example-test-key"


@pytest.mark.parametrize(
    "content",
    [
        "",
        "# MASSIVE_API_KEY=comment",
        "MASSIVE_API_KEY=",
        "MASSIVE_API_KEY=${OTHER_KEY}",
        "MASSIVE_API_KEY=one\nMASSIVE_API_KEY=two",
        'MASSIVE_API_KEY="unterminated',
    ],
)
def test_dotenv_missing_or_invalid_never_falls_back(tmp_path, monkeypatch, content):
    monkeypatch.setenv("MASSIVE_API_KEY", "inherited-test-key")
    path = tmp_path / ".env"
    path.write_text(content, encoding="utf-8")
    assert probe.dotenv_credential(path) == ""
    assert probe.dotenv_credential(tmp_path / "absent.env") == ""


def document():
    return {
        "results": {"T": "AAPL", "p": "100", "P": "100.01", "t": STAMP, "y": STAMP - 1000, "q": 7},
        "status": "OK",
    }


def test_ns_ms_and_timezone():
    assert probe.epoch_ns(STAMP, "ns") == STAMP
    assert probe.epoch_ns(STAMP // 1_000_000, "ms") == STAMP // 1_000_000 * 1_000_000
    assert probe.iso_ns(STAMP) == "2026-09-16T15:00:00.123456789Z"


@pytest.mark.parametrize(
    "value,unit",
    [(True, "ns"), (str(STAMP), "ns"), (STAMP // 1_000_000, "ns"), (STAMP, "ms"), (STAMP, "s")],
)
def test_wrong_units_and_types(value, unit):
    with pytest.raises(ValueError):
        probe.epoch_ns(value, unit)


def test_receive_and_decision_age_distinct():
    row = probe.observation("AAPL", document(), STAMP + 2_000000000, STAMP + 4_000000000, None)
    assert row["sip_age_at_receive"] == 2
    assert row["sip_age_at_decision"] == 4
    assert row["participant_age_at_decision"] == 4.000001


def test_future_not_clamped():
    row = probe.observation("AAPL", document(), STAMP - 1, STAMP, None)
    assert row["future_timestamp"]
    assert row["sip_age_at_receive"] < 0


def test_duplicate_and_out_of_order():
    first = probe.observation("AAPL", document(), STAMP, STAMP, None)
    duplicate = probe.observation(
        "AAPL", document(), STAMP + 9_000000000, STAMP + 9_000000000, first
    )
    assert duplicate["repeated"] and duplicate["sip_age_at_decision"] == 9
    earlier = document()
    earlier["results"]["t"] -= 1
    assert probe.observation("AAPL", earlier, STAMP, STAMP, first)["out_of_order"]


def test_serialization_redacts_and_does_not_retain_extra_fields():
    raw = document()
    raw["secret"] = "sensitive-test-value"
    row = probe.observation("AAPL", raw, STAMP, STAMP, None)
    assert "secret" not in row
    row["note"] = raw["secret"]
    serialized = probe.serialize(row, raw["secret"])
    assert raw["secret"] not in serialized
    assert json.loads(serialized)["note"] == "[REDACTED]"


def test_missing_participant_is_unknown_not_replaced_by_receipt():
    raw = document()
    raw["results"].pop("y")
    row = probe.observation("AAPL", raw, STAMP, STAMP, None)
    assert row["participant_age_at_decision"] is None


def test_errors_are_not_zero_age_successes():
    report = probe.summarize([{"symbol": "AAPL", "http_status": 403, "result_status": "HTTP_403"}])
    assert report["AAPL"]["errors"] == 1
    assert report["AAPL"]["ages"]["sip"]["median"] is None
    assert report["AAPL"]["ages"]["sip"]["percent_le_3s"] is None
