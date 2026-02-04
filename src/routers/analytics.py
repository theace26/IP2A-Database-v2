"""Analytics dashboard routes."""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.services.analytics_service import AnalyticsService
from src.services.report_builder_service import ReportBuilderService
from src.routers.dependencies.auth_cookie import require_auth

router = APIRouter(prefix="/analytics", tags=["Analytics"])

templates = Jinja2Templates(directory="src/templates")


def check_officer_role(current_user: dict) -> bool:
    """Check if user has officer-level access or higher."""
    officer_roles = {"admin", "officer", "secretary", "treasurer", "business_manager"}
    user_roles = set(current_user.get("roles", []))
    return bool(user_roles & officer_roles)


@router.get("", response_class=HTMLResponse, response_model=None)
async def analytics_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """Executive analytics dashboard."""
    # Handle redirect
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Check role access
    if not check_officer_role(current_user):
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request, "message": "Analytics requires officer-level access"},
            status_code=403,
        )

    analytics = AnalyticsService(db)

    membership = analytics.get_membership_stats()
    membership_trend = analytics.get_membership_trend(months=12)
    dues = analytics.get_dues_analytics()
    training = analytics.get_training_metrics()
    activity = analytics.get_activity_metrics(days=30)

    return templates.TemplateResponse(
        "analytics/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "membership": membership,
            "membership_trend": membership_trend,
            "dues": dues,
            "training": training,
            "activity": activity,
        },
    )


@router.get("/membership", response_class=HTMLResponse, response_model=None)
async def membership_analytics(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """Detailed membership analytics."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    if not check_officer_role(current_user):
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request},
            status_code=403,
        )

    analytics = AnalyticsService(db)

    stats = analytics.get_membership_stats()
    trend = analytics.get_membership_trend(months=24)

    return templates.TemplateResponse(
        "analytics/membership.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats,
            "trend": trend,
        },
    )


@router.get("/dues", response_class=HTMLResponse, response_model=None)
async def dues_analytics(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """Detailed dues analytics."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    if not check_officer_role(current_user):
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request},
            status_code=403,
        )

    analytics = AnalyticsService(db)

    dues = analytics.get_dues_analytics()
    delinquency = analytics.get_delinquency_report()

    return templates.TemplateResponse(
        "analytics/dues.html",
        {
            "request": request,
            "current_user": current_user,
            "dues": dues,
            "delinquency": delinquency,
        },
    )


@router.get("/builder", response_class=HTMLResponse, response_model=None)
async def report_builder_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """Custom report builder page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    if not check_officer_role(current_user):
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request},
            status_code=403,
        )

    builder = ReportBuilderService(db)
    entities = builder.get_available_entities()

    return templates.TemplateResponse(
        "analytics/builder.html",
        {
            "request": request,
            "current_user": current_user,
            "entities": entities,
        },
    )


@router.post("/api/build", response_model=None)
async def build_report_api(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """API endpoint to build a report."""
    if isinstance(current_user, RedirectResponse):
        return {"error": "Not authenticated"}

    if not check_officer_role(current_user):
        return {"error": "Access denied"}

    data = await request.json()

    builder = ReportBuilderService(db)
    try:
        report = builder.build_report(
            entity=data.get("entity", ""),
            fields=data.get("fields", []),
            filters=data.get("filters"),
            order_by=data.get("order_by"),
            limit=data.get("limit", 1000),
        )
        return report
    except ValueError as e:
        return {"error": str(e)}


@router.get("/export/csv", response_model=None)
async def export_csv(
    request: Request,
    entity: str,
    fields: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """Export report as CSV."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    if not check_officer_role(current_user):
        return Response(content="Access denied", status_code=403)

    builder = ReportBuilderService(db)
    try:
        field_list = fields.split(",") if fields else []
        report = builder.build_report(entity=entity, fields=field_list)
        csv_content = builder.export_to_csv(report)

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{entity}_report.csv"'
            },
        )
    except ValueError as e:
        return Response(content=str(e), status_code=400)


@router.get("/export/excel", response_model=None)
async def export_excel(
    request: Request,
    entity: str,
    fields: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """Export report as Excel."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    if not check_officer_role(current_user):
        return Response(content="Access denied", status_code=403)

    builder = ReportBuilderService(db)
    try:
        field_list = fields.split(",") if fields else []
        report = builder.build_report(entity=entity, fields=field_list)
        excel_content = builder.export_to_excel(report)

        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{entity}_report.xlsx"'
            },
        )
    except ValueError as e:
        return Response(content=str(e), status_code=400)
