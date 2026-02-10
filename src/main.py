import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

# Configuration checks
from src.config.auth_config import check_jwt_secret_configuration
from src.config.settings import get_settings

# Middleware
from src.middleware import AuditContextMiddleware, SecurityHeadersMiddleware

# Logging and monitoring
from src.core.logging_config import setup_logging
from src.core.monitoring import init_sentry

logger = logging.getLogger(__name__)

# Routers
from src.routers.instructors import router as instructors_router
from src.routers.students import router as students_router
from src.routers.cohorts import router as cohorts_router
from src.routers.locations import router as locations_router
from src.routers.instructor_hours import router as instructor_hours_router
from src.routers.credentials import router as credentials_router
from src.routers.tools import router as tools_router
from src.routers.jatc_applications import router as jatc_router
from src.routers.file_attachments import router as file_router
from src.routers.files import router as files_router

# Phase 1 routers
from src.routers.organizations import router as organizations_router
from src.routers.organization_contacts import router as organization_contacts_router
from src.routers.members import router as members_router
from src.routers.member_employments import router as member_employments_router
from src.routers.audit_logs import router as audit_logs_router

# Phase 2 routers
from src.routers.salting_activities import router as salting_activities_router
from src.routers.benevolence_applications import (
    router as benevolence_applications_router,
)
from src.routers.benevolence_reviews import router as benevolence_reviews_router
from src.routers.grievances import router as grievances_router

# Authentication router
from src.routers.auth import router as auth_router

# Phase 2 Training System routers
from src.routers.courses import router as courses_router
from src.routers.class_sessions import router as class_sessions_router
from src.routers.enrollments import router as enrollments_router
from src.routers.attendances import router as attendances_router
from src.routers.grades import router as grades_router
from src.routers.certifications import router as certifications_router

# Phase 3 Document Management router
from src.routers.documents import router as documents_router

# Phase 4 Dues Tracking routers
from src.routers.dues_rates import router as dues_rates_router
from src.routers.dues_periods import router as dues_periods_router
from src.routers.dues_payments import router as dues_payments_router
from src.routers.dues_adjustments import router as dues_adjustments_router

# Phase 6 Frontend router
from src.routers import frontend
from src.routers.staff import router as staff_router
from src.routers.training_frontend import router as training_frontend_router
from src.routers.member_frontend import router as member_frontend_router
from src.routers.operations_frontend import router as operations_frontend_router
from src.routers.reports import router as reports_router
from src.routers.documents_frontend import router as documents_frontend_router
from src.routers.dues_frontend import router as dues_frontend_router
from src.routers.member_notes import router as member_notes_router
from src.routers.audit_frontend import router as audit_frontend_router
from src.routers.profile_frontend import router as profile_frontend_router
from src.routers.grants_frontend import router as grants_frontend_router

# Health checks
from src.routers.health import router as health_router

# Admin metrics
from src.routers.admin_metrics import router as admin_metrics_router

# Analytics dashboard
from src.routers.analytics import router as analytics_router

# Phase 7: Referral & Dispatch
from src.routers.referral_books_api import router as referral_books_api_router
from src.routers.registration_api import router as registration_api_router
from src.routers.labor_request_api import router as labor_request_api_router
from src.routers.job_bid_api import router as job_bid_api_router
from src.routers.dispatch_api import router as dispatch_api_router
from src.routers.referral_frontend import router as referral_frontend_router
from src.routers.dispatch_frontend import router as dispatch_frontend_router
from src.routers.referral_reports_api import router as referral_reports_api_router

# Phase 8A: Square Payment Integration
from src.routers.square_payments import router as square_payments_router

# Developer Tools: View As (ADR-019)
from src.routers.view_as import router as view_as_router

# ------------------------------------------------------------
# Initialize FastAPI
# ------------------------------------------------------------
app = FastAPI(
    title="IP2A Database API",
    description="Backend API for the IBEW IP2A Program",
    version="2.0.0",
)


# ------------------------------------------------------------
# Middleware
# ------------------------------------------------------------

# Session middleware for View As feature (ADR-019)
# Must be added before other middleware that might use session
settings = get_settings()
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="unioncore_session",
    max_age=None,  # Session cookie (expires when browser closes)
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

# Audit context middleware (must be before CORS for proper request handling)
app.add_middleware(AuditContextMiddleware)

# Security headers middleware (production hardening)
app.add_middleware(SecurityHeadersMiddleware)

