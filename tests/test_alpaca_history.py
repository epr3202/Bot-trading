"""Contract tests with fabricated bars; no test is evidence of Alpaca access."""

import json
import runpy
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from intraday_etoro_lab.data.alpaca import AlpacaHistoricalProvider
from intraday_etoro_lab.data.alpaca_audit import audit_capture
from intraday_etoro_lab.data.alpaca_http import (
    AlpacaCredentials,
    AlpacaDataError,
    AlpacaHistoryClient,
    HistoricalRequest,
    sha256,
)
from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.data.importer import import_market_data
from intraday_etoro_lab.strategies.orb import ORBStrategy

NOW = datetime(2026, 9, 14, 18, tzinfo=UTC)
REQUEST = HistoricalRequest(date(2026, 9, 11))


def row(time, volume=1000):
    return {
        "t": time.isoformat(),
        "o": 100,
        "h": 102,
        "l": 99,
        "c": 101,
        "v": volume,
        "n": 25,
        "vw": 100.75,
    }


def response(rows, token=None, **extra):
    return httpx.Response(200, json={"bars": {"AAPL": rows}, "next_page_token": token, **extra})


def capture(tmp_path, handler, request=REQUEST, **kwargs):
    client = AlpacaHistoryClient(
        AlpacaCredentials("test-alpaca-id", "test-alpaca-secret"),
        transport=httpx.MockTransport(handler),
        now=lambda: NOW,
        **kwargs,
    )
    try:
        client.capture(request, tmp_path / "raw")
    finally:
        client.close()
    return tmp_path / "raw"


def rewrite_manifest(raw, modify):
    path = raw / "capture.json"
    payload = json.loads(path.read_text())
    modify(payload)
    path.write_text(json.dumps(payload))


def test_mapping_feed_timestamp_counts_and_no_etoro_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("ETORO_API_KEY", "not-for-alpaca")
    monkeypatch.setenv("ETORO_USER_KEY", "not-for-alpaca")
    monkeypatch.setenv("HTTPS_PROXY", "http://unreachable.invalid")
    calls = []
    bar = row(session(REQUEST.target).open)

    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        assert request.url.host == "data.alpaca.markets"
        assert request.url.path == "/v2/stocks/bars"
        assert request.url.params["feed"] == "sip"
        assert request.url.params["timeframe"] == "1Min"
        assert request.url.params["adjustment"] == "split"
        assert request.headers["APCA-API-KEY-ID"] == "test-alpaca-id"
        assert "x-api-key" not in request.headers and "x-user-key" not in request.headers
        return response([bar], feed="sip")

    raw = capture(tmp_path, handler)
    provider = AlpacaHistoricalProvider(raw)
    bundle = provider.load()
    assert len(calls) == 1
    assert bundle.bars[0].event_time == session(REQUEST.target).open
    assert bundle.bars[0].received_at == NOW == bundle.bars[0].available_at
    assert bundle.bars[0].volume == 1000
    assert bundle.bars[0].high == 102 and bundle.bars[0].low == 99
    assert bundle.manifest.availability_kind == "historical_download"
    assert bundle.manifest.feed_id == "alpaca:sip:1Min:split"
    assert provider.audit["trade_count_present"] == provider.audit["vwap_present"] == 1
    assert bundle.manifest.synthetic  # Mock acquisition must never pass as real evidence.


def test_pagination_uses_every_token_even_short_page_and_deduplicates(tmp_path):
    first = row(session(REQUEST.target).open)
    second = row(session(REQUEST.target).open + timedelta(minutes=1))
    queries = []

    def handler(request):
        queries.append(dict(request.url.params))
        return response([first], "token-a") if len(queries) == 1 else response([first, second])

    raw = capture(tmp_path, handler)
    provider = AlpacaHistoricalProvider(raw)
    bundle = provider.load()
    assert len(queries) == 2 and queries[1]["page_token"] == "token-a"
    assert {q["feed"] for q in queries} == {"sip"}
    assert len(bundle.bars) == 2 and provider.audit["exact_duplicates_removed"] == 1


