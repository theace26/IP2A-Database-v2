"""
Frontend routes for serving HTML pages.

These routes render Jinja2 templates and handle browser-based navigation.
API routes remain separate in their respective routers.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.routers.dependencies.auth_cookie import (
    require_auth,
    require_auth_api,
    get_current_user_from_cookie,
)
from src.services.setup_service import (
    has_any_users,
    validate_password,
    create_setup_user,
    get_available_roles,
    PasswordValidationError,
    is_setup_required,
    get_default_admin_status,
    DEFAULT_ADMIN_EMAIL,
)

router = APIRouter(tags=["Frontend"])

# Initialize templates
templates = Jinja2Templates(directory="src/templates")


# ============================================================================
# Helper: Add common template context
# ============================================================================


def get_template_context(request: Request, current_user=None, **kwargs):
    """Build common context for all templates."""
    return {
        "request": request,
        "current_user": current_user,
        "now": datetime.now(),
        "messages": [],  # Flash messages placeholder
        **kwargs,
    }


def _format_time_ago(dt: datetime) -> str:
    """Format datetime as relative time string."""
    now = datetime.utcnow()
    diff = now - dt

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"

    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"

    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"

    return "Just now"


# ============================================================================
# Public Routes (No Auth Required)
# ============================================================================


@router.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_from_cookie),
):
    """Root redirect to setup if needed, dashboard if authenticated, otherwise to login."""
    # Check if system needs setup (no users or only default admin)
    if is_setup_required(db):
        return RedirectResponse(url="/setup", status_code=302)

    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    db: Session = Depends(get_db),
    next: Optional[str] = None,
    message: Optional[str] = None,
    type: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user_from_cookie),
):
    """Render login page. Redirect to setup if needed, dashboard if logged in."""
    # Check if system needs setup (no users or only default admin)
    if is_setup_required(db):
        return RedirectResponse(url="/setup", status_code=302)

    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)

    # Ensure message is a string (fix [object Object] bug)
    display_message = None
    if message:
        if isinstance(message, str):
            display_message = message
        else:
            display_message = str(message)

    return templates.TemplateResponse(
        "auth/login.html",
        get_template_context(
            request, next=next or "/dashboard", message=display_message, message_type=type
        ),
    )


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Render forgot password page."""
    return templates.TemplateResponse(
        "auth/forgot_password.html", get_template_context(request)
    )


# ============================================================================
# Setup Routes (First-Time Configuration)
# ============================================================================


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """Render setup page for first-time system configuration."""
    # If setup is not required (non-default users exist), redirect to login
    if not is_setup_required(db):
        return RedirectResponse(
            url="/login?message=System+already+configured&type=info",
            status_code=302,
        )

    roles = get_available_roles()
    default_admin_status = get_default_admin_status(db)

    return templates.TemplateResponse(
        "auth/setup.html",
        get_template_context(
            request,
            roles=roles,
            default_admin_status=default_admin_status,
        ),
    )


