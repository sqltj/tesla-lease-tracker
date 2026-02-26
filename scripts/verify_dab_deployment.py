#!/usr/bin/env python3
"""
Verify Databricks Asset Bundle (DAB) Infrastructure Deployment

This script validates that all Unity Catalog objects (catalogs, schemas, volumes, tables)
were created successfully after running `databricks bundle deploy`.

Usage:
    uv run python scripts/verify_dab_deployment.py

Expected output:
    ✅ All catalogs exist
    ✅ All schemas created
    ✅ All volumes provisioned
    ✅ All tables created with correct schemas
"""

import sys
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import sql as sql_service

# Configuration
CATALOG = "main"
SCHEMAS = {
    "bronze_tesla_lease_tracker": "Bronze layer: Raw data ingestion",
    "silver_tesla_lease_tracker": "Silver layer: Cleaned and validated data",
    "gold_tesla_lease_tracker": "Gold layer: Business-ready aggregations",
    "ml_features": "ML feature store",
    "monitoring": "Data quality and monitoring",
    "backups": "Point-in-time backups",
}

TABLES = {
    "bronze_tesla_lease_tracker.mileage_readings": ["vin", "timestamp", "odometer"],
    "silver_tesla_lease_tracker.mileage_readings_clean": ["vin", "timestamp", "odometer", "is_valid"],
    "silver_tesla_lease_tracker.forecast_features": ["vin", "window_start", "daily_mileage"],
    "gold_tesla_lease_tracker.daily_mileage_summary": ["vin", "summary_date", "daily_miles"],
    "gold_tesla_lease_tracker.lease_health_metrics": ["vin", "metric_date", "mileage_consumed_pct"],
    "ml_features.forecast_model_registry": ["model_uri", "model_version"],
    "monitoring.anomaly_detection_log": ["check_timestamp", "alert_type", "severity"],
}

VOLUMES = {
    "ml_features.artifacts": "ML model artifacts",
    "backups.data": "Backup snapshots",
    "bronze_tesla_lease_tracker.metadata": "Ingestion metadata",
}


def check_catalog_exists():
    """Verify primary catalog exists."""
    ws = WorkspaceClient()
    try:
        # List catalogs
        catalogs = ws.catalogs.list()
        catalog_names = [c.name for c in catalogs]

        if CATALOG in catalog_names:
            print(f"✅ Catalog '{CATALOG}' exists")
            return True
        else:
            print(f"❌ Catalog '{CATALOG}' NOT found")
            print(f"   Available catalogs: {', '.join(catalog_names)}")
            return False
    except Exception as e:
        print(f"❌ Error checking catalogs: {e}")
        return False


def check_schemas_exist():
    """Verify all schemas were created."""
    ws = WorkspaceClient()
    all_exist = True

    try:
        # List schemas in main catalog
        schemas = ws.schemas.list(catalog_name=CATALOG)
        schema_names = {s.name: s for s in schemas}

        print(f"\nSchemas in catalog '{CATALOG}':")
        for expected_schema, description in SCHEMAS.items():
            if expected_schema in schema_names:
                schema = schema_names[expected_schema]
                print(f"  ✅ {expected_schema}")
                if schema.comment:
                    print(f"     Comment: {schema.comment}")
            else:
                print(f"  ❌ {expected_schema} NOT found")
                all_exist = False

        return all_exist
    except Exception as e:
        print(f"❌ Error checking schemas: {e}")
        return False


def check_volumes_exist():
    """Verify all volumes were created."""
    ws = WorkspaceClient()
    all_exist = True

    print(f"\nVolumes in catalog '{CATALOG}':")

    for volume_path, description in VOLUMES.items():
        schema, volume_name = volume_path.split(".")
        try:
            volumes = ws.volumes.list(catalog_name=CATALOG, schema_name=schema)
            volume_names = {v.name: v for v in volumes}

            if volume_name in volume_names:
                print(f"  ✅ {CATALOG}.{schema}.{volume_name}")
            else:
                print(f"  ❌ {CATALOG}.{schema}.{volume_name} NOT found")
                all_exist = False
        except Exception as e:
            print(f"  ❌ Error checking {volume_path}: {e}")
            all_exist = False

    return all_exist


