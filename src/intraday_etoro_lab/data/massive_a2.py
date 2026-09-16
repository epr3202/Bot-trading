"""Reproducible historical data sufficiency audit; never runs trading or replay."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from intraday_etoro_lab.data.calendar import session
from intraday_etoro_lab.data.massive import MassiveHistoricalProvider
from intraday_etoro_lab.data.massive_audit import independent_metrics
from intraday_etoro_lab.data.massive_http import (
    MassiveDataError,
    MassiveHistoricalRequest,
    sha256,
    utc_now,
)
from intraday_etoro_lab.data.providers import DataBundle
from intraday_etoro_lab.strategies.features import relative_strength, session_vwap
from intraday_etoro_lab.strategies.orb import ORBStrategy


def validate_a2(paths: dict[str, Path], target: date) -> dict[str, Any]:
    request = MassiveHistoricalRequest(target)
    report: dict[str, Any] = {
        "schema_version": "massive-a2-v1",
        "provider": "Massive",
        "generated_at": utc_now().isoformat(),
        "symbol": "AAPL",
        "benchmarks": ["SPY", "QQQ"],
        "target": str(target),
        "first_session": str(request.days[0]),
        "last_session": str(target),
        "sessions": [str(day) for day in request.days],
        "interval": "1m",
        "timezone": "America/New_York",
        "parameters": {"adjusted": True, "sort": "asc", "limit": 50000},
        "availability": "HISTORICAL_DOWNLOAD; not contemporaneous observations",
        "datasets": {},
        "errors": {},
        "criteria": dict.fromkeys(
            ["sessions_21", "real_massive", "orb", "rvol_20", "spy_qqq", "vwap", "evidence"],
            "FAIL",
        ),
        "regime": "NOT_APPLICABLE: no regime rule exists in ORB_RVOL_v0.1",
        "feature_scope": "RS and HLC3 VWAP are existing research functions, inactive in v0.1",
    }
    bundles: dict[str, DataBundle] = {}
    for symbol in ("AAPL", "SPY", "QQQ"):
        try:
            if symbol not in paths:
                raise MassiveDataError("DATASET_MISSING")
            provider = MassiveHistoricalProvider(paths[symbol])
            bundle = provider.load()
            if provider.capture["target"] != str(target) or provider.audit["symbol"] != symbol:
                raise MassiveDataError("SYMBOL_OR_TARGET_MISMATCH")
            report["datasets"][symbol] = {
                **provider.audit,
                "path": paths[symbol].as_posix(),
                "capture_sha256": sha256(paths[symbol] / "capture.json"),
                "raw_sha256": {p["file"]: p["sha256"] for p in provider.capture["pages"]},
                "acquisition_class": provider.capture["acquisition_class"],
                "request_bounds_ms": request.bounds,
            }
            if provider.audit["data_quality"]["status"] != "PASS":
                raise MassiveDataError("DATA_QUALITY_FAILED")
            if bundle.manifest.synthetic or not provider.audit["volume_semantics_verified"]:
                raise MassiveDataError("REAL_MASSIVE_SEMANTICS_REQUIRED")
            bundles[symbol] = bundle
        except MassiveDataError as exc:
            report["errors"][symbol] = str(exc)
        except (OSError, ValueError, KeyError, TypeError):
            report["errors"][symbol] = "LOCAL_INPUT_INVALID"
    criteria = report["criteria"]
    if len(bundles) == 3:
        criteria["sessions_21"] = criteria["real_massive"] = "PASS"
    if "AAPL" in bundles:
        bundle = bundles["AAPL"]
        by_time = {bar.event_time: bar for bar in bundle.bars}
        opening = [by_time[session(target).open + timedelta(minutes=i)] for i in range(5)]
        previous = [
            sum(
                (by_time[session(day).open + timedelta(minutes=i)].volume for i in range(5)),
                Decimal(0),
            )
            for day in request.days[:-1]
        ]
        metrics = ORBStrategy.opening_metrics(opening, previous).model_dump()
        independent = independent_metrics(paths["AAPL"], request)
        report["opening_timestamps"] = [bar.event_time.isoformat() for bar in opening]
        report["metrics"] = metrics
        report["independent_metrics"] = independent
        report["previous_opening_volumes"] = dict(
            zip(map(str, request.days[:-1]), previous, strict=True)
        )
        report["rvol_formula"] = "sum(target first 5 volumes) / mean(previous 20 first 5 volumes)"
        if metrics == independent:
            criteria["orb"] = criteria["rvol_20"] = "PASS"
        daily = tuple(bar for bar in bundle.bars if bar.session_date == target)
        vwap = session_vwap(daily, volume_verified=True)
        # Independent algebraic ordering, same HLC3 bar approximation (not trade VWAP).
        numerator = sum(((b.high + b.low + b.close) * b.volume for b in daily), Decimal(0))
        reference = numerator / (3 * sum((b.volume for b in daily), Decimal(0)))
        report["vwap"] = {
            "value": vwap,
            "independent": reference,
            "bars": len(daily),
            "formula": "sum(((h+l+c)/3)*v)/sum(v); regular target session",
            "fields": ["h", "l", "c", "v"],
            "absolute_tolerance": "1e-20",
        }
        if vwap.is_finite() and abs(vwap - reference) <= Decimal("1e-20"):
            criteria["vwap"] = "PASS"
        liquidity = (
            sum((b.close * b.volume for b in bundle.bars if b.session_date != target), Decimal(0))
            / 20
        )
        prior_close = by_time[session(request.days[-2]).close - timedelta(minutes=1)].close
        report["universe_eligibility"] = {
            "previous_close": prior_close,
            "average_dollar_volume": liquidity,
            "eligible": prior_close > 10 and liquidity > 50000000,
            "scope": "AAPL common stock historical universe; no broker eligibility or signal",
        }
        if not report["universe_eligibility"]["eligible"]:
            criteria["orb"] = "FAIL"
    if all(symbol in bundles for symbol in ("SPY", "QQQ")):
        stamps = [{b.event_time for b in bundles[s].bars} for s in bundles]
        if all(stamp == stamps[0] for stamp in stamps):
            criteria["spy_qqq"] = "PASS"
            if "AAPL" in bundles:
                report["relative_strength"] = {}
                for symbol in ("SPY", "QQQ"):
                    bars = [b for b in bundles[symbol].bars if b.session_date == target]
                    report["relative_strength"][symbol] = relative_strength(
                        opening[0].open, opening[4].close, bars[0].open, bars[4].close
                    )
                report["relative_strength_window"] = "09:30 open to 09:34 bar close (09:35 NY)"
    criteria["evidence"] = "PASS"
    report["status"] = "PASS" if all(v == "PASS" for v in criteria.values()) else "FAIL"
    return report
