# Databricks notebook source
# MAGIC %md
# MAGIC # Silver: Forecast Features Streaming Table
# MAGIC
# MAGIC Computes ML-ready features from bronze mileage readings:
# MAGIC - lease_miles: miles driven since lease start (odometer - start_odometer)
# MAGIC - days_since_start: calendar days elapsed since lease start date
# MAGIC
# MAGIC Pipeline parameters (set per target in databricks.yml):
# MAGIC - lease_start_odometer: starting odometer at lease inception
# MAGIC - lease_start_date: lease start date (YYYY-MM-DD)

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import col, datediff, lit, to_date

start_odo = float(spark.conf.get("lease_start_odometer", "0"))  # noqa: F821
start_date = spark.conf.get("lease_start_date", "2024-01-01")  # noqa: F821


@dp.table(name="silver_forecast_features")
def silver_forecast_features():
    return (
        spark.readStream.table("bronze_mileage")  # noqa: F821
        .withColumn("lease_miles", col("odometer") - lit(start_odo))
        .withColumn(
            "days_since_start",
            datediff(to_date(col("timestamp")), lit(start_date).cast("date")),
        )
        .filter(col("days_since_start") >= 0)
        .filter(col("lease_miles") >= 0)
    )
