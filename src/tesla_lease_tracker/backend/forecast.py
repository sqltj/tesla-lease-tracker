from datetime import date, timedelta

import numpy as np

from .logger import logger
from .models import ForecastOut, ForecastPoint, LeaseConfig, MileageReading


MIN_READINGS = 3


def forecast_linear(
    readings: list[MileageReading],
    config: LeaseConfig,
) -> ForecastOut:
    """Linear regression forecast using numpy polyfit (degree 1)."""
    if len(readings) < MIN_READINGS:
        raise ValueError(f"Need at least {MIN_READINGS} readings for forecast")

    start_odo = config.start_odometer
    lease_end = config.lease_end_date

    # Convert to days-since-lease-start and lease-miles
    base = config.lease_start_date
    days = np.array([(r.timestamp.date() - base).days for r in readings], dtype=float)
    miles = np.array([r.odometer - start_odo for r in readings], dtype=float)

    # Fit degree-1 polynomial
    coeffs = np.polyfit(days, miles, 1)
    daily_rate = float(coeffs[0])

    # Generate forecast points from today through lease end + buffer
    today = date.today()
    end = lease_end + timedelta(days=30)
    points: list[ForecastPoint] = []

    current = today
    while current <= end:
        day_num = (current - base).days
        predicted = float(np.polyval(coeffs, day_num))
        points.append(ForecastPoint(date=current, predicted_miles=round(predicted, 0)))
        current += timedelta(days=7)  # Weekly points

    # Project end-of-lease miles
    end_day = (lease_end - base).days
    projected_end = float(np.polyval(coeffs, end_day))
    over_under = projected_end - config.mileage_limit

    return ForecastOut(
        model="linear",
        points=points,
        daily_rate=round(daily_rate, 1),
        projected_end_miles=round(projected_end, 0),
        over_under=round(over_under, 0),
    )


def forecast_timeseries(
    readings: list[MileageReading],
    config: LeaseConfig,
) -> ForecastOut:
    """Time-series forecast using statsmodels Holt-Winters exponential smoothing."""
    if len(readings) < MIN_READINGS:
        raise ValueError(f"Need at least {MIN_READINGS} readings for forecast")

    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    start_odo = config.start_odometer
    lease_end = config.lease_end_date
    base = config.lease_start_date

    miles = [r.odometer - start_odo for r in readings]

    # Fit Holt's linear trend (no seasonality for mileage data)
    try:
        model = ExponentialSmoothing(
            miles,
            trend="add",
            seasonal=None,
        ).fit(optimized=True)
    except Exception as e:
        logger.warning(f"Holt-Winters failed, falling back to linear: {e}")
        return forecast_linear(readings, config)

    # Forecast horizon: from last reading to lease end + 30 days
    today = date.today()
    end = lease_end + timedelta(days=30)
    last_reading_date = readings[-1].timestamp.date()

    # Number of steps (one per reading interval, approximate as days between readings)
    avg_interval = max(
        (last_reading_date - readings[0].timestamp.date()).days / max(len(readings) - 1, 1),
        1,
    )
    horizon_days = (end - last_reading_date).days
    n_steps = max(int(horizon_days / avg_interval), 1)

    forecast_values = model.forecast(n_steps)

    # Build confidence intervals using residuals
    residuals = model.resid
    std_err = float(np.std(residuals)) if len(residuals) > 1 else 0

    points: list[ForecastPoint] = []
    for i, val in enumerate(forecast_values):
        step_days = int((i + 1) * avg_interval)
        forecast_date = last_reading_date + timedelta(days=step_days)
        if forecast_date > end:
            break
        # Confidence grows with distance
        ci = 1.96 * std_err * np.sqrt(i + 1)
        points.append(
            ForecastPoint(
                date=forecast_date,
                predicted_miles=round(float(val), 0),
                lower_bound=round(float(val) - ci, 0),
                upper_bound=round(float(val) + ci, 0),
            )
        )

    # Interpolate to find projected end-of-lease
    end_day_offset = (lease_end - last_reading_date).days
    end_step = end_day_offset / avg_interval
    if end_step <= n_steps and len(forecast_values) > 0:
        # Linear interpolation between nearest forecast steps
        idx = min(int(end_step), len(forecast_values) - 1)
        projected_end = float(forecast_values[idx])
    else:
        projected_end = float(forecast_values[-1]) if len(forecast_values) > 0 else miles[-1]

    # Daily rate from model trend
    daily_rate = (projected_end - miles[-1]) / max(horizon_days, 1) if horizon_days > 0 else 0
    over_under = projected_end - config.mileage_limit

    return ForecastOut(
        model="prophet",
        points=points,
        daily_rate=round(daily_rate, 1),
        projected_end_miles=round(projected_end, 0),
        over_under=round(over_under, 0),
    )
