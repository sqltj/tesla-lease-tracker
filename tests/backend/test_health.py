from datetime import date, datetime

from tesla_lease_tracker.backend.models import HealthOut, LeaseConfig, MileageReading, AppData


class TestHealthOut:
    def test_basic_construction(self):
        h = HealthOut(
            status="ok",
            version="0.1.0",
            has_lease=False,
            readings_count=0,
            last_sync=None,
        )
        assert h.status == "ok"
        assert h.readings_count == 0

    def test_with_data(self):
        h = HealthOut(
            status="ok",
            version="0.1.0",
            has_lease=True,
            readings_count=42,
            last_sync=datetime(2024, 6, 15, 10, 30),
        )
        assert h.has_lease is True
        assert h.readings_count == 42
        assert h.last_sync is not None

    def test_serialization_roundtrip(self):
        h = HealthOut(
            status="ok",
            version="0.1.0",
            has_lease=True,
            readings_count=5,
            last_sync=datetime(2024, 6, 15),
        )
        json_str = h.model_dump_json()
        restored = HealthOut.model_validate_json(json_str)
        assert restored.status == h.status
        assert restored.readings_count == h.readings_count
