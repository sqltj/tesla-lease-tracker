# Databricks notebook source
# COMMAND ----------
# Create Lakebase instance for Tesla Lease Tracker

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import EndpointConfPair, GetWarehouseResponse
import time

# COMMAND ----------

print("🔧 Tesla Lease Tracker - Setting up Lakebase Instance")
print("=" * 60)

ws = WorkspaceClient()

instance_name = "tesla-lease-tracker"
capacity = "SMALL"

# COMMAND ----------

print(f"\n1. Checking for existing Lakebase instance: {instance_name}")

try:
    # List existing Lakebase instances
    warehouses = ws.warehouses.list()
    existing = None

    for warehouse in warehouses:
        if warehouse.name == instance_name:
            existing = warehouse
            print(f"   ✓ Found existing instance: {warehouse.id}")
            print(f"   - Status: {warehouse.state}")
            print(f"   - Type: {warehouse.warehouse_type}")
            break

    if not existing:
        print(f"   → No existing instance found, creating new one...")

        # Create Lakebase (provisioned warehouse)
        warehouse_config = {
            "name": instance_name,
            "cluster_size": capacity,
            "warehouse_type": "PROVISIONED",
            "auto_stop_mins": 15,
            "enable_serverless_compute": False
        }

        response = ws.warehouses.create(**warehouse_config)
        instance_id = response.id

        print(f"   ✓ Lakebase instance created: {instance_id}")
        print(f"   → Waiting for instance to start (this may take 2-3 minutes)...")

        # Wait for instance to be ready
        max_retries = 60  # 5 minutes with 5-second intervals
        for i in range(max_retries):
            warehouse = ws.warehouses.get(instance_id)
            if warehouse.state == "RUNNING":
                print(f"   ✓ Instance is running!")
                break
            elif warehouse.state in ["STOPPED", "UNKNOWN"]:
                print(f"   → Status: {warehouse.state}... waiting ({i * 5}s)")
                time.sleep(5)
            else:
                print(f"   → Status: {warehouse.state}... waiting ({i * 5}s)")
                time.sleep(5)
        else:
            print(f"   ⚠ Instance did not reach RUNNING state within timeout")
            print(f"   → Check Databricks UI to monitor progress")

except Exception as e:
    print(f"   ❌ Error: {e}")
    raise

# COMMAND ----------

print("\n" + "=" * 60)
print("✅ Lakebase instance setup complete!")
print("=" * 60)
print(f"\nNext: Create Delta table for mileage analytics")
