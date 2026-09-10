from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)


class Instrument(FrozenModel):
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.\-]{0,14}$")
    exchange: str = "XNYS"
    currency: str = "USD"
    asset_class: Literal["common_stock", "etf", "adr", "other"] = "common_stock"
    stable_id: str | None = None
    broker_id: int | None = Field(default=None, gt=0)


class Bar(FrozenModel):
    instrument: Instrument
    event_time: datetime
    received_at: datetime
    available_at: datetime
    open: Decimal = Field(gt=0)
    high: Decimal = Field(gt=0)
    low: Decimal = Field(gt=0)
    close: Decimal = Field(gt=0)
    volume: Decimal = Field(ge=0)
    source: str = Field(min_length=1)
    interval_seconds: Literal[60] = 60
    final: bool = True
    revision: int = Field(default=0, ge=0)

    @field_validator("event_time", "received_at", "available_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timezone-aware timestamp required")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def valid_bar(self) -> Self:
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("OHLC high invalid")
        if self.low > min(self.open, self.close):
            raise ValueError("OHLC low invalid")
        if self.event_time.second or self.event_time.microsecond:
            raise ValueError("bar must start on a minute boundary")
        if self.available_at < self.received_at:
            raise ValueError("available_at precedes received_at")
        if self.final and self.received_at < self.end_time:
            raise ValueError("complete bar received before interval end")
        return self

    @property
    def end_time(self) -> datetime:
        return self.event_time + timedelta(seconds=self.interval_seconds)

    @property
    def session_date(self) -> date:
        from zoneinfo import ZoneInfo

        return self.event_time.astimezone(ZoneInfo("America/New_York")).date()


class Signal(FrozenModel):
    signal_id: str
    session_date: date
    instrument: Instrument
    available_at: datetime
    expires_at: datetime
    reference_price: Decimal = Field(gt=0)
    stop_price: Decimal = Field(gt=0)
    rank: int = Field(ge=1)
    rvol: Decimal = Field(ge=0)
    strategy_version: str = "ORB_RVOL_v0.1"


class DataManifest(FrozenModel):
    schema_version: str = "1"
    source: str = Field(min_length=1)
    synthetic: bool
    volume_kind: Literal["synthetic_shares", "consolidated_shares", "venue_shares", "unknown"]
    adjustments: Literal["unadjusted", "split_adjusted", "unknown"]
    license: str = Field(min_length=1)
    provenance: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    coverage_start: datetime
    coverage_end: datetime
    rows: int = Field(gt=0)
    calendar: str = "XNYS"
    point_in_time_universe: bool = False
    availability_evidence: str = Field(min_length=1)
    availability_kind: Literal["synthetic", "observed", "historical_download", "unknown"] = (
        "unknown"
    )
    acquired_at: datetime | None = None
    feed_id: str | None = None
    quality: tuple[str, ...] = ()

    @field_validator("coverage_start", "coverage_end", "acquired_at")
    @classmethod
    def manifest_time(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("MANIFEST_TIMEZONE_REQUIRED")
            return value.astimezone(UTC)
        return value

    @model_validator(mode="after")
    def consistent_evidence(self) -> Self:
        if self.coverage_start >= self.coverage_end:
            raise ValueError("MANIFEST_COVERAGE_INVALID")
        if (self.volume_kind == "synthetic_shares") != self.synthetic:
            raise ValueError("SYNTHETIC_VOLUME_LABEL_MISMATCH")
        if not self.synthetic and self.availability_kind == "synthetic":
            raise ValueError("REAL_DATA_WITH_SYNTHETIC_AVAILABILITY")
        if self.availability_kind == "historical_download" and self.acquired_at is None:
            raise ValueError("HISTORICAL_DOWNLOAD_TIME_REQUIRED")
        return self