@pytest.mark.parametrize("case", ["echo", "page", "manifest"])
def test_feed_identity_mismatch_never_becomes_sip(case, tmp_path):
    if case == "echo":
        with pytest.raises(AlpacaDataError, match="FEED_IDENTITY_MISMATCH"):
            capture(tmp_path, lambda _: response([], feed="iex"))
        return
    raw = capture(tmp_path, lambda _: response([row(session(REQUEST.target).open)]))

    def modify(doc):
        if case == "page":
            doc["pages"][0]["params"]["feed"] = "iex"
        else:
            doc["feed_effective"] = "iex"

    rewrite_manifest(raw, modify)
    with pytest.raises(AlpacaDataError, match="FEED"):
        AlpacaHistoricalProvider(raw).load()


@pytest.mark.parametrize(
    "case", ["conflict", "naive", "unaligned", "negative", "ohlc", "count", "vwap", "missing"]
)
def test_invalid_or_incomplete_bars_are_blocked(case, tmp_path):
    bar = row(session(REQUEST.target).open)
    rows = [bar]
    if case == "conflict":
        rows.append(dict(bar, v=2000))
    elif case == "naive":
        bar["t"] = "2026-09-11T13:30:00"
    elif case == "unaligned":
        bar["t"] = "2026-09-11T13:30:01Z"
    elif case == "negative":
        bar["v"] = -1
    elif case == "ohlc":
        bar["h"] = 1
    elif case == "count":
        bar["n"] = -1
    elif case == "vwap":
        bar["vw"] = "NaN"
    elif case == "missing":
        del bar["v"]
    raw = capture(tmp_path, lambda _: response(rows))
    with pytest.raises(AlpacaDataError):
        AlpacaHistoricalProvider(raw).load()


def test_missing_bars_not_filled_or_attributed_to_halt(tmp_path):
    raw = capture(tmp_path, lambda _: response([row(session(REQUEST.target).open)]))
    provider = AlpacaHistoricalProvider(raw)
    provider.load()
    audit = provider.audit["sessions"][-1]
    assert audit["missing_count"] == 389
    assert audit["gap_cause"] == "UNKNOWN_NO_HALT_EVIDENCE"
    assert not audit["early_close"] and not audit["complete"]


def test_early_close_and_dst_from_system_calendar(tmp_path):
    request = HistoricalRequest(date(2025, 11, 28))
    market = session(request.target)
    rows = [row(market.open + timedelta(minutes=i)) for i in range(210)]
    raw = capture(tmp_path, lambda _: response(rows), request)
    provider = AlpacaHistoricalProvider(raw)
    provider.load()
    audit = provider.audit["sessions"][-1]
    assert audit["expected_minutes"] == 210 and audit["complete"] and audit["early_close"]
    assert market.open.hour == 14
    assert session(date(2025, 3, 7)).open.hour == 14
    assert session(date(2025, 3, 10)).open.hour == 13


@pytest.mark.parametrize(
    "status,body,reason",
    [
        (401, {"message": "private-upstream"}, "AUTHENTICATION_FAILED"),
        (403, {"message": "private-upstream"}, "ALPACA_HTTP_403"),
        (
            403,
            {"message": "subscription does not permit querying recent SIP data"},
            "SIP_ENTITLEMENT_REQUIRED",
        ),
        (
            422,
            {"message": "subscription does not permit querying recent SIP data"},
            "SIP_ENTITLEMENT_REQUIRED",
        ),
        (302, {}, "ALPACA_HTTP_302"),
        (500, {"message": "private-upstream"}, "ALPACA_HTTP_500"),
    ],
)
def test_http_errors_redacted_no_auth_retry_or_fallback(status, body, reason, tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json=body, headers={"Location": "https://other.invalid"})

    with pytest.raises(AlpacaDataError, match=reason) as error:
        capture(tmp_path, handler)
    assert len(calls) == 1 and "private-upstream" not in str(error.value)
    saved = (tmp_path / "raw/capture.json").read_text()
    assert "private-upstream" not in saved and "test-alpaca-secret" not in saved


