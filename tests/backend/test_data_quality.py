from datetime import datetime, timedelta

from tests.backend.conftest import SAMPLE_VIN


class TestOdometerMonotonicity:
    def test_backward_odometer_detected(self, mileage_repo):
        """Decreasing odometer flagged as validation error."""
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=datetime(2024, 1, 1), odometer=1000.0)
        errors = mileage_repo.validate_reading(SAMPLE_VIN, datetime(2024, 1, 2), 900.0)
        assert len(errors) > 0
        assert any("monotonicity" in e.lower() or "decrease" in e.lower() for e in errors)

    def test_increasing_odometer_valid(self, mileage_repo):
        """Increasing odometer passes validation."""
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=datetime(2024, 1, 1), odometer=1000.0)
        errors = mileage_repo.validate_reading(SAMPLE_VIN, datetime(2024, 1, 2), 1100.0)
        assert len(errors) == 0

    def test_first_reading_always_valid(self, mileage_repo):
        """First reading for a VIN has no previous to compare."""
        errors = mileage_repo.validate_reading(SAMPLE_VIN, datetime(2024, 1, 1), 500.0)
        assert len(errors) == 0


class TestDuplicateDetection:
    def test_duplicate_within_window(self, mileage_repo):
        """Reading within 5 minutes flagged as duplicate."""
        ts = datetime(2024, 3, 1, 10, 0, 0)
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=ts, odometer=1500.0)
        errors = mileage_repo.validate_reading(SAMPLE_VIN, ts + timedelta(minutes=2), 1510.0)
        assert any("duplicate" in e.lower() for e in errors)

    def test_not_duplicate_outside_window(self, mileage_repo):
        """Reading outside 5 minutes not flagged."""
        ts = datetime(2024, 3, 1, 10, 0, 0)
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=ts, odometer=1500.0)
        errors = mileage_repo.validate_reading(SAMPLE_VIN, ts + timedelta(minutes=10), 1510.0)
        assert not any("duplicate" in e.lower() for e in errors)


class TestValidatedInsert:
    def test_valid_reading_inserted(self, mileage_repo):
        """Clean reading inserted with no errors."""
        record, errors = mileage_repo.add_reading_validated(
            vin=SAMPLE_VIN, timestamp=datetime(2024, 1, 1), odometer=1000.0
        )
        assert record is not None
        assert record.odometer == 1000.0
        assert len(errors) == 0

    def test_invalid_reading_still_inserted(self, mileage_repo):
        """Invalid reading inserted anyway (non-fatal pattern)."""
        mileage_repo.add_reading(vin=SAMPLE_VIN, timestamp=datetime(2024, 1, 1), odometer=1000.0)
        record, errors = mileage_repo.add_reading_validated(
            vin=SAMPLE_VIN, timestamp=datetime(2024, 1, 2), odometer=900.0
        )
        assert record is not None  # Still inserted
        assert record.odometer == 900.0
        assert len(errors) > 0  # But flagged
        assert mileage_repo.count() == 2  # Both readings exist
