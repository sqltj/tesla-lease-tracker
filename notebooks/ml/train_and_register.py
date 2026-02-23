# Databricks notebook source
# MAGIC %md
# MAGIC # Tesla Lease Tracker — Train and Register Forecast Model
# MAGIC
# MAGIC Reads `silver_forecast_features` from the SDP pipeline, fits linear
# MAGIC and Holt-Winters models, saves state as JSON artifacts, logs to MLflow,
# MAGIC registers to Unity Catalog, and updates the Model Serving endpoint.

# COMMAND ----------

import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path

import mlflow
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# COMMAND ----------


def train_and_register(
    catalog: str = "main",
    schema: str = "tesla_lease_tracker",
    endpoint_name: str | None = None,
) -> str:
    """Fit forecast models on silver features and register to Unity Catalog.

    Args:
        catalog: Unity Catalog catalog name
        schema: Unity Catalog schema name
        endpoint_name: Model Serving endpoint to update (skipped if None)

    Returns:
        Registered model version number as string
    """
    # 1. Read silver feature table
    table_fqn = f"{catalog}.{schema}.silver_forecast_features"
    df = spark.table(table_fqn).orderBy("timestamp").toPandas()  # noqa: F821 (spark injected)

    if len(df) < 3:
        raise ValueError(f"Need at least 3 rows in {table_fqn}, got {len(df)}")

    days = df["days_since_start"].astype(float).values
    miles = df["lease_miles"].astype(float).values
    timestamps = df["timestamp"].tolist()

    # 2. Fit linear model: y = slope*x + intercept
    coeffs = np.polyfit(days, miles, 1)
    slope, intercept = float(coeffs[0]), float(coeffs[1])

    # Compute residuals for confidence interval width
    residuals = miles - (slope * days + intercept)
    linear_residual_std = float(np.std(residuals))

    # 3. Fit Holt-Winters (trend only, no seasonality)
    hw_model = ExponentialSmoothing(miles, trend="add", seasonal=None).fit(optimized=True)
    last_level = float(hw_model.level.iloc[-1])
    last_trend = float(hw_model.trend.iloc[-1])
    hw_fitted = hw_model.fittedvalues.values
    hw_residuals = miles - hw_fitted
    hw_residual_std = float(np.std(hw_residuals))

    # Compute average interval between readings (in days, used for HW step size)
    if len(days) >= 2:
        avg_interval = float(np.mean(np.diff(days)))
    else:
        avg_interval = 30.0

    # 4. Build metadata
    base_date = date.today().isoformat()
    last_reading_date = (
        timestamps[-1].date().isoformat()
        if hasattr(timestamps[-1], "date")
        else str(timestamps[-1])[:10]
    )
    last_miles = float(miles[-1])

    # 5. Write JSON artifact files to a temp directory
    with tempfile.TemporaryDirectory() as tmp:
        linear_path = os.path.join(tmp, "linear_coeffs.json")
        hw_path = os.path.join(tmp, "hw_state.json")
        meta_path = os.path.join(tmp, "training_meta.json")

        with open(linear_path, "w") as f:
            json.dump({"slope": slope, "intercept": intercept}, f)

        with open(hw_path, "w") as f:
            json.dump(
                {
                    "last_level": last_level,
                    "last_trend": last_trend,
                    "residual_std": hw_residual_std,
                },
                f,
            )

        with open(meta_path, "w") as f:
            json.dump(
                {
                    "base_date": base_date,
                    "last_reading_date": last_reading_date,
                    "avg_interval": avg_interval,
                    "last_miles": last_miles,
                },
                f,
            )

        # 6. Log model to MLflow
        mlflow.set_registry_uri("databricks-uc")

        # Experiment path uses current user from Databricks context
        try:
            user_email = spark.sql("SELECT current_user()").collect()[0][0]  # noqa: F821
        except Exception:
            user_email = os.environ.get("DATABRICKS_USER_EMAIL", "unknown")

        experiment_path = f"/Users/{user_email}/tesla-lease-tracker/forecast"
        mlflow.set_experiment(experiment_path)

        model_name = f"{catalog}.{schema}.forecast_model"
        notebook_dir = Path(__file__).parent

        with mlflow.start_run() as run:
            mlflow.log_params(
                {
                    "slope": round(slope, 6),
                    "intercept": round(intercept, 2),
                    "hw_last_level": round(last_level, 2),
                    "hw_last_trend": round(last_trend, 4),
                    "training_rows": len(df),
                    "avg_interval_days": round(avg_interval, 1),
                }
            )
            mlflow.log_metrics(
                {
                    "linear_residual_std": round(linear_residual_std, 2),
                    "hw_residual_std": round(hw_residual_std, 2),
                }
            )

            model_info = mlflow.pyfunc.log_model(
                artifact_path="forecast_model",
                python_model=str(notebook_dir / "forecast_model.py"),
                artifacts={
                    "linear_coeffs": linear_path,
                    "hw_state": hw_path,
                    "training_meta": meta_path,
                },
                pip_requirements=[
                    "mlflow>=3.6.0",
                    "numpy>=2.0",
                    "statsmodels>=0.14",
                    "pandas",
                ],
                registered_model_name=model_name,
            )

        run_id = run.info.run_id

    # 7. Get the version that was just registered
    client = mlflow.tracking.MlflowClient()
    versions = client.search_model_versions(f"name='{model_name}'")
    latest_version = sorted(versions, key=lambda v: int(v.version))[-1].version

    # 8. Set @champion alias
    client.set_registered_model_alias(model_name, "champion", latest_version)
    print(f"Registered {model_name} version {latest_version} with @champion alias")

    # 9. Update Model Serving endpoint if configured
    if endpoint_name:
        _update_serving_endpoint(endpoint_name, model_name, latest_version)

    return latest_version


def _update_serving_endpoint(endpoint_name: str, model_name: str, version: str) -> None:
    """Update Model Serving endpoint to the newly registered model version."""
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.serving import (
        EndpointCoreConfigInput,
        ServedEntityInput,
    )

    ws = WorkspaceClient()
    ws.serving_endpoints.update_config(
        name=endpoint_name,
        served_entities=[
            ServedEntityInput(
                entity_name=f"{model_name}@champion",
                scale_to_zero_enabled=True,
                workload_size="Small",
            )
        ],
    )
    print(f"Updated endpoint '{endpoint_name}' to {model_name}@champion")


# COMMAND ----------

# Entry point when run as a Databricks notebook task
if __name__ == "__main__" or "spark" in dir():  # noqa: F821
    endpoint = os.environ.get("TESLA_LEASE_TRACKER_FORECAST_ENDPOINT")
    version = train_and_register(endpoint_name=endpoint)
    print(f"Training complete. Model version: {version}")
