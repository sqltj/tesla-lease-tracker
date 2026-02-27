import time
from datetime import UTC, datetime

from sqlmodel import Session, text

from .logger import logger
from .models import DependencyHealth, ServiceStatus


def check_database(session: Session | None) -> DependencyHealth:
    """Test database connectivity and query speed."""
    if session is None:
        return DependencyHealth(name="database", status=ServiceStatus.HEALTHY, error="JSON mode (no database)")

    try:
        start = time.perf_counter()
        session.exec(text("SELECT 1"))
        duration = time.perf_counter() - start

        if duration > 0.5:
            return DependencyHealth(
                name="database",
                status=ServiceStatus.DEGRADED,
                error=f"Slow response ({duration:.2f}s)",
            )
        return DependencyHealth(name="database", status=ServiceStatus.HEALTHY)
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return DependencyHealth(name="database", status=ServiceStatus.UNHEALTHY, error=str(e))


def check_zerobus(zerobus_service) -> DependencyHealth | None:
    """Check Zerobus stream status. Returns None if service not configured."""
    if zerobus_service is None:
        return None

    try:
        is_ready = getattr(zerobus_service, "_stream", None) is not None
        if is_ready:
            return DependencyHealth(name="zerobus", status=ServiceStatus.HEALTHY)
        return DependencyHealth(name="zerobus", status=ServiceStatus.DEGRADED, error="Stream not initialized")
    except Exception as e:
        logger.warning(f"Zerobus health check failed: {e}")
        return DependencyHealth(name="zerobus", status=ServiceStatus.UNHEALTHY, error=str(e))


def compute_overall_status(*deps: DependencyHealth | None) -> ServiceStatus:
    """Compute overall status from dependency health checks."""
    statuses = [d.status for d in deps if d is not None]
    if not statuses:
        return ServiceStatus.HEALTHY
    if ServiceStatus.UNHEALTHY in statuses:
        return ServiceStatus.UNHEALTHY
    if ServiceStatus.DEGRADED in statuses:
        return ServiceStatus.DEGRADED
    return ServiceStatus.HEALTHY
