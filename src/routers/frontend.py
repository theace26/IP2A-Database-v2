"""
Frontend routes for serving HTML pages.

These routes render Jinja2 templates and handle browser-based navigation.
API routes remain separate in their respective routers.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.session import get_db

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
        **kwargs
    }


# ============================================================================
# Public Routes (No Auth Required)
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root redirect to login or dashboard."""
    # TODO: Week 2 - Check if user is authenticated via cookie
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page."""
    return templates.TemplateResponse(
        "auth/login.html",
        get_template_context(request)
    )


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Render forgot password page."""
    return templates.TemplateResponse(
        "auth/forgot_password.html",
        get_template_context(request)
    )


# ============================================================================
# Protected Routes (Auth Required)
# NOTE: Week 2 will add cookie-based auth middleware
# ============================================================================

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """Render main dashboard."""
    # TODO: Week 2 - Replace with real stats queries once auth works
    stats = {
        "member_count": 6247,
        "student_count": 42,
        "open_grievances": 18,
        "dues_mtd": 127450.00
    }

    # Placeholder user for now (Week 2 will use real authenticated user)
    current_user = type('User', (), {
        'first_name': 'Admin',
        'last_name': 'User',
        'email': 'admin@local46.org'
    })()

    # Placeholder activities (Week 2 will query audit log)
    activities = []

    return templates.TemplateResponse(
        "dashboard/index.html",
        get_template_context(
            request,
            current_user=current_user,
            stats=stats,
            activities=activities
        )
    )


@router.get("/logout")
async def logout(request: Request):
    """Handle logout - clear session and redirect to login."""
    response = RedirectResponse(url="/login", status_code=302)
    # TODO: Week 2 - Clear JWT cookie
    # response.delete_cookie("access_token")
    return response


# ============================================================================
# Placeholder Routes (Future Weeks)
# ============================================================================

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """User profile page - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html",
        get_template_context(request),
        status_code=404
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html",
        get_template_context(request),
        status_code=404
    )


@router.get("/members", response_class=HTMLResponse)
@router.get("/members/{path:path}", response_class=HTMLResponse)
async def members_placeholder(request: Request, path: str = ""):
    """Members pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html",
        get_template_context(request),
        status_code=404
    )


@router.get("/dues", response_class=HTMLResponse)
@router.get("/dues/{path:path}", response_class=HTMLResponse)
async def dues_placeholder(request: Request, path: str = ""):
    """Dues pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html",
        get_template_context(request),
        status_code=404
    )


@router.get("/grievances", response_class=HTMLResponse)
@router.get("/grievances/{path:path}", response_class=HTMLResponse)
async def grievances_placeholder(request: Request, path: str = ""):
    """Grievances pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html",
        get_template_context(request),
        status_code=404
    )


@router.get("/training", response_class=HTMLResponse)
@router.get("/training/{path:path}", response_class=HTMLResponse)
async def training_placeholder(request: Request, path: str = ""):
    """Training pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html",
        get_template_context(request),
        status_code=404
    )


@router.get("/staff", response_class=HTMLResponse)
@router.get("/staff/{path:path}", response_class=HTMLResponse)
async def staff_placeholder(request: Request, path: str = ""):
    """Staff pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html",
        get_template_context(request),
        status_code=404
    )


@router.get("/organizations", response_class=HTMLResponse)
@router.get("/organizations/{path:path}", response_class=HTMLResponse)
async def organizations_placeholder(request: Request, path: str = ""):
    """Organizations pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html",
        get_template_context(request),
        status_code=404
    )


@router.get("/reports", response_class=HTMLResponse)
@router.get("/reports/{path:path}", response_class=HTMLResponse)
async def reports_placeholder(request: Request, path: str = ""):
    """Reports pages - placeholder."""
    return templates.TemplateResponse(
        "errors/404.html",
        get_template_context(request),
        status_code=404
    )
