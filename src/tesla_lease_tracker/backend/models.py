from datetime import UTC, date, datetime
from enum import Enum

import re

from pydantic import BaseModel, Field, field_validator, model_validator

from .. import __version__


class VersionOut(BaseModel):
    version: str

    @classmethod
    def from_metadata(cls):
        return cls(version=__version__)


# --- Lease Config ---


class LeaseConfigIn(BaseModel):
    vin: str = Field(min_length=17, max_length=17, description="17-character vehicle identification number")

    @field_validator("vin")
    @classmethod
    def validate_vin_chars(cls, v: str) -> str:
        v = v.upper()
        if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", v):
            raise ValueError("VIN must be 17 alphanumeric characters (I, O, Q not allowed)")
        return v

    lease_start_date: date
    lease_end_date: date
    mileage_limit: int = Field(gt=0, description="Total allowed miles over lease term")
    start_odometer: float = Field(ge=0, description="Odometer reading at lease start")

    @model_validator(mode="after")
    def check_date_ordering(self) -> "LeaseConfigIn":
        if self.lease_start_date >= self.lease_end_date:
            raise ValueError("lease_start_date must be before lease_end_date")
        return self


class LeaseConfig(LeaseConfigIn):
    """Stored lease configuration."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LeaseConfigOut(LeaseConfigIn):
    created_at: datetime
    updated_at: datetime


# --- Mileage Reading ---


class ReadingQualityStatus(str, Enum):
    VALID = "valid"
    WARN_MONOTONICITY = "warn_monotonicity"
    WARN_DUPLICATE = "warn_duplicate"


class MileageReading(BaseModel):
    timestamp: datetime
    odometer: float

    @property
    def lease_miles(self) -> float | None:
        """Computed in context of a lease config — not stored."""
        return None


class MileageReadingOut(BaseModel):
    timestamp: datetime
    odometer: float
    lease_miles: float = Field(description="Miles driven since lease start")


# --- Forecast ---


class ForecastPoint(BaseModel):
    date: date
    predicted_miles: float
    lower_bound: float | None = None
    upper_bound: float | None = None


class ForecastOut(BaseModel):
    model: str = Field(description="linear or prophet")
    points: list[ForecastPoint]
    daily_rate: float = Field(description="Predicted average miles/day")
    projected_end_miles: float = Field(description="Predicted total lease miles at end")
    over_under: float = Field(description="Positive = over limit, negative = under")


# --- Dashboard ---


class DashboardOut(BaseModel):
    lease_miles_used: float
    mileage_limit: int
    daily_average: float
    budget_daily_rate: float
    days_remaining: int
    total_lease_days: int
    projected_end_miles: float
    over_under: float
    last_sync: datetime | None = None
    last_odometer: float | None = None


# --- Health ---


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth(BaseModel):
    name: str
    status: ServiceStatus
    error: str | None = None


class HealthOut(BaseModel):
    status: ServiceStatus = Field(description="Overall service status")
    version: str = Field(description="Application version")
    has_lease: bool = Field(description="Whether a lease is configured")
    readings_count: int = Field(description="Number of mileage readings stored")
    last_sync: datetime | None = Field(default=None, description="Last mileage sync timestamp")
    storage_mode: str = Field(default="database", description="Current storage mode")
    database: DependencyHealth | None = Field(default=None, description="Database health")
    zerobus: DependencyHealth | None = Field(default=None, description="Zerobus stream health")


# --- Metrics ---


class EndpointStats(BaseModel):
    path: str
    request_count: int
    error_count: int
    error_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float


class MetricsOut(BaseModel):
    window_size: int
    request_count: int
    error_count: int
    error_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    data_quality_warnings: int
    by_endpoint: list[EndpointStats]


# --- Seed Result ---


class SeedResultOut(BaseModel):
    status: str
    lease_vin: str
    readings_count: int
    odometer_range: str