# CORS (allow frontend development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# Static Files
# ------------------------------------------------------------
app.mount("/static", StaticFiles(directory="src/static"), name="static")


# ------------------------------------------------------------
# Startup Events
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Run configuration checks and initialize monitoring on startup."""
    # Setup structured logging
    setup_logging()

    # Initialize error tracking (Sentry)
    init_sentry()

    # Check JWT configuration
    check_jwt_secret_configuration()

    logger.info("IP2A Database API started successfully")


# ------------------------------------------------------------
# Health check (root handled by frontend router)
# ------------------------------------------------------------
@app.get("/health")
def health():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "version": "0.9.6-alpha"}


# ------------------------------------------------------------
# Register Routers
# ------------------------------------------------------------
app.include_router(instructors_router)
app.include_router(students_router)
app.include_router(cohorts_router)
app.include_router(locations_router)
app.include_router(instructor_hours_router)
app.include_router(credentials_router)
app.include_router(tools_router)
app.include_router(jatc_router)
app.include_router(file_router)
app.include_router(files_router)

# Phase 1 routers
app.include_router(organizations_router)
app.include_router(organization_contacts_router)
app.include_router(members_router)
app.include_router(member_employments_router)
app.include_router(audit_logs_router)

# Phase 2 routers
app.include_router(salting_activities_router)
app.include_router(benevolence_applications_router)
app.include_router(benevolence_reviews_router)
app.include_router(grievances_router)

# Authentication router
app.include_router(auth_router)

# Phase 2 Training System routers
app.include_router(courses_router)
app.include_router(class_sessions_router)
app.include_router(enrollments_router)
app.include_router(attendances_router)
app.include_router(grades_router)
app.include_router(certifications_router)

# Phase 3 Document Management router
app.include_router(documents_router)

# Phase 4 Dues Tracking routers
app.include_router(dues_rates_router)
app.include_router(dues_periods_router)
app.include_router(dues_payments_router)
app.include_router(dues_adjustments_router)

# Phase 6 Staff Management router
app.include_router(staff_router)

# Phase 6 Training Frontend router
app.include_router(training_frontend_router)

# Phase 6 Member Frontend router
app.include_router(member_frontend_router)

# Phase 6 Operations Frontend router
app.include_router(operations_frontend_router)

# Phase 6 Reports router
app.include_router(reports_router)

# Phase 6 Documents Frontend router
app.include_router(documents_frontend_router)

# Phase 6 Dues Frontend router
app.include_router(dues_frontend_router)

# Week 11: Member notes (audit infrastructure)
app.include_router(member_notes_router, prefix="/api/v1")
app.include_router(audit_frontend_router)  # Frontend audit log viewer
app.include_router(profile_frontend_router)  # User profile management
app.include_router(grants_frontend_router)  # Grant management frontend

# Health check routes (production monitoring)
app.include_router(health_router)

# Admin metrics dashboard
app.include_router(admin_metrics_router)

# Analytics dashboard (Week 19)
app.include_router(analytics_router)

# Phase 7: Referral & Dispatch (Weeks 20-25)
app.include_router(referral_books_api_router)
app.include_router(registration_api_router)
app.include_router(labor_request_api_router)
app.include_router(job_bid_api_router)
app.include_router(dispatch_api_router)
app.include_router(referral_frontend_router)  # Week 26: Books & Registration UI
app.include_router(dispatch_frontend_router)  # Week 27: Dispatch Workflow UI
app.include_router(
    referral_reports_api_router,
    prefix="/api/v1/reports/referral",
    tags=["referral-reports"],
)  # Week 33A: Out-of-Work Reports

# Phase 8A: Square Payment Integration (Week 47-49)
app.include_router(square_payments_router)  # Square online payments API

# Developer Tools: View As (ADR-019)
app.include_router(view_as_router)  # View As impersonation API

# Frontend routes (HTML pages) - include LAST to not interfere with API routes
app.include_router(frontend.router)


# ============================================================================
# Custom Exception Handlers (HTML for browser, JSON for API)
# ============================================================================

_templates = Jinja2Templates(directory="src/templates")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler - returns JSON for API, HTML for browser."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return _templates.TemplateResponse(
        "errors/404.html", {"request": request}, status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Custom 500 handler - returns JSON for API, HTML for browser."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
    return _templates.TemplateResponse(
        "errors/500.html", {"request": request}, status_code=500
    )
