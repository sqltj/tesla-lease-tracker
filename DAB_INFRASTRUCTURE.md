# Declarative Unity Catalog Infrastructure (databricks.yml) - Free Tier

## Overview

The Tesla Lease Tracker uses **Databricks Asset Bundles (DAB)** to declaratively define Unity Catalog infrastructure optimized for **free tier**.

This configuration:
- ✅ Defines catalogs, schemas, and volumes declaratively in databricks.yml
- ✅ Maintains Infrastructure-as-Code principles
- ✅ Uses free tier UC features (catalogs, schemas, volumes)
- ✅ Keeps implementation pragmatic and cost-effective
- ⚠️ Single shared SQL warehouse for all jobs
- ⚠️ No Model Serving endpoints (forecast API runs in backend)
- ⚠️ Tables created via SQL notebooks (DAB table resources not yet supported)

**Free Tier Optimizations:**
- Minimal resource footprint (3 schemas, 2 volumes)
- Single warehouse (shared across all jobs)
- Lightweight jobs (no endpoints, no clusters)

---

## Architecture (Free Tier)

### Catalog Organization

Single unified `main` catalog with medallion-tier schemas and essential volumes:

```
Catalog: main
├── bronze_tesla_lease_tracker
│   ├── mileage_readings (table)
│   ├── artifacts (volume - ML models)
│   └── metadata (volume - ingestion state)
├── silver_tesla_lease_tracker
│   ├── mileage_readings_clean (table)
│   └── forecast_features (table)
└── gold_tesla_lease_tracker
    ├── daily_mileage_summary (table)
    └── lease_health_metrics (table)
```

### Design Principles for Free Tier

- **Minimal scope** — 3 schemas, 2 volumes, 5 tables
- **Single shared warehouse** — All jobs use one SQL warehouse (cost-effective)
- **No endpoints** — Forecast API runs in backend (not Model Serving)
- **Infrastructure-as-Code** — Catalogs/schemas/volumes in DAB, tables via SQL
- **Environment agnostic** — Single `main` catalog for dev/staging/prod

---

## DAB Variables (databricks.yml) - Free Tier

### Catalog & Schema Variables
```yaml
primary_catalog: "main"
bronze_schema: "bronze_tesla_lease_tracker"
silver_schema: "silver_tesla_lease_tracker"
gold_schema: "gold_tesla_lease_tracker"
```

### Volume Paths
```yaml
ml_artifacts_volume: "/Volumes/main/bronze_tesla_lease_tracker/artifacts"
metadata_volume: "/Volumes/main/bronze_tesla_lease_tracker/metadata"
```

These volumes store ML model artifacts and ingestion metadata respectively.

---

## Resources by Layer (Free Tier)

### Bronze Layer
**Schema:** `bronze_tesla_lease_tracker`
- **Table:** `mileage_readings` — Raw readings from Zerobus (vin, timestamp, odometer, _ingested_at)
- **Volume:** `artifacts/` — ML model artifacts
- **Volume:** `metadata/` — Ingestion state and checkpoints

### Silver Layer
**Schema:** `silver_tesla_lease_tracker`
- **Table:** `mileage_readings_clean` — Validated, deduplicated readings
- **Table:** `forecast_features` — ML model feature inputs (vin, window_start, daily_mileage, etc.)

### Gold Layer
**Schema:** `gold_tesla_lease_tracker`
- **Table:** `daily_mileage_summary` — Daily rollups by VIN for dashboards
- **Table:** `lease_health_metrics` — KPIs: mileage %, days remaining, overage risk, etc.

---

## Deployment

### Step 1: Validate Bundle

```bash
databricks bundle validate -t dev
```

**Expected output:** All resources valid, schema syntax correct

### Step 2: Preview Resources

```bash
databricks bundle validate -t dev --json | jq '.resources'
```

Shows all catalogs, schemas, volumes, and tables that will be created.

### Step 3: Deploy

```bash
# Deploy to dev
databricks bundle deploy -t dev --auto-approve

# Deploy to staging
databricks bundle deploy -t staging --auto-approve

# Deploy to prod-na
databricks bundle deploy -t prod-na --auto-approve
```

**What gets created:**
1. ✅ Catalog `main` (if not exists)
2. ✅ All 6 schemas
3. ✅ All 3 volumes
4. ✅ All 8 tables with proper clustering, properties, and comments

### Step 4: Verify in Databricks

