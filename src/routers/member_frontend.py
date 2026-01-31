"""
Member Frontend Router - HTML pages for member management.
"""

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.db.session import get_db
from src.services.member_frontend_service import MemberFrontendService
from src.routers.dependencies.auth_cookie import require_auth
from src.db.enums import MemberStatus, MemberClassification

router = APIRouter(prefix="/members", tags=["members-frontend"])
templates = Jinja2Templates(directory="src/templates")


# ============================================================
# Main Pages
# ============================================================


@router.get("", response_class=HTMLResponse)
async def members_landing_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the members landing page with overview stats."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = MemberFrontendService(db)

    # Get stats
    stats = await service.get_member_stats()

    # Get classification breakdown
    classification_breakdown = await service.get_classification_breakdown()

    # Get recent members
    recent_members = await service.get_recent_members(limit=5)

    # Get all statuses and classifications for filter dropdowns
    all_statuses = [s.value for s in MemberStatus]
    all_classifications = [c.value for c in MemberClassification]

    return templates.TemplateResponse(
        "members/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "classification_breakdown": classification_breakdown,
            "recent_members": recent_members,
            "all_statuses": all_statuses,
            "all_classifications": all_classifications,
            "format_classification": service.format_classification,
            "get_status_badge_class": service.get_status_badge_class,
        },
    )


@router.get("/stats", response_class=HTMLResponse)
async def members_stats_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: Return just the stats cards."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/auth/login?next=/members"},
        )

    service = MemberFrontendService(db)
    stats = await service.get_member_stats()

    return templates.TemplateResponse(
        "members/partials/_stats.html",
        {
            "request": request,
            "stats": stats,
        },
    )


# ============================================================
# Search Endpoint (for HTMX)
# ============================================================


@router.get("/search", response_class=HTMLResponse)
async def members_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status"),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    page: int = Query(1, ge=1, description="Page number"),
):
    """
    HTMX partial: Return member table body for search results.
    Used for live search without full page reload.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/auth/login?next=/members"},
        )

    service = MemberFrontendService(db)

    members, total, total_pages = await service.search_members(
        query=q,
        status=status,
        classification=classification,
        page=page,
        per_page=20,
    )

    # Get current employer for each member
    members_with_employer = []
    for member in members:
        employer = await service.get_member_current_employer(member)
        members_with_employer.append(
            {
                "member": member,
                "current_employer": employer,
            }
        )

    return templates.TemplateResponse(
        "members/partials/_table.html",
        {
            "request": request,
            "members_data": members_with_employer,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "status_filter": status or "all",
            "classification_filter": classification or "all",
            "format_classification": service.format_classification,
            "get_status_badge_class": service.get_status_badge_class,
            "get_classification_badge_class": service.get_classification_badge_class,
        },
    )


# ============================================================
# Member Detail Page
# ============================================================


@router.get("/{member_id}", response_class=HTMLResponse)
async def member_detail_page(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the full member detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = MemberFrontendService(db)
    member = await service.get_member_by_id(member_id)

    if not member:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Member not found"},
            status_code=404,
        )

    # Get current employer
    current_employer = await service.get_member_current_employer(member)

    # Get employment history
    employment_history = await service.get_employment_history(member_id)

    # Get dues summary
    dues_summary = await service.get_member_dues_summary(member_id)

    # Get all statuses and classifications for editing
    all_statuses = [s.value for s in MemberStatus]
    all_classifications = [c.value for c in MemberClassification]

    return templates.TemplateResponse(
        "members/detail.html",
        {
            "request": request,
            "user": current_user,
            "member": member,
            "current_employer": current_employer,
            "employment_history": employment_history,
            "dues_summary": dues_summary,
            "all_statuses": all_statuses,
            "all_classifications": all_classifications,
            "format_classification": service.format_classification,
            "get_status_badge_class": service.get_status_badge_class,
            "get_classification_badge_class": service.get_classification_badge_class,
        },
    )


# ============================================================
# HTMX Partial Endpoints
# ============================================================


@router.get("/{member_id}/edit", response_class=HTMLResponse)
async def member_edit_modal(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: Return the edit modal content for a member."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/auth/login?next=/members"},
        )

    service = MemberFrontendService(db)
    member = await service.get_member_by_id(member_id)

    if not member:
        return HTMLResponse("Member not found", status_code=404)

    all_statuses = [s.value for s in MemberStatus]
    all_classifications = [c.value for c in MemberClassification]

    return templates.TemplateResponse(
        "members/partials/_edit_modal.html",
        {
            "request": request,
            "member": member,
            "all_statuses": all_statuses,
            "all_classifications": all_classifications,
            "format_classification": service.format_classification,
        },
    )


@router.get("/{member_id}/employment", response_class=HTMLResponse)
async def member_employment_partial(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: Return employment history section."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/auth/login?next=/members"},
        )

    service = MemberFrontendService(db)
    employment_history = await service.get_employment_history(member_id)

    return templates.TemplateResponse(
        "members/partials/_employment.html",
        {
            "request": request,
            "member_id": member_id,
            "employment_history": employment_history,
        },
    )


@router.get("/{member_id}/dues", response_class=HTMLResponse)
async def member_dues_partial(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: Return dues summary section."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/auth/login?next=/members"},
        )

    service = MemberFrontendService(db)
    dues_summary = await service.get_member_dues_summary(member_id)

    return templates.TemplateResponse(
        "members/partials/_dues_summary.html",
        {
            "request": request,
            "member_id": member_id,
            "dues_summary": dues_summary,
        },
    )