@pytest.mark.parametrize(
    "header", [{"Retry-After": "2"}, {"X-RateLimit-Reset": str(int(NOW.timestamp()) + 2)}]
)
def test_429_respects_wait_before_same_feed_retry(header, tmp_path):
    clock = [NOW]
    calls, sleeps = [], []

    def sleep(delay):
        sleeps.append(delay)
        clock[0] += timedelta(seconds=delay)

    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers=header) if len(calls) == 1 else response([])

    client = AlpacaHistoryClient(
        AlpacaCredentials("placeholder", "placeholder"),
        transport=httpx.MockTransport(handler),
        now=lambda: clock[0],
        sleeper=sleep,
    )
    try:
        client.capture(REQUEST, tmp_path / "raw")
    finally:
        client.close()
    assert sleeps == [2] and len(calls) == 2
    assert calls[0].url == calls[1].url


@pytest.mark.parametrize("case", ["loop", "missing_token", "nonterminal"])
def test_pagination_cannot_silently_truncate(case, tmp_path):
    if case == "loop":
        with pytest.raises(AlpacaDataError, match="PAGINATION_LOOP"):
            capture(tmp_path, lambda _: response([], "same"))
        return
    if case == "missing_token":
        with pytest.raises(AlpacaDataError, match="PAGINATION_STATE_MISSING"):
            capture(tmp_path, lambda _: httpx.Response(200, json={"bars": {"AAPL": []}}))
        return
    raw = capture(tmp_path, lambda _: response([row(session(REQUEST.target).open)]))
    path = raw / "page-000.json"
    data = json.loads(path.read_text())
    data["next_page_token"] = "missing-page"
    path.write_text(json.dumps(data))
    rewrite_manifest(raw, lambda d: d["pages"][0].update(sha256=sha256(path)))
    with pytest.raises(AlpacaDataError, match="PAGINATION_INCOMPLETE"):
        AlpacaHistoricalProvider(raw).load()


def test_raw_hash_and_existing_output_are_protected(tmp_path):
    raw = capture(tmp_path, lambda _: response([row(session(REQUEST.target).open)]))
    with pytest.raises(FileExistsError):
        capture(tmp_path, lambda _: pytest.fail("network"))
    with (raw / "page-000.json").open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(AlpacaDataError, match="CHECKSUM"):
        AlpacaHistoricalProvider(raw).load()


def test_credentials_are_dedicated_and_repr_redacted(monkeypatch):
    monkeypatch.setenv("ETORO_API_KEY", "etoro-placeholder")
    monkeypatch.setenv("ETORO_USER_KEY", "etoro-placeholder")
    with pytest.raises(AlpacaDataError, match="CREDENTIALS_UNAVAILABLE"):
        AlpacaCredentials.from_environment()
    monkeypatch.setenv("ALPACA_API_KEY", "alpaca-placeholder-id")
    monkeypatch.setenv("ALPACA_API_SECRET", "alpaca-placeholder-secret")
    credentials = AlpacaCredentials.from_environment()
    assert credentials.api_key == "alpaca-placeholder-id"
    assert "placeholder" not in repr(credentials)


@pytest.mark.parametrize("feed", ["sip", "iex"])
def test_full_history_independent_engine_metrics_and_import_roundtrip(feed, tmp_path):
    request = HistoricalRequest(REQUEST.target, feed)
    rows = []
    for day in request.days:
        market = session(day)
        for i in range(market.minutes):
            # Independently known denominator 5*1000; evaluation 5*3000 -> RVOL 3.
            rows.append(
                row(market.open + timedelta(minutes=i), 3000 if day == request.target else 1000)
            )
    raw = capture(tmp_path, lambda _: response(rows), request)
    before = sha256(raw / "page-000.json")
    report = audit_capture(raw, tmp_path / "audit")
    assert report["complete_sessions"] == 21 and report["metric_comparison"] == "MATCH"
    assert report["independent"]["rvol"] == Decimal(3)
    assert report["independent"]["or_high"] == 102 and report["independent"]["or_low"] == 99
    assert report["independent"]["historical_opening_volume"] == 5000
    assert report["status"] == (
        "ALPACA_CONTRACT_TEST_VERIFIED"
        if feed == "sip"
        else "ALPACA_IEX_INSUFFICIENT_FOR_PRODUCTION_RVOL"
    )
    bundle = import_market_data(
        tmp_path / "audit/regular-minutes.csv", tmp_path / "audit/import-manifest.json"
    )
    assert bundle.manifest.availability_kind == "historical_download"
    assert all(bar.available_at == NOW for bar in bundle.bars)
    assert sha256(raw / "page-000.json") == before
    # Real historical metadata must still be refused operationally, regardless of arithmetic.
    real_manifest = bundle.manifest.model_copy(
        update={"synthetic": False, "volume_kind": "consolidated_shares"}
    )
    from dataclasses import replace

    decision = ORBStrategy().process_session(
        replace(bundle, manifest=real_manifest), request.target
    )
    assert (
        not decision.signals and decision.rejections[0].reason == "OBSERVED_AVAILABILITY_REQUIRED"
    )


