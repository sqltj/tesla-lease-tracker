from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from tesla_lease_tracker.backend.health_service import (
    check_database,
    check_zerobus,
    compute_overall_status,
)
from tesla_lease_tracker.backend.models import (
    DependencyHealth,
    HealthOut,
    LeaseConfig,
    MileageReading,
    ServiceStatus,
)


class TestHealthOut:
    def test_basic_construction(self):
        h = HealthOut(
            status=ServiceStatus.HEALTHY,
            version="0.1.0",
            has_lease=False,
            readings_count=0,
            last_sync=None,
        )
        assert h.status == ServiceStatus.HEALTHY
        assert h.readings_count == 0

    def test_with_data(self):
        h = HealthOut(
            status=ServiceStatus.HEALTHY,
            version="0.1.0",
            has_lease=True,
            readings_count=42,
            last_sync=datetime(2024, 6, 15, 10, 30),
        )
        assert h.has_lease is True
        assert h.readings_count == 42
        assert h.last_sync is not None

    def test_serialization_roundtrip(self):
        h = HealthOut(
            status=ServiceStatus.HEALTHY,
            version="0.1.0",
            has_lease=True,
            readings_count=5,
            last_sync=datetime(2024, 6, 15),
        )
        json_str = h.model_dump_json()
        restored = HealthOut.model_validate_json(json_str)
        assert restored.status == h.status
        assert restored.readings_count == h.readings_count


class TestCheckDatabase:
    def test_healthy_database(self, db_session):
        """Database that responds quickly is healthy."""
        result = check_database(db_session)
        assert result.status == ServiceStatus.HEALTHY
        assert result.error is None

    def test_none_session_json_mode(self):
        """None session (JSON mode) returns healthy."""
        result = check_database(None)
        assert result.status == ServiceStatus.HEALTHY
        assert "JSON" in result.error


class TestCheckZerobus:
    def test_none_service_returns_none(self):
        """No Zerobus service configured returns None."""
        assert check_zerobus(None) is None

    def test_stream_ready_healthy(self):
        """Zerobus with active stream is healthy."""
        mock_zb = MagicMock()
        mock_zb._stream = MagicMock()  # Stream exists
        result = check_zerobus(mock_zb)
        assert result.status == ServiceStatus.HEALTHY

    def test_stream_not_ready_degraded(self):
        """Zerobus without stream is degraded."""
        mock_zb = MagicMock()
        mock_zb._stream = None
        result = check_zerobus(mock_zb)
        assert result.status == ServiceStatus.DEGRADED
        assert "not initialized" in result.error


class TestOverallStatus:
    def test_all_healthy(self):
        """All deps healthy = overall healthy."""
        d1 = DependencyHealth(name="a", status=ServiceStatus.HEALTHY)
        d2 = DependencyHealth(name="b", status=ServiceStatus.HEALTHY)
        assert compute_overall_status(d1, d2) == ServiceStatus.HEALTHY

    def test_one_degraded(self):
        """One degraded = overall degraded."""
        d1 = DependencyHealth(name="a", status=ServiceStatus.HEALTHY)
        d2 = DependencyHealth(name="b", status=ServiceStatus.DEGRADED, error="slow")
        assert compute_overall_status(d1, d2) == ServiceStatus.DEGRADED

    def test_one_unhealthy(self):
        """One unhealthy = overall unhealthy."""
        d1 = DependencyHealth(name="a", status=ServiceStatus.HEALTHY)
        d2 = DependencyHealth(name="b", status=ServiceStatus.UNHEALTHY, error="down")
        assert compute_overall_status(d1, d2) == ServiceStatus.UNHEALTHY

    def test_none_deps_skipped(self):
        """None dependencies are skipped."""
        d1 = DependencyHealth(name="a", status=ServiceStatus.HEALTHY)
        assert compute_overall_status(d1, None) == ServiceStatus.HEALTHY

    def test_empty_deps(self):
        """No dependencies = healthy."""
        assert compute_overall_status() == ServiceStatus.HEALTHY
