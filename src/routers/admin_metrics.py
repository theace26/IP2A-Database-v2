"""Admin metrics dashboard for system monitoring."""

from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models import Member, User, AuditLog, DuesPayment, Student
from src.routers.dependencies.auth_cookie import require_auth

router = APIRouter(prefix="/admin/metrics", tags=["admin-metrics"])
templates = Jinja2Templates(directory="src/templates")


def is_admin(user: dict) -> bool:
    """Check if user has admin role."""
    return "admin" in user.get("roles", [])


@router.get("", response_class=HTMLResponse)
async def metrics_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Admin metrics dashboard."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    if not is_admin(current_user):
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request, "message": "Admin access required"},
            status_code=403,
        )

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today_start - timedelta(days=7)
    month_ago = today_start - timedelta(days=30)

    # User metrics
    total_users = db.scalar(select(func.count(User.id))) or 0
    active_users_today = db.scalar(
        select(func.count(User.id)).where(User.last_login >= today_start)
    ) or 0

    # Member metrics
    total_members = db.scalar(select(func.count(Member.id))) or 0
    active_members = db.scalar(
        select(func.count(Member.id)).where(Member.status == "ACTIVE")
    ) or 0

    # Audit metrics
    audits_today = db.scalar(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= today_start)
    ) or 0
    audits_week = db.scalar(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= week_ago)
    ) or 0

    # Payment metrics
    payments_month = db.scalar(
        select(func.sum(DuesPayment.amount))
        .where(DuesPayment.payment_date >= month_ago.date())
        .where(DuesPayment.status == "PAID")
    ) or 0

    # Student metrics
    active_students = db.scalar(
        select(func.count(Student.id)).where(Student.status == "ACTIVE")
    ) or 0

    return templates.TemplateResponse(
        "admin/metrics.html",
        {
            "request": request,
            "user": current_user,
            "metrics": {
                "users": {
                    "total": total_users,
                    "active_today": active_users_today,
                },
                "members": {
                    "total": total_members,
                    "active": active_members,
                },
                "audit": {
                    "today": audits_today,
                    "week": audits_week,
                },
                "payments": {
                    "month_total": float(payments_month),
                },
                "students": {
                    "active": active_students,
                },
            },
            "generated_at": now.isoformat(),
        },
    )


@router.get("/api", response_model=None)
async def metrics_api(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
) -> dict[str, Any]:
    """API endpoint for metrics (JSON)."""
    if isinstance(current_user, RedirectResponse):
        return {"error": "Not authenticated"}

    if not is_admin(current_user):
        return {"error": "Admin access required"}

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today_start - timedelta(days=7)
    month_ago = today_start - timedelta(days=30)

    return {
        "status": "ok",
        "timestamp": now.isoformat(),
        "metrics": {
            "users": {
                "total": db.scalar(select(func.count(User.id))) or 0,
                "active_today": db.scalar(
                    select(func.count(User.id)).where(User.last_login >= today_start)
                ) or 0,
            },
            "members": {
                "total": db.scalar(select(func.count(Member.id))) or 0,
                "active": db.scalar(
                    select(func.count(Member.id)).where(Member.status == "ACTIVE")
                ) or 0,
            },
            "audit": {
                "today": db.scalar(
                    select(func.count(AuditLog.id)).where(AuditLog.created_at >= today_start)
                ) or 0,
                "week": db.scalar(
                    select(func.count(AuditLog.id)).where(AuditLog.created_at >= week_ago)
                ) or 0,
            },
            "payments": {
                "month_total": float(
                    db.scalar(
                        select(func.sum(DuesPayment.amount))
                        .where(DuesPayment.payment_date >= month_ago.date())
                        .where(DuesPayment.status == "PAID")
                    ) or 0
                ),
            },
            "students": {
                "active": db.scalar(
                    select(func.count(Student.id)).where(Student.status == "ACTIVE")
                ) or 0,
            },
        },
    }