@router.post("/setup", response_class=HTMLResponse)
async def setup_submit(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle setup form submission."""
    # If setup is not required, redirect to login
    if not is_setup_required(db):
        return RedirectResponse(
            url="/login?message=System+already+configured&type=info",
            status_code=302,
        )

    # Get form data
    form = await request.form()
    email = form.get("email", "").strip()
    first_name = form.get("first_name", "").strip()
    last_name = form.get("last_name", "").strip()
    password = form.get("password", "")
    confirm_password = form.get("confirm_password", "")
    role = form.get("role", "admin")
    disable_default_admin = form.get("disable_default_admin") == "1"

    roles = get_available_roles()
    default_admin_status = get_default_admin_status(db)
    form_data = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "disable_default_admin": disable_default_admin,
    }

    # Validate required fields
    if not all([email, first_name, last_name, password, confirm_password]):
        return templates.TemplateResponse(
            "auth/setup.html",
            get_template_context(
                request,
                roles=roles,
                default_admin_status=default_admin_status,
                error="All fields are required",
                form_data=form_data,
            ),
        )

    # Prevent using the default admin email
    if email.lower() == DEFAULT_ADMIN_EMAIL:
        return templates.TemplateResponse(
            "auth/setup.html",
            get_template_context(
                request,
                roles=roles,
                default_admin_status=default_admin_status,
                error=f"Cannot use {DEFAULT_ADMIN_EMAIL} - please choose a different email address",
                form_data=form_data,
            ),
        )

    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse(
            "auth/setup.html",
            get_template_context(
                request,
                roles=roles,
                default_admin_status=default_admin_status,
                error="Passwords do not match",
                form_data=form_data,
            ),
        )

    # Validate password requirements
    password_errors = validate_password(password)
    if password_errors:
        return templates.TemplateResponse(
            "auth/setup.html",
            get_template_context(
                request,
                roles=roles,
                default_admin_status=default_admin_status,
                errors=password_errors,
                form_data=form_data,
            ),
        )

    # Create the user account
    try:
        create_setup_user(
            db=db,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            disable_default_admin_account=disable_default_admin,
        )
    except PasswordValidationError as e:
        return templates.TemplateResponse(
            "auth/setup.html",
            get_template_context(
                request,
                roles=roles,
                default_admin_status=default_admin_status,
                errors=e.errors,
                form_data=form_data,
            ),
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "auth/setup.html",
            get_template_context(
                request,
                roles=roles,
                default_admin_status=default_admin_status,
                error=str(e),
                form_data=form_data,
            ),
        )

    # Success - redirect to login
    return RedirectResponse(
        url="/login?message=Setup+complete!+Please+log+in+with+your+new+account&type=success",
        status_code=302,
    )


@router.get("/auth/change-password", response_class=HTMLResponse)
async def change_password_page(
    request: Request,
    error: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user_from_cookie),
):
    """Render change password page for users who must change their password."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "auth/change_password.html",
        get_template_context(request, current_user=current_user, error=error),
    )


@router.post("/auth/change-password", response_class=HTMLResponse)
async def change_password_submit(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_from_cookie),
):
    """Handle password change submission."""
    from src.models.user import User
    from src.core.security import hash_password, verify_password
    from src.services.auth_service import create_tokens

    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    form = await request.form()
    current_password = form.get("current_password")
    new_password = form.get("new_password")
    confirm_password = form.get("confirm_password")

    # Validate passwords match
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "auth/change_password.html",
            get_template_context(
                request, current_user=current_user, error="New passwords do not match"
            ),
        )

    # Validate minimum length
    if len(new_password) < 8:
        return templates.TemplateResponse(
            "auth/change_password.html",
            get_template_context(
                request,
                current_user=current_user,
                error="Password must be at least 8 characters",
            ),
        )

    # Get user from database
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Verify current password
    if not verify_password(current_password, user.password_hash):
        return templates.TemplateResponse(
            "auth/change_password.html",
            get_template_context(
                request, current_user=current_user, error="Current password is incorrect"
            ),
        )

    # Update password and clear the flag
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.commit()

    # Generate new tokens with updated must_change_password=False
    tokens = create_tokens(db, user)

    # Redirect to dashboard with new cookies
    response = RedirectResponse(
        url="/dashboard?message=Password+changed+successfully&type=success",
        status_code=302,
    )
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=tokens["expires_in"],
        path="/",
    )

    return response


# ============================================================================
# Protected Routes (Auth Required)
# ============================================================================


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render main dashboard with real data."""
    # Handle redirect from auth middleware
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Import here to avoid circular imports
    from src.services.dashboard_service import DashboardService

    # Get real stats from dashboard service
    dashboard_service = DashboardService(db)
    stats = await dashboard_service.get_stats()
    activities = await dashboard_service.get_recent_activity(limit=10)

    # Format activity timestamps
    for activity in activities:
        activity["time_ago"] = _format_time_ago(activity["timestamp"])

    return templates.TemplateResponse(
        "dashboard/index.html",
        get_template_context(
            request,
            current_user=current_user,
            user=current_user,
            stats=stats,
            activities=activities,
        ),
    )


@router.get("/api/dashboard/refresh", response_class=HTMLResponse)
async def dashboard_stats_partial(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth_api),
):
    """Return just the stats cards for HTMX refresh."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            content="<div class='alert alert-error'>Unauthorized</div>", status_code=401
        )

    from src.services.dashboard_service import DashboardService

    dashboard_service = DashboardService(db)
    stats = await dashboard_service.get_stats()

    # Return stats HTML partial
    html = f"""
    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-primary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
        </div>
        <div class="stat-title">Active Members</div>
        <div class="stat-value text-primary">{stats['active_members']:,}</div>
        <div class="stat-desc">{stats['members_change']} this month</div>
    </div>

    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-secondary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
        </div>
        <div class="stat-title">Active Students</div>
        <div class="stat-value text-secondary">{stats['active_students']}</div>
        <div class="stat-desc">In current cohorts</div>
    </div>

    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-warning">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
        </div>
        <div class="stat-title">Pending Grievances</div>
        <div class="stat-value text-warning">{stats['pending_grievances']}</div>
        <div class="stat-desc">Requires attention</div>
    </div>

    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-success">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
        </div>
        <div class="stat-title">Dues MTD</div>
        <div class="stat-value text-success">${stats['dues_mtd']:,.0f}</div>
        <div class="stat-desc">This month</div>
    </div>
    """
    return HTMLResponse(content=html)


