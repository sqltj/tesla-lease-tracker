from datetime import date, datetime

from pydantic import BaseModel, Field

from .. import __version__


class VersionOut(BaseModel):
    version: str

    @classmethod
    def from_metadata(cls):
        return cls(version=__version__)


# --- Lease Config ---


class LeaseConfigIn(BaseModel):
    vin: str
    lease_start_date: date
    lease_end_date: date
    mileage_limit: int = Field(description="Total allowed miles over lease term")
    start_odometer: float = Field(description="Odometer reading at lease start")


class LeaseConfig(LeaseConfigIn):
    """Stored lease configuration."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LeaseConfigOut(LeaseConfigIn):
    created_at: datetime
    updated_at: datetime


# --- Mileage Reading ---


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


# --- AppData (root persistence object) ---


class AppData(BaseModel):
    lease_config: LeaseConfig | None = None
    readings: list[MileageReading] = Field(default_factory=list)
    last_sync: datetime | None = None
