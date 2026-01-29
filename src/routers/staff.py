"""
Staff Router - User management pages and actions.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from src.db.session import get_db
from src.services.staff_service import StaffService
from src.routers.dependencies.auth_cookie import require_auth

router = APIRouter(prefix="/staff", tags=["staff"])
templates = Jinja2Templates(directory="src/templates")

# Add now() function to Jinja2 globals for templates
templates.env.globals["now"] = datetime.utcnow


# ============================================================
# Main Pages
# ============================================================


@router.get("", response_class=HTMLResponse)
async def staff_list_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None, description="Search query"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query("all", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
):
    """Render the staff list page."""
    # Handle auth redirect
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Check if user has permission (admin, officer, or staff)
    user_roles = current_user.get("roles", [])
    if not any(r in ["admin", "officer", "staff"] for r in user_roles):
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request, "message": "You don't have permission to access staff management."},
            status_code=403,
        )

    service = StaffService(db)

    # Get users with search/filter
    users, total, total_pages = service.search_users(
        query=q,
        role=role,
        status=status,
        page=page,
        per_page=20,
    )

    # Get all roles for filter dropdown
    all_roles = service.get_all_roles()

    # Get counts for status badges
    counts = service.get_user_counts()

    return templates.TemplateResponse(
        "staff/index.html",
        {
            "request": request,
            "user": current_user,
            "users": users,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "role_filter": role or "all",
            "status_filter": status or "all",
            "all_roles": all_roles,
            "counts": counts,
            "service": service,  # Pass service for is_user_locked helper
        },
    )


# ============================================================
# HTMX Partials
# ============================================================


@router.get("/search", response_class=HTMLResponse)
async def staff_search_partial(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query("all"),
    page: int = Query(1, ge=1),
):
    """
    HTMX partial: Return just the table body for search results.
    Used for live search without full page reload.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            content="<tr><td colspan='6'>Session expired. Please refresh.</td></tr>",
            status_code=401,
        )

    service = StaffService(db)

    users, total, total_pages = service.search_users(
        query=q,
        role=role,
        status=status,
        page=page,
        per_page=20,
    )

    return templates.TemplateResponse(
        "staff/partials/_table_body.html",
        {
            "request": request,
            "users": users,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "role_filter": role or "all",
            "status_filter": status or "all",
            "service": service,
        },
    )
