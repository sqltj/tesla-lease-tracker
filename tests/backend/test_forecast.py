from datetime import date, datetime, timedelta

import pytest

from tesla_lease_tracker.backend.forecast import forecast_linear, forecast_timeseries
from tesla_lease_tracker.backend.models import LeaseConfig, MileageReading


def make_config(**overrides):
    defaults = dict(
        vin="5YJ3E1EA1NF123456",
        lease_start_date=date(2024, 1, 1),
        lease_end_date=date(2027, 1, 1),
        mileage_limit=36000,
        start_odometer=10000.0,
    )
    defaults.update(overrides)
    return LeaseConfig(**defaults)


def make_readings(n=5, start_odo=10000.0, miles_per_month=1000.0):
    base = datetime(2024, 1, 15, 12, 0)
    return [
        MileageReading(
            timestamp=base + timedelta(days=i * 30),
            odometer=start_odo + i * miles_per_month,
        )
        for i in range(n)
    ]


class TestForecastLinear:
    def test_too_few_readings(self):
        config = make_config()
        readings = make_readings(n=2)
        with pytest.raises(ValueError, match="at least"):
            forecast_linear(readings, config)

    def test_returns_linear_model(self):
        result = forecast_linear(make_readings(5), make_config())
        assert result.model == "linear"
        assert len(result.points) > 0

    def test_daily_rate_positive(self):
        result = forecast_linear(make_readings(5), make_config())
        assert result.daily_rate > 0

    def test_projects_end_miles(self):
        result = forecast_linear(make_readings(5), make_config())
        assert result.projected_end_miles > 0

    def test_over_under_calculated(self):
        config = make_config(mileage_limit=36000)
        result = forecast_linear(make_readings(5), config)
        expected = result.projected_end_miles - 36000
        assert abs(result.over_under - expected) < 1

    def test_exactly_three_readings(self):
        result = forecast_linear(make_readings(n=3), make_config())
        assert result.model == "linear"

    def test_many_readings(self):
        result = forecast_linear(make_readings(n=20), make_config())
        assert len(result.points) > 0


class TestForecastTimeseries:
    def test_too_few_readings(self):
        config = make_config()
        readings = make_readings(n=2)
        with pytest.raises(ValueError, match="at least"):
            forecast_timeseries(readings, config)

    def test_returns_prophet_model(self):
        result = forecast_timeseries(make_readings(10), make_config())
        assert result.model == "prophet"

    def test_has_confidence_intervals(self):
        result = forecast_timeseries(make_readings(10), make_config())
        points_with_bounds = [p for p in result.points if p.lower_bound is not None]
        assert len(points_with_bounds) > 0

    def test_projects_end_miles(self):
        result = forecast_timeseries(make_readings(10), make_config())
        assert result.projected_end_miles > 0
