from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

# Middleware
from src.middleware import AuditContextMiddleware

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

# Audit context middleware (must be before CORS for proper request handling)
app.add_middleware(AuditContextMiddleware)

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
# Health check (root handled by frontend router)
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


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
