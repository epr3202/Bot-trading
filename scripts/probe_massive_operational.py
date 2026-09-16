"""Isolated GET-only feasibility diagnostic. No imports from the trading application."""

import argparse
import json
import math
import os
import re
import ssl
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any

import httpx

SYMBOLS = ("AAPL", "SPY", "QQQ")
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def dotenv_credential(path: Path) -> str:
    """Read only a literal MASSIVE_API_KEY; never inherit or expand another secret."""
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        return ""
    assignments = [
        match.group(1)
        for line in lines
        if (match := re.fullmatch(r"\s*(?:export\s+)?MASSIVE_API_KEY\s*=\s*(.*)", line))
    ]
    if len(assignments) != 1:
        return ""
    # Deliberately no interpolation, multiline values, or environment fallback.
    match = re.fullmatch(r"(['\"]?)([A-Za-z0-9_-]+)\1\s*(?:#.*)?", assignments[0])
    return match.group(2) if match else ""


def epoch_ns(value: Any, unit: str) -> int:
    if type(value) is not int or unit not in {"ns", "ms"}:
        raise ValueError("TIMESTAMP_INVALID")
    result = value * (1_000_000 if unit == "ms" else 1)
    if not 946684800_000000000 <= result < 4102444800_000000000:
        raise ValueError("TIMESTAMP_RANGE_OR_UNIT_INVALID")
    return result


def iso_ns(value: int) -> str:
    seconds, nano = divmod(value, 1_000_000_000)
    stamp = EPOCH + timedelta(seconds=seconds)
    return stamp.strftime("%Y-%m-%dT%H:%M:%S") + f".{nano:09d}Z"


def observation(
    symbol: str, doc: dict, received: int, decision: int, previous: dict | None
) -> dict:
    row = doc["results"]
    if symbol not in SYMBOLS or row["T"] != symbol or decision < received:
        raise ValueError("IDENTITY_OR_CLOCK_INVALID")
    bid, ask = Decimal(str(row["p"])), Decimal(str(row["P"]))
    if not bid.is_finite() or not ask.is_finite() or not 0 < bid <= ask:
        raise ValueError("PRICE_INVALID")
    sip = epoch_ns(row["t"], "ns")
    participant = epoch_ns(row["y"], "ns") if row.get("y") is not None else None
    sequence = row.get("q")
    if sequence is not None and type(sequence) is not int:
        raise ValueError("SEQUENCE_INVALID")
    result = {
        "symbol": symbol,
        "bid": str(bid),
        "ask": str(ask),
        "sip_raw": sip,
        "participant_raw": participant,
        "original_unit": "ns",
        "sequence": sequence,
        "received_at_utc": iso_ns(received),
        "decision_at_utc": iso_ns(decision),
        "repeated": bool(
            previous and (sip, sequence) == (previous["sip_raw"], previous["sequence"])
        ),
        "out_of_order": bool(previous and sip < previous["sip_raw"]),
        "event_gap_seconds": (sip - previous["sip_raw"]) / 1e9 if previous else None,
    }
    for label, stamp in (("sip", sip), ("participant", participant)):
        result[label + "_utc"] = iso_ns(stamp) if stamp is not None else None
        result[label + "_age_at_receive"] = (received - stamp) / 1e9 if stamp is not None else None
        result[label + "_age_at_decision"] = (decision - stamp) / 1e9 if stamp is not None else None
    result["future_timestamp"] = any(t > received for t in (sip, participant) if t is not None)
    return result


def serialize(value: Any, secret: str) -> str:
    # No raw payloads/headers/errors are evidence. Defense against reflected credentials.
    text = json.dumps(value, ensure_ascii=True, allow_nan=False)
    return text.replace(secret, "[REDACTED]") if secret else text


