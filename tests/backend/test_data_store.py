from datetime import date, datetime

from tesla_lease_tracker.backend.data_store import DataStore
from tesla_lease_tracker.backend.models import LeaseConfig, MileageReading


def make_config():
    return LeaseConfig(
        vin="5YJ3E1EA1NF123456",
        lease_start_date=date(2024, 1, 1),
        lease_end_date=date(2027, 1, 1),
        mileage_limit=36000,
        start_odometer=0.0,
    )


class TestDataStore:
    def test_starts_empty(self, tmp_path):
        store = DataStore(tmp_path / "data.json")
        assert store.data.lease_config is None
        assert store.data.readings == []

    def test_save_and_reload(self, tmp_path):
        path = tmp_path / "data.json"
        store = DataStore(path)
        store.data.lease_config = make_config()
        store.data.readings.append(
            MileageReading(timestamp=datetime(2024, 3, 1), odometer=1500)
        )
        store.save()

        store2 = DataStore(path)
        assert store2.data.lease_config is not None
        assert store2.data.lease_config.vin == "5YJ3E1EA1NF123456"
        assert len(store2.data.readings) == 1
        assert store2.data.readings[0].odometer == 1500

    def test_corrupt_json_falls_back(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text("{invalid json!!")
        store = DataStore(path)
        assert store.data.lease_config is None
        assert store.data.readings == []

    def test_nested_directory_creation(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "data.json"
        store = DataStore(path)
        store.data.lease_config = make_config()
        store.save()
        assert path.exists()

    def test_multiple_readings_persist(self, tmp_path):
        path = tmp_path / "data.json"
        store = DataStore(path)
        for i in range(10):
            store.data.readings.append(
                MileageReading(
                    timestamp=datetime(2024, 1, 1 + i),
                    odometer=10000.0 + i * 500,
                )
            )
        store.save()

        store2 = DataStore(path)
        assert len(store2.data.readings) == 10
