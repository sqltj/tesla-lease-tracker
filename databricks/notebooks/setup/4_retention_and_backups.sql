-- Databricks notebook source
-- Phase 3: Retention Policies and Backup Configuration for Tesla Lease Tracker

-- COMMAND ----------

PRINT "🔄 Tesla Lease Tracker - Setting up Retention and Backup Policies"

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Retention Policy Configuration

-- COMMAND ----------

-- Enable Delta table time travel for backup/recovery (30 days retention)
ALTER TABLE main.default.mileage_readings
SET TBLPROPERTIES (
    'delta.logRetentionDays' = '30',
    'delta.deletedFileRetentionDays' = '7'
);

PRINT "✓ Delta time travel enabled (30-day retention)"

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Vacuum Configuration

-- COMMAND ----------

-- Configure vacuum to clean up old files after 7 days
-- This is non-destructive and respects time travel retention
-- Run this periodically (e.g., weekly) to optimize storage

PRINT "ℹ️ Vacuum Configuration:"
PRINT "   Run periodically to optimize storage:"
PRINT "   VACUUM main.default.mileage_readings RETAIN 168 HOURS"
PRINT "   (This keeps 7 days of history for time travel/recovery)"

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Backup Strategy

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Delta Backup Best Practices
-- MAGIC
-- MAGIC 1. **Time Travel (Default)**
-- MAGIC    - Restore to any point in last 30 days
-- MAGIC    - `SELECT * FROM main.default.mileage_readings TIMESTAMP AS OF '2026-01-15'`
-- MAGIC    - No extra storage cost (included in delta logs)
-- MAGIC
-- MAGIC 2. **Clone for Point-in-Time Snapshots**
-- MAGIC    - `CREATE TABLE main.backups.mileage_readings_2026_02_01 CLONE main.default.mileage_readings`
-- MAGIC    - Useful for compliance and audit trails
-- MAGIC    - Can be on separate cluster/workspace
-- MAGIC
-- MAGIC 3. **Change Data Feed (CDC)**
-- MAGIC    - Enabled in Phase 2
-- MAGIC    - Capture all inserts, updates, deletes
-- MAGIC    - Stream to external system via Zerobus/Kafka

-- COMMAND ----------

-- Create backup schema for point-in-time snapshots
CREATE SCHEMA IF NOT EXISTS main.backups
COMMENT 'Point-in-time backup snapshots of production tables';

PRINT "✓ Backup schema created: main.backups"

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Automated Backup Job (Optional)

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Schedule Weekly Backups
-- MAGIC
-- MAGIC To automate weekly backups, add this job to `databricks.yml`:
-- MAGIC
-- MAGIC ```yaml
-- MAGIC resources:
-- MAGIC   jobs:
-- MAGIC     backup_mileage_readings:
-- MAGIC       name: "Tesla Lease Tracker - Weekly Backup"
-- MAGIC       schedule:
-- MAGIC         quartz_cron_expression: "0 0 1 ? * SUN"  # Every Sunday at 1 AM
-- MAGIC         timezone_id: "UTC"
-- MAGIC       tasks:
-- MAGIC         - task_key: backup
-- MAGIC           notebook_task:
-- MAGIC             notebook_path: /path/to/backup_notebook
-- MAGIC           job_cluster_key: backup_cluster
-- MAGIC ```

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Data Retention Guidelines

-- COMMAND ----------

-- Summary of retention strategy
SELECT
    'Mileage Readings' as table_name,
    'main.default.mileage_readings' as table_path,
    '30 days' as time_travel_window,
    '7 days' as deleted_file_retention,
    'Liquid Clustering (vin, timestamp)' as optimization,
    'CDC enabled' as capabilities
UNION ALL
SELECT
    'Backups',
    'main.backups.mileage_readings_*',
    'Manual snapshots',
    'N/A',
    'On-demand clones',
    'Point-in-time restore'
;

-- COMMAND ----------

PRINT "✅ Retention and backup configuration complete!"
PRINT ""
PRINT "Next steps:"
PRINT "1. Review time travel and vacuum strategies"
PRINT "2. Set up automated backup job in databricks.yml (optional)"
PRINT "3. Monitor table storage usage"