def summarize(rows: list[dict]) -> dict:
    result = {}
    for symbol in SYMBOLS:
        samples = [r for r in rows if r["symbol"] == symbol]
        good = [r for r in samples if r["result_status"] == "OBSERVED"]
        metrics = {}
        for source in ("sip", "participant"):
            ages = sorted(
                r[source + "_age_at_decision"]
                for r in good
                if r.get(source + "_age_at_decision") is not None
            )
            metrics[source] = {
                "samples": len(ages),
                "percent_le_3s": 100 * sum(0 <= a <= 3 for a in ages) / len(ages) if ages else None,
                "median": median(ages) if ages else None,
                "p95_nearest_rank": ages[math.ceil(0.95 * len(ages)) - 1] if ages else None,
                "maximum": max(ages) if ages else None,
            }
        result[symbol] = {
            "requests": len(samples),
            "observed": len(good),
            "errors": len(samples) - len(good),
            "http_statuses": [r.get("http_status") for r in samples],
            "ages": metrics,
            "repeated": sum(r.get("repeated", False) for r in good),
            "out_of_order": sum(r.get("out_of_order", False) for r in good),
            "future": sum(r.get("future_timestamp", False) for r in good),
            "event_gaps_gt_3s": sum((r.get("event_gap_seconds") or 0) > 3 for r in good),
            "rate_limits": sum(r.get("http_status") == 429 for r in samples),
            "network_failures": sum(r["result_status"] == "NETWORK_ERROR" for r in samples),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    dotenv_path = Path(__file__).resolve().parent.parent / ".env"
    secret = dotenv_credential(dotenv_path)
    report = {
        "credential": "PRESENT" if secret else "MISSING",
        "credential_source": "REPOSITORY_DOTENV_ONLY",
        "planned_seconds": 300,
        "method": "GET",
        "origin": "https://api.massive.com",
        "trading_mutations": 0,
        "clock_offset_bound": "UNVERIFIED",
        "plan_name": "UNKNOWN",
    }
    rows: list[dict] = []
    previous: dict[str, dict] = {}
    disabled: set[str] = set()
    start = time.monotonic()
    report["started_at_utc"] = datetime.now(UTC).isoformat()
    try:
        if not secret or any(c.isspace() for c in secret):
            raise ValueError("CREDENTIAL_UNAVAILABLE")
        ca = Path("certs/epm-root.cer")
        context = ssl.create_default_context(
            cafile=str(ca) if ca.exists() else os.getenv("REQUESTS_CA_BUNDLE")
        )
        with httpx.Client(
            verify=context, trust_env=True, follow_redirects=False, timeout=10
        ) as client:
            while time.monotonic() - start < 300 and len(disabled) < len(SYMBOLS):
                for symbol in SYMBOLS:
                    if symbol in disabled or time.monotonic() - start >= 300:
                        continue
                    path = "/v2/last/nbbo/" + symbol
                    record = {
                        "symbol": symbol,
                        "path": path,
                        "http_status": None,
                        "request_at_utc": datetime.now(UTC).isoformat(),
                    }
                    try:
                        response = client.get(
                            report["origin"] + path, headers={"Authorization": "Bearer " + secret}
                        )
                        received = time.time_ns()
                        record.update(
                            http_status=response.status_code, received_at_utc=iso_ns(received)
                        )
                        if response.status_code != 200:
                            record["result_status"] = "HTTP_" + str(response.status_code)
                            disabled.add(symbol)
                            if response.status_code == 429:
                                disabled.update(SYMBOLS)
                        else:
                            doc = json.loads(response.content, parse_float=Decimal)
                            status = doc.get("status")
                            record["provider_status"] = (
                                status
                                if status in {"OK", "DELAYED", "ERROR", "NOT_AUTHORIZED"}
                                else "UNKNOWN"
                            )
                            if status != "OK":
                                raise ValueError("PROVIDER_NOT_OK")
                            record.update(
                                observation(
                                    symbol, doc, received, time.time_ns(), previous.get(symbol)
                                )
                            )
                            record["result_status"] = "OBSERVED"
                            if not record["out_of_order"]:
                                previous[symbol] = record.copy()
                    except httpx.TransportError:
                        record["result_status"] = "NETWORK_ERROR"
                        disabled.add(symbol)
                    except (ValueError, TypeError, KeyError, ArithmeticError):
                        record["result_status"] = "INVALID_RESPONSE"
                        disabled.add(symbol)
                    record.setdefault("decision_at_utc", iso_ns(time.time_ns()))
                    rows.append(record)
                    with (args.output / "observations.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(serialize(record, secret) + "\n")
                    print(
                        serialize(
                            {
                                "symbol": symbol,
                                "status": record["result_status"],
                                "sip_age": record.get("sip_age_at_decision"),
                            },
                            secret,
                        ),
                        flush=True,
                    )
                    # Access discovery stays under 5/min. Once all are observed, 1 GET/s.
                    time.sleep(1 if len(previous) == 3 else 13)
        report["stop_reason"] = (
            "WINDOW_COMPLETE" if time.monotonic() - start >= 300 else "ACCESS_OR_DATA_FAILURE"
        )
    except Exception:
        report["stop_reason"] = "DIAGNOSTIC_CONFIGURATION_ERROR"
    report.update(
        elapsed_seconds=time.monotonic() - start,
        finished_at_utc=datetime.now(UTC).isoformat(),
        symbols=summarize(rows),
    )
    report["decision"] = "CONTRACT_CHANGE_NOT_JUSTIFIED"
    report["decision_note"] = (
        "Quote observations alone do not prove bars or eToro execution guarantees."
    )
    (args.output / "summary.json").write_text(serialize(report, secret) + "\n", encoding="utf-8")
    print(serialize({"stop_reason": report["stop_reason"], "evidence": str(args.output)}, secret))
    return 0 if report["stop_reason"] == "WINDOW_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
