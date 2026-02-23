# Databricks notebook source
# MAGIC %md
# MAGIC # Tesla Lease Tracker — Forecast MLflow PyFunc Model
# MAGIC
# MAGIC This module defines the MLflow pyfunc class for forecast inference.
# MAGIC Model state is stored as JSON artifacts (slope/intercept for linear,
# MAGIC level/trend for Holt-Winters). Prediction math is re-implemented
# MAGIC from those numeric values at inference time.

# COMMAND ----------

import json
import math
from datetime import date, timedelta
from typing import Any

import mlflow
import numpy as np
import pandas as pd

# COMMAND ----------


class ForecastPyfunc(mlflow.pyfunc.PythonModel):
    """MLflow pyfunc wrapper for lease mileage forecasting.

    Artifacts (JSON):
        linear_coeffs.json: {"slope": float, "intercept": float}
        hw_state.json: {"last_level": float, "last_trend": float, "residual_std": float}
        training_meta.json: {
            "base_date": "YYYY-MM-DD",
            "last_reading_date": "YYYY-MM-DD",
            "avg_interval": float,
            "last_miles": float
        }

    Input DataFrame columns:
        model_type (str): "linear" or "prophet"
        lease_config_json (str): JSON of LeaseConfig fields

    Output DataFrame column:
        forecast_json (str): JSON of ForecastOut dict
    """

    def load_context(self, context: mlflow.pyfunc.PythonModelContext) -> None:
        with open(context.artifacts["linear_coeffs"], "r") as f:
            self._linear = json.load(f)
        with open(context.artifacts["hw_state"], "r") as f:
            self._hw = json.load(f)
        with open(context.artifacts["training_meta"], "r") as f:
            self._meta = json.load(f)

    def predict(
        self, context: mlflow.pyfunc.PythonModelContext, model_input: pd.DataFrame
    ) -> pd.DataFrame:
        results = []
        for _, row in model_input.iterrows():
            model_type = row["model_type"]
            lease_cfg = json.loads(row["lease_config_json"])
            forecast_json = self._run_forecast(model_type, lease_cfg)
            results.append({"forecast_json": forecast_json})
        return pd.DataFrame(results)

    def _run_forecast(self, model_type: str, lease_cfg: dict[str, Any]) -> str:
        base_date = date.fromisoformat(self._meta["base_date"])
        last_date = date.fromisoformat(self._meta["last_reading_date"])
        lease_end = date.fromisoformat(lease_cfg["lease_end_date"])
        mileage_limit = lease_cfg["mileage_limit"]
        avg_interval = self._meta["avg_interval"]

        # Build forecast dates from day after last reading through lease end
        forecast_dates: list[date] = []
        d = last_date + timedelta(days=max(1, int(avg_interval)))
        while d <= lease_end:
            forecast_dates.append(d)
            d += timedelta(days=max(1, int(avg_interval)))
        if not forecast_dates or forecast_dates[-1] < lease_end:
            forecast_dates.append(lease_end)

        points = []
        if model_type == "linear":
            slope = self._linear["slope"]
            intercept = self._linear["intercept"]
            for fd in forecast_dates:
                day_num = (fd - base_date).days
                pred_lease_miles = slope * day_num + intercept
                points.append(
                    {
                        "date": fd.isoformat(),
                        "predicted_miles": round(max(pred_lease_miles, 0.0), 1),
                        "lower_bound": None,
                        "upper_bound": None,
                    }
                )
            end_day = (lease_end - base_date).days
            projected_end_miles = slope * end_day + intercept
            daily_rate = slope

        else:
            # Holt-Winters (Holt's linear trend extrapolation)
            last_level = self._hw["last_level"]
            last_trend = self._hw["last_trend"]
            residual_std = self._hw["residual_std"]

            for fd in forecast_dates:
                h = (fd - last_date).days / max(avg_interval, 1.0)
                pred_lease_miles = last_level + h * last_trend
                ci = 1.96 * residual_std * math.sqrt(max(h, 1.0))
                points.append(
                    {
                        "date": fd.isoformat(),
                        "predicted_miles": round(max(pred_lease_miles, 0.0), 1),
                        "lower_bound": round(max(pred_lease_miles - ci, 0.0), 1),
                        "upper_bound": round(max(pred_lease_miles + ci, 0.0), 1),
                    }
                )
            total_days = (lease_end - last_date).days
            projected_end_miles = last_level + (total_days / max(avg_interval, 1.0)) * last_trend
            daily_rate = last_trend / max(avg_interval, 1.0)

        over_under = projected_end_miles - mileage_limit

        forecast_out = {
            "model": model_type,
            "points": points,
            "daily_rate": round(daily_rate, 2),
            "projected_end_miles": round(max(projected_end_miles, 0.0), 0),
            "over_under": round(over_under, 0),
        }
        return json.dumps(forecast_out)


# COMMAND ----------

mlflow.models.set_model(ForecastPyfunc())
