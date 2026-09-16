"""Isolated A7 read-only spike; no runner, account reads or trading capability."""

import argparse
import importlib
import json
import os
import re
import ssl
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from intraday_etoro_lab.brokers.transport import Credentials

ORIGIN = "wss://ws.etoro.com/ws"
TOPIC = "instrument:1001"  # AAPL resolved in the existing A5/A7 evidence.


def decode(text: str) -> dict:
    def unique(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_FIELD")
            result[key] = value
        return result

    value = json.loads(text, object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("OBJECT_REQUIRED")
    return value


def rate(message: dict, received: datetime, checked: datetime) -> dict:
    if message.get("topic") != TOPIC or message.get("type") != "Trading.Instrument.Rate":
        raise ValueError("UNEXPECTED_MESSAGE")
    content = decode(message["content"])
    bid, ask = Decimal(str(content["Bid"])), Decimal(str(content["Ask"]))
    if not bid.is_finite() or not ask.is_finite() or not 0 < bid <= ask:
        raise ValueError("PRICE_INVALID")
    stamp = content["Date"]
    if not isinstance(stamp, str) or "T" not in stamp:
        raise ValueError("TIMESTAMP_INVALID")
    event = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if event.tzinfo is None or received.tzinfo is None or checked.tzinfo is None:
        raise ValueError("TIMEZONE_REQUIRED")
    event = event.astimezone(UTC)
    age = (checked - event).total_seconds()
    identifier = content.get("PriceRateID")
    if identifier is not None and (not str(identifier).isdigit() or len(str(identifier)) > 24):
        raise ValueError("RATE_ID_INVALID")
    return {
        "instrument_id": 1001,
        "type": "Trading.Instrument.Rate",
        "bid": str(bid),
        "ask": str(ask),
        "provider_timestamp": stamp,
        "event_time": event.isoformat(),
        "received_at": received.isoformat(),
        "check_time": checked.isoformat(),
        "quote_age": age,
        "fresh": 0 <= age <= 3 and event <= received <= checked,
        "spread_fraction": str((ask - bid) / ask),
        "price_rate_id": str(identifier) if identifier is not None else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {
        "origin": ORIGIN,
        "topic": TOPIC,
        "state": "DISCONNECTED",
        "authenticated": False,
        "subscribed": False,
        "events": 0,
        "fresh_events": 0,
        "duplicates": 0,
        "out_of_order": 0,
        "reconnections": 0,
        "mutations": 0,
        "planned_seconds": 120,
        "started_at": datetime.now(UTC).isoformat(),
    }
    socket = None
    ages = []
    previous = None
    try:
        credentials = Credentials.from_environment()
        report["ETORO_API_KEY"] = "PRESENT"
        report["ETORO_USER_KEY"] = "PRESENT"
        # Optional diagnostic dependency, isolated with uv --with; frozen lock unchanged.
        ws = importlib.import_module("websocket")
        ca = Path("certs/epm-root.cer")
        context = ssl.create_default_context(
            cafile=str(ca) if ca.exists() else os.getenv("REQUESTS_CA_BUNDLE")
        )
        report["state"] = "CONNECTING"
        socket = ws.create_connection(
            ORIGIN, timeout=10, redirect_limit=0, sslopt={"context": context}
        )
        if socket.getstatus() != 101:
            raise ValueError("UPGRADE_REQUIRED")
        report["state"] = "AUTHENTICATING"
        auth_id = str(uuid4())
        socket.send(
            json.dumps(
                {
                    "id": auth_id,
                    "operation": "Authenticate",
                    "data": {
                        "userKey": credentials.user_key,
                        "apiKey": credentials.api_key,
                    },
                }
            )
        )
        ack = decode(socket.recv())
        if ack.get("id") != auth_id or ack.get("operation") != "Authenticate":
            raise ValueError("AUTH_ACK_INVALID")
        if ack.get("success") is not True:
            code = ack.get("errorCode")
            report["auth_error"] = (
                code
                if code
                in {
                    "Forbidden",
                    "Unauthorized",
                    "InvalidKey",
                    "TooManyRequests",
                    "DataRequired",
                    "ApiKeyRequired",
                    "UserKeyRequired",
                    "UnhandledException",
                }
                else "UNRECOGNIZED"
            )
            raise ValueError("AUTH_REJECTED")
        report["authenticated"] = True
        report["state"] = "SUBSCRIBING"
        sub_id = str(uuid4())
        socket.send(
            json.dumps(
                {
                    "id": sub_id,
                    "operation": "Subscribe",
                    "data": {
                        "topics": [TOPIC],
                        "snapshot": True,
                    },
                }
            )
        )
        until = time.monotonic() + 120
        while time.monotonic() < until:
            socket.settimeout(min(10, max(0.1, until - time.monotonic())))
            try:
                raw = socket.recv()
                received = datetime.now(UTC)
            except ws.WebSocketTimeoutException:
                report["state"] = "DEGRADED"
                continue
            if not raw:
                raise ValueError("DISCONNECTED")
            doc = decode(raw)
            if doc.get("operation") == "Subscribe":
                if doc.get("id") != sub_id or doc.get("success") is not True:
                    raise ValueError("SUBSCRIBE_REJECTED")
                report["subscribed"] = True
                continue
            for message in doc.get("messages", []):
                row = rate(message, received, datetime.now(UTC))
                report["events"] += 1
                stamp = datetime.fromisoformat(row["event_time"])
                duplicate = bool(previous and stamp == previous[0])
                out_of_order = bool(previous and stamp < previous[0])
                report["duplicates"] += duplicate
                report["out_of_order"] += out_of_order
                row.update(duplicate=duplicate, out_of_order=out_of_order)
                valid = report["subscribed"] and row["fresh"] and not out_of_order
                report["state"] = "READY" if valid else "DEGRADED"
                report["fresh_events"] += bool(valid)
                row["connection_state"] = report["state"]
                ages.append(row["quote_age"])
                if not duplicate and not out_of_order:
                    previous = (stamp, row["price_rate_id"])
                safe = json.dumps(row)
                for secret in (credentials.api_key, credentials.user_key):
                    safe = safe.replace(secret, "[REDACTED]")
                with (args.output / "events.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(safe + "\n")
        report["stop_reason"] = "OBSERVATION_COMPLETE"
    except Exception as exc:
        # Never print exception text, handshake bodies, headers or authentication payloads.
        report["error_type"] = type(exc).__name__
        status = getattr(exc, "status_code", None)
        if type(status) is int:
            report["handshake_http_status"] = status
        headers = getattr(exc, "resp_headers", {}) or {}
        report["cloudflare_header_present"] = "cf-ray" in headers
        for name in ("x-mitmproxy-blocked-reason", "x-webcache-source"):
            value = headers.get(name)
            report[name] = (
                value
                if value
                in {
                    "PERMISSION_DENIED",
                    "ROBOTS_DENIED",
                    "BLOCK_LIST",
                    "INTERNAL",
                    "HTTPS_ONLY",
                    "CACHE_MISS",
                    "origin",
                    "cache",
                }
                else ("PRESENT" if value is not None else "MISSING")
            )
        body = getattr(exc, "resp_body", "") or ""
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
        report["handshake_body_class"] = (
            "CLOUDFLARE_CHALLENGE"
            if "challenge-platform" in body
            else "FORBIDDEN"
            if "forbidden" in body.lower()
            else "NOT_CLASSIFIED"
        )
        report["handshake_body_markers"] = [
            word
            for word in ("proxy", "policy", "denied", "blocked", "upgrade", "cloudflare")
            if word in body.lower()
        ]
        if not report["authenticated"] and report["state"] == "CONNECTING":
            safe_body = body
            for name in ("ETORO_API_KEY", "ETORO_USER_KEY"):
                secret = os.getenv(name)
                if secret:
                    safe_body = safe_body.replace(secret, "[REDACTED]")
            safe_body = re.sub(r"https?://\S+", "[URL_REMOVED]", safe_body)
            safe_body = re.sub(r"[\w.+-]+@[\w.-]+", "[EMAIL_REMOVED]", safe_body)
            safe_body = re.sub(r"[A-Za-z0-9_./+=-]{24,}", "[IDENTIFIER_REMOVED]", safe_body)
            report["handshake_message_sanitized"] = "".join(
                c for c in safe_body[:500] if c.isprintable()
            )
        allowed = {
            "AUTH_REJECTED",
            "AUTH_ACK_INVALID",
            "UPGRADE_REQUIRED",
            "SUBSCRIBE_REJECTED",
            "DISCONNECTED",
        }
        report["stop_reason"] = str(exc) if str(exc) in allowed else "READ_ONLY_PROBE_FAILED"
    finally:
        if socket is not None:
            socket.close()
        report["state"] = "DISCONNECTED"
    report["finished_at"] = datetime.now(UTC).isoformat()
    report["minimum_age"] = min(ages) if ages else None
    report["maximum_age"] = max(ages) if ages else None
    report["migration"] = "NOT_INTEGRATED"
    (args.output / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report.get("stop_reason") == "OBSERVATION_COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
