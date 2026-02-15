-- Databricks notebook source
-- Monitoring Dashboard for Mileage Readings
-- Provides real-time insights into data quality and ingestion patterns

-- COMMAND ----------

PRINT "📊 Tesla Lease Tracker - Mileage Readings Monitoring Dashboard"

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 📈 Data Quality Metrics

-- COMMAND ----------

-- Total readings and unique vehicles
SELECT
    COUNT(*) as total_readings,
    COUNT(DISTINCT vin) as unique_vehicles,
    COUNT(DISTINCT CAST(timestamp AS DATE)) as days_with_data,
    MIN(timestamp) as earliest_reading,
    MAX(timestamp) as latest_reading,
    DATEDIFF(MAX(timestamp), MIN(timestamp)) as days_tracked
FROM main.default.mileage_readings;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🚗 Vehicles Being Tracked

-- COMMAND ----------

-- Readings per vehicle with statistics
SELECT
    vin,
    COUNT(*) as reading_count,
    COUNT(DISTINCT CAST(timestamp AS DATE)) as days_tracked,
    MIN(timestamp) as first_reading,
    MAX(timestamp) as last_reading,
    MIN(odometer) as min_odometer,
    MAX(odometer) as max_odometer,
    MAX(odometer) - MIN(odometer) as total_miles_driven,
    ROUND((MAX(odometer) - MIN(odometer)) / NULLIF(COUNT(DISTINCT CAST(timestamp AS DATE)), 0), 1) as avg_miles_per_day
FROM main.default.mileage_readings
GROUP BY vin
ORDER BY reading_count DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 📅 Ingestion Pattern

-- COMMAND ----------

-- Readings by date to identify ingestion patterns
SELECT
    date_partition as reading_date,
    COUNT(*) as reading_count,
    COUNT(DISTINCT vin) as vehicle_count,
    ROUND(AVG(odometer), 1) as avg_odometer,
    ROUND(MIN(odometer), 1) as min_odometer,
    ROUND(MAX(odometer), 1) as max_odometer
FROM main.default.mileage_readings
GROUP BY date_partition
ORDER BY reading_date DESC
LIMIT 30;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## ⏰ Recent Activity (Last 7 Days)

-- COMMAND ----------

-- Last 7 days summary
WITH last_7_days AS (
    SELECT *
    FROM main.default.mileage_readings
    WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
)
SELECT
    COUNT(*) as recent_readings,
    COUNT(DISTINCT vin) as vehicles_active,
    ROUND(AVG(odometer), 1) as avg_odometer,
    MAX(timestamp) as last_sync,
    ROUND(
        (CURRENT_TIMESTAMP - MAX(timestamp)) / 3600,
        1
    ) as hours_since_last_sync
FROM last_7_days;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 🔍 Data Validation Checks

-- COMMAND ----------

-- Check for data quality issues
SELECT
    'Missing VIN values' as check_type,
    COUNT(*) as issue_count
FROM main.default.mileage_readings
WHERE vin IS NULL OR vin = ''

UNION ALL

SELECT
    'Invalid timestamps (future dates)',
    COUNT(*)
FROM main.default.mileage_readings
WHERE timestamp > CURRENT_TIMESTAMP

UNION ALL

SELECT
    'Negative odometer values',
    COUNT(*)
FROM main.default.mileage_readings
WHERE odometer < 0

UNION ALL

SELECT
    'Duplicate readings (same VIN + timestamp)',
    COUNT(*) - COUNT(DISTINCT (vin, timestamp))
FROM main.default.mileage_readings;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 💾 Storage Statistics

-- COMMAND ----------

-- Table storage information
DESCRIBE DETAIL main.default.mileage_readings;

-- COMMAND ----------

-- Partition statistics
SELECT
    date_partition,
    COUNT(*) as record_count,
    SUM(LENGTH(CAST(vin AS STRING))) as vin_bytes,
    SUM(8) as timestamp_bytes,
    SUM(8) as odometer_bytes
FROM main.default.mileage_readings
GROUP BY date_partition
ORDER BY date_partition DESC
LIMIT 30;

-- COMMAND ----------

PRINT "✅ Monitoring dashboard complete!"
PRINT "Tip: Pin these queries to a Databricks dashboard for continuous monitoring"
