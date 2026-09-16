"""Manufactured contract inputs only; never evidence for the real A4 dataset."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from intraday_etoro_lab.backtesting import a4
from intraday_etoro_lab.backtesting.engine import run_backtest
from intraday_etoro_lab.backtesting.replay import BAR_CLOSE_SEMANTICS, ReplayAsOf
from intraday_etoro_lab.config import load_config
from intraday_etoro_lab.data import FixtureProvider
from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.domain import Instrument
from intraday_etoro_lab.strategies.orb import ORBStrategy


@pytest.fixture(scope="module")
def historical():
    fixture = FixtureProvider().load()
    day = fixture.evaluation_sessions[0]
    receipt = session(day).close + timedelta(days=1)
    stock = fixture.instruments[0]
    benchmarks = tuple(Instrument(symbol=s, asset_class="etf") for s in ("SPY", "QQQ"))
    bars = []
    for bar in fixture.bars:
        if bar.instrument != stock or bar.session_date > day:
            continue
        bar = bar.model_copy(update={"available_at": receipt, "received_at": receipt})
        bars.append(bar)
        for instrument in benchmarks:
            bars.append(
                bar.model_copy(
                    update={
                        "instrument": instrument,
                        "open": Decimal(100),
                        "close": Decimal(100),
                        "high": Decimal(101),
                        "low": Decimal(99),
                    }
                )
            )
    return replace(
        fixture,
        bars=tuple(bars),
        instruments=(stock, *benchmarks),
        evaluation_sessions=(day,),
        manifest=fixture.manifest.model_copy(
            update={
                "synthetic": False,
                "availability_kind": "historical_download",
                "provenance": "CONTRACT_TEST fabricated historical input; not NETWORK_HTTP",
            }
        ),
    )


def boundary(bundle, **kwargs):
    return ReplayAsOf(bundle, bar_close_semantics=BAR_CLOSE_SEMANTICS, **kwargs)


def test_visibility_is_inclusive_and_preserves_original_provenance(historical):
    replay = boundary(historical)
    first = replay.records[0]
    original_receipt = first.original.received_at
    before = replay.view(first.available_at - timedelta(microseconds=1))
    assert before.bars == ()
    visible = replay.view(first.available_at)
    assert len(visible.bars) == 3  # Equal-time batch, including both benchmarks.
    assert all(b.available_at <= first.available_at for b in visible.bars)
    assert visible.manifest.availability_kind == "observed"
    assert visible.manifest.provenance.startswith("historical_download;")
    assert historical.manifest.availability_kind == "historical_download"
    assert replay.records[0].original.received_at == original_receipt > first.available_at
    assert before.bars == ()  # Later reveals cannot mutate an earlier snapshot.
    assert replay.metadata()["dataset_provenance"] == "historical_download"
    with pytest.raises(ValueError, match="CANNOT_REWIND"):
        replay.view(first.available_at - timedelta(seconds=1))


def test_explicit_publication_has_priority_and_is_not_replaced_by_close(historical):
    bar = historical.bars[0]
    late = bar.end_time + timedelta(seconds=9)
    replay = boundary(historical, publication_times={(bar.instrument.symbol, bar.event_time): late})
    assert bar.instrument.symbol not in {
        b.instrument.symbol for b in replay.view(bar.end_time).bars
    }
    assert any(b.instrument == bar.instrument for b in replay.view(late).bars)
    assert (
        replay.metadata()["available_at_semantics"]["basis_counts"][
            "explicit_publication_timestamp"
        ]
        == 1
    )


def test_missing_contract_invalid_publication_and_duplicates_fail_closed(historical):
    with pytest.raises(ValueError, match="CONTRACT_MISSING"):
        ReplayAsOf(historical)
    bar = historical.bars[0]
    for stamp, reason in (
        (bar.event_time, "BEFORE_BAR_CLOSE"),
        (datetime(2025, 1, 1), "TIMEZONE_REQUIRED"),
    ):
        with pytest.raises(ValueError, match=reason):
            boundary(historical, publication_times={(bar.instrument.symbol, bar.event_time): stamp})
    with pytest.raises(ValueError, match="DUPLICATE"):
        boundary(replace(historical, bars=historical.bars + (bar,)))
    with pytest.raises(ValueError, match="TEMPORAL_SEMANTICS_UNSUPPORTED"):
        ReplayAsOf(historical, bar_close_semantics="guess")
    with pytest.raises(ValueError, match="PROVENANCE"):
        boundary(
            replace(historical, manifest=historical.manifest.model_copy(update={"synthetic": True}))
        )


def test_frozen_strategy_only_receives_visible_observed_snapshots(historical, monkeypatch):
    original = ORBStrategy.process_session
    clocks = []
    replay = boundary(historical)
    view = replay.view

    def checked_view(clock):
        result = view(clock)
        clocks.append(clock)
        return result

    def checked_strategy(self, bundle, day):
        assert bundle.manifest.availability_kind == "observed"
        assert bundle.manifest.provenance.startswith("historical_download;")
        assert all(
            b.available_at <= clocks[-1] and b.received_at <= clocks[-1] for b in bundle.bars
        )
        return original(self, bundle, day)

    monkeypatch.setattr(replay, "view", checked_view)
    monkeypatch.setattr(ORBStrategy, "process_session", checked_strategy)
    config = load_config("configs/strategy-1-v1.yaml")
    decision = replay.process_session(
        ORBStrategy(config.strategy), historical.evaluation_sessions[0]
    )
    assert decision.signals
    assert all(s.strategy_version == "ORB_RVOL_v1.0" for s in decision.signals)
    assert len(clocks) >= 2 and clocks == sorted(clocks)


def test_future_perturbation_cannot_change_prefix_or_earlier_decisions(historical):
    day = historical.evaluation_sessions[0]
    cutoff = session(day).open + timedelta(minutes=6)
    changed = replace(
        historical,
        bars=tuple(
            b.model_copy(
                update={"close": b.close * 2, "high": b.high * 3, "volume": b.volume * 100}
            )
            if b.event_time >= cutoff
            else b
            for b in historical.bars
        ),
    )
    assert boundary(historical).view(cutoff) == boundary(changed).view(cutoff)
    strategy = ORBStrategy(load_config("configs/strategy-1-v1.yaml").strategy)
    assert boundary(historical).process_session(strategy, day) == boundary(changed).process_session(
        strategy, day
    )


def test_late_benchmark_cannot_reopen_terminal_rs_rejection(historical):
    day = historical.evaluation_sessions[0]
    candidate_time = session(day).open + timedelta(minutes=5)
    late = candidate_time + timedelta(minutes=1, seconds=1)
    replay = boundary(historical, publication_times={("QQQ", candidate_time): late})
    strategy = ORBStrategy(load_config("configs/strategy-1-v1.yaml").strategy)
    result = replay.process_session(strategy, day)
    assert not result.signals
    assert any(r.reason == "RS_SYNCHRONIZED_DATA_MISSING" for r in result.rejections)


def test_deterministic_order_and_replay_including_nonempty_trades(historical):
    config = load_config("configs/strategy-1-v1.yaml")
    reversed_input = replace(
        historical,
        bars=tuple(reversed(historical.bars)),
        instruments=tuple(reversed(historical.instruments)),
    )

    def run(bundle):
        return run_backtest(
            bundle,
            config.strategy,
            config.backtest,
            config.risk,
            config.costs,
            replay=boundary(bundle),
            commit="unit-test",
            code_hash="unit-test",
        )

    first = run(historical)
    second = run(reversed_input)
    assert first.trades and first.signals
    assert first == second
    assert first.data_manifest["availability_kind"] == "historical_download"
    assert first.research_status == "EXPLORATORY_REPLAY_AS_OF"
    assert not any(
        r.reason == "OBSERVED_AVAILABILITY_REQUIRED" for d in first.decisions for r in d.rejections
    )
    assert run_backtest(historical, config.strategy).research_status == "RESEARCH_BLOCKED_DATA"


def test_explicit_schedule_changes_identity_and_timezone_equivalence(historical):
    replay = boundary(historical)
    assert replay.view(datetime(2020, 1, 1, tzinfo=UTC)).bars == ()
    with pytest.raises(ValueError, match="CLOCK_TIMEZONE"):
        replay.view(datetime(2025, 1, 1))
    bar = historical.bars[0]
    late = boundary(
        historical,
        publication_times={
            (bar.instrument.symbol, bar.event_time): bar.end_time + timedelta(seconds=1)
        },
    )
    assert (
        late.metadata()["availability_schedule_sha256"]
        != replay.metadata()["availability_schedule_sha256"]
    )


def test_a4_rejects_changed_approved_reference_before_loading(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    (tmp_path / a4.A2_PATH).write_text('{"provider":"fixtures"}', encoding="utf-8")
    calls = []
    monkeypatch.setattr(a4, "MassiveHistoricalProvider", lambda path: calls.append(path))
    with pytest.raises(ValueError, match="APPROVED_REFERENCE_CHANGED"):
        a4.approved_dataset(tmp_path)
    assert calls == []


def test_a4_rejects_changed_strategy_sources_and_snapshot(monkeypatch):
    original = a4.sha256
    config, snapshot = a4.frozen_strategy(Path.cwd())
    assert config.strategy.version == "ORB_RVOL_v1.0"
    assert snapshot["effective"]["strategy"] == config.strategy.model_dump(mode="json")
    monkeypatch.setattr(a4, "sha256", lambda p: "0" * 64 if p.name == "orb.py" else original(p))
    with pytest.raises(ValueError, match="FROZEN_SOURCE_CHANGED"):
        a4.frozen_strategy(Path.cwd())
    monkeypatch.setattr(a4, "sha256", lambda p: "0" * 64)
    with pytest.raises(ValueError, match="SNAPSHOT_CHANGED"):
        a4.frozen_strategy(Path.cwd())


def test_a4_persistence_and_exact_comparison_with_mocked_market_input(
    historical, tmp_path, monkeypatch
):
    # Exercise storage with explicitly mocked market input; not A4 acquisition evidence.
    monkeypatch.setattr(a4, "approved_dataset", lambda root: (historical, {"datasets": {}}))
    first_path = a4.persist_run(Path.cwd(), tmp_path / "first")
    second_path = a4.persist_run(Path.cwd(), tmp_path / "second")
    first = json.loads(first_path.read_text(encoding="utf-8"))
    assert first["trades"] and first["metrics"]
    metadata = first["run_metadata"]
    assert metadata["code"]["commit"] and metadata["code"]["source_tree_sha256"]
    assert metadata["strategy"]["version"] == "ORB_RVOL_v1.0"
    assert metadata["dataset_reference"]["sha256"] == a4.A2_SHA256
    assert metadata["availability_policy"] == "replay_as_of_v1"
    assert metadata["dataset_provenance"] == "historical_download"
    assert (first_path.parent / "experiments.jsonl").is_file()
    result = a4.compare_runs(first_path, second_path, tmp_path / "comparison.json")
    assert result["status"] == "PASS" and result["trades_equal_in_order"]
    with pytest.raises(ValueError, match="OUTPUT_MUST_BE_NEW"):
        a4.persist_run(Path.cwd(), tmp_path / "first")
    with pytest.raises(ValueError, match="DISTINCT_ARTIFACTS"):
        a4.compare_runs(first_path, first_path, tmp_path / "same.json")
    second = json.loads(second_path.read_text(encoding="utf-8"))
    second["trades"][0]["entry_price"] = "999"
    # Identical aggregate metrics must not hide a different individual operation.
    second_path.write_text(json.dumps(second), encoding="utf-8")
    changed = a4.compare_runs(first_path, second_path, tmp_path / "changed.json")
    assert changed["status"] == "FAIL" and changed["summary_equal"]
    assert not changed["trades_equal_in_order"]
    (second_path.parent / "availability.jsonl").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="AVAILABILITY_ARTIFACT_CHANGED"):
        a4.compare_runs(first_path, second_path, tmp_path / "corrupt.json")


def test_a4_rejects_wrong_capture_before_any_provider_call(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    approved = Path(a4.A2_PATH).read_bytes()
    (tmp_path / a4.A2_PATH).write_bytes(approved)
    aapl = json.loads(approved)["datasets"]["AAPL"]
    directory = tmp_path / aapl["path"]
    directory.mkdir(parents=True)
    (directory / "capture.json").write_text("{}", encoding="utf-8")
    calls = []
    monkeypatch.setattr(a4, "MassiveHistoricalProvider", lambda path: calls.append(path))
    with pytest.raises(ValueError, match="CAPTURE_HASH_MISMATCH"):
        a4.approved_dataset(tmp_path)
    assert calls == []


def test_publication_after_session_cannot_change_that_sessions_stop_or_pnl(historical):
    config = load_config("configs/strategy-1-v1.yaml")
    day = historical.evaluation_sessions[0]
    market = session(day)
    event = market.open + timedelta(minutes=10)
    times = {("SIMA", event): market.close + timedelta(days=1)}
    changed = replace(
        historical,
        bars=tuple(
            b.model_copy(update={"low": Decimal(1)})
            if b.instrument.symbol == "SIMA" and b.event_time == event
            else b
            for b in historical.bars
        ),
    )

    def run(bundle):
        return run_backtest(
            bundle,
            config.strategy,
            config.backtest,
            config.risk,
            config.costs,
            replay=boundary(bundle, publication_times=times),
        )

    original = run(historical)
    perturbed = run(changed)
    assert original.trades and original.trades == perturbed.trades
    assert original.metrics == perturbed.metrics
    assert all(datetime.fromisoformat(t["exit_at"]) <= market.close for t in original.trades)
