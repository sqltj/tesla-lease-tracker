# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze: Mileage Readings Streaming Table
# MAGIC
# MAGIC Ingests raw mileage readings from the Delta source table into the
# MAGIC ML feature pipeline. This is a passthrough streaming table.

# COMMAND ----------

from pyspark import pipelines as dp


@dp.table(name="bronze_mileage")
def bronze_mileage():
    return spark.readStream.table("main.default.mileage_readings")  # noqa: F821
