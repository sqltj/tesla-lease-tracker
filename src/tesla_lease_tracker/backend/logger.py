"""Structured application logging with correlation ID support."""

import logging
import json
import uuid
from contextvars import ContextVar
from typing import Optional

from .._metadata import app_name

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        cid = correlation_id_var.get("")
        if cid:
            log_entry["correlation_id"] = cid
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logger(name: str = app_name, level: int = logging.INFO) -> logging.Logger:
    """Configure and return the application logger with JSON formatting."""
    log = logging.getLogger(name)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        log.addHandler(handler)
        log.setLevel(level)
    return log


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return uuid.uuid4().hex[:12]


# Default logger instance
logger = setup_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    if name is None:
        return logger
    return logging.getLogger(name)
