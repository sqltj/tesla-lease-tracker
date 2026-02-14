from datetime import datetime

from sqlmodel import Session, select

from .db_models import AppStateDB, LeaseConfigDB, MileageReadingDB
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
        now = datetime.utcnow()
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
