from datetime import date

import pytest
from sqlalchemy import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from tesla_lease_tracker.backend.db_models import (
    AppStateDB,
    LeaseConfigDB,
    MileageReadingDB,
)
from tesla_lease_tracker.backend.repositories import LeaseRepository, MileageRepository


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def lease_repo(db_session):
    return LeaseRepository(db_session)


@pytest.fixture
def mileage_repo(db_session):
    return MileageRepository(db_session)


SAMPLE_VIN = "5YJ3E1EA1NF123456"


def make_lease_in():
    from tesla_lease_tracker.backend.models import LeaseConfigIn

    return LeaseConfigIn(
        vin=SAMPLE_VIN,
        lease_start_date=date(2024, 1, 1),
        lease_end_date=date(2027, 1, 1),
        mileage_limit=36000,
        start_odometer=0.0,
    )
