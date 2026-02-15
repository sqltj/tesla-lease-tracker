#!/usr/bin/env python3
"""Seed local dev database with sample Tesla lease data.

Usage:
    uv run python scripts/seed_local.py             # Seed sample data
    uv run python scripts/seed_local.py --force     # Force reset (if data exists)

Requires the dev server to be running (uv run apx dev start).
Calls the /api/seed-local-data endpoint to populate sample data.
"""

import argparse
import sys

import requests


def seed_database(force: bool = False) -> None:
    """Seed the local database with sample lease and mileage data."""
    base_url = "http://127.0.0.1:9000"
    endpoint = "/api/seed-local-data"

    url = f"{base_url}{endpoint}"
    if force:
        url += "?force=true"

    try:
        print("Connecting to dev server at http://127.0.0.1:9000...")
        response = requests.post(url, timeout=5)

        if response.status_code == 200:
            result = response.json()
            print("\n✅ Seed successful!")
            print(f"   VIN: {result['lease_vin']}")
            print(f"   Readings: {result['readings_count']}")
            print(f"   Odometer: {result['odometer_range']}")
            print("\n📊 Refresh your browser to see the populated dashboard")
            return

        elif response.status_code == 409 and not force:
            print("⚠️  Database already contains lease data")
            print("\nRun with --force to reset:")
            print("  uv run python scripts/seed_local.py --force")
            sys.exit(1)

        elif response.status_code == 403:
            print("❌ Seed endpoint only available in dev mode")
            print("\nMake sure dev server is running:")
            print("  uv run apx dev start")
            sys.exit(1)

        else:
            print(f"❌ Seed failed: {response.status_code}")
            print(response.text)
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to dev server")
        print("\nMake sure the dev server is running:")
        print("  uv run apx dev start")
        print("\nThen run seed script:")
        print("  uv run python scripts/seed_local.py")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed local database with sample Tesla lease data"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reset (truncate existing data before seeding)",
    )
    args = parser.parse_args()
    seed_database(force=args.force)
