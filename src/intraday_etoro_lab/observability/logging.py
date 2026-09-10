from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

_SENSITIVE = re.compile(r"(authorization|api.?key|user.?key|token|secret|password|cookie)", re.I)
_BEARER = re.compile(r"(?i)bearer\s+[^\s,;]+")


def redact(value: Any, secrets: tuple[str, ...] = ()) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if _SENSITIVE.search(str(key)) else redact(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [redact(item, secrets) for item in value]
    if isinstance(value, str):
        value = _BEARER.sub("Bearer [REDACTED]", value)
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
    return value


class JsonFormatter(logging.Formatter):
    def __init__(self, secrets: tuple[str, ...] = ()) -> None:
        super().__init__()
        self.secrets = secrets

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "at": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        return json.dumps(redact(payload, self.secrets), ensure_ascii=False)
