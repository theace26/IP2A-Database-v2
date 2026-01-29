"""
Staff Router - User management pages and actions.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List

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


# ============================================================
# Edit Modal Endpoints
# ============================================================


@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def get_edit_modal(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """
    HTMX partial: Return the edit modal content for a user.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="<p>Session expired</p>", status_code=401)

    service = StaffService(db)
    user = service.get_user_by_id(user_id)

    if not user:
        return HTMLResponse(content="<p>User not found</p>", status_code=404)

    all_roles = service.get_all_roles()
    user_role_names = [r.name for r in user.roles]

    return templates.TemplateResponse(
        "staff/partials/_edit_modal.html",
        {
            "request": request,
            "target_user": user,
            "all_roles": all_roles,
            "user_role_names": user_role_names,
            "service": service,
        },
    )


@router.post("/{user_id}/edit", response_class=HTMLResponse)
async def update_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
    email: str = Form(...),
    first_name: str = Form(""),
    last_name: str = Form(""),
    roles: List[str] = Form(default=[]),
    is_locked: str = Form(default="false"),
):
    """
    Update user details from the edit modal.
    Returns success/error message for HTMX swap.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="Session expired", status_code=401)

    service = StaffService(db)

    # Convert is_locked string to bool
    lock_account = is_locked.lower() == "true"

    try:
        updated_user = service.update_user(
            user_id=user_id,
            email=email,
            first_name=first_name or None,
            last_name=last_name or None,
            roles=roles,
            is_locked=lock_account,
            updated_by=current_user.get("email", "unknown"),
        )

        if not updated_user:
            return HTMLResponse(
                content='<div class="alert alert-error">User not found</div>',
                status_code=404,
            )

        # Return success message for toast
        return HTMLResponse(
            content="""
            <div class="alert alert-success" id="save-success">
                <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>User updated successfully!</span>
            </div>
            <script>
                setTimeout(() => {
                    document.getElementById('edit-modal').close();
                    htmx.trigger(document.querySelector('input[name="q"]'), 'search');
                }, 1000);
            </script>
            """,
            status_code=200,
        )

    except ValueError as e:
        return HTMLResponse(
            content=f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400,
        )
    except Exception as e:
        return HTMLResponse(
            content=f'<div class="alert alert-error">Failed to update user: {str(e)}</div>',
            status_code=500,
        )


@router.post("/{user_id}/roles", response_class=HTMLResponse)
async def update_user_roles(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
    roles: List[str] = Form(default=[]),
):
    """
    Update only the user's roles.
    Returns updated role badges HTML.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="Session expired", status_code=401)

    service = StaffService(db)

    try:
        updated_user = service.update_user_roles(
            user_id=user_id,
            roles=roles,
            updated_by=current_user.get("email", "unknown"),
        )

        if not updated_user:
            return HTMLResponse(content="User not found", status_code=404)

        # Return updated role badges
        badges_html = ""
        for role in updated_user.roles:
            badge_class = (
                "primary"
                if role.name == "admin"
                else "secondary"
                if role.name == "officer"
                else "accent"
                if role.name == "staff"
                else "ghost"
            )
            badges_html += f'<span class="badge badge-{badge_class} badge-sm">{role.name}</span>'

        if not updated_user.roles:
            badges_html = '<span class="badge badge-ghost badge-sm">No roles</span>'

        return HTMLResponse(content=badges_html)

    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
