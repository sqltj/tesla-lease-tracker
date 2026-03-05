"""FastAPI middleware for request logging and correlation IDs."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .logger import correlation_id_var, generate_correlation_id, logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with timing and correlation ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        cid = request.headers.get("X-Correlation-ID") or generate_correlation_id()
        token = correlation_id_var.set(cid)

        start = time.perf_counter()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 1)

            # Skip logging static file requests
            if not path.startswith("/api"):
                return response

            logger.info(
                "%s %s %d %sms",
                method,
                path,
                response.status_code,
                duration_ms,
            )
            response.headers["X-Correlation-ID"] = cid
            if hasattr(request.app.state, "metrics"):
                request.app.state.metrics.record(method, path, response.status_code, duration_ms)
            return response
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            logger.exception(
                "%s %s FAILED %sms",
                method,
                path,
                duration_ms,
            )
            raise
        finally:
            correlation_id_var.reset(token)