def test_current_session_cannot_be_requested(tmp_path):
    with pytest.raises(AlpacaDataError, match="CLOSED_HISTORICAL"):
        capture(tmp_path, lambda _: pytest.fail("network"), HistoricalRequest(date(2026, 9, 14)))


def test_bad_engine_calculation_is_detected_independently(tmp_path, monkeypatch):
    rows = [
        row(session(day).open + timedelta(minutes=i))
        for day in REQUEST.days
        for i in range(session(day).minutes)
    ]
    raw = capture(tmp_path, lambda _: response(rows))
    original = ORBStrategy.opening_metrics

    def wrong(opening, previous):
        metrics = original(opening, previous)
        return metrics.model_copy(update={"or_high": metrics.or_high + 1})

    monkeypatch.setattr(ORBStrategy, "opening_metrics", staticmethod(wrong))
    report = audit_capture(raw, tmp_path / "audit")
    assert report["independent"]["or_high"] == 102
    assert report["engine_metrics"]["or_high"] == 103
    assert report["metric_comparison"] == "MISMATCH"
    assert report["status"] == "ALPACA_DATA_INSUFFICIENT_FOR_RVOL"


def test_429_has_bounded_retries_without_long_or_invalid_waits(tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers={"Retry-After": "0"})

    with pytest.raises(AlpacaDataError, match="RATE_LIMIT_EXHAUSTED"):
        capture(tmp_path, handler)
    assert len(calls) == 3
    for value in ("NaN", "-1", "61"):
        with pytest.raises(AlpacaDataError, match="WAIT_REQUIRED"):
            capture(
                tmp_path / value, lambda _, v=value: httpx.Response(429, headers={"Retry-After": v})
            )


def test_zero_quota_on_success_defers_next_page(tmp_path):
    clock, calls, sleeps = [NOW], [], []

    def sleep(delay):
        sleeps.append(delay)
        clock[0] += timedelta(seconds=delay)

    def handler(request):
        calls.append(request)
        result = response([], "next") if len(calls) == 1 else response([])
        if len(calls) == 1:
            result.headers.update({"X-RateLimit-Remaining": "0", "Retry-After": "3"})
        return result

    client = AlpacaHistoryClient(
        AlpacaCredentials("placeholder", "placeholder"),
        transport=httpx.MockTransport(handler),
        now=lambda: clock[0],
        sleeper=sleep,
    )
    try:
        client.capture(REQUEST, tmp_path / "raw")
    finally:
        client.close()
    assert sleeps == [3] and len(calls) == 2


def test_cli_missing_context_is_configuration_not_data_or_entitlement(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts/audit_alpaca_history.py"
    namespace = runpy.run_path(str(script))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(script), "--capture", "--target", "2026-09-11"])
    assert namespace["main"]() == 2
    results = list((tmp_path / "runtime/alpaca-audits").glob("*/result.json"))
    payload = json.loads(results[0].read_text())
    assert payload["status"] == "ALPACA_CREDENTIALS_UNAVAILABLE"
    assert payload["observed_feed"] is None and payload["raw_sha256"] == {}
    assert payload["feed_effective"] is None and not payload["entitlement_verified"]
    assert not (tmp_path / "data/raw").exists()


