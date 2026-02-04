"""Enhanced health check endpoints for production monitoring.

Provides:
- /health/live: Simple liveness check (is the app running?)
- /health/ready: Readiness check (are all dependencies ready?)
- /health: Basic health check (alias for live)
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def liveness_check() -> dict[str, Any]:
    """
    Liveness probe - checks if the application is running.

    Used by container orchestration (K8s, Railway, etc.) to determine
    if the container should be restarted.

    Returns 200 if the app is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness probe - checks if all dependencies are available.

    Used by container orchestration to determine if traffic
    should be routed to this instance.

    Checks:
    - Database connectivity
    - S3 connectivity (if configured)

    Returns:
    - status: "healthy" if all checks pass, "degraded" if some fail
    - checks: Individual check results
    - version: Application version
    """
    checks: dict[str, dict[str, Any]] = {}
    overall_healthy = True

    # Database check
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        checks["database"] = {
            "status": "healthy",
            "latency_ms": None,  # Could add timing here
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        overall_healthy = False

    # S3 check (only if configured)
    if settings.S3_ENDPOINT_URL:
        try:
            import boto3
            from botocore.config import Config

            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                region_name=settings.S3_REGION,
                config=Config(connect_timeout=5, read_timeout=5),
            )
            s3_client.list_buckets()
            checks["s3"] = {"status": "healthy"}
        except Exception as e:
            checks["s3"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            # S3 failure is degraded, not critical
            # overall_healthy = False

    # Stripe check (only verify key is configured, don't make API call)
    if settings.STRIPE_SECRET_KEY:
        checks["stripe"] = {
            "status": "configured",
            "note": "API key present",
        }

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("")
def basic_health_check() -> dict[str, Any]:
    """
    Basic health check - alias for liveness check.

    Simple endpoint that returns 200 if the app is running.
    Used for basic uptime monitoring.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/metrics")
def metrics_endpoint(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Basic metrics endpoint for monitoring.

    Returns counts of key entities for dashboards and alerting.
    Note: This is a lightweight alternative to Prometheus metrics.
    For production, consider using prometheus_fastapi_instrumentator.
    """
    from sqlalchemy import func, select
    from src.models import Member, User, Student, DuesPayment

    try:
        # Get counts
        member_count = db.scalar(select(func.count(Member.id))) or 0
        user_count = db.scalar(select(func.count(User.id))) or 0
        student_count = db.scalar(select(func.count(Student.id))) or 0

        # Get today's payment count
        today = datetime.now(timezone.utc).date()
        payment_count_today = db.scalar(
            select(func.count(DuesPayment.id)).where(
                func.date(DuesPayment.payment_date) == today
            )
        ) or 0

        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "members_total": member_count,
                "users_total": user_count,
                "students_total": student_count,
                "payments_today": payment_count_today,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
