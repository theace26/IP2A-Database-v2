"""
Operations Frontend Router.

Handles all Union Operations frontend pages:
- Operations landing page with overview stats
- SALTing activities management
- Benevolence fund management
- Grievance tracking
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.enums import (
    BenevolenceReason,
    BenevolenceStatus,
    GrievanceStatus,
    GrievanceStep,
    SALTingActivityType,
    SALTingOutcome,
)
from src.db.session import get_db
from src.routers.dependencies.auth_cookie import require_auth
from src.services.operations_frontend_service import OperationsFrontendService

router = APIRouter(prefix="/operations", tags=["Operations Frontend"])

templates = Jinja2Templates(directory="src/templates")


# ============================================================
# Landing Page
# ============================================================


@router.get("", response_class=HTMLResponse)
async def operations_landing_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render operations landing page with overview stats."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    stats = await service.get_overview_stats()

    return templates.TemplateResponse(
        "operations/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
        },
    )


# ============================================================
# SALTing Routes
# ============================================================


@router.get("/salting", response_class=HTMLResponse)
async def salting_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render SALTing activities list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    stats = await service.get_salting_stats()
    all_types = [t.value for t in SALTingActivityType]
    all_outcomes = [o.value for o in SALTingOutcome]

    return templates.TemplateResponse(
        "operations/salting/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "all_types": all_types,
            "all_outcomes": all_outcomes,
            "get_outcome_badge_class": service.get_salting_outcome_badge_class,
            "get_type_badge_class": service.get_salting_type_badge_class,
        },
    )


@router.get("/salting/search", response_class=HTMLResponse)
async def salting_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    activity_type: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
):
    """HTMX partial: SALTing activities table body."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = OperationsFrontendService(db)
    activities, total, total_pages = await service.search_salting_activities(
        query=q,
        activity_type=activity_type,
        outcome=outcome,
        page=page,
    )

    return templates.TemplateResponse(
        "operations/salting/partials/_table.html",
        {
            "request": request,
            "activities": activities,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "type_filter": activity_type or "all",
            "outcome_filter": outcome or "all",
            "get_outcome_badge_class": service.get_salting_outcome_badge_class,
            "get_type_badge_class": service.get_salting_type_badge_class,
        },
    )


@router.get("/salting/{activity_id}", response_class=HTMLResponse)
async def salting_detail_page(
    request: Request,
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render SALTing activity detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    activity = await service.get_salting_activity_by_id(activity_id)

    if not activity:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "SALTing activity not found"},
            status_code=404,
        )

    all_types = [t.value for t in SALTingActivityType]
    all_outcomes = [o.value for o in SALTingOutcome]

    return templates.TemplateResponse(
        "operations/salting/detail.html",
        {
            "request": request,
            "user": current_user,
            "activity": activity,
            "all_types": all_types,
            "all_outcomes": all_outcomes,
            "get_outcome_badge_class": service.get_salting_outcome_badge_class,
            "get_type_badge_class": service.get_salting_type_badge_class,
        },
    )


# ============================================================
# Benevolence Routes
# ============================================================


@router.get("/benevolence", response_class=HTMLResponse)
async def benevolence_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render benevolence applications list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    stats = await service.get_benevolence_stats()
    all_statuses = [s.value for s in BenevolenceStatus]
    all_reasons = [r.value for r in BenevolenceReason]

    return templates.TemplateResponse(
        "operations/benevolence/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "all_statuses": all_statuses,
            "all_reasons": all_reasons,
            "get_status_badge_class": service.get_benevolence_status_badge_class,
            "get_reason_badge_class": service.get_benevolence_reason_badge_class,
        },
    )


@router.get("/benevolence/search", response_class=HTMLResponse)
async def benevolence_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    reason: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
):
    """HTMX partial: Benevolence applications table body."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = OperationsFrontendService(db)
    applications, total, total_pages = await service.search_benevolence_applications(
        query=q,
        status=status,
        reason=reason,
        page=page,
    )

    return templates.TemplateResponse(
        "operations/benevolence/partials/_table.html",
        {
            "request": request,
            "applications": applications,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "status_filter": status or "all",
            "reason_filter": reason or "all",
            "get_status_badge_class": service.get_benevolence_status_badge_class,
            "get_reason_badge_class": service.get_benevolence_reason_badge_class,
        },
    )


@router.get("/benevolence/{application_id}", response_class=HTMLResponse)
async def benevolence_detail_page(
    request: Request,
    application_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render benevolence application detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    application = await service.get_benevolence_application_by_id(application_id)

    if not application:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Application not found"},
            status_code=404,
        )

    all_statuses = [s.value for s in BenevolenceStatus]

    return templates.TemplateResponse(
        "operations/benevolence/detail.html",
        {
            "request": request,
            "user": current_user,
            "application": application,
            "all_statuses": all_statuses,
            "get_status_badge_class": service.get_benevolence_status_badge_class,
            "get_reason_badge_class": service.get_benevolence_reason_badge_class,
        },
    )


# ============================================================
# Grievance Routes
# ============================================================


@router.get("/grievances", response_class=HTMLResponse)
async def grievances_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render grievances list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    stats = await service.get_grievance_stats()
    all_statuses = [s.value for s in GrievanceStatus]
    all_steps = [s.value for s in GrievanceStep]

    return templates.TemplateResponse(
        "operations/grievances/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "all_statuses": all_statuses,
            "all_steps": all_steps,
            "get_status_badge_class": service.get_grievance_status_badge_class,
            "get_step_badge_class": service.get_grievance_step_badge_class,
        },
    )


@router.get("/grievances/search", response_class=HTMLResponse)
async def grievances_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    step: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
):
    """HTMX partial: Grievances table body."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = OperationsFrontendService(db)
    grievances, total, total_pages = await service.search_grievances(
        query=q,
        status=status,
        step=step,
        page=page,
    )

    return templates.TemplateResponse(
        "operations/grievances/partials/_table.html",
        {
            "request": request,
            "grievances": grievances,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "status_filter": status or "all",
            "step_filter": step or "all",
            "get_status_badge_class": service.get_grievance_status_badge_class,
            "get_step_badge_class": service.get_grievance_step_badge_class,
        },
    )


@router.get("/grievances/{grievance_id}", response_class=HTMLResponse)
async def grievance_detail_page(
    request: Request,
    grievance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render grievance detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    grievance = await service.get_grievance_by_id(grievance_id)

    if not grievance:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Grievance not found"},
            status_code=404,
        )

    all_statuses = [s.value for s in GrievanceStatus]
    all_steps = [s.value for s in GrievanceStep]

    return templates.TemplateResponse(
        "operations/grievances/detail.html",
        {
            "request": request,
            "user": current_user,
            "grievance": grievance,
            "all_statuses": all_statuses,
            "all_steps": all_steps,
            "get_status_badge_class": service.get_grievance_status_badge_class,
            "get_step_badge_class": service.get_grievance_step_badge_class,
        },
    )
