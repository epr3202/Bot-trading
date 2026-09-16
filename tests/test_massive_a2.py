"""Fabricated mathematical/contract checks; never final external A2 evidence."""

import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from test_massive_history import KEY, NOW, TARGET, capture_rows, payload, rewrite_capture, rows_for

from intraday_etoro_lab.data.massive import MassiveHistoricalProvider
from intraday_etoro_lab.data.massive_a2 import validate_a2
from intraday_etoro_lab.data.massive_http import (
    MassiveCredentials,
    MassiveDataError,
    MassiveHistoricalRequest,
    MassiveHistoryClient,
    save_json,
)
from intraday_etoro_lab.strategies.features import session_vwap


@pytest.mark.parametrize("symbol", ["SPY", "QQQ"])
def test_benchmark_identity_and_transport(tmp_path: Path, symbol: str) -> None:
    request = MassiveHistoricalRequest(TARGET, symbol)
    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        now=lambda: NOW,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=payload(rows_for(), ticker=symbol))
        ),
    )
    try:
        client.capture(request, tmp_path / "raw")
    finally:
        client.close()
    bundle = MassiveHistoricalProvider(tmp_path / "raw").load()
    assert bundle.instruments[0].symbol == symbol
    assert bundle.instruments[0].asset_class == "etf"
    assert bundle.manifest.synthetic
    with pytest.raises(MassiveDataError, match="PAGINATION_URL_NOT_ALLOWED"):
        request.validate_url(request.url.replace(symbol, "AAPL"))


def test_symbol_allowlist() -> None:
    with pytest.raises(MassiveDataError, match="SYMBOL_NOT_ALLOWED"):
        MassiveHistoricalRequest(TARGET, "TSLA")


def test_missing_benchmarks_and_contract_capture_cannot_pass(tmp_path: Path) -> None:
    raw = capture_rows(tmp_path)
    report = validate_a2({"AAPL": raw}, TARGET)
    assert report["status"] == "FAIL"
    assert report["errors"]["SPY"] == "DATASET_MISSING"
    assert report["errors"]["AAPL"] == "REAL_MASSIVE_SEMANTICS_REQUIRED"
    save_json(tmp_path / "evidence.json", report)
    assert json.loads((tmp_path / "evidence.json").read_text())["criteria"] == report["criteria"]


@pytest.mark.parametrize("defect", ["short", "field", "alignment"])
def test_invalid_data_blocks_a2(tmp_path: Path, defect: str) -> None:
    rows = rows_for()
    if defect == "short":
        rows = rows[390:]
    elif defect == "field":
        del rows[0]["v"]
    else:
        rows[0]["t"] += 1000
    raw = capture_rows(tmp_path, rows)
    report = validate_a2({"AAPL": raw}, TARGET)
    assert report["status"] == "FAIL"
    assert report["criteria"]["orb"] == "FAIL"
    assert "AAPL" in report["errors"]


def test_existing_vwap_math(tmp_path: Path) -> None:
    bundle = MassiveHistoricalProvider(capture_rows(tmp_path)).load()
    bars = tuple(b for b in bundle.bars if b.session_date == TARGET)
    assert session_vwap(bars, volume_verified=True) == Decimal(302) / 3
    with pytest.raises(ValueError, match="verified"):
        session_vwap(bars, volume_verified=False)


def test_report_arithmetic_and_target_alignment(tmp_path: Path) -> None:
    # Forge provenance only to exercise report branches; this directory is test-only.
    paths = {}
    for symbol in ("AAPL", "SPY", "QQQ"):
        path = tmp_path / symbol
        client = MassiveHistoryClient(
            MassiveCredentials(KEY),
            now=lambda: NOW,
            transport=httpx.MockTransport(
                lambda _, s=symbol: httpx.Response(200, json=payload(rows_for(), ticker=s))
            ),
        )
        try:
            client.capture(MassiveHistoricalRequest(TARGET, symbol), path)
        finally:
            client.close()
        rewrite_capture(path, acquisition_class="NETWORK_HTTP")
        paths[symbol] = path
    result = validate_a2(paths, TARGET)
    assert result["status"] == "FAIL"  # Fabricated liquidity is below the universe minimum.
    assert result["metrics"]["or_high"] == 102
    assert result["metrics"]["or_low"] == 99
    assert result["metrics"]["rvol"] == Decimal(15000) / Decimal(5475)
    assert result["criteria"]["rvol_20"] == "PASS"
    assert result["criteria"]["vwap"] == "PASS"
    assert result["relative_strength"] == {"SPY": Decimal(0), "QQQ": Decimal(0)}
    result = validate_a2({**paths, "SPY": paths["QQQ"]}, TARGET)
    assert result["criteria"]["spy_qqq"] == "FAIL"
    assert result["errors"]["SPY"] == "SYMBOL_OR_TARGET_MISMATCH"