@router.get("/api/dashboard/recent-activity", response_class=HTMLResponse)
async def recent_activity_partial(
    request: Request,
    db: Session = Depends(get_db),
):
    """Return recent activity from audit log."""
    from src.services.dashboard_service import DashboardService

    dashboard_service = DashboardService(db)
    activities = await dashboard_service.get_recent_activity(limit=10)

    if not activities:
        return HTMLResponse(
            content="""
            <p class="text-center text-base-content/50 py-4">No recent activity</p>
        """
        )

    items_html = ""
    for activity in activities:
        badge = activity["badge"]
        time_ago = _format_time_ago(activity["timestamp"])
        items_html += f"""
        <li class="flex items-start gap-3 p-2 rounded hover:bg-base-200">
            <div class="badge {badge['class']} badge-sm mt-1">{badge['text']}</div>
            <div>
                <p class="text-sm font-medium">{activity['description']}</p>
                <p class="text-xs text-base-content/60">{time_ago}</p>
            </div>
        </li>
        """

    return HTMLResponse(
        content=f"""
        <ul class="space-y-3">{items_html}</ul>
        <p class="text-xs text-base-content/50 mt-4 text-center">Showing last 10 activities</p>
    """
    )


@router.get("/logout")
async def logout_page(request: Request):
    """Handle logout - clear cookies and redirect to login."""
    response = RedirectResponse(
        url="/login?message=You+have+been+logged+out&type=success", status_code=302
    )
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")
    return response


# ============================================================================
# Placeholder Routes (Future Weeks)
# ============================================================================


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """User profile page - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html", get_template_context(request), status_code=404
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html", get_template_context(request), status_code=404
    )


@router.get("/members", response_class=HTMLResponse)
@router.get("/members/{path:path}", response_class=HTMLResponse)
async def members_placeholder(request: Request, path: str = ""):
    """Members pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html", get_template_context(request), status_code=404
    )


@router.get("/dues", response_class=HTMLResponse)
@router.get("/dues/{path:path}", response_class=HTMLResponse)
async def dues_placeholder(request: Request, path: str = ""):
    """Dues pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html", get_template_context(request), status_code=404
    )


@router.get("/grievances", response_class=HTMLResponse)
@router.get("/grievances/{path:path}", response_class=HTMLResponse)
async def grievances_placeholder(request: Request, path: str = ""):
    """Grievances pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html", get_template_context(request), status_code=404
    )


@router.get("/training", response_class=HTMLResponse)
@router.get("/training/{path:path}", response_class=HTMLResponse)
async def training_placeholder(request: Request, path: str = ""):
    """Training pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html", get_template_context(request), status_code=404
    )


@router.get("/staff", response_class=HTMLResponse)
@router.get("/staff/{path:path}", response_class=HTMLResponse)
async def staff_placeholder(request: Request, path: str = ""):
    """Staff pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html", get_template_context(request), status_code=404
    )


@router.get("/organizations", response_class=HTMLResponse)
@router.get("/organizations/{path:path}", response_class=HTMLResponse)
async def organizations_placeholder(request: Request, path: str = ""):
    """Organizations pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html", get_template_context(request), status_code=404
    )


@router.get("/reports", response_class=HTMLResponse)
@router.get("/reports/{path:path}", response_class=HTMLResponse)
async def reports_placeholder(request: Request, path: str = ""):
    """Reports pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html", get_template_context(request), status_code=404
    )
