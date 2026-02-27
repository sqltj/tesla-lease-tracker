#!/usr/bin/env python3
"""
Verify Databricks Asset Bundle deployment.

Checks that expected catalog, schemas, and volumes exist in the workspace
after running `databricks bundle deploy`.

Usage:
    uv run python scripts/verify_dab_deployment.py
"""

import sys


EXPECTED_CATALOG = "main"
EXPECTED_SCHEMAS = [
    "bronze_tesla_lease_tracker",
    "silver_tesla_lease_tracker",
    "gold_tesla_lease_tracker",
]
EXPECTED_VOLUMES = {
    "bronze_tesla_lease_tracker": ["metadata", "artifacts"],
}


def connect():
    """Create a WorkspaceClient and verify connectivity."""
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        print("FAIL: databricks-sdk is not installed. Install with: uv add databricks-sdk")
        sys.exit(1)

    try:
        ws = WorkspaceClient()
        # Quick connectivity check
        ws.current_user.me()
        return ws
    except Exception as exc:
        print(f"FAIL: Could not connect to Databricks workspace: {exc}")
        print()
        print("Ensure the Databricks CLI is authenticated:")
        print("  databricks auth login --host <workspace-url>")
        sys.exit(1)


def check_catalog(ws) -> bool:
    """Check that the expected catalog exists."""
    try:
        catalog_names = [c.name for c in ws.catalogs.list()]
    except Exception as exc:
        print(f"  FAIL: catalog '{EXPECTED_CATALOG}' -- error listing catalogs: {exc}")
        return False

    if EXPECTED_CATALOG in catalog_names:
        print(f"  PASS: catalog '{EXPECTED_CATALOG}' exists")
        return True
    else:
        print(f"  FAIL: catalog '{EXPECTED_CATALOG}' not found (available: {catalog_names})")
        return False


def check_schemas(ws) -> bool:
    """Check that expected schemas exist in the catalog."""
    try:
        schema_names = [s.name for s in ws.schemas.list(catalog_name=EXPECTED_CATALOG)]
    except Exception as exc:
        print(f"  FAIL: could not list schemas in '{EXPECTED_CATALOG}': {exc}")
        return False

    all_passed = True
    for schema in EXPECTED_SCHEMAS:
        if schema in schema_names:
            print(f"  PASS: schema '{EXPECTED_CATALOG}.{schema}' exists")
        else:
            print(f"  FAIL: schema '{EXPECTED_CATALOG}.{schema}' not found")
            all_passed = False

    return all_passed


def check_volumes(ws) -> bool:
    """Check that expected volumes exist in the appropriate schemas."""
    all_passed = True
    for schema_name, volume_names in EXPECTED_VOLUMES.items():
        try:
            existing_volumes = [
                v.name
                for v in ws.volumes.list(
                    catalog_name=EXPECTED_CATALOG,
                    schema_name=schema_name,
                )
            ]
        except Exception as exc:
            print(f"  FAIL: could not list volumes in '{EXPECTED_CATALOG}.{schema_name}': {exc}")
            all_passed = False
            continue

        for volume in volume_names:
            if volume in existing_volumes:
                print(f"  PASS: volume '{EXPECTED_CATALOG}.{schema_name}.{volume}' exists")
            else:
                print(f"  FAIL: volume '{EXPECTED_CATALOG}.{schema_name}.{volume}' not found")
                all_passed = False

    return all_passed


def main() -> int:
    """Run all deployment verification checks."""
    print("Verifying Databricks Asset Bundle deployment...")
    print()

    ws = connect()
    results = []

    print("[1/3] Checking catalog...")
    results.append(check_catalog(ws))
    print()

    print("[2/3] Checking schemas...")
    results.append(check_schemas(ws))
    print()

    print("[3/3] Checking volumes...")
    results.append(check_volumes(ws))
    print()

    if all(results):
        print("All checks passed.")
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"{failed} check(s) failed. Review output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
