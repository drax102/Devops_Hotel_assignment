import json
import logging
import os
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """
    Format log records as single-line JSON objects with ISO8601 UTC timestamps,
    request tracing IDs, and contextual metadata.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include tracing and HTTP metadata if present
        for field in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client_ip",
            "error",
        ):
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging():
    """Configure structured JSON logging driven by LOG_LEVEL."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers = [handler]

    # Configure uvicorn loggers to use the same JSON formatter
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False
        uvicorn_logger.setLevel(numeric_level)

    logger = logging.getLogger("hotel_api")
    logger.setLevel(numeric_level)
    return logger
