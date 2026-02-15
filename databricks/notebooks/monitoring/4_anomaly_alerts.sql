-- Databricks notebook source
-- Phase 3: Anomaly Detection and Alert Rules
-- Monitors data ingestion patterns and raises alerts for anomalies

-- COMMAND ----------

PRINT "🚨 Tesla Lease Tracker - Anomaly Detection and Alerts"

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Alert Rule 1: No Readings in 24 Hours

-- COMMAND ----------

-- Check for vehicles with no new readings in the last 24 hours
WITH recent_vehicles AS (
    SELECT DISTINCT vin FROM main.default.mileage_readings
    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 24 HOUR
),
all_tracked_vehicles AS (
    SELECT DISTINCT vin FROM main.default.mileage_readings
    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 7 DAY
)
SELECT
    atv.vin as vehicle_id,
    MAX(mr.timestamp) as last_reading_time,
    ROUND(
        (CURRENT_TIMESTAMP - MAX(mr.timestamp)) / 3600,
        1
    ) as hours_since_reading,
    CASE
        WHEN (CURRENT_TIMESTAMP - MAX(mr.timestamp)) > INTERVAL 48 HOUR THEN 'CRITICAL'
        WHEN (CURRENT_TIMESTAMP - MAX(mr.timestamp)) > INTERVAL 24 HOUR THEN 'WARNING'
        ELSE 'OK'
    END as alert_status
FROM all_tracked_vehicles atv
LEFT JOIN recent_vehicles rv ON atv.vin = rv.vin
LEFT JOIN main.default.mileage_readings mr ON atv.vin = mr.vin
WHERE rv.vin IS NULL  -- Vehicle not in last 24 hours
GROUP BY atv.vin
ORDER BY hours_since_reading DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Alert Rule 2: Impossible Odometer Values

-- COMMAND ----------

-- Detect negative odometer changes (impossible in real world)
WITH readings_with_lag AS (
    SELECT
        vin,
        timestamp,
        odometer,
        LAG(odometer) OVER (PARTITION BY vin ORDER BY timestamp) as prev_odometer,
        odometer - LAG(odometer) OVER (PARTITION BY vin ORDER BY timestamp) as odometer_delta
    FROM main.default.mileage_readings
    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 7 DAY
)
SELECT
    vin,
    timestamp,
    prev_odometer,
    odometer,
    odometer_delta,
    CASE
        WHEN odometer_delta < 0 THEN 'CRITICAL - Negative mileage'
        WHEN odometer_delta > 5000 THEN 'WARNING - Extreme jump'
        ELSE 'OK'
    END as alert_type
FROM readings_with_lag
WHERE odometer_delta IS NOT NULL AND (odometer_delta < 0 OR odometer_delta > 5000)
ORDER BY timestamp DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Alert Rule 3: Data Quality Issues

-- COMMAND ----------

-- Detect data quality anomalies
SELECT
    CURRENT_TIMESTAMP as check_timestamp,
    alert_type,
    COUNT(*) as issue_count
FROM (
    SELECT 'NULL VIN' as alert_type FROM main.default.mileage_readings WHERE vin IS NULL
    UNION ALL
    SELECT 'NULL TIMESTAMP' FROM main.default.mileage_readings WHERE timestamp IS NULL
    UNION ALL
    SELECT 'NULL ODOMETER' FROM main.default.mileage_readings WHERE odometer IS NULL
    UNION ALL
    SELECT 'NEGATIVE ODOMETER' FROM main.default.mileage_readings WHERE odometer < 0
    UNION ALL
    SELECT 'FUTURE TIMESTAMP' FROM main.default.mileage_readings WHERE timestamp > CURRENT_TIMESTAMP
    UNION ALL
    SELECT 'DUPLICATE READING'
    FROM main.default.mileage_readings
    GROUP BY vin, timestamp
    HAVING COUNT(*) > 1
)
GROUP BY alert_type
HAVING COUNT(*) > 0
ORDER BY issue_count DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Alert Rule 4: Ingestion Rate Anomaly

-- COMMAND ----------

-- Monitor ingestion rate - alert if significantly lower than baseline
WITH hourly_ingestion AS (
    SELECT
        DATE_TRUNC('HOUR', timestamp) as hour,
        COUNT(*) as reading_count
    FROM main.default.mileage_readings
    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 7 DAY
    GROUP BY DATE_TRUNC('HOUR', timestamp)
),
stats AS (
    SELECT
        AVG(reading_count) as avg_readings_per_hour,
        STDDEV(reading_count) as stddev_readings,
        MIN(reading_count) as min_readings,
        MAX(reading_count) as max_readings
    FROM hourly_ingestion
)
SELECT
    hi.hour,
    hi.reading_count,
    ROUND(s.avg_readings_per_hour, 1) as expected_avg,
    CASE
        WHEN hi.reading_count < (s.avg_readings_per_hour - 2 * s.stddev_readings) THEN 'CRITICAL - Well below baseline'
        WHEN hi.reading_count < (s.avg_readings_per_hour - s.stddev_readings) THEN 'WARNING - Below baseline'
        ELSE 'OK'
    END as alert_status
FROM hourly_ingestion hi
CROSS JOIN stats s
WHERE hi.hour >= CURRENT_TIMESTAMP - INTERVAL 24 HOUR
ORDER BY hi.hour DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Setting Up SQL Alerts in Databricks

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Option 1: Databricks SQL Alerts (Recommended)
-- MAGIC
-- MAGIC 1. Go to Databricks SQL workspace
-- MAGIC 2. Create a new alert query:
-- MAGIC    ```sql
-- MAGIC    SELECT COUNT(*) as issue_count
-- MAGIC    FROM main.default.mileage_readings
-- MAGIC    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL 24 HOUR
-- MAGIC    HAVING COUNT(*) = 0
-- MAGIC    ```
-- MAGIC 3. Set trigger: "When result count is not empty"
-- MAGIC 4. Set notification: Email/Slack
-- MAGIC
-- MAGIC ### Option 2: Scheduled Job with Notification
-- MAGIC
-- MAGIC Add to `databricks.yml`:
-- MAGIC ```yaml
-- MAGIC resources:
-- MAGIC   jobs:
-- MAGIC     alert_data_quality:
-- MAGIC       name: "Tesla Lease Tracker - Data Quality Alerts"
-- MAGIC       schedule:
-- MAGIC         quartz_cron_expression: "0 */30 * * * ?"  # Every 30 minutes
-- MAGIC       tasks:
-- MAGIC         - task_key: check_anomalies
-- MAGIC           notebook_task:
-- MAGIC             notebook_path: /path/to/4_anomaly_alerts
-- MAGIC           job_cluster_key: alert_cluster
-- MAGIC       notifications:
-- MAGIC         on_failure:
-- MAGIC           - email_address: "team@company.com"
-- MAGIC ```

-- COMMAND ----------

PRINT "✅ Anomaly detection queries ready!"
PRINT "Next: Set up alerts in Databricks SQL or schedule job"
