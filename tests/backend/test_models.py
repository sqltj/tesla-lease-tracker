from datetime import date, datetime

import pytest
from pydantic import ValidationError

from tesla_lease_tracker.backend.models import (
    AppData,
    LeaseConfig,
    LeaseConfigIn,
    MileageReading,
)


def make_valid_input(**overrides) -> dict:
    defaults = dict(
        vin="5YJ3E1EA1NF123456",
        lease_start_date=date(2024, 1, 1),
        lease_end_date=date(2027, 1, 1),
        mileage_limit=36000,
        start_odometer=0.0,
    )
    defaults.update(overrides)
    return defaults


class TestLeaseConfigIn:
    def test_valid_construction(self):
        cfg = LeaseConfigIn(**make_valid_input())
        assert cfg.vin == "5YJ3E1EA1NF123456"
        assert cfg.mileage_limit == 36000

    def test_vin_rejects_I(self):
        with pytest.raises(ValidationError, match="I, O, Q not allowed"):
            LeaseConfigIn(**make_valid_input(vin="5YJ3E1IA1NF123456"))

    def test_vin_rejects_O(self):
        with pytest.raises(ValidationError, match="I, O, Q not allowed"):
            LeaseConfigIn(**make_valid_input(vin="5YJ3E1OA1NF123456"))

    def test_vin_rejects_Q(self):
        with pytest.raises(ValidationError, match="I, O, Q not allowed"):
            LeaseConfigIn(**make_valid_input(vin="5YJ3E1QA1NF123456"))

    def test_vin_normalizes_lowercase(self):
        cfg = LeaseConfigIn(**make_valid_input(vin="5yj3e1ea1nf123456"))
        assert cfg.vin == "5YJ3E1EA1NF123456"

    def test_vin_wrong_length(self):
        with pytest.raises(ValidationError):
            LeaseConfigIn(**make_valid_input(vin="SHORT"))

    def test_mileage_limit_must_be_positive(self):
        with pytest.raises(ValidationError):
            LeaseConfigIn(**make_valid_input(mileage_limit=0))

    def test_start_odometer_allows_zero(self):
        cfg = LeaseConfigIn(**make_valid_input(start_odometer=0))
        assert cfg.start_odometer == 0

    def test_start_odometer_rejects_negative(self):
        with pytest.raises(ValidationError):
            LeaseConfigIn(**make_valid_input(start_odometer=-1))

    def test_date_ordering(self):
        with pytest.raises(ValidationError, match="before"):
            LeaseConfigIn(**make_valid_input(
                lease_start_date=date(2027, 1, 1),
                lease_end_date=date(2024, 1, 1),
            ))

    def test_same_dates_rejected(self):
        with pytest.raises(ValidationError, match="before"):
            LeaseConfigIn(**make_valid_input(
                lease_start_date=date(2024, 1, 1),
                lease_end_date=date(2024, 1, 1),
            ))


class TestRoundTrip:
    def test_lease_config_serialization(self):
        cfg = LeaseConfig(**make_valid_input())
        json_str = cfg.model_dump_json()
        restored = LeaseConfig.model_validate_json(json_str)
        assert restored.vin == cfg.vin
        assert restored.mileage_limit == cfg.mileage_limit

    def test_mileage_reading_serialization(self):
        reading = MileageReading(timestamp=datetime(2024, 6, 1, 12, 0), odometer=15000.5)
        json_str = reading.model_dump_json()
        restored = MileageReading.model_validate_json(json_str)
        assert restored.odometer == reading.odometer

    def test_app_data_defaults(self):
        data = AppData()
        assert data.lease_config is None
        assert data.readings == []
        assert data.last_sync is None

    def test_app_data_full_roundtrip(self):
        data = AppData(
            lease_config=LeaseConfig(**make_valid_input()),
            readings=[
                MileageReading(timestamp=datetime(2024, 3, 1), odometer=1000),
                MileageReading(timestamp=datetime(2024, 4, 1), odometer=2000),
            ],
        )
        json_str = data.model_dump_json()
        restored = AppData.model_validate_json(json_str)
        assert restored.lease_config is not None
        assert restored.lease_config.vin == "5YJ3E1EA1NF123456"
        assert len(restored.readings) == 2
