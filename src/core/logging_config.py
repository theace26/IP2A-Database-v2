"""Structured logging configuration for production.

Provides JSON-formatted logs for production environments,
making logs easily parseable by log aggregation services.
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional

from src.config.settings import settings


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Outputs logs in JSON format with standardized fields:
    - timestamp: ISO 8601 timestamp in UTC
    - level: Log level (INFO, WARNING, ERROR, etc.)
    - logger: Logger name
    - message: Log message
    - module: Source module
    - function: Source function
    - line: Line number
    - extra: Any additional fields
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields passed to the logger
        # Skip standard LogRecord attributes
        standard_attrs = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "taskName", "message",
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                log_data[key] = value

        return json.dumps(log_data, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter for development.

    Format: [LEVEL] timestamp - logger - message
    """

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output."""
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"{color}[{record.levelname:8}]{self.RESET} {timestamp} - {record.name} - {record.getMessage()}"

        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logging(
    level: Optional[str] = None,
    json_format: Optional[bool] = None,
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to settings.LOG_LEVEL
        json_format: Use JSON format. Defaults to settings.JSON_LOGS in production

    Usage:
        # In main.py startup
        from src.core.logging_config import setup_logging
        setup_logging()

        # In modules
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Something happened", extra={"user_id": 123})
    """
    log_level = level or settings.LOG_LEVEL
    use_json = json_format if json_format is not None else (
        settings.JSON_LOGS and settings.is_production
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Set formatter based on environment
    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Log startup message
    root_logger.info(
        f"Logging configured: level={log_level}, format={'JSON' if use_json else 'console'}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name, typically __name__

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class RequestLogger:
    """
    Context manager for logging request-scoped information.

    Usage:
        with RequestLogger(request_id="abc123", user_id=42) as log:
            log.info("Processing request")
            # ... request handling ...
            log.info("Request complete")
    """

    def __init__(self, **context):
        """Initialize with request context."""
        self.context = context
        self.logger = logging.getLogger("request")

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, log any exceptions."""
        if exc_type:
            self.error(f"Request failed: {exc_val}", exc_info=True)
        return False

    def _log(self, level: int, message: str, **kwargs):
        """Log with request context."""
        extra = {**self.context, **kwargs.pop("extra", {})}
        self.logger.log(level, message, extra=extra, **kwargs)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
