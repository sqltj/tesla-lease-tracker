"""One-time migration: copy data from JSON file to Lakebase (PostgreSQL).

Usage:
    uv run python scripts/migrate_json_to_lakebase.py [--json-path data/app_data.json]

Requires the database to be accessible (set APX_DEV_DB_PORT for local dev,
or run in a Databricks environment for production).
"""

import argparse
import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tesla_lease_tracker.backend.config import AppConfig
from tesla_lease_tracker.backend.data_store import DataStore
from tesla_lease_tracker.backend.db_models import (
    AppStateDB,
    LeaseConfigDB,
    MileageReadingDB,
)
from tesla_lease_tracker.backend.runtime import Runtime


def migrate(json_path: str) -> None:
    path = Path(json_path)
    if not path.exists():
        print(f"JSON file not found: {path}")
        sys.exit(1)

    store = DataStore(path)
    data = store.data

    config = AppConfig(storage_mode="database")
    runtime = Runtime(config)

    print("Validating database connection...")
    runtime.validate_db()
    runtime.initialize_models()

    with runtime.get_session() as session:
        # Migrate lease config
        if data.lease_config:
            lc = data.lease_config
            row = LeaseConfigDB(
                vin=lc.vin,
                lease_start_date=lc.lease_start_date,
                lease_end_date=lc.lease_end_date,
                mileage_limit=lc.mileage_limit,
                start_odometer=lc.start_odometer,
                created_at=lc.created_at,
                updated_at=lc.updated_at,
            )
            session.add(row)
            print(f"Migrated lease config for VIN {lc.vin}")

        # Migrate mileage readings
        vin = data.lease_config.vin if data.lease_config else "UNKNOWN"
        for reading in data.readings:
            row = MileageReadingDB(
                vin=vin,
                timestamp=reading.timestamp,
                odometer=reading.odometer,
            )
            session.add(row)
        print(f"Migrated {len(data.readings)} mileage readings")

        # Migrate last_sync
        if data.last_sync:
            state = AppStateDB(last_sync=data.last_sync)
            session.add(state)
            print(f"Migrated last_sync: {data.last_sync}")

        session.commit()
        print("Migration complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate JSON data to Lakebase")
    parser.add_argument(
        "--json-path",
        default="data/app_data.json",
        help="Path to the JSON data file (default: data/app_data.json)",
    )
    args = parser.parse_args()
    migrate(args.json_path)
