# Phase 6 Week 4 - Session A: Training Overview

**Document:** 1 of 3
**Estimated Time:** 2-3 hours
**Focus:** Training landing page with stats and navigation

---

## Objective

Create the Training module landing page with:
- Stats cards (students, courses, enrollments)
- Quick action buttons
- Navigation to student/course lists
- Recent training activity

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show 205 passed
```

---

## Step 1: Verify Existing Models (10 min)

Before creating the service, verify what models exist:

```bash
# Check for Student model
grep -l "class Student" src/models/*.py

# Check for Course model
grep -l "class Course" src/models/*.py

# Check for Enrollment model
grep -l "class Enrollment" src/models/*.py

# Check existing enums
ls src/db/enums/
```

Expected: Models should exist from Phase 2. If not, check `src/models/` structure.

---

## Step 2: Create Training Frontend Service (45 min)

Create `src/services/training_frontend_service.py`:

```python
"""
Training Frontend Service - Stats and queries for training pages.
Provides aggregated data for the training dashboard and lists.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta
import logging

from src.models.student import Student
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.cohort import Cohort
from src.db.enums import StudentStatus, EnrollmentStatus

logger = logging.getLogger(__name__)


class TrainingFrontendService:
    """Service for training frontend pages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Dashboard Stats
    # ============================================================

    async def get_training_stats(self) -> dict:
        """
        Get all stats for the training dashboard.
        Returns counts and recent changes.
        """
        # Total students
        total_students = (await self.db.execute(
            select(func.count(Student.id))
        )).scalar() or 0

        # Active students
        active_students = (await self.db.execute(
            select(func.count(Student.id)).where(
                Student.status == StudentStatus.ACTIVE
            )
        )).scalar() or 0

        # Students enrolled this month
        first_of_month = date.today().replace(day=1)
        new_this_month = (await self.db.execute(
            select(func.count(Student.id)).where(
                Student.enrollment_date >= first_of_month
            )
        )).scalar() or 0

        # Graduated students
        graduated = (await self.db.execute(
            select(func.count(Student.id)).where(
                Student.status == StudentStatus.GRADUATED
            )
        )).scalar() or 0

        # Total courses
        total_courses = (await self.db.execute(
            select(func.count(Course.id))
        )).scalar() or 0

        # Active courses
        active_courses = (await self.db.execute(
            select(func.count(Course.id)).where(Course.is_active == True)
        )).scalar() or 0

        # Total enrollments
        total_enrollments = (await self.db.execute(
            select(func.count(Enrollment.id))
        )).scalar() or 0

        # Active enrollments (status = enrolled)
        active_enrollments = (await self.db.execute(
            select(func.count(Enrollment.id)).where(
                Enrollment.status == EnrollmentStatus.ENROLLED
            )
        )).scalar() or 0

        # Completion rate (completed / total non-active)
        completed = (await self.db.execute(
            select(func.count(Enrollment.id)).where(
                Enrollment.status == EnrollmentStatus.COMPLETED
            )
        )).scalar() or 0

        total_finished = (await self.db.execute(
            select(func.count(Enrollment.id)).where(
                Enrollment.status.in_([
                    EnrollmentStatus.COMPLETED,
                    EnrollmentStatus.DROPPED,
                    EnrollmentStatus.FAILED
                ])
            )
        )).scalar() or 0

        completion_rate = round((completed / total_finished * 100) if total_finished > 0 else 0, 1)

        return {
            "total_students": total_students,
            "active_students": active_students,
            "new_this_month": new_this_month,
            "graduated": graduated,
            "total_courses": total_courses,
            "active_courses": active_courses,
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "completion_rate": completion_rate,
        }

    # ============================================================
    # Student Queries
    # ============================================================

    async def get_recent_students(self, limit: int = 5) -> List[Student]:
        """Get recently enrolled students."""
        stmt = (
            select(Student)
            .options(selectinload(Student.cohort))
            .order_by(Student.enrollment_date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_students(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        cohort_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Student], int, int]:
        """
        Search and filter students with pagination.

        Returns:
            Tuple of (students, total_count, total_pages)
        """
        stmt = select(Student).options(selectinload(Student.cohort))

        # Search filter
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Student.first_name.ilike(search_term),
                    Student.last_name.ilike(search_term),
                    Student.email.ilike(search_term),
                    Student.student_number.ilike(search_term),
                )
            )

        # Status filter
        if status and status != "all":
            try:
                status_enum = StudentStatus(status)
                stmt = stmt.where(Student.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter

        # Cohort filter
        if cohort_id:
            stmt = stmt.where(Student.cohort_id == cohort_id)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Apply sorting and pagination
        stmt = stmt.order_by(Student.last_name, Student.first_name)
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        result = await self.db.execute(stmt)
        students = list(result.scalars().all())

        total_pages = (total + per_page - 1) // per_page

        return students, total, total_pages

    async def get_student_by_id(self, student_id: int) -> Optional[Student]:
        """Get a single student with relationships loaded."""
        stmt = (
            select(Student)
            .options(
                selectinload(Student.cohort),
                selectinload(Student.enrollments).selectinload(Enrollment.course),
            )
            .where(Student.id == student_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ============================================================
    # Course Queries
    # ============================================================

    async def get_courses_with_enrollment_counts(self) -> List[dict]:
        """Get all courses with their enrollment counts."""
        # Get courses
        courses_stmt = select(Course).where(Course.is_active == True).order_by(Course.code)
        courses_result = await self.db.execute(courses_stmt)
        courses = list(courses_result.scalars().all())

        # Get enrollment counts per course
        counts_stmt = (
            select(
                Enrollment.course_id,
                func.count(Enrollment.id).label("total"),
                func.count(Enrollment.id).filter(
                    Enrollment.status == EnrollmentStatus.ENROLLED
                ).label("active"),
            )
            .group_by(Enrollment.course_id)
        )
        counts_result = await self.db.execute(counts_stmt)
        counts = {row.course_id: {"total": row.total, "active": row.active}
                  for row in counts_result}

        # Combine
        result = []
        for course in courses:
            course_counts = counts.get(course.id, {"total": 0, "active": 0})
            result.append({
                "course": course,
                "total_enrollments": course_counts["total"],
                "active_enrollments": course_counts["active"],
            })

        return result

    async def get_course_by_id(self, course_id: int) -> Optional[Course]:
        """Get a single course with relationships."""
        stmt = (
            select(Course)
            .options(selectinload(Course.enrollments).selectinload(Enrollment.student))
            .where(Course.id == course_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ============================================================
    # Cohort Queries
    # ============================================================

    async def get_all_cohorts(self) -> List[Cohort]:
        """Get all cohorts for filter dropdown."""
        stmt = select(Cohort).order_by(Cohort.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ============================================================
    # Status Helpers
    # ============================================================

    @staticmethod
    def get_status_badge_class(status: StudentStatus) -> str:
        """Get DaisyUI badge class for student status."""
        mapping = {
            StudentStatus.ACTIVE: "badge-success",
            StudentStatus.GRADUATED: "badge-info",
            StudentStatus.DROPPED: "badge-error",
            StudentStatus.SUSPENDED: "badge-warning",
            StudentStatus.ON_LEAVE: "badge-warning",
        }
        return mapping.get(status, "badge-ghost")

    @staticmethod
    def get_enrollment_badge_class(status: EnrollmentStatus) -> str:
        """Get DaisyUI badge class for enrollment status."""
        mapping = {
            EnrollmentStatus.ENROLLED: "badge-primary",
            EnrollmentStatus.COMPLETED: "badge-success",
            EnrollmentStatus.DROPPED: "badge-error",
            EnrollmentStatus.FAILED: "badge-error",
        }
        return mapping.get(status, "badge-ghost")


# Convenience function
async def get_training_service(db: AsyncSession) -> TrainingFrontendService:
    return TrainingFrontendService(db)
```

---

## Step 3: Create Training Frontend Router (30 min)

Create `src/routers/training_frontend.py`:

```python
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
        }
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
    cohort: Optional[int] = Query(None),
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
        cohort_id=cohort,
        page=page,
        per_page=20,
    )

    # Get cohorts for filter dropdown
    cohorts = await service.get_all_cohorts()

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
            "cohort_filter": cohort,
            "cohorts": cohorts,
            "get_status_badge": TrainingFrontendService.get_status_badge_class,
        }
    )


@router.get("/students/search", response_class=HTMLResponse)
async def student_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query("all"),
    cohort: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
):
    """HTMX partial: Return just the student table body."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="<tr><td colspan='6'>Session expired</td></tr>", status_code=401)

    service = TrainingFrontendService(db)

    students, total, total_pages = await service.search_students(
        query=q,
        status=status,
        cohort_id=cohort,
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
            "cohort_filter": cohort,
            "get_status_badge": TrainingFrontendService.get_status_badge_class,
        }
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
        }
    )
```

---

## Step 4: Create Directory Structure

```bash
mkdir -p src/templates/training/students/partials
mkdir -p src/templates/training/courses/partials
```

---

## Step 5: Create Training Landing Page (30 min)

Create `src/templates/training/index.html`:

```html
{% extends "base.html" %}

{% block title %}Training - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold">Training Program</h1>
            <p class="text-base-content/60">Pre-apprenticeship training management</p>
        </div>
        <div class="flex gap-2">
            <a href="/training/students" class="btn btn-outline">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
                </svg>
                View Students
            </a>
            <a href="/training/courses" class="btn btn-primary">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
                View Courses
            </a>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Students Card -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-primary">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
                </svg>
            </div>
            <div class="stat-title">Total Students</div>
            <div class="stat-value text-primary">{{ stats.total_students }}</div>
            <div class="stat-desc">
                <span class="text-success">{{ stats.active_students }} active</span>
                {% if stats.new_this_month > 0 %}
                · <span class="text-info">+{{ stats.new_this_month }} this month</span>
                {% endif %}
            </div>
        </div>

        <!-- Graduated Card -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-success">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
                </svg>
            </div>
            <div class="stat-title">Graduated</div>
            <div class="stat-value text-success">{{ stats.graduated }}</div>
            <div class="stat-desc">Completed the program</div>
        </div>

        <!-- Courses Card -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-secondary">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
            </div>
            <div class="stat-title">Courses</div>
            <div class="stat-value text-secondary">{{ stats.active_courses }}</div>
            <div class="stat-desc">{{ stats.total_courses }} total courses</div>
        </div>

        <!-- Completion Rate Card -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-accent">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
            </div>
            <div class="stat-title">Completion Rate</div>
            <div class="stat-value text-accent">{{ stats.completion_rate }}%</div>
            <div class="stat-desc">{{ stats.active_enrollments }} active enrollments</div>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Recent Students -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="card-title">Recent Students</h2>
                    <a href="/training/students" class="btn btn-ghost btn-sm">View All →</a>
                </div>

                {% if recent_students %}
                <div class="overflow-x-auto">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Student</th>
                                <th>Status</th>
                                <th>Enrolled</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for student in recent_students %}
                            <tr class="hover">
                                <td>
                                    <div>
                                        <div class="font-bold">{{ student.first_name }} {{ student.last_name }}</div>
                                        <div class="text-sm text-base-content/60">{{ student.student_number }}</div>
                                    </div>
                                </td>
                                <td>
                                    <span class="badge {{ get_status_badge(student.status) }} badge-sm">
                                        {{ student.status.value | title }}
                                    </span>
                                </td>
                                <td class="text-sm">{{ student.enrollment_date.strftime('%b %d, %Y') }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-8 text-base-content/50">
                    <p>No students enrolled yet</p>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title mb-4">Quick Actions</h2>

                <div class="grid grid-cols-2 gap-3">
                    <a href="/training/students" class="btn btn-outline btn-block justify-start gap-3">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                        </svg>
                        Student List
                    </a>

                    <a href="/training/courses" class="btn btn-outline btn-block justify-start gap-3">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                        </svg>
                        Course List
                    </a>

                    <a href="#" class="btn btn-outline btn-block justify-start gap-3" onclick="alert('Coming soon!')">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
                        </svg>
                        Attendance
                    </a>

                    <a href="#" class="btn btn-outline btn-block justify-start gap-3" onclick="alert('Coming soon!')">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        Reports
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 6: Register Router in main.py

Update `src/main.py`:

```python
# Add import
from src.routers.training_frontend import router as training_frontend_router

# Add router (after staff router, before frontend router)
app.include_router(training_frontend_router)
```

---

## Step 7: Update Sidebar Navigation

Update `src/templates/components/_sidebar.html` to highlight Training menu:

Find the Training link and ensure it matches:

```html
<li>
    <a href="/training" class="{{ 'active' if request.url.path.startswith('/training') else '' }}">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
        </svg>
        Training
    </a>
</li>
```

---

## Step 8: Test Manually

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

1. Login at `/login`
2. Navigate to `/training`
3. Verify stats cards show data
4. Verify recent students table
5. Click "View Students" and "View Courses" (will 404 until Session B)

---

## Step 9: Add Initial Tests

Create `src/tests/test_training_frontend.py`:

```python
"""
Training frontend tests.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestTrainingLanding:
    """Tests for training landing page."""

    @pytest.mark.asyncio
    async def test_training_page_requires_auth(self, async_client: AsyncClient):
        """Training page should redirect to login when not authenticated."""
        response = await async_client.get("/training", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_training_page_exists(self, async_client: AsyncClient):
        """Training page route should exist."""
        response = await async_client.get("/training")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestStudentList:
    """Tests for student list page."""

    @pytest.mark.asyncio
    async def test_students_page_exists(self, async_client: AsyncClient):
        """Students page route should exist."""
        response = await async_client.get("/training/students")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_students_search_exists(self, async_client: AsyncClient):
        """Students search endpoint should exist."""
        response = await async_client.get("/training/students/search")
        assert response.status_code in [200, 302, 401]


class TestCourseList:
    """Tests for course list page."""

    @pytest.mark.asyncio
    async def test_courses_page_exists(self, async_client: AsyncClient):
        """Courses page route should exist."""
        response = await async_client.get("/training/courses")
        assert response.status_code != status.HTTP_404_NOT_FOUND
```

---

## Step 10: Run Tests

```bash
pytest -v --tb=short

# Expected: 210+ tests passing (205 + 5 new)
```

---

## Step 11: Commit

```bash
git add -A
git status

git commit -m "feat(training): Phase 6 Week 4 Session A - Training landing page

- Create TrainingFrontendService with stats queries
- Create training_frontend router
- Create training/index.html landing page
- Stats: students, graduated, courses, completion rate
- Recent students table
- Quick action buttons
- 5 new tests (210 total)

Dashboard shows:
- Total/active students with monthly change
- Graduation count
- Active courses
- Completion rate percentage"

git push origin main
```

---

## Session A Checklist

- [ ] Created `src/services/training_frontend_service.py`
- [ ] Created `src/routers/training_frontend.py`
- [ ] Created `src/templates/training/index.html`
- [ ] Created directory structure for students/courses
- [ ] Registered router in main.py
- [ ] Updated sidebar navigation
- [ ] Stats cards working
- [ ] Recent students table working
- [ ] Initial tests passing
- [ ] Committed changes

---

## Files Created This Session

```
src/
├── services/
│   └── training_frontend_service.py  # Stats and queries
├── routers/
│   └── training_frontend.py          # Training page routes
├── templates/
│   └── training/
│       ├── index.html                # Landing page
│       ├── students/                 # (directory only)
│       │   └── partials/
│       └── courses/                  # (directory only)
│           └── partials/
└── tests/
    └── test_training_frontend.py     # Training tests (started)
```

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

*Session A complete. Proceed to Session B for student list with search and filters.*
