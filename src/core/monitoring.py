"""Monitoring and error tracking setup.

Integrates with Sentry for error tracking and performance monitoring.
"""

import logging
from typing import Optional

from src.config.settings import settings

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """
    Initialize Sentry error tracking and performance monitoring.

    Call this during application startup.
    Requires SENTRY_DSN environment variable to be set.
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured - error tracking disabled")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            release=f"ip2a-database@{settings.APP_VERSION}",
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture INFO and above
                    event_level=logging.ERROR,  # Create events for ERROR and above
                ),
            ],
            # Sample rate for performance monitoring (10% of transactions)
            traces_sample_rate=0.1,
            # Don't send PII (emails, usernames, etc.)
            send_default_pii=False,
            # Additional context
            attach_stacktrace=True,
            # Filter out health check endpoints from performance monitoring
            traces_sampler=traces_sampler,
        )

        logger.info(
            f"Sentry initialized for environment: {settings.ENVIRONMENT}, "
            f"version: {settings.APP_VERSION}"
        )

    except ImportError:
        logger.warning(
            "sentry-sdk not installed - error tracking disabled. "
            "Install with: pip install sentry-sdk[fastapi]"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def traces_sampler(sampling_context: dict) -> float:
    """
    Custom sampling function for Sentry performance monitoring.

    Excludes health checks and static files from performance monitoring
    to reduce noise and costs.
    """
    transaction_context = sampling_context.get("transaction_context", {})
    op = transaction_context.get("op", "")
    name = transaction_context.get("name", "")

    # Don't trace health checks
    if "/health" in name:
        return 0.0

    # Don't trace static files
    if name.startswith("/static"):
        return 0.0

    # Sample API endpoints at a higher rate
    if name.startswith("/api/"):
        return 0.2  # 20% of API requests

    # Default sample rate
    return 0.1  # 10% of other requests


def capture_exception(exception: Exception, extra: Optional[dict] = None) -> None:
    """
    Capture an exception to Sentry.

    Args:
        exception: The exception to capture
        extra: Optional additional context to include
    """
    try:
        import sentry_sdk

        if extra:
            with sentry_sdk.push_scope() as scope:
                for key, value in extra.items():
                    scope.set_extra(key, value)
                sentry_sdk.capture_exception(exception)
        else:
            sentry_sdk.capture_exception(exception)
    except ImportError:
        # Sentry not installed, just log
        logger.exception(f"Exception occurred (Sentry not available): {exception}")


def capture_message(message: str, level: str = "info", extra: Optional[dict] = None) -> None:
    """
    Capture a message to Sentry.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        extra: Optional additional context to include
    """
    try:
        import sentry_sdk

        if extra:
            with sentry_sdk.push_scope() as scope:
                for key, value in extra.items():
                    scope.set_extra(key, value)
                sentry_sdk.capture_message(message, level=level)
        else:
            sentry_sdk.capture_message(message, level=level)
    except ImportError:
        # Sentry not installed, just log
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, f"Message (Sentry not available): {message}")
