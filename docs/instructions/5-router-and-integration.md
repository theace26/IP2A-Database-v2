# Phase 6 Week 1: Document 5 - Router & Integration

**Execution Order:** 5 of 6
**Estimated Time:** 30-40 minutes
**Goal:** Create frontend router and integrate into main.py
**Prerequisites:** Document 4 complete (pages and static files exist)

---

## Overview

This document:
1. Creates the frontend router (`src/routers/frontend.py`)
2. Updates `src/main.py` to mount static files and include the router
3. Adds custom exception handlers for 404/500 HTML responses

---

## Task 5.1: Create Frontend Router

This router serves HTML pages. API routes remain separate.

**File:** `src/routers/frontend.py`

```python
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
```

---

## Task 5.2: Update main.py

You need to make several changes to `src/main.py`. Here are the specific edits:

### 5.2.1: Add New Imports

**Add these imports near the top of the file:**

```python
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from src.routers import frontend
```

### 5.2.2: Mount Static Files

**Add this AFTER the `app = FastAPI(...)` line but BEFORE router includes:**

```python
# Mount static files for frontend
app.mount("/static", StaticFiles(directory="src/static"), name="static")
```

### 5.2.3: Include Frontend Router

**Add this with your other router includes:**

```python
# Frontend routes (HTML pages) - include LAST to not interfere with API routes
app.include_router(frontend.router)
```

**Important:** The frontend router should be included LAST because it has catch-all routes.

### 5.2.4: Add Exception Handlers

**Add these at the END of the file (after all router includes):**

```python
# ============================================================================
# Custom Exception Handlers (HTML for browser, JSON for API)
# ============================================================================

_templates = Jinja2Templates(directory="src/templates")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler - returns JSON for API, HTML for browser."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not found"}
        )
    return _templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Custom 500 handler - returns JSON for API, HTML for browser."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    return _templates.TemplateResponse(
        "errors/500.html",
        {"request": request},
        status_code=500
    )
```

---

## Task 5.3: Verify Router Registration

Your `main.py` router section should look something like this:

```python
# API routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(organization_router, prefix="/api/organizations", tags=["Organizations"])
# ... other API routers ...

# Frontend routes (HTML pages) - LAST
app.include_router(frontend.router)
```

---

## Task 5.4: Quick Test

Start the server and verify:

```bash
# Restart Docker containers to pick up changes
docker-compose down
docker-compose up -d

# Wait a few seconds, then test
curl -s http://localhost:8000/login | head -20
# Should return HTML containing "IBEW Local 46"

curl -s http://localhost:8000/dashboard | head -20
# Should return HTML containing "Dashboard"

curl -s -I http://localhost:8000/static/css/custom.css
# Should return 200 OK with content-type: text/css
```

---

## Troubleshooting

**If you get import errors:**
- Ensure `src/routers/frontend.py` exists
- Check for typos in import paths

**If static files 404:**
- Verify `src/static/` directory exists
- Check that `app.mount()` line is BEFORE router includes

**If templates don't render:**
- Verify `src/templates/` has all required files
- Check Jinja2 template syntax (no Python syntax errors)

**If API routes stop working:**
- Ensure frontend router is included LAST
- API routes should still be prefixed with `/api/`

---

## ✅ Document 5 Complete

**Checklist:**
- [ ] `src/routers/frontend.py` created
- [ ] Static files mounted in main.py
- [ ] Frontend router included in main.py
- [ ] Exception handlers added
- [ ] Quick test passed (login page renders)

**Next:** Run Document 6 - Testing & Commit

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*Document 5 of 6 | Phase 6 Week 1*