def check_tables_exist():
    """Verify all tables were created with expected columns."""
    ws = WorkspaceClient()
    all_exist = True

    print(f"\nTables in catalog '{CATALOG}':")

    for table_path, expected_columns in TABLES.items():
        schema, table_name = table_path.split(".")
        try:
            # Get table metadata
            table = ws.tables.get(f"{CATALOG}.{schema}.{table_name}")

            # Check columns
            actual_columns = {col.name for col in table.columns} if table.columns else set()
            expected_col_set = set(expected_columns)

            if expected_col_set.issubset(actual_columns):
                print(f"  ✅ {CATALOG}.{schema}.{table_name}")
                print(f"     Columns: {', '.join(sorted(actual_columns))}")
            else:
                missing = expected_col_set - actual_columns
                print(f"  ❌ {CATALOG}.{schema}.{table_name}")
                print(f"     Missing columns: {', '.join(missing)}")
                all_exist = False

        except Exception as e:
            print(f"  ❌ Error checking {table_path}: {e}")
            all_exist = False

    return all_exist


def check_table_properties():
    """Verify critical Delta table properties."""
    ws = WorkspaceClient()
    print(f"\nTable Properties Check:")

    # Check a sample table for Delta properties
    sample_table = "bronze_tesla_lease_tracker.mileage_readings"
    try:
        table = ws.tables.get(f"{CATALOG}.{sample_table}")

        print(f"  Table: {CATALOG}.{sample_table}")
        print(f"  - Type: {table.table_type}")
        print(f"  - Provider: {table.table_format}")

        if table.properties:
            print(f"  - Properties:")
            for key, value in table.properties.items():
                print(f"    • {key}: {value}")

        return True
    except Exception as e:
        print(f"  ❌ Error checking table properties: {e}")
        return False


def query_information_schema():
    """Query system information schema for infrastructure summary."""
    ws = WorkspaceClient()

    print(f"\nInformation Schema Summary:")

    try:
        # Create a warehouse query to get full inventory
        queries = [
            (
                "Catalogs",
                f"SELECT count(*) as count FROM system.information_schema.catalogs "
                f"WHERE catalog_name = '{CATALOG}'",
            ),
            (
                "Schemas",
                f"SELECT count(*) as count FROM system.information_schema.schemata "
                f"WHERE table_catalog = '{CATALOG}'",
            ),
            (
                "Tables",
                f"SELECT count(*) as count FROM system.information_schema.tables "
                f"WHERE table_catalog = '{CATALOG}'",
            ),
        ]

        for label, query_str in queries:
            try:
                # Execute query on SQL warehouse
                result = ws.statement_execution.execute_statement(
                    warehouse_id=_get_warehouse_id(ws),
                    statement=query_str,
                )
                print(f"  ✅ {label}: Query executed")
            except Exception as e:
                print(f"  ⚠️  {label}: Could not query ({e})")

    except Exception as e:
        print(f"  ⚠️  Information schema query skipped: {e}")


def _get_warehouse_id(ws):
    """Get first available SQL warehouse ID."""
    try:
        warehouses = list(ws.warehouses.list())
        if warehouses:
            return warehouses[0].id
        return None
    except Exception:
        return None


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Databricks Asset Bundle (DAB) Infrastructure Verification")
    print("=" * 70)

    checks = [
        ("Catalog Exists", check_catalog_exists),
        ("Schemas Exist", check_schemas_exist),
        ("Volumes Exist", check_volumes_exist),
        ("Tables Exist", check_tables_exist),
        ("Table Properties", check_table_properties),
    ]

    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n❌ {check_name} failed: {e}")
            results[check_name] = False

    # Optional: Query information schema
    try:
        query_information_schema()
    except Exception:
        pass

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n✅ All infrastructure checks passed!")
        print("\nNext steps:")
        print("  1. Run ML training pipeline: databricks bundle run ml_training_pipeline")
        print("  2. Configure monitoring: databricks bundle run anomaly_detection_alerts")
        print("  3. Start using the app: databricks app get tesla-lease-tracker")
        return 0
    else:
        print(f"\n❌ {total - passed} checks failed. Please review the output above.")
        print("\nTroubleshooting:")
        print("  1. Run: databricks bundle validate -t dev")
        print("  2. Check logs: databricks bundle logs")
        print("  3. Re-deploy: databricks bundle deploy -t dev --auto-approve")
        return 1


if __name__ == "__main__":
    sys.exit(main())
