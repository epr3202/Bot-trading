"""Pinned A2/A3 offline integration and persistence for reproducible A4 runs."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Context, localcontext
from pathlib import Path
from typing import Any

from intraday_etoro_lab.backtesting.engine import BacktestResult, run_backtest
from intraday_etoro_lab.backtesting.replay import BAR_CLOSE_SEMANTICS, ReplayAsOf
from intraday_etoro_lab.config import AppConfig, load_config
from intraday_etoro_lab.data.massive import MassiveHistoricalProvider
from intraday_etoro_lab.data.providers import DataBundle

A2_SHA256 = "7605880936ef74ff27ded089af134b6a3538b3d051300ff861a091e5d2da0805"
A3_SHA256 = "3268550aa4e110c29673003262787172f9c6ddaf52bea5af96670372d32579e0"
A2_PATH = "docs/massive-a2-manifest.json"
A3_PATH = "docs/strategy-1-a3-audit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def frozen_strategy(root: Path) -> tuple[AppConfig, dict[str, Any]]:
    snapshot_path = root / A3_PATH
    if sha256(snapshot_path) != A3_SHA256:
        raise ValueError("A4_A3_SNAPSHOT_CHANGED")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not snapshot["frozen"] or snapshot["version"] != "ORB_RVOL_v1.0":
        raise ValueError("A4_STRATEGY_NOT_FROZEN")
    config = load_config(root / snapshot["configuration"], mode="backtest")
    if config.order_submission_enabled:
        raise ValueError("A4_EXTERNAL_SUBMISSION_FORBIDDEN")
    effective = {
        key: getattr(config, key).model_dump(mode="json") for key in ("strategy", "risk", "costs")
    }
    if effective != snapshot["effective"] or config.strategy_hash != snapshot["strategy_hash"]:
        raise ValueError("A4_STRATEGY_CONFIGURATION_CHANGED")
    for path, expected in snapshot["source_sha256"].items():
        if sha256(root / path) != expected:
            raise ValueError(f"A4_FROZEN_SOURCE_CHANGED: {path}")
    return config, snapshot


def approved_dataset(root: Path) -> tuple[DataBundle, dict[str, Any]]:
    approved_path = root / A2_PATH
    if sha256(approved_path) != A2_SHA256:
        raise ValueError("A4_A2_APPROVED_REFERENCE_CHANGED")
    approved = json.loads(approved_path.read_text(encoding="utf-8"))
    if approved["status"] != "PASS" or set(approved["datasets"]) != {"AAPL", "SPY", "QQQ"}:
        raise ValueError("A4_A2_NOT_APPROVED")
    bundles = []
    for symbol, expected in sorted(approved["datasets"].items()):
        directory = (root / expected["path"]).resolve()
        if not directory.is_relative_to((root / "data/raw/massive").resolve()):
            raise ValueError("A4_CAPTURE_PATH_OUTSIDE_APPROVED_ROOT")
        if sha256(directory / "capture.json") != expected["capture_sha256"]:
            raise ValueError("A4_CAPTURE_HASH_MISMATCH")
        for page, digest in expected["raw_sha256"].items():
            if sha256(directory / page) != digest:
                raise ValueError("A4_RAW_HASH_MISMATCH")
            rows = json.loads((directory / page).read_text(encoding="utf-8"))["results"]
            # These pinned A2 records have no publication timestamp. Unexpected
            # temporal fields require a reviewed mapping, never silently ignoring them.
            if any(set(row) - {"t", "o", "h", "l", "c", "v", "n", "vw"} for row in rows):
                raise ValueError("A4_RAW_TEMPORAL_SCHEMA_REVIEW_REQUIRED")
        provider = MassiveHistoricalProvider(directory)
        bundle = provider.load()
        if (
            provider.capture["acquisition_class"] != "NETWORK_HTTP"
            or bundle.manifest.synthetic
            or bundle.manifest.source != "massive"
            or bundle.manifest.availability_kind != "historical_download"
            or bundle.manifest.quality
            or bundle.instruments[0].symbol != symbol
            or len(bundle.bars) != expected["bar_count"]
            or str(bundle.evaluation_sessions[0]) != approved["target"]
        ):
            raise ValueError("A4_REAL_MASSIVE_CONTRACT_REQUIRED")
        bundles.append(bundle)
    timestamps = {b.event_time for b in bundles[0].bars}
    if any({b.event_time for b in bundle.bars} != timestamps for bundle in bundles):
        raise ValueError("A4_BENCHMARK_SESSIONS_NOT_ALIGNED")
    bars = tuple(
        sorted(
            (b for bundle in bundles for b in bundle.bars),
            key=lambda b: (b.event_time, b.instrument.symbol),
        )
    )
    combined = replace(
        bundles[0],
        bars=bars,
        instruments=tuple(i for bundle in bundles for i in bundle.instruments),
        manifest=bundles[0].manifest.model_copy(
            update={
                "sha256": A2_SHA256,
                "rows": len(bars),
                "provenance": (
                    "historical_download; approved A2 Massive AAPL/SPY/QQQ immutable captures"
                ),
            }
        ),
    )
    return combined, approved


def code_identity(root: Path) -> dict[str, Any]:
    paths = [root / p for p in ("pyproject.toml", "uv.lock", ".python-version")]
    for directory in ("src", "scripts", "configs", "tests"):
        paths.extend(
            p
            for p in (root / directory).rglob("*")
            if p.is_file() and p.suffix in {".py", ".yaml", ".ps1", ".js", ".mjs", ".html", ".css"}
        )
    hashes = {p.relative_to(root).as_posix(): sha256(p) for p in sorted(paths)}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    return {"commit": commit, "source_tree_sha256": canonical_hash(hashes), "files_sha256": hashes}


def persist_run(root: Path, output: Path) -> Path:
    # No service or broker is started; reuse only the established report writer.
    from intraday_etoro_lab.service import append_experiment, save_report

    if output.exists():
        raise ValueError("A4_OUTPUT_MUST_BE_NEW")
    if platform.python_version() != "3.12.12":
        raise ValueError("A4_PYTHON_3_12_12_REQUIRED")
    started = datetime.now(UTC).isoformat()
    identity = code_identity(root)
    config, snapshot = frozen_strategy(root)
    bundle, approved = approved_dataset(root)
    replay = ReplayAsOf(bundle, bar_close_semantics=BAR_CLOSE_SEMANTICS)
    # A4 arithmetic is local to this run, independent of the caller's Decimal context.
    with localcontext(Context(prec=28)) as context:
        result = run_backtest(
            bundle,
            config.strategy,
            config.backtest,
            config.risk,
            config.costs,
            commit=identity["commit"],
            code_hash=identity["source_tree_sha256"],
            replay=replay,
        )
        decimal_context = str(context)
    if code_identity(root) != identity:
        raise ValueError("A4_CODE_CHANGED_DURING_RUN")
    frozen_strategy(root)
    # Recheck raw and captures without loading or transforming them again.
    for data in approved["datasets"].values():
        directory = root / data["path"]
        if sha256(directory / "capture.json") != data["capture_sha256"] or any(
            sha256(directory / p) != h for p, h in data["raw_sha256"].items()
        ):
            raise ValueError("A4_DATA_CHANGED_DURING_RUN")
    output.mkdir(parents=True, exist_ok=False)
    schedule = output / "availability.jsonl"
    with schedule.open("x", encoding="utf-8", newline="\n") as stream:
        for record in replay.records:
            stream.write(
                json.dumps(
                    {
                        "symbol": record.original.instrument.symbol,
                        "event_time": record.original.event_time.isoformat(),
                        "original_received_at": record.original.received_at.isoformat(),
                        "original_available_at": record.original.available_at.isoformat(),
                        "available_at": record.available_at.isoformat(),
                        "availability_basis": record.availability_basis,
                        "dataset_provenance": "historical_download",
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    metadata = {
        **result.run_metadata,
        "code": identity,
        "strategy": {
            "id": snapshot["strategy_id"],
            "version": snapshot["version"],
            "strategy_hash": snapshot["strategy_hash"],
            "snapshot_sha256": A3_SHA256,
            "configuration": snapshot["configuration"],
            "effective": snapshot["effective"],
        },
        "dataset_reference": {
            "path": A2_PATH,
            "sha256": A2_SHA256,
            "datasets": approved["datasets"],
        },
        "availability_file": {"path": schedule.name, "sha256": sha256(schedule)},
        "backtest_parameters": config.backtest.model_dump(mode="json"),
        "evaluation_sessions": [str(day) for day in bundle.evaluation_sessions],
        "processed_range": {
            "start": bundle.manifest.coverage_start.isoformat(),
            "end": bundle.manifest.coverage_end.isoformat(),
        },
        "tradable_symbols": ["AAPL"],
        "reference_symbols": ["SPY", "QQQ"],
        "python": platform.python_version(),
        "decimal_context": decimal_context,
        "execution": {"started_at": started, "finished_at": datetime.now(UTC).isoformat()},
    }
    result = result.model_copy(update={"run_metadata": metadata})
    target = save_report(result, output)
    append_experiment(
        output / "experiments.jsonl",
        result,
        "A4: frozen Strategy 1; approved A2; replay_as_of_v1; no tuning",
    )
    return target


def compare_runs(first: Path, second: Path, output: Path) -> dict[str, Any]:
    if first.resolve() == second.resolve():
        raise ValueError("A4_TWO_DISTINCT_ARTIFACTS_REQUIRED")
    reports = [
        BacktestResult.model_validate_json(p.read_text(encoding="utf-8")) for p in (first, second)
    ]
    for path, report in zip((first, second), reports, strict=True):
        schedule = report.run_metadata["availability_file"]
        if (
            schedule["path"] != "availability.jsonl"
            or sha256(path.parent / schedule["path"]) != schedule["sha256"]
        ):
            raise ValueError("A4_AVAILABILITY_ARTIFACT_CHANGED")
        if (
            report.research_status != "EXPLORATORY_REPLAY_AS_OF"
            or report.data_manifest["synthetic"]
        ):
            raise ValueError("A4_VALID_REPLAY_REQUIRED")
    functional = []
    for report in reports:
        value = report.model_dump(mode="json")
        del value["run_metadata"]["execution"]
        functional.append(value)
    result = {
        "status": "PASS" if functional[0] == functional[1] else "FAIL",
        "functional_equal": functional[0] == functional[1],
        "trades_equal_in_order": reports[0].trades == reports[1].trades,
        "summary_equal": reports[0].metrics == reports[1].metrics,
        "excluded_fields": [
            "run_metadata.execution.started_at",
            "run_metadata.execution.finished_at",
        ],
        "functional_sha256": [canonical_hash(value) for value in functional],
        "artifacts": [{"path": str(p), "sha256": sha256(p)} for p in (first, second)],
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    return result
