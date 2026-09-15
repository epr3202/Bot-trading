"""Fabricated contract data, never evidence of Massive access or market profitability."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pytest

from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.data.importer import import_market_data
from intraday_etoro_lab.data.massive import MassiveHistoricalProvider, event_time
from intraday_etoro_lab.data.massive_audit import audit_capture, independent_metrics
from intraday_etoro_lab.data.massive_http import (
    MassiveCredentials,
    MassiveDataError,
    MassiveHistoricalRequest,
    MassiveHistoryClient,
    parse_time,
    read_document,
    sha256,
)
from intraday_etoro_lab.data.providers import MarketDataProvider
from intraday_etoro_lab.strategies.orb import ORBStrategy

TARGET = date(2025, 11, 28)
NOW = datetime(2025, 11, 29, 18, tzinfo=UTC)
KEY = "fabricated-contract-token"


def rows_for(target: date = TARGET) -> list[dict[str, Any]]:
    rows = []
    for index, day in enumerate(MassiveHistoricalRequest(target).days):
        market = session(day)
        for minute in range(market.minutes):
            rows.append(
                {
                    "t": int((market.open + timedelta(minutes=minute)).timestamp() * 1000),
                    "o": 100,
                    "h": 102,
                    "l": 99,
                    "c": 101,
                    "v": 3000 if index == 20 else 1000 + index * 10,
                    "n": 10,
                    "vw": 100.5,
                }
            )
    return rows


def payload(rows: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    return {
        "status": "OK",
        "ticker": "AAPL",
        "adjusted": True,
        "resultsCount": len(rows),
        "results": rows,
        **extra,
    }


def capture_rows(
    tmp_path: Path,
    rows: list[dict[str, Any]] | None = None,
    *,
    target: date = TARGET,
) -> Path:
    directory = tmp_path / "raw"
    document = payload(rows if rows is not None else rows_for(target))
    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=document)),
        now=lambda: NOW,
    )
    try:
        client.capture(MassiveHistoricalRequest(target), directory)
    finally:
        client.close()
    return directory


def rewrite_capture(directory: Path, **updates: Any) -> None:
    # Tests deliberately forge metadata to exercise validation; never edit production raw.
    doc = read_document(directory / "capture.json")
    doc.update(updates)
    (directory / "capture.json").write_text(json.dumps(doc, default=str), encoding="utf-8")


def test_auth_missing_and_credential_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(MassiveDataError, match="AUTH_MISSING_OR_INVALID") as error:
        MassiveCredentials.from_environment()
    assert error.value.status == "MASSIVE_AUTHENTICATION_FAILED"
    assert KEY not in repr(MassiveCredentials(KEY))
    for value in ("", "a b", "a\nb", "á"):
        monkeypatch.setenv("MASSIVE_API_KEY", value)
        with pytest.raises(MassiveDataError):
            MassiveCredentials.from_environment()


@pytest.mark.parametrize("status", [401, 403, 429, 302, 500])
def test_http_errors_no_retries_or_leaked_bodies(tmp_path: Path, status: int) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(status, text=KEY, headers={"Location": "https://invalid/orders"})

    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        transport=httpx.MockTransport(handler),
        now=lambda: NOW,
    )
    with pytest.raises(MassiveDataError) as error:
        client.capture(MassiveHistoricalRequest(TARGET), tmp_path / "raw")
    client.close()
    expected = (
        "MASSIVE_AUTHENTICATION_FAILED"
        if status in {401, 403}
        else ("MASSIVE_RATE_LIMITED" if status == 429 else "MASSIVE_DATA_INCOMPLETE")
    )
    assert error.value.status == expected
    assert len(calls) == 1
    assert KEY not in str(error.value)
    assert KEY not in (tmp_path / "raw/capture.json").read_text()
    assert not (tmp_path / "raw/page-000.json").exists()


@pytest.mark.parametrize("retry", ["61", "NaN", "-1", "invalid"])
def test_invalid_rate_limit_blocks(tmp_path: Path, retry: str) -> None:
    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        now=lambda: NOW,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(429, headers={"Retry-After": retry})
        ),
    )
    with pytest.raises(MassiveDataError, match="RATE_LIMIT_WAIT_REQUIRED"):
        client.capture(MassiveHistoricalRequest(TARGET), tmp_path / "raw")
    client.close()


def test_bounded_429_retries(tmp_path: Path) -> None:
    clock = [NOW]
    waits = []

    def sleep(seconds: float) -> None:
        waits.append(seconds)
        clock[0] += timedelta(seconds=seconds)

    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        now=lambda: clock[0],
        sleeper=sleep,
        transport=httpx.MockTransport(lambda _: httpx.Response(429, headers={"Retry-After": "2"})),
    )
    with pytest.raises(MassiveDataError, match="RATE_LIMIT_EXHAUSTED"):
        client.capture(MassiveHistoricalRequest(TARGET), tmp_path / "raw")
    assert waits == [2, 2]
    assert len(client.records) == 3
    client.close()


def test_pagination_rate_limit_and_no_external_mutations(tmp_path: Path) -> None:
    request = MassiveHistoricalRequest(TARGET)
    rows = rows_for()
    next_url = request.endpoint + "?cursor=cGFnZTI="
    calls: list[httpx.Request] = []
    clock = [NOW]
    waits = []

    def sleep(seconds: float) -> None:
        waits.append(seconds)
        clock[0] += timedelta(seconds=seconds)

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        assert req.method == "GET" and req.url.host == "api.massive.com"
        assert req.url.path.startswith("/v2/aggs/ticker/AAPL/range/1/minute/")
        assert req.headers["Authorization"] == "Bearer " + KEY
        assert "apiKey" not in req.url.params and not req.content
        if len(calls) == 1:
            return httpx.Response(
                200,
                json=payload(rows[:100], next_url=next_url),
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(NOW.timestamp() + 30),
                },
            )
        return httpx.Response(200, json=payload(rows[100:]))

    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        transport=httpx.MockTransport(handler),
        now=lambda: clock[0],
        sleeper=sleep,
    )
    directory = tmp_path / "raw"
    capture = client.capture(request, directory)
    client.close()
    assert len(capture["pages"]) == 2 and waits == [30]
    provider: MarketDataProvider = MassiveHistoricalProvider(directory)
    assert len(provider.load().bars) == 8010
    assert all(KEY not in p.read_text() for p in directory.iterdir())


@pytest.mark.parametrize(
    "suffix",
    [
        "https://evil.example/orders?cursor=a",
        "http://api.massive.com/anything",
        "https://api.massive.com:443/v2/aggs/ticker/AAPL/range/1/minute/1/2?cursor=a",
        "https://api.massive.com/orders?cursor=a",
        "?apiKey=forbidden",
        "?cursor=a&sort=desc",
        "?cursor=a&cursor=b",
        "?cursor=",
        "?cursor=a#fragment",
        "?limit=10",
        "?cursor=a&adjusted=false",
    ],
)
def test_pagination_allowlist(tmp_path: Path, suffix: str) -> None:
    request = MassiveHistoricalRequest(TARGET)
    url = request.endpoint + suffix if suffix.startswith("?") else suffix
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        return httpx.Response(200, json=payload([], next_url=url))

    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        transport=httpx.MockTransport(handler),
        now=lambda: NOW,
    )
    with pytest.raises(MassiveDataError):
        client.capture(request, tmp_path / "raw")
    assert len(calls) == 1
    client.close()


@pytest.mark.parametrize("mutation", ["duplicate", "missing_open", "gap", "zero_volume"])
def test_quality_blocks_without_filling(tmp_path: Path, mutation: str) -> None:
    rows = rows_for()
    if mutation == "duplicate":
        rows.insert(1, rows[0].copy())
    elif mutation == "missing_open":
        rows.pop(-210)
    elif mutation == "gap":
        rows.pop(200)
    else:
        rows[0]["v"] = 0
    directory = capture_rows(tmp_path, rows)
    report = audit_capture(directory, tmp_path / "audit")
    assert report["status"] == "MASSIVE_DATA_INCOMPLETE"
    assert report["sessions_valid"] == 20
    assert report["metric_comparison"] == "NOT_RUN"
    assert report["data_quality"]["status"] == "BLOCKED"
    if mutation in {"missing_open", "gap"}:
        assert report["bar_count"] == 8009
        assert report["data_quality"]["missing_bars"] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("v", -1),
        ("v", "NaN"),
        ("o", 0),
        ("h", 98),
        ("l", 103),
        ("c", 200),
        ("t", "2025-11-28T09:30:00"),
        ("t", 1764340200001),
        ("v", None),
    ],
)
def test_invalid_ohlcv_and_timestamp_block(tmp_path: Path, field: str, value: Any) -> None:
    rows = rows_for()
    rows[0][field] = value
    directory = capture_rows(tmp_path, rows)
    with pytest.raises(MassiveDataError):
        audit_capture(directory, tmp_path / "audit")
    quality = read_document(tmp_path / "audit/data-quality.json")
    assert quality["counts"] is None and quality["status"] == "BLOCKED"


def test_out_of_order(tmp_path: Path) -> None:
    rows = rows_for()
    rows[1], rows[2] = rows[2], rows[1]
    directory = capture_rows(tmp_path, rows)
    with pytest.raises(MassiveDataError, match="TIMESTAMPS_OUT_OF_ORDER"):
        MassiveHistoricalProvider(directory).load()


def test_timezone_dst_holiday_early_close_and_mapping(tmp_path: Path) -> None:
    directory = capture_rows(tmp_path)
    provider = MassiveHistoricalProvider(directory)
    bundle = provider.load()
    assert len(bundle.bars) == 8010
    coverage = {item["date"]: item for item in provider.audit["sessions"]}
    assert "2025-11-27" not in coverage
    assert coverage["2025-11-28"]["early_close"] is True
    assert coverage["2025-11-28"]["expected_minutes"] == 210
    assert datetime.fromisoformat(coverage["2025-10-31"]["open"]).hour == 13
    assert datetime.fromisoformat(coverage["2025-11-03"]["open"]).hour == 14
    for day in provider.audit["sessions"]:
        local = datetime.fromisoformat(day["open"]).astimezone(ZoneInfo("America/New_York"))
        assert (local.hour, local.minute) == (9, 30)
    bar = bundle.bars[0]
    assert (bar.open, bar.high, bar.low, bar.close, bar.volume) == (
        Decimal(100),
        Decimal(102),
        Decimal(99),
        Decimal(101),
        Decimal(1000),
    )
    assert bar.available_at == bar.received_at == NOW
    assert bundle.manifest.availability_kind == "historical_download"
    assert parse_time("2025-11-28T09:30:00-05:00").hour == 14
    with pytest.raises(MassiveDataError, match="TIMESTAMP_ZONE_REQUIRED"):
        parse_time("2025-11-28T09:30:00")
    for day, utc_hour in [(date(2025, 3, 7), 14), (date(2025, 3, 10), 13)]:
        assert event_time(int(session(day).open.timestamp() * 1000)).hour == utc_hour
    with pytest.raises(ValueError):
        MassiveHistoricalRequest(date(2025, 12, 25))


def test_independent_rvol_engine_match_and_import(tmp_path: Path) -> None:
    directory = capture_rows(tmp_path)
    expected = independent_metrics(directory, MassiveHistoricalRequest(TARGET))
    assert expected == {
        "or_high": Decimal(102),
        "or_low": Decimal(99),
        "opening_volume": Decimal(15000),
        "historical_opening_volume": Decimal(5475),
        "rvol": Decimal(15000) / Decimal(5475),
    }
    report = audit_capture(directory, tmp_path / "audit")
    assert report["metric_comparison"] == "MATCH"
    assert report["reason"] == "CONTRACT_TEST_ONLY_NO_EXTERNAL_VERIFICATION"
    assert report["status"] != "MASSIVE_HISTORICAL_RVOL_VERIFIED"
    bundle = import_market_data(
        tmp_path / "audit/regular-minutes.csv", tmp_path / "audit/import-manifest.json"
    )
    assert len(bundle.bars) == 8010


def test_engine_mismatch_is_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = capture_rows(tmp_path)
    original = ORBStrategy.opening_metrics

    def wrong(*args: Any) -> Any:
        value = original(*args)
        return value.model_copy(update={"rvol": value.rvol + Decimal("0.0000000000001")})

    monkeypatch.setattr(ORBStrategy, "opening_metrics", staticmethod(wrong))
    report = audit_capture(directory, tmp_path / "audit")
    assert report["metric_comparison"] == "MISMATCH"
    assert report["status"] == "MASSIVE_DATA_INCOMPLETE"


def test_no_lookahead_or_operational_signals(tmp_path: Path) -> None:
    directory = capture_rows(tmp_path)
    before = independent_metrics(directory, MassiveHistoricalRequest(TARGET))
    # This metadata alteration exercises a real-data guard with fabricated bars, not real evidence.
    rewrite_capture(directory, acquisition_class="NETWORK_HTTP")
    bundle = MassiveHistoricalProvider(directory).load()
    decision = ORBStrategy().process_session(bundle, TARGET)
    assert not decision.signals and not decision.selection
    assert decision.rejections[0].reason == "OBSERVED_AVAILABILITY_REQUIRED"
    changed = rows_for()
    for row in changed:
        local = event_time(row["t"]).astimezone(ZoneInfo("America/New_York"))
        if local.date() == TARGET and (local.hour, local.minute) >= (9, 35):
            row.update(v=9999999, h=200)
    altered = capture_rows(tmp_path / "future", changed)
    assert independent_metrics(altered, MassiveHistoricalRequest(TARGET)) == before


def test_semantics_missing_cannot_verify(tmp_path: Path) -> None:
    directory = capture_rows(tmp_path)
    rewrite_capture(directory, acquisition_class="NETWORK_HTTP", semantics_version="unknown")
    provider = MassiveHistoricalProvider(directory)
    assert provider.load().manifest.volume_kind == "unknown"
    report = audit_capture(directory, tmp_path / "audit")
    assert report["status"] == "MASSIVE_VOLUME_SEMANTICS_UNVERIFIED"
    assert report["coverage"] is None


def test_historical_success_branch_with_fabricated_data(tmp_path: Path) -> None:
    directory = capture_rows(tmp_path)
    rewrite_capture(directory, acquisition_class="NETWORK_HTTP")
    report = audit_capture(directory, tmp_path / "audit")
    assert report["status"] == "MASSIVE_HISTORICAL_RVOL_VERIFIED"
    assert report["coverage"] == "100_percent_market" and report["plan_observed"] is None
    assert report["writes"] == 0 and report["order_submission_enabled"] is False


@pytest.mark.parametrize(
    "update",
    [
        {"status": "INCOMPLETE"},
        {"timeframe": "1d"},
        {"latency": 0.2},
        {"timezone": "America/Bogota"},
        {"availability_class": "OBSERVED"},
        {"started_at": "2025-12-01T00:00:00+00:00"},
    ],
)
def test_capture_metadata_validation(tmp_path: Path, update: dict[str, Any]) -> None:
    directory = capture_rows(tmp_path)
    rewrite_capture(directory, **update)
    with pytest.raises(MassiveDataError):
        MassiveHistoricalProvider(directory).load()


def test_raw_immutable_checksum_and_incomplete_pagination(tmp_path: Path) -> None:
    directory = capture_rows(tmp_path)
    original = sha256(directory / "page-000.json")
    audit_capture(directory, tmp_path / "audit")
    assert sha256(directory / "page-000.json") == original
    with pytest.raises(FileExistsError):
        capture_rows(tmp_path)
    doc = read_document(directory / "capture.json")
    doc["pages"][0]["sha256"] = "0" * 64
    rewrite_capture(directory, pages=doc["pages"])
    with pytest.raises(MassiveDataError, match="RAW_CHECKSUM_MISMATCH"):
        MassiveHistoricalProvider(directory).load()


def test_today_is_rejected_before_network(tmp_path: Path) -> None:
    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        transport=httpx.MockTransport(lambda _: pytest.fail("network")),
        now=lambda: datetime(2025, 11, 28, 23, tzinfo=UTC),
    )
    with pytest.raises(MassiveDataError, match="PREVIOUS_DATE_HISTORICAL_SESSION_REQUIRED"):
        client.capture(MassiveHistoricalRequest(TARGET), tmp_path / "raw")
    client.close()


def test_reflected_secret_never_persisted(tmp_path: Path) -> None:
    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        now=lambda: NOW,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload([], message=KEY))),
    )
    with pytest.raises(MassiveDataError, match="RESPONSE_CONTAINS_CREDENTIAL"):
        client.capture(MassiveHistoricalRequest(TARGET), tmp_path / "raw")
    client.close()
    assert all(KEY not in p.read_text() for p in (tmp_path / "raw").iterdir())


@pytest.mark.parametrize(
    "change",
    [
        {"ticker": "MSFT"},
        {"adjusted": False},
        {"status": "ERROR"},
        {"status": "NOT_AUTHORIZED"},
        {"resultsCount": 1},
        {"results": "invalid"},
    ],
)
def test_response_identity_and_schema(tmp_path: Path, change: dict[str, Any]) -> None:
    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        now=lambda: NOW,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload([], **change)))
        if "results" not in change
        else httpx.MockTransport(lambda _: httpx.Response(200, json=payload([]) | change)),
    )
    with pytest.raises(MassiveDataError):
        client.capture(MassiveHistoricalRequest(TARGET), tmp_path / "raw")
    client.close()


def test_connectivity_error_redacted(tmp_path: Path) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(KEY)

    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        now=lambda: NOW,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(MassiveDataError, match="CONNECTIVITY_FAILED"):
        client.capture(MassiveHistoricalRequest(TARGET), tmp_path / "raw")
    client.close()
    assert KEY not in (tmp_path / "raw/capture.json").read_text()


def test_incomplete_pagination_reader_and_loop(tmp_path: Path) -> None:
    directory = capture_rows(tmp_path)
    path = directory / "page-000.json"
    document = read_document(path)
    document["next_url"] = MassiveHistoricalRequest(TARGET).endpoint + "?cursor=next"
    path.write_text(json.dumps(document, default=float), encoding="utf-8")
    capture = read_document(directory / "capture.json")
    capture["pages"][0]["sha256"] = sha256(path)
    rewrite_capture(directory, pages=capture["pages"])
    with pytest.raises(MassiveDataError, match="PAGINATION_INCOMPLETE"):
        MassiveHistoricalProvider(directory).load()
    clock = [NOW]

    def sleep(seconds: float) -> None:
        clock[0] += timedelta(seconds=seconds)

    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        now=lambda: clock[0],
        sleeper=sleep,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=json.dumps(document, default=float))
        ),
    )
    with pytest.raises(MassiveDataError, match="PAGINATION_LOOP"):
        client.capture(MassiveHistoricalRequest(TARGET), tmp_path / "loop")
    assert len(client.records) == 2
    client.close()


def test_success_after_429_and_date_retry_header(tmp_path: Path) -> None:
    clock = [NOW]
    calls = []

    def sleep(seconds: float) -> None:
        clock[0] += timedelta(seconds=seconds)

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "Sat, 29 Nov 2025 18:00:01 GMT"})
        return httpx.Response(200, json=payload([]))

    client = MassiveHistoryClient(
        MassiveCredentials(KEY),
        now=lambda: clock[0],
        sleeper=sleep,
        transport=httpx.MockTransport(handler),
    )
    result = client.capture(MassiveHistoricalRequest(TARGET), tmp_path / "raw")
    client.close()
    assert result["status"] == "COMPLETE" and len(calls) == 2
    with pytest.raises(MassiveDataError, match="NO_REGULAR_BARS"):
        MassiveHistoricalProvider(tmp_path / "raw").load()


def test_excludes_extended_hours_and_preserves_fractional_volume(tmp_path: Path) -> None:
    rows = rows_for()
    rows[0]["v"] = 1000.25
    last = rows[-1]
    # Intermediate sessions include after-hours; endpoint range still bounds first/last day.
    day = MassiveHistoricalRequest(TARGET).days[1]
    extra = dict(last, t=int(session(day).close.timestamp() * 1000))
    rows.append(extra)
    rows.sort(key=lambda row: row["t"])
    directory = capture_rows(tmp_path, rows)
    provider = MassiveHistoricalProvider(directory)
    bundle = provider.load()
    assert provider.audit["data_quality"]["outside_regular_session"] == 1
    assert provider.audit["sessions_valid"] == 21
    assert bundle.bars[0].volume == Decimal("1000.25")
    assert audit_capture(directory, tmp_path / "audit")["metric_comparison"] == "MATCH"
