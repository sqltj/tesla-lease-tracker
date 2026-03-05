"""In-memory ring-buffer metrics collector for request latency and error tracking."""

import threading
from collections import deque
from dataclasses import dataclass, field

BUFFER_SIZE = 1000

_quality_warning_count = 0
_quality_warning_lock = threading.Lock()


def increment_quality_warnings() -> None:
    """Increment the module-level data quality warning counter."""
    global _quality_warning_count
    with _quality_warning_lock:
        _quality_warning_count += 1


def get_quality_warning_count() -> int:
    with _quality_warning_lock:
        return _quality_warning_count


@dataclass
class RequestRecord:
    method: str
    path: str
    status_code: int
    duration_ms: float


def _percentile(sorted_values: list[float], p: float) -> float:
    """Return the p-th percentile (0-100) of a sorted list."""
    if not sorted_values:
        return 0.0
    idx = int(len(sorted_values) * p / 100)
    idx = min(idx, len(sorted_values) - 1)
    return sorted_values[idx]


class MetricsCollector:
    """Thread-safe bounded ring buffer that computes latency percentiles on demand."""

    def __init__(self, buffer_size: int = BUFFER_SIZE) -> None:
        self._buffer: deque[RequestRecord] = deque(maxlen=buffer_size)
        self._lock = threading.Lock()

    def record(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._buffer.append(RequestRecord(method, path, status_code, duration_ms))

    def _snapshot(self) -> list[RequestRecord]:
        with self._lock:
            return list(self._buffer)

    def summary(self):
        """Return a MetricsOut summary over the current buffer window."""
        from .models import EndpointStats, MetricsOut

        records = self._snapshot()
        total = len(records)

        if total == 0:
            return MetricsOut(
                window_size=0,
                request_count=0,
                error_count=0,
                error_rate=0.0,
                latency_p50=0.0,
                latency_p95=0.0,
                latency_p99=0.0,
                data_quality_warnings=get_quality_warning_count(),
                by_endpoint=[],
            )

        errors = sum(1 for r in records if r.status_code >= 400)
        durations = sorted(r.duration_ms for r in records)

        # Per-endpoint breakdown
        by_path: dict[str, list[RequestRecord]] = {}
        for r in records:
            by_path.setdefault(r.path, []).append(r)

        endpoint_stats = []
        for path, path_records in by_path.items():
            path_errors = sum(1 for r in path_records if r.status_code >= 400)
            path_durations = sorted(r.duration_ms for r in path_records)
            count = len(path_records)
            endpoint_stats.append(
                EndpointStats(
                    path=path,
                    request_count=count,
                    error_count=path_errors,
                    error_rate=round(path_errors / count, 4),
                    latency_p50=round(_percentile(path_durations, 50), 1),
                    latency_p95=round(_percentile(path_durations, 95), 1),
                    latency_p99=round(_percentile(path_durations, 99), 1),
                )
            )

        return MetricsOut(
            window_size=total,
            request_count=total,
            error_count=errors,
            error_rate=round(errors / total, 4),
            latency_p50=round(_percentile(durations, 50), 1),
            latency_p95=round(_percentile(durations, 95), 1),
            latency_p99=round(_percentile(durations, 99), 1),
            data_quality_warnings=get_quality_warning_count(),
            by_endpoint=endpoint_stats,
        )