```bash
# List catalogs
databricks sql execute "SHOW CATALOGS;"

# List schemas in main catalog
databricks sql execute "SHOW SCHEMAS IN main;"

# List tables in bronze schema
databricks sql execute "SHOW TABLES IN main.bronze_tesla_lease_tracker;"

# Check table properties
databricks sql execute "
SELECT
  table_catalog,
  table_schema,
  table_name,
  table_type,
  table_provider
FROM system.information_schema.tables
WHERE table_catalog = 'main'
ORDER BY table_schema, table_name;
"

# Check volumes
databricks sql execute "SHOW VOLUMES IN main.ml_features;"
```

---

## Migration from Imperative to Declarative

### Before (SQL Notebooks)
```sql
-- notebooks/setup/2_create_delta_table.sql
CREATE CATALOG IF NOT EXISTS main;
CREATE SCHEMA IF NOT EXISTS main.default;
CREATE TABLE IF NOT EXISTS main.default.mileage_readings (...)
-- Manual, hard to version control
```

### After (DAB Infrastructure)
```yaml
# databricks.yml
variables:
  primary_catalog: "main"
  bronze_schema: "bronze_tesla_lease_tracker"
resources:
  catalogs:
    primary_catalog:
      name: ${var.primary_catalog}
  schemas:
    bronze_schema:
      catalog_name: ${var.primary_catalog}
      name: ${var.bronze_schema}
  tables:
    mileage_readings_bronze:
      catalog_name: ${var.primary_catalog}
      schema_name: ${var.bronze_schema}
      columns: [...]
```

**Benefits:**
- Version-controlled in Git
- Reviewable via PR
- Reproducible across workspaces
- No manual SQL execution needed
- Full audit trail

---

## Jobs Updated to Use Variables

### ml_feature_pipeline
- **Before:** Hardcoded schema `schema: tesla_lease_tracker`
- **After:** Uses `schema: ${var.silver_schema}`

### ml_training_pipeline
- Reads from silver schema (auto-updated via variables)
- Writes to gold schema (auto-updated via variables)

### Monitoring Jobs
- anomaly_detection_alerts — queries monitoring schema
- backup_mileage_readings — writes to backups schema

---

## Optional: Production Grants

To restrict access in production, add grants to the catalog resource. Example:

```yaml
catalogs:
  primary_catalog:
    name: ${var.primary_catalog}
    grants:
      - principal: "data_engineers@company.com"
        privileges: ["USE_CATALOG", "CREATE_SCHEMA"]
      - principal: "analysts@company.com"
        privileges: ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
      - principal: "admins@company.com"
        privileges: ["USE_CATALOG", "CREATE_SCHEMA", "DROP"]
```

Apply only to production targets by using target-specific variables.

---

## Troubleshooting

### Resources not created after deploy

**Issue:** `databricks bundle deploy` completes but catalogs/schemas not visible

**Solution:**
```bash
# Check bundle status
databricks bundle validate -t dev

# Check resource state
databricks bundle show-resources -t dev

# Re-deploy with --no-skip-validation
databricks bundle deploy -t dev --no-skip-validation
```

### Conflicting schema names

**Issue:** Schema already exists in another catalog

**Solution:**
```bash
# Check existing catalogs
databricks sql execute "SHOW CATALOGS;"

# Check schemas in specific catalog
databricks sql execute "SHOW SCHEMAS IN main;"

# Drop conflicting schema (if safe)
databricks sql execute "DROP SCHEMA main.old_schema CASCADE;"
```

### Can't find tables after deploy

**Issue:** Tables created but not queryable

**Solution:**
```bash
# Verify table exists
databricks sql execute "SHOW TABLES IN main.bronze_tesla_lease_tracker;"

# Check table permissions
databricks sql execute "SHOW GRANTS ON TABLE main.bronze_tesla_lease_tracker.mileage_readings;"

# Verify current catalog
USE CATALOG main;
SHOW TABLES IN bronze_tesla_lease_tracker;
```

---

## Next Steps

1. **Deploy infrastructure:** `databricks bundle deploy -t dev`
2. **Verify resources:** Run SQL verification queries above
3. **Configure jobs:** ML pipeline automatically uses new schemas via variables
4. **Set up monitoring:** Enable anomaly detection job
5. **Add grants (optional):** Configure access control for production

---

## References

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/en/dev-tools/bundles/)
- [Unity Catalog Best Practices](https://docs.databricks.com/en/data-governance/unity-catalog/best-practices.html)
- [Medallion Architecture](https://www.databricks.com/blog/2022/06/24/applying-software-maturity-stages-to-machine-learning-project.html)
- [Delta Table Properties](https://docs.databricks.com/en/sql/language-manual/sql-ref-table-properties.html)
