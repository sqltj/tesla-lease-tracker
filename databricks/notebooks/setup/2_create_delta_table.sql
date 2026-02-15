-- Databricks notebook source
-- Create mileage_readings Delta table for Zerobus streaming analytics

-- COMMAND ----------

PRINT "🔧 Tesla Lease Tracker - Setting up Delta Table for Analytics"

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS main;

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS main.default;

-- COMMAND ----------

CREATE TABLE IF NOT EXISTS main.default.mileage_readings (
    vin STRING NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    odometer DOUBLE NOT NULL
)
USING DELTA
TBLPROPERTIES (
    'description' = 'Mileage readings streamed from Tesla Fleet API via Zerobus',
    'owner' = 'tesla-lease-tracker',
    'created_by' = 'post_deploy_setup'
);

-- COMMAND ----------

-- Add comment to table
COMMENT ON TABLE main.default.mileage_readings IS
  'Mileage readings streamed from Tesla Fleet API via Zerobus for analytics and reporting';

-- COMMAND ----------

-- Create index for common query patterns (VIN + timestamp)
CREATE INDEX IF NOT EXISTS idx_vin_timestamp
  ON main.default.mileage_readings (vin, timestamp);

-- COMMAND ----------

-- Verify table was created
SELECT
    COUNT(*) as table_rows,
    COUNT(DISTINCT vin) as unique_vins,
    MIN(timestamp) as earliest_reading,
    MAX(timestamp) as latest_reading
FROM main.default.mileage_readings;

-- COMMAND ----------

PRINT "✅ Delta table setup complete!"
PRINT "Table: main.default.mileage_readings"
PRINT "Status: Ready for Zerobus streaming"