@pytest.mark.parametrize(
    "count,volumes", [(4, [Decimal(1)] * 20), (5, [Decimal(1)] * 19), (5, [Decimal(0)] * 20)]
)
def test_engine_metrics_reject_invalid_windows(count, volumes):
    from intraday_etoro_lab.domain import Bar, Instrument

    bars = [
        Bar(
            instrument=Instrument(symbol="SIMA"),
            event_time=session(REQUEST.target).open + timedelta(minutes=i),
            received_at=NOW,
            available_at=NOW,
            open=100,
            high=102,
            low=99,
            close=101,
            volume=1000,
            source="synthetic",
        )
        for i in range(count)
    ]
    with pytest.raises(ValueError):
        ORBStrategy.opening_metrics(bars, volumes)


@pytest.mark.parametrize("error_type", [httpx.ConnectError, httpx.ReadTimeout])
def test_transport_failure_classified_without_private_exception(error_type, tmp_path):
    def handler(request):
        raise error_type("private-upstream-credentials", request=request)

    with pytest.raises(AlpacaDataError) as error:
        capture(tmp_path, handler)
    assert error.value.status == "ALPACA_CONNECTIVITY_FAILED"
    assert "private-upstream" not in (tmp_path / "raw/capture.json").read_text()


@pytest.mark.parametrize(
    "status,body,expected",
    [
        (401, {}, "ALPACA_AUTHENTICATION_FAILED"),
        (403, {}, "ALPACA_HTTP_403"),
        (403, {"message": "subscription does not permit SIP"}, "ALPACA_SIP_ENTITLEMENT_REQUIRED"),
        (429, {}, "ALPACA_RATE_LIMITED"),
        (200, {"bars": []}, "ALPACA_INVALID_RESPONSE"),
        (200, {"bars": {}, "feed": "iex"}, "ALPACA_FEED_MISMATCH"),
        (200, {"bars": {}}, "ALPACA_HISTORICAL_INCOMPLETE"),
    ],
)
def test_acquisition_failure_categories(status, body, expected, tmp_path):
    with pytest.raises(AlpacaDataError) as error:
        capture(tmp_path, lambda _: httpx.Response(status, json=body, headers={"Retry-After": "0"}))
    assert error.value.status == expected


def full_rows():
    return [
        row(session(day).open + timedelta(minutes=i), 3000 if day == REQUEST.target else 1000)
        for day in REQUEST.days
        for i in range(session(day).minutes)
    ]


def test_no_payload_echo_is_unverified_even_with_legacy_real_marker(tmp_path):
    raw = capture(tmp_path, lambda _: response(full_rows()))
    # Model an older manifest that inferred effective feed solely from its request.
    # Fabricated contents remain a test; this is not an external observation.
    rewrite_manifest(
        raw, lambda d: d.update(acquisition_class="NETWORK_HTTP", feed_effective="sip")
    )
    report = audit_capture(raw, tmp_path / "audit")
    assert report["metric_comparison"] == "MATCH"
    assert report["status"] == "FEED_UNVERIFIED"
    assert report["observed_feed"] is report["feed_effective"] is None
    assert report["data_quality"]["aggregate"]["status"] == "BLOCKED"
    imported = import_market_data(
        tmp_path / "audit/regular-minutes.csv", tmp_path / "audit/import-manifest.json"
    )
    assert imported.manifest.volume_kind == "unknown"
    assert imported.manifest.feed_id == "alpaca:unverified:1Min:split"
    assert "FEED_UNVERIFIED" in imported.manifest.quality
    assert report["engine_decision"]["rejections"][0]["reason"] == "OBSERVED_AVAILABILITY_REQUIRED"
    assert not report["engine_decision"]["signals"]


def test_payload_echo_contract_test_never_certifies_external_access(tmp_path):
    raw = capture(tmp_path, lambda _: response(full_rows(), feed="sip"))
    report = audit_capture(raw, tmp_path / "audit")
    assert report["observed_feed"] == "sip"
    assert report["status"] == "ALPACA_CONTRACT_TEST_VERIFIED"
    assert report["external_mutations"] == "DISABLED"
    assert not report["entries_armed"] and not report["order_submission_enabled"]
    assert report["shadow"] == "NOT_STARTED_THIS_PHASE" and report["writes"] == 0


