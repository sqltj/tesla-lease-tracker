"""Tests for MetricsCollector and the /api/metrics endpoint."""

import pytest

from tesla_lease_tracker.backend.metrics_service import (
    MetricsCollector,
    get_quality_warning_count,
    increment_quality_warnings,
)


# ---------------------------------------------------------------------------
# MetricsCollector unit tests
# ---------------------------------------------------------------------------


class TestMetricsCollectorEmpty:
    def test_empty_summary_zeros(self):
        collector = MetricsCollector()
        summary = collector.summary()
        assert summary.request_count == 0
        assert summary.error_count == 0
        assert summary.error_rate == 0.0
        assert summary.latency_p50 == 0.0
        assert summary.latency_p95 == 0.0
        assert summary.latency_p99 == 0.0
        assert summary.by_endpoint == []


class TestMetricsCollectorRecord:
    def test_single_request_recorded(self):
        collector = MetricsCollector()
        collector.record("GET", "/api/health", 200, 12.5)
        summary = collector.summary()
        assert summary.request_count == 1
        assert summary.error_count == 0
        assert summary.error_rate == 0.0
        assert summary.latency_p50 == 12.5

    def test_error_requests_counted(self):
        collector = MetricsCollector()
        collector.record("GET", "/api/health", 200, 10.0)
        collector.record("GET", "/api/health", 500, 20.0)
        collector.record("POST", "/api/mileage", 400, 5.0)
        summary = collector.summary()
        assert summary.request_count == 3
        assert summary.error_count == 2
        assert summary.error_rate == pytest.approx(2 / 3, rel=1e-3)

    def test_percentiles_computed_correctly(self):
        collector = MetricsCollector()
        # 10 requests with known durations
        for i in range(1, 11):
            collector.record("GET", "/api/test", 200, float(i * 10))
        summary = collector.summary()
        # p50: position int(10 * 50/100) = 5 → sorted[5] = 60ms
        assert summary.latency_p50 == 60.0
        # p95: position int(10 * 95/100) = 9 → sorted[9] = 100ms
        assert summary.latency_p95 == 100.0
        # p99: position int(10 * 99/100) = 9 → sorted[9] = 100ms
        assert summary.latency_p99 == 100.0

    def test_ring_buffer_bounded(self):
        collector = MetricsCollector(buffer_size=5)
        for i in range(10):
            collector.record("GET", "/api/test", 200, float(i))
        summary = collector.summary()
        # Only the last 5 are retained
        assert summary.request_count == 5
        assert summary.window_size == 5

    def test_per_endpoint_breakdown(self):
        collector = MetricsCollector()
        collector.record("GET", "/api/health", 200, 10.0)
        collector.record("GET", "/api/health", 200, 20.0)
        collector.record("GET", "/api/mileage", 500, 30.0)
        summary = collector.summary()
        paths = {ep.path: ep for ep in summary.by_endpoint}
        assert "/api/health" in paths
        assert "/api/mileage" in paths
        assert paths["/api/health"].request_count == 2
        assert paths["/api/health"].error_count == 0
        assert paths["/api/mileage"].error_count == 1
        assert paths["/api/mileage"].error_rate == 1.0


# ---------------------------------------------------------------------------
# Quality warning counter tests
# ---------------------------------------------------------------------------


class TestQualityWarningCounter:
    def test_increment_and_get(self):
        before = get_quality_warning_count()
        increment_quality_warnings()
        after = get_quality_warning_count()
        assert after == before + 1

    def test_counter_reflected_in_summary(self):
        collector = MetricsCollector()
        collector.record("POST", "/api/mileage/sync", 200, 50.0)
        before = collector.summary().data_quality_warnings
        increment_quality_warnings()
        after = collector.summary().data_quality_warnings
        assert after == before + 1


# ---------------------------------------------------------------------------
# Repository integration: add_reading_validated increments counter
# ---------------------------------------------------------------------------


SAMPLE_VIN = "5YJ3E1EA1NF123456"


class TestRepositoryQualityWarning:
    def test_duplicate_reading_increments_counter(self, mileage_repo, lease_repo):
        from datetime import date, datetime
        from tesla_lease_tracker.backend.models import LeaseConfigIn

        lease_in = LeaseConfigIn(
            vin=SAMPLE_VIN,
            lease_start_date=date(2024, 1, 1),
            lease_end_date=date(2027, 1, 1),
            mileage_limit=36000,
            start_odometer=0.0,
        )
        lease_repo.save_lease_config(lease_in)
        ts = datetime(2024, 6, 15, 12, 0)
        mileage_repo.add_reading(SAMPLE_VIN, ts, 100.0)

        before = get_quality_warning_count()
        # Same timestamp ± 5 min is a duplicate
        _, errors = mileage_repo.add_reading_validated(SAMPLE_VIN, ts, 105.0)
        after = get_quality_warning_count()

        assert len(errors) > 0
        assert after == before + 1
