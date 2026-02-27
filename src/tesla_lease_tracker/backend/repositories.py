from datetime import UTC, datetime, timedelta

from sqlmodel import Session, func, select

from .db_models import AppStateDB, LeaseConfigDB, MileageReadingDB
from .logger import logger
from .models import LeaseConfig, LeaseConfigIn, MileageReading


class LeaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_lease_config(self) -> LeaseConfig | None:
        row = self.session.exec(select(LeaseConfigDB)).first()
        if not row:
            return None
        return LeaseConfig(
            vin=row.vin,
            lease_start_date=row.lease_start_date,
            lease_end_date=row.lease_end_date,
            mileage_limit=row.mileage_limit,
            start_odometer=row.start_odometer,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def save_lease_config(self, lease_in: LeaseConfigIn) -> LeaseConfig:
        now = datetime.now(UTC)
        row = self.session.exec(select(LeaseConfigDB)).first()
        if row:
            row.vin = lease_in.vin
            row.lease_start_date = lease_in.lease_start_date
            row.lease_end_date = lease_in.lease_end_date
            row.mileage_limit = lease_in.mileage_limit
            row.start_odometer = lease_in.start_odometer
            row.updated_at = now
        else:
            row = LeaseConfigDB(
                vin=lease_in.vin,
                lease_start_date=lease_in.lease_start_date,
                lease_end_date=lease_in.lease_end_date,
                mileage_limit=lease_in.mileage_limit,
                start_odometer=lease_in.start_odometer,
                created_at=now,
                updated_at=now,
            )
            self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return LeaseConfig(
            vin=row.vin,
            lease_start_date=row.lease_start_date,
            lease_end_date=row.lease_end_date,
            mileage_limit=row.mileage_limit,
            start_odometer=row.start_odometer,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def get_last_sync(self) -> datetime | None:
        row = self.session.exec(select(AppStateDB)).first()
        return row.last_sync if row else None

    def set_last_sync(self, ts: datetime) -> None:
        row = self.session.exec(select(AppStateDB)).first()
        if row:
            row.last_sync = ts
        else:
            row = AppStateDB(last_sync=ts)
            self.session.add(row)
        self.session.commit()


class MileageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_readings(self, vin: str | None = None) -> list[MileageReading]:
        stmt = select(MileageReadingDB).order_by(MileageReadingDB.timestamp)
        if vin:
            stmt = stmt.where(MileageReadingDB.vin == vin)
        rows = self.session.exec(stmt).all()
        return [
            MileageReading(timestamp=r.timestamp, odometer=r.odometer) for r in rows
        ]

    def add_reading(self, vin: str, timestamp: datetime, odometer: float) -> None:
        row = MileageReadingDB(vin=vin, timestamp=timestamp, odometer=odometer)
        self.session.add(row)
        self.session.commit()

    def count(self) -> int:
        rows = self.session.exec(select(MileageReadingDB)).all()
        return len(rows)

    def validate_reading(self, vin: str, timestamp: datetime, odometer: float) -> list[str]:
        """Validate a reading against existing data. Returns list of error strings (empty = valid)."""
        errors: list[str] = []

        # Check odometer monotonicity: new reading should not be less than max for this VIN
        max_odometer_result = self.session.exec(
            select(func.max(MileageReadingDB.odometer)).where(MileageReadingDB.vin == vin)
        ).one_or_none()
        if max_odometer_result is not None and odometer < max_odometer_result:
            errors.append(
                f"Odometer monotonicity violation: new value {odometer} is less than "
                f"current max {max_odometer_result} for VIN {vin}"
            )

        # Check for duplicates: reading within 5 minutes of existing timestamp for same VIN
        window_start = timestamp - timedelta(minutes=5)
        window_end = timestamp + timedelta(minutes=5)
        duplicate_stmt = (
            select(MileageReadingDB)
            .where(MileageReadingDB.vin == vin)
            .where(MileageReadingDB.timestamp >= window_start)
            .where(MileageReadingDB.timestamp <= window_end)
        )
        duplicate = self.session.exec(duplicate_stmt).first()
        if duplicate is not None:
            errors.append(
                f"Duplicate reading detected: existing reading at {duplicate.timestamp} "
                f"is within 5 minutes of new timestamp {timestamp} for VIN {vin}"
            )

        return errors

    def add_reading_validated(
        self, vin: str, timestamp: datetime, odometer: float
    ) -> tuple[MileageReadingDB, list[str]]:
        """Validate and insert a reading. Always inserts (non-fatal pattern)."""
        errors = self.validate_reading(vin, timestamp, odometer)

        if errors:
            for error in errors:
                logger.warning("Data quality warning: %s", error)

        # Always insert the reading regardless of validation errors
        row = MileageReadingDB(vin=vin, timestamp=timestamp, odometer=odometer)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)

        return (row, errors)