@pytest.mark.parametrize("case", ["duplicate", "zero_volume", "missing_opening"])
def test_complete_quality_report_blocks_defects_without_repair(case, tmp_path):
    rows = full_rows()
    if case == "duplicate":
        rows.insert(1, dict(rows[0]))
    elif case == "zero_volume":
        rows[0]["v"] = 0
    else:
        del rows[1]
    raw = capture(tmp_path, lambda _: response(rows, feed="sip"))
    before = sha256(raw / "page-000.json")
    report = audit_capture(raw, tmp_path / "audit")
    quality = report["data_quality"]["aggregate"]
    assert quality == report["data_quality"]["by_symbol"]["AAPL"]
    assert quality["status"] == "BLOCKED"
    assert quality["sessions_requested"] == 21
    assert quality["sessions_valid"] == 20 and quality["sessions_invalid"] == 1
    assert quality["duplicate_bars"] == (case == "duplicate")
    assert quality["zero_volume_bars"] == (case == "zero_volume")
    assert quality["missing_bars"] == (case == "missing_opening")
    assert quality["opening_windows_complete"] == (20 if case == "missing_opening" else 21)
    assert report["status"] not in {
        "ALPACA_SIP_HISTORICAL_VERIFIED",
        "ALPACA_CONTRACT_TEST_VERIFIED",
    }
    assert sha256(raw / "page-000.json") == before
    assert (tmp_path / "audit/data-quality.json").exists()


def test_failed_quality_parse_reports_unknown_counts_not_clean_dataset(tmp_path):
    bad = dict(row(session(REQUEST.target).open), v=-1)
    raw = capture(tmp_path, lambda _: response([bad]))
    with pytest.raises(AlpacaDataError):
        audit_capture(raw, tmp_path / "audit")
    quality = json.loads((tmp_path / "audit/data-quality.json").read_text())
    assert quality["status"] == "BLOCKED" and quality["counts"] is None
    assert quality["reason_codes"] and quality["aggregate"] is None


def test_calendar_holiday_timezone_and_outside_session_exclusion(tmp_path):
    with pytest.raises(ValueError):
        HistoricalRequest(date(2025, 12, 25))
    first_day, second_day = REQUEST.days[:2]
    rows = [
        row(session(first_day).close),
        dict(row(session(second_day).open), t=f"{second_day}T09:30:00-04:00"),
    ]
    raw = capture(tmp_path, lambda _: response(rows))
    provider = AlpacaHistoricalProvider(raw)
    bundle = provider.load()
    assert bundle.bars[0].event_time == session(second_day).open
    quality = provider.audit["data_quality"]["aggregate"]
    assert quality["out_of_session_bars"] == 1
    assert quality["exclusions"] == [{"reason_code": "OUTSIDE_REGULAR_SESSION", "count": 1}]


def test_out_of_order_duplicate_cannot_hide_transport_order_error(tmp_path):
    first = row(session(REQUEST.target).open)
    second = row(session(REQUEST.target).open + timedelta(minutes=1))
    raw = capture(tmp_path, lambda _: response([first, second, first]))
    with pytest.raises(AlpacaDataError, match="BARS_OUT_OF_ORDER"):
        AlpacaHistoricalProvider(raw).load()


def test_arithmetic_is_deterministic_and_ignores_after_opening_data(tmp_path):
    rows = full_rows()
    raw = capture(tmp_path / "original", lambda _: response(rows))
    first = audit_capture(raw, tmp_path / "audit1")
    second = audit_capture(raw, tmp_path / "audit2")
    assert first == second
    for name in ("audit.json", "manifest.json", "data-quality.json", "regular-minutes.csv"):
        assert sha256(tmp_path / "audit1" / name) == sha256(tmp_path / "audit2" / name)
    # A separate capture perturbs only target minutes after 09:34; raw stays immutable.
    cutoff = session(REQUEST.target).open + timedelta(minutes=5)
    altered = [
        dict(bar, v=9999999, h=999) if datetime.fromisoformat(bar["t"]) >= cutoff else bar
        for bar in rows
    ]
    other = capture(tmp_path / "perturbed", lambda _: response(altered))
    third = audit_capture(other, tmp_path / "audit3")
    assert first["independent"] == third["independent"]
    assert first["engine_metrics"] == third["engine_metrics"]
