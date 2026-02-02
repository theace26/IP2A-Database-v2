"""
Grants Frontend Router.

Handles all Grant Management frontend pages:
- Grants landing page with overview stats
- Grant list and detail views
- Enrollment management
- Expense tracking
- Report generation
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.enums import GrantStatus, GrantEnrollmentStatus, GrantOutcome
from src.routers.dependencies.auth_cookie import require_auth
from src.services.grant_metrics_service import GrantMetricsService
from src.services.grant_report_service import GrantReportService
from src.models import Grant
from src.models.grant_enrollment import GrantEnrollment

router = APIRouter(prefix="/grants", tags=["Grants Frontend"])

templates = Jinja2Templates(directory="src/templates")


# ============================================================
# Landing Page
# ============================================================


@router.get("", response_class=HTMLResponse)
def grants_landing_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render grants landing page with overview stats."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = GrantMetricsService(db)
    stats = service.get_dashboard_stats()
    grants = service.get_all_grants_summary()

    return templates.TemplateResponse(
        "grants/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "grants": grants,
            "status_badge": GrantMetricsService.get_status_badge_class,
        },
    )


# ============================================================
# Grant List
# ============================================================


@router.get("/list", response_class=HTMLResponse)
def grants_list_page(
    request: Request,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render grants list page with filtering."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    query = db.query(Grant).filter(Grant.is_deleted == False)

    if status:
        try:
            status_enum = GrantStatus(status)
            query = query.filter(Grant.status == status_enum)
        except ValueError:
            pass

    grants = query.order_by(Grant.start_date.desc()).all()

    # Get enrollment counts for each grant
    service = GrantMetricsService(db)
    grants_data = service.get_all_grants_summary()

    return templates.TemplateResponse(
        "grants/list.html",
        {
            "request": request,
            "user": current_user,
            "grants": grants_data,
            "statuses": [s.value for s in GrantStatus],
            "selected_status": status,
            "status_badge": GrantMetricsService.get_status_badge_class,
        },
    )


# ============================================================
# Grant Detail
# ============================================================


@router.get("/{grant_id}", response_class=HTMLResponse)
def grant_detail_page(
    request: Request,
    grant_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render grant detail page with metrics dashboard."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = GrantMetricsService(db)
    summary = service.get_grant_summary(grant_id)

    if not summary:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Grant not found"},
            status_code=404,
        )

    return templates.TemplateResponse(
        "grants/detail.html",
        {
            "request": request,
            "user": current_user,
            "summary": summary,
            "status_badge": GrantMetricsService.get_status_badge_class,
            "enrollment_badge": GrantMetricsService.get_enrollment_status_badge_class,
            "outcome_badge": GrantMetricsService.get_outcome_badge_class,
        },
    )


# ============================================================
# Enrollments
# ============================================================


@router.get("/{grant_id}/enrollments", response_class=HTMLResponse)
def grant_enrollments_page(
    request: Request,
    grant_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Manage student enrollments for a grant."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    grant = db.query(Grant).filter(
        Grant.id == grant_id,
        Grant.is_deleted == False
    ).first()

    if not grant:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Grant not found"},
            status_code=404,
        )

    report_service = GrantReportService(db)
    enrollments = report_service._get_enrollment_details(grant_id)

    return templates.TemplateResponse(
        "grants/enrollments.html",
        {
            "request": request,
            "user": current_user,
            "grant": grant,
            "enrollments": enrollments,
            "statuses": [s.value for s in GrantEnrollmentStatus],
            "outcomes": [o.value for o in GrantOutcome],
            "selected_status": status,
            "enrollment_badge": GrantMetricsService.get_enrollment_status_badge_class,
            "outcome_badge": GrantMetricsService.get_outcome_badge_class,
        },
    )


# ============================================================
# Expenses
# ============================================================


@router.get("/{grant_id}/expenses", response_class=HTMLResponse)
def grant_expenses_page(
    request: Request,
    grant_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Manage expenses for a grant."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    grant = db.query(Grant).filter(
        Grant.id == grant_id,
        Grant.is_deleted == False
    ).first()

    if not grant:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Grant not found"},
            status_code=404,
        )

    report_service = GrantReportService(db)
    expenses = report_service._get_expense_details(grant_id)

    # Calculate totals
    total_spent = sum(e["total_price"] for e in expenses)

    return templates.TemplateResponse(
        "grants/expenses.html",
        {
            "request": request,
            "user": current_user,
            "grant": grant,
            "expenses": expenses,
            "total_spent": total_spent,
            "remaining": float(grant.total_amount) - total_spent,
        },
    )


# ============================================================
# Reports
# ============================================================


@router.get("/{grant_id}/reports", response_class=HTMLResponse)
def grant_reports_page(
    request: Request,
    grant_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Report generation page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    grant = db.query(Grant).filter(
        Grant.id == grant_id,
        Grant.is_deleted == False
    ).first()

    if not grant:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Grant not found"},
            status_code=404,
        )

    service = GrantMetricsService(db)
    summary = service.get_grant_summary(grant_id)

    return templates.TemplateResponse(
        "grants/reports.html",
        {
            "request": request,
            "user": current_user,
            "grant": grant,
            "summary": summary,
        },
    )


@router.get("/{grant_id}/reports/summary", response_class=HTMLResponse)
def grant_summary_report(
    request: Request,
    grant_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Generate and display summary report."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    report_service = GrantReportService(db)
    report = report_service.generate_report(grant_id, "summary")

    if not report:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Grant not found"},
            status_code=404,
        )

    return templates.TemplateResponse(
        "grants/report_summary.html",
        {
            "request": request,
            "user": current_user,
            "report": report,
        },
    )


@router.get("/{grant_id}/reports/excel")
def download_excel_report(
    grant_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Download Excel report for grant."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    report_service = GrantReportService(db)
    excel_buffer = report_service.generate_excel_report(grant_id)

    if not excel_buffer:
        return RedirectResponse(
            url=f"/grants/{grant_id}/reports?error=failed",
            status_code=303
        )

    grant = db.query(Grant).filter(Grant.id == grant_id).first()
    filename = f"grant_report_{grant.grant_number or grant_id}_{date.today().isoformat()}.xlsx"

    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================
# HTMX Partials
# ============================================================


@router.get("/partials/enrollments-table", response_class=HTMLResponse)
def enrollments_table_partial(
    request: Request,
    grant_id: int = Query(...),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial for enrollments table."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401, headers={"HX-Redirect": "/auth/login"})

    query = db.query(GrantEnrollment).filter(
        GrantEnrollment.grant_id == grant_id,
        GrantEnrollment.is_deleted == False
    )

    if status:
        try:
            status_enum = GrantEnrollmentStatus(status)
            query = query.filter(GrantEnrollment.status == status_enum)
        except ValueError:
            pass

    enrollments = query.order_by(GrantEnrollment.enrollment_date.desc()).all()

    # Format for template
    report_service = GrantReportService(db)
    enrollments_data = report_service._get_enrollment_details(grant_id)

    return templates.TemplateResponse(
        "grants/partials/_enrollments_table.html",
        {
            "request": request,
            "enrollments": enrollments_data,
            "enrollment_badge": GrantMetricsService.get_enrollment_status_badge_class,
            "outcome_badge": GrantMetricsService.get_outcome_badge_class,
        },
    )
