from datetime import date, datetime

import pytest

from tesla_lease_tracker.backend.models import LeaseConfigIn
from tesla_lease_tracker.backend.repositories import LeaseRepository, MileageRepository

from .conftest import SAMPLE_VIN, make_lease_in


class TestLeaseRepository:
    def test_get_lease_config_empty(self, lease_repo):
        assert lease_repo.get_lease_config() is None

    def test_save_and_get_lease_config(self, lease_repo):
        lease_in = make_lease_in()
        result = lease_repo.save_lease_config(lease_in)

        assert result.vin == SAMPLE_VIN
        assert result.mileage_limit == 36000
        assert result.created_at is not None
        assert result.updated_at is not None

        fetched = lease_repo.get_lease_config()
        assert fetched is not None
        assert fetched.vin == SAMPLE_VIN

    def test_save_lease_config_upsert(self, lease_repo):
        lease_in = make_lease_in()
        first = lease_repo.save_lease_config(lease_in)

        updated_in = LeaseConfigIn(
            vin=SAMPLE_VIN,
            lease_start_date=date(2024, 1, 1),
            lease_end_date=date(2027, 1, 1),
            mileage_limit=45000,
            start_odometer=100.0,
        )
        second = lease_repo.save_lease_config(updated_in)

        assert second.mileage_limit == 45000
        assert second.start_odometer == 100.0
        assert second.created_at == first.created_at
        assert second.updated_at >= first.updated_at

    def test_get_last_sync_empty(self, lease_repo):
        assert lease_repo.get_last_sync() is None

    def test_set_and_get_last_sync(self, lease_repo):
        now = datetime(2024, 6, 15, 12, 0, 0)
        lease_repo.set_last_sync(now)
        assert lease_repo.get_last_sync() == now

    def test_set_last_sync_upsert(self, lease_repo):
        t1 = datetime(2024, 6, 15, 12, 0, 0)
        t2 = datetime(2024, 6, 16, 12, 0, 0)
        lease_repo.set_last_sync(t1)
        lease_repo.set_last_sync(t2)
        assert lease_repo.get_last_sync() == t2


class TestMileageRepository:
    def test_empty_readings(self, mileage_repo):
        assert mileage_repo.get_readings() == []
        assert mileage_repo.count() == 0

    def test_add_and_get_reading(self, mileage_repo):
        ts = datetime(2024, 3, 1, 10, 0, 0)
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=ts, odometer=1500.0)

        readings = mileage_repo.get_readings()
        assert len(readings) == 1
        assert readings[0].odometer == 1500.0
        assert readings[0].timestamp == ts
        assert mileage_repo.count() == 1

    def test_readings_ordered_by_timestamp(self, mileage_repo):
        ts1 = datetime(2024, 3, 1)
        ts2 = datetime(2024, 2, 1)
        ts3 = datetime(2024, 4, 1)
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=ts1, odometer=1500)
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=ts2, odometer=1000)
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=ts3, odometer=2000)

        readings = mileage_repo.get_readings()
        assert [r.odometer for r in readings] == [1000, 1500, 2000]

    def test_filter_by_vin(self, mileage_repo):
        ts = datetime(2024, 3, 1)
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=ts, odometer=1500)
        mileage_repo.add_reading(vin="5YJ3E1EA1NF999999", timestamp=ts, odometer=2000)

        readings = mileage_repo.get_readings(vin=SAMPLE_VIN)
        assert len(readings) == 1
        assert readings[0].odometer == 1500

    def test_count_multiple(self, mileage_repo):
        for i in range(5):
            mileage_repo.add_reading(
                vin=SAMPLE_VIN,
                timestamp=datetime(2024, 1, 1 + i),
                odometer=10000 + i * 500,
            )
        assert mileage_repo.count() == 5
