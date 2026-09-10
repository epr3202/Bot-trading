from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from importlib.metadata import version
from typing import Any

import exchange_calendars as xcals


@dataclass(frozen=True)
class Session:
    day: date
    open: datetime
    close: datetime

    @property
    def flatten_at(self) -> datetime:
        return self.close - timedelta(minutes=5)

    @property
    def minutes(self) -> int:
        return int((self.close - self.open).total_seconds() // 60)


@lru_cache(maxsize=1)
def _calendar() -> Any:
    return xcals.get_calendar("XNYS", start="2000-01-01", end="2035-12-31")


def calendar_version() -> str:
    return "XNYS/exchange-calendars/" + version("exchange-calendars")


@lru_cache(maxsize=8192)
def session(day: date) -> Session:
    calendar = _calendar()
    if not calendar.is_session(day.isoformat()):
        raise ValueError(f"NOT_TRADING_SESSION: {day}")
    return Session(
        day,
        calendar.session_open(day.isoformat()).to_pydatetime(),
        calendar.session_close(day.isoformat()).to_pydatetime(),
    )


def sessions(start: date, end: date) -> tuple[date, ...]:
    return tuple(stamp.date() for stamp in _calendar().sessions_in_range(start, end))
