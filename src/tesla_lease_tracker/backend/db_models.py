from datetime import date, datetime

from sqlmodel import Field, SQLModel


class LeaseConfigDB(SQLModel, table=True):
    __tablename__ = "lease_config"

    id: int | None = Field(default=None, primary_key=True)
    vin: str = Field(max_length=17, index=True)
    lease_start_date: date
    lease_end_date: date
    mileage_limit: int
    start_odometer: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AppStateDB(SQLModel, table=True):
    __tablename__ = "app_state"

    id: int | None = Field(default=None, primary_key=True)
    last_sync: datetime | None = None


class MileageReadingDB(SQLModel, table=True):
    __tablename__ = "mileage_readings"

    id: int | None = Field(default=None, primary_key=True)
    vin: str = Field(max_length=17, index=True)
    timestamp: datetime
    odometer: float
