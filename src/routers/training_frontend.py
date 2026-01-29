"""
Training Frontend Router - Pages for training management.
"""

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.db.session import get_db
from src.services.training_frontend_service import TrainingFrontendService
from src.routers.dependencies.auth_cookie import require_auth
from src.db.enums import StudentStatus

router = APIRouter(prefix="/training", tags=["training-frontend"])
templates = Jinja2Templates(directory="src/templates")


# ============================================================
# Training Landing Page
# ============================================================


@router.get("", response_class=HTMLResponse)
async def training_landing(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the training landing/overview page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = TrainingFrontendService(db)

    # Get dashboard stats
    stats = await service.get_training_stats()

    # Get recent students for quick view
    recent_students = await service.get_recent_students(limit=5)

    return templates.TemplateResponse(
        "training/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "recent_students": recent_students,
            "get_status_badge": TrainingFrontendService.get_status_badge_class,
        },
    )


# ============================================================
# Student List Page
# ============================================================


@router.get("/students", response_class=HTMLResponse)
async def student_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query("all"),
    cohort: Optional[str] = Query("all"),
    page: int = Query(1, ge=1),
):
    """Render the student list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = TrainingFrontendService(db)

    # Get students with search/filter
    students, total, total_pages = await service.search_students(
        query=q,
        status=status,
        cohort=cohort,
        page=page,
        per_page=20,
    )

    # Get cohorts for filter dropdown
    cohorts = await service.get_all_cohorts()

    # Get all statuses for filter dropdown
    statuses = list(StudentStatus)

    return templates.TemplateResponse(
        "training/students/index.html",
        {
            "request": request,
            "user": current_user,
            "students": students,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "status_filter": status or "all",
            "cohort_filter": cohort or "all",
            "cohorts": cohorts,
            "statuses": statuses,
            "get_status_badge": TrainingFrontendService.get_status_badge_class,
        },
    )


@router.get("/students/search", response_class=HTMLResponse)
async def student_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query("all"),
    cohort: Optional[str] = Query("all"),
    page: int = Query(1, ge=1),
):
    """HTMX partial: Return just the student table body."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            content="<tr><td colspan='6'>Session expired</td></tr>", status_code=401
        )

    service = TrainingFrontendService(db)

    students, total, total_pages = await service.search_students(
        query=q,
        status=status,
        cohort=cohort,
        page=page,
        per_page=20,
    )

    return templates.TemplateResponse(
        "training/students/partials/_table.html",
        {
            "request": request,
            "students": students,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "status_filter": status or "all",
            "cohort_filter": cohort or "all",
            "get_status_badge": TrainingFrontendService.get_status_badge_class,
        },
    )


# ============================================================
# Student Detail Page
# ============================================================


@router.get("/students/{student_id}", response_class=HTMLResponse)
async def student_detail_page(
    request: Request,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the student detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = TrainingFrontendService(db)
    student = await service.get_student_by_id(student_id)

    if not student:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Student not found"},
            status_code=404,
        )

    return templates.TemplateResponse(
        "training/students/detail.html",
        {
            "request": request,
            "user": current_user,
            "student": student,
            "get_status_badge": TrainingFrontendService.get_status_badge_class,
            "get_enrollment_badge": TrainingFrontendService.get_enrollment_badge_class,
        },
    )


# ============================================================
# Course List Page
# ============================================================


@router.get("/courses", response_class=HTMLResponse)
async def course_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the course list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = TrainingFrontendService(db)

    # Get courses with enrollment counts
    courses = await service.get_courses_with_enrollment_counts()

    return templates.TemplateResponse(
        "training/courses/index.html",
        {
            "request": request,
            "user": current_user,
            "courses": courses,
        },
    )


# ============================================================
# Course Detail Page
# ============================================================


@router.get("/courses/{course_id}", response_class=HTMLResponse)
async def course_detail_page(
    request: Request,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the course detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = TrainingFrontendService(db)
    course = await service.get_course_by_id(course_id)

    if not course:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Course not found"},
            status_code=404,
        )

    # Count active enrollments
    enrolled_count = sum(1 for e in course.enrollments if e.status.value == "enrolled")

    return templates.TemplateResponse(
        "training/courses/detail.html",
        {
            "request": request,
            "user": current_user,
            "course": course,
            "enrolled_count": enrolled_count,
            "get_enrollment_badge": TrainingFrontendService.get_enrollment_badge_class,
        },
    )
