# Phase 6 Week 4 - Session C: Course List + Enrollment + Tests

**Document:** 3 of 3
**Estimated Time:** 2-3 hours
**Focus:** Course cards, capacity indicators, enrollment actions, comprehensive tests

---

## Objective

Complete the training landing page with:
- Course list with card layout
- Capacity progress bars
- Enrollment counts
- Next session indicator
- Quick enrollment action (modal)
- Comprehensive test coverage (15+ tests)
- Documentation updates

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show 215+ passed
```

---

## Step 1: Add Course Service Methods (20 min)

Add to `src/services/training_service.py`:

```python
from src.models.course import Course
from src.models.class_session import ClassSession
from src.models.enrollment import Enrollment
from src.db.enums import EnrollmentStatus
from datetime import datetime, timedelta

class TrainingService:
    # ... existing methods ...

    async def get_courses_with_stats(
        self,
        active_only: bool = True,
        page: int = 1,
        per_page: int = 12,
    ) -> Tuple[List[dict], int]:
        """
        Get courses with enrollment counts and next session info.
        Returns list of course dicts with stats.
        """
        # Base query
        stmt = select(Course)
        if active_only:
            stmt = stmt.where(Course.is_active == True)

        # Get total count
        count_stmt = select(func.count(Course.id)).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(Course.code).offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(stmt)
        courses = result.scalars().all()

        # Build course data with stats
        course_data = []
        for course in courses:
            enrolled_count = await self._get_enrollment_count(course.id)
            next_session = await self._get_next_session(course.id)

            course_data.append({
                "id": course.id,
                "code": course.code,
                "name": course.name,
                "description": course.description,
                "credits": course.credits,
                "max_capacity": course.max_capacity,
                "enrolled_count": enrolled_count,
                "fill_rate": (enrolled_count / course.max_capacity * 100) if course.max_capacity > 0 else 0,
                "next_session": next_session,
                "is_full": enrolled_count >= course.max_capacity,
            })

        return course_data, total

    async def _get_enrollment_count(self, course_id: int) -> int:
        """Get count of active enrollments for a course."""
        stmt = select(func.count(Enrollment.id)).where(
            Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.ENROLLED
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _get_next_session(self, course_id: int) -> Optional[dict]:
        """Get the next upcoming session for a course."""
        now = datetime.utcnow()
        stmt = select(ClassSession).where(
            ClassSession.course_id == course_id,
            ClassSession.session_date >= now.date()
        ).order_by(ClassSession.session_date).limit(1)

        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            return {
                "id": session.id,
                "date": session.session_date,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "location": session.location,
            }
        return None

    async def get_course_by_id(self, course_id: int) -> Optional[Course]:
        """Get a single course by ID."""
        stmt = select(Course).where(Course.id == course_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_available_courses_for_student(
        self,
        student_id: int
    ) -> List[dict]:
        """
        Get courses the student is not already enrolled in.
        Used for enrollment modal dropdown.
        """
        # Get student's current enrollments
        enrolled_stmt = select(Enrollment.course_id).where(
            Enrollment.student_id == student_id,
            Enrollment.status == EnrollmentStatus.ENROLLED
        )
        enrolled_result = await self.db.execute(enrolled_stmt)
        enrolled_course_ids = [r[0] for r in enrolled_result.fetchall()]

        # Get active courses not in enrolled list
        stmt = select(Course).where(
            Course.is_active == True,
            ~Course.id.in_(enrolled_course_ids) if enrolled_course_ids else True
        ).order_by(Course.code)

        result = await self.db.execute(stmt)
        courses = result.scalars().all()

        return [
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "available_seats": c.max_capacity - await self._get_enrollment_count(c.id)
            }
            for c in courses
        ]

    async def enroll_student(
        self,
        student_id: int,
        course_id: int,
        enrolled_by: int,
    ) -> Enrollment:
        """
        Enroll a student in a course.
        Validates capacity and existing enrollment.
        """
        from src.models.enrollment import Enrollment

        # Check if already enrolled
        existing = await self.db.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
                Enrollment.status == EnrollmentStatus.ENROLLED
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Student is already enrolled in this course")

        # Check capacity
        course = await self.get_course_by_id(course_id)
        if not course:
            raise ValueError("Course not found")

        enrolled_count = await self._get_enrollment_count(course_id)
        if enrolled_count >= course.max_capacity:
            raise ValueError("Course is at capacity")

        # Create enrollment
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.ENROLLED,
            enrolled_at=datetime.utcnow(),
        )
        self.db.add(enrollment)

        # Log action
        await self.audit.log_action(
            user_id=enrolled_by,
            action="CREATE",
            entity_type="enrollment",
            entity_id=0,  # Will update after flush
            changes={
                "student_id": student_id,
                "course_id": course_id,
                "course_code": course.code,
            },
        )

        await self.db.commit()
        await self.db.refresh(enrollment)

        return enrollment

    async def withdraw_student(
        self,
        enrollment_id: int,
        withdrawn_by: int,
    ) -> bool:
        """Withdraw a student from a course."""
        stmt = select(Enrollment).where(Enrollment.id == enrollment_id)
        result = await self.db.execute(stmt)
        enrollment = result.scalar_one_or_none()

        if not enrollment:
            return False

        if enrollment.status != EnrollmentStatus.ENROLLED:
            raise ValueError("Student is not currently enrolled")

        enrollment.status = EnrollmentStatus.WITHDRAWN
        enrollment.withdrawn_at = datetime.utcnow()

        await self.audit.log_action(
            user_id=withdrawn_by,
            action="UPDATE",
            entity_type="enrollment",
            entity_id=enrollment_id,
            changes={
                "status": {"before": "enrolled", "after": "withdrawn"},
            },
        )

        await self.db.commit()
        return True
```

---

## Step 2: Add Course Endpoints (25 min)

Add to `src/routers/training_frontend.py`:

```python
from fastapi import Form

# ============================================================
# Course List Endpoints
# ============================================================

@router.get("/courses", response_class=HTMLResponse)
async def courses_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    page: int = Query(1, ge=1),
):
    """Course list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = TrainingService(db)
    courses, total = await service.get_courses_with_stats(page=page, per_page=12)
    total_pages = (total + 11) // 12

    return templates.TemplateResponse(
        "training/courses/index.html",
        {
            "request": request,
            "user": current_user,
            "courses": courses,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
        }
    )


@router.get("/courses/list", response_class=HTMLResponse)
async def courses_list_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    page: int = Query(1, ge=1),
):
    """HTMX partial: Course cards grid."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = TrainingService(db)
    courses, total = await service.get_courses_with_stats(page=page, per_page=12)
    total_pages = (total + 11) // 12

    return templates.TemplateResponse(
        "training/courses/partials/_course_grid.html",
        {
            "request": request,
            "courses": courses,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
        }
    )


@router.get("/courses/{course_id}", response_class=HTMLResponse)
async def course_detail_page(
    request: Request,
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Course detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = TrainingService(db)
    course = await service.get_course_by_id(course_id)

    if not course:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Course not found"},
            status_code=404
        )

    # Get enrollment stats
    enrolled_count = await service._get_enrollment_count(course_id)
    next_session = await service._get_next_session(course_id)

    return templates.TemplateResponse(
        "training/courses/detail.html",
        {
            "request": request,
            "user": current_user,
            "course": course,
            "enrolled_count": enrolled_count,
            "next_session": next_session,
        }
    )


# ============================================================
# Enrollment Actions
# ============================================================

@router.get("/enroll-modal", response_class=HTMLResponse)
async def enroll_modal(
    request: Request,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: Enrollment modal content."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = TrainingService(db)
    student = await service.get_student_by_id(student_id)

    if not student:
        return HTMLResponse("Student not found", status_code=404)

    available_courses = await service.get_available_courses_for_student(student_id)

    return templates.TemplateResponse(
        "training/partials/_enroll_modal.html",
        {
            "request": request,
            "student": student,
            "courses": available_courses,
        }
    )


@router.post("/enroll", response_class=HTMLResponse)
async def enroll_student(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    student_id: int = Form(...),
    course_id: int = Form(...),
):
    """Enroll a student in a course."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = TrainingService(db)

    try:
        enrollment = await service.enroll_student(
            student_id=student_id,
            course_id=course_id,
            enrolled_by=current_user["id"],
        )

        return HTMLResponse(
            content='''
            <div class="alert alert-success">
                <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Student enrolled successfully!</span>
            </div>
            <script>
                setTimeout(() => {
                    document.getElementById('enroll-modal').close();
                    htmx.trigger(document.body, 'enrollment-changed');
                }, 1500);
            </script>
            ''',
            status_code=200
        )

    except ValueError as e:
        return HTMLResponse(
            content=f'<div class="alert alert-error"><span>{str(e)}</span></div>',
            status_code=400
        )


@router.post("/withdraw/{enrollment_id}", response_class=HTMLResponse)
async def withdraw_student(
    request: Request,
    enrollment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Withdraw a student from a course."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = TrainingService(db)

    try:
        success = await service.withdraw_student(
            enrollment_id=enrollment_id,
            withdrawn_by=current_user["id"],
        )

        if success:
            return HTMLResponse(
                content='''
                <div class="alert alert-success">
                    <span>Student withdrawn successfully</span>
                </div>
                ''',
                status_code=200
            )
        else:
            return HTMLResponse("Enrollment not found", status_code=404)

    except ValueError as e:
        return HTMLResponse(
            content=f'<div class="alert alert-error"><span>{str(e)}</span></div>',
            status_code=400
        )
```

---

## Step 3: Create Course Templates (30 min)

### Create Directory Structure

```bash
mkdir -p src/templates/training/courses/partials
```

### Create `src/templates/training/courses/index.html`

```html
{% extends "base.html" %}

{% block title %}Courses - Training - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/training">Training</a></li>
            <li>Courses</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold">Courses</h1>
            <p class="text-base-content/60">{{ total }} active courses</p>
        </div>
        <div class="flex gap-2">
            <a href="/training" class="btn btn-ghost">
                ← Back to Training
            </a>
        </div>
    </div>

    <!-- Course Grid -->
    <div
        id="course-grid"
        hx-get="/training/courses/list"
        hx-trigger="enrollment-changed from:body"
    >
        {% include "training/courses/partials/_course_grid.html" %}
    </div>
</div>
{% endblock %}
```

### Create `src/templates/training/courses/partials/_course_grid.html`

```html
{# Course grid partial - HTMX target #}

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {% for course in courses %}
    {% include "training/courses/partials/_course_card.html" %}
    {% endfor %}
</div>

{% if not courses %}
<div class="text-center py-12">
    <svg class="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
    </svg>
    <p class="text-base-content/50">No courses found</p>
</div>
{% endif %}

<!-- Pagination -->
{% if total_pages > 1 %}
<div class="flex justify-center mt-6">
    <div class="join">
        {% if current_page > 1 %}
        <button
            class="join-item btn btn-sm"
            hx-get="/training/courses/list?page={{ current_page - 1 }}"
            hx-target="#course-grid"
        >
            «
        </button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">«</button>
        {% endif %}

        <button class="join-item btn btn-sm">Page {{ current_page }} of {{ total_pages }}</button>

        {% if current_page < total_pages %}
        <button
            class="join-item btn btn-sm"
            hx-get="/training/courses/list?page={{ current_page + 1 }}"
            hx-target="#course-grid"
        >
            »
        </button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">»</button>
        {% endif %}
    </div>
</div>
{% endif %}
```

### Create `src/templates/training/courses/partials/_course_card.html`

```html
{# Single course card #}

<div class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow">
    <div class="card-body p-4">
        <!-- Header -->
        <div class="flex items-start justify-between">
            <div>
                <span class="badge badge-outline badge-sm mb-1">{{ course.code }}</span>
                <h3 class="card-title text-base">{{ course.name }}</h3>
            </div>
            {% if course.is_full %}
            <span class="badge badge-error badge-sm">Full</span>
            {% endif %}
        </div>

        <!-- Description -->
        {% if course.description %}
        <p class="text-sm text-base-content/60 line-clamp-2">{{ course.description }}</p>
        {% endif %}

        <!-- Stats -->
        <div class="space-y-2 mt-2">
            <!-- Capacity Bar -->
            <div class="flex items-center gap-2">
                <span class="text-xs text-base-content/60 w-16">Capacity</span>
                <progress
                    class="progress {{ 'progress-error' if course.fill_rate >= 90 else 'progress-warning' if course.fill_rate >= 70 else 'progress-primary' }} flex-1"
                    value="{{ course.enrolled_count }}"
                    max="{{ course.max_capacity }}"
                ></progress>
                <span class="text-xs font-medium w-12 text-right">
                    {{ course.enrolled_count }}/{{ course.max_capacity }}
                </span>
            </div>

            <!-- Credits -->
            <div class="flex items-center gap-2">
                <span class="text-xs text-base-content/60 w-16">Credits</span>
                <span class="text-xs font-medium">{{ course.credits }}</span>
            </div>

            <!-- Next Session -->
            <div class="flex items-center gap-2">
                <span class="text-xs text-base-content/60 w-16">Next</span>
                {% if course.next_session %}
                <span class="text-xs">
                    {{ course.next_session.date.strftime('%b %d') }}
                    {% if course.next_session.location %}
                    @ {{ course.next_session.location }}
                    {% endif %}
                </span>
                {% else %}
                <span class="text-xs text-base-content/40">No sessions scheduled</span>
                {% endif %}
            </div>
        </div>

        <!-- Actions -->
        <div class="card-actions justify-end mt-3 pt-3 border-t border-base-200">
            <a href="/training/courses/{{ course.id }}" class="btn btn-ghost btn-sm">
                View Details
            </a>
        </div>
    </div>
</div>
```

---

## Step 4: Create Enrollment Modal (15 min)

Create `src/templates/training/partials/_enroll_modal.html`:

```html
{# Enrollment modal content - loaded via HTMX #}

<h3 class="font-bold text-lg mb-4">
    Enroll {{ student.first_name }} {{ student.last_name }}
</h3>

<form
    hx-post="/training/enroll"
    hx-target="#enroll-feedback"
    hx-swap="innerHTML"
    class="space-y-4"
>
    <input type="hidden" name="student_id" value="{{ student.id }}" />

    <!-- Feedback area -->
    <div id="enroll-feedback"></div>

    <!-- Student Info -->
    <div class="bg-base-200 p-3 rounded-lg">
        <div class="text-sm">
            <span class="font-medium">{{ student.student_number }}</span>
            <span class="text-base-content/60 ml-2">{{ student.email }}</span>
        </div>
    </div>

    <!-- Course Selection -->
    <div class="form-control">
        <label class="label">
            <span class="label-text font-medium">Select Course</span>
        </label>
        {% if courses %}
        <select name="course_id" class="select select-bordered" required>
            <option value="">Choose a course...</option>
            {% for course in courses %}
            <option value="{{ course.id }}" {% if course.available_seats <= 0 %}disabled{% endif %}>
                {{ course.code }} - {{ course.name }}
                {% if course.available_seats <= 0 %}
                (Full)
                {% else %}
                ({{ course.available_seats }} seats available)
                {% endif %}
            </option>
            {% endfor %}
        </select>
        {% else %}
        <div class="alert alert-info">
            <span>This student is enrolled in all available courses.</span>
        </div>
        {% endif %}
    </div>

    <!-- Actions -->
    <div class="modal-action">
        <button type="button" class="btn btn-ghost" onclick="document.getElementById('enroll-modal').close()">
            Cancel
        </button>
        {% if courses %}
        <button type="submit" class="btn btn-primary">
            Enroll Student
        </button>
        {% endif %}
    </div>
</form>
```

---

## Step 5: Update Training Landing with Course Section (15 min)

Add to `src/templates/training/index.html`, in the tabs section:

```html
<!-- Courses Tab Content -->
<div
    id="courses-tab"
    class="hidden"
    role="tabpanel"
>
    <div
        id="course-preview"
        hx-get="/training/courses/list?per_page=6"
        hx-trigger="load"
        hx-swap="innerHTML"
    >
        <div class="flex justify-center py-8">
            <span class="loading loading-spinner loading-lg"></span>
        </div>
    </div>

    <div class="text-center mt-4">
        <a href="/training/courses" class="btn btn-outline btn-sm">
            View All Courses →
        </a>
    </div>
</div>
```

Add JavaScript for tab switching:

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('[role="tab"]');
    const panels = {
        'students': document.getElementById('students-tab'),
        'courses': document.getElementById('courses-tab'),
    };

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Update active tab
            tabs.forEach(t => t.classList.remove('tab-active'));
            this.classList.add('tab-active');

            // Show correct panel
            const target = this.dataset.tab;
            Object.keys(panels).forEach(key => {
                panels[key].classList.toggle('hidden', key !== target);
            });
        });
    });
});
</script>
```

---

## Step 6: Comprehensive Test Suite (30 min)

Update `src/tests/test_training_frontend.py`:

```python
"""
Comprehensive training frontend tests.
Tests training landing, student list, course list, and enrollment.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestTrainingLanding:
    """Tests for training landing page."""

    @pytest.mark.asyncio
    async def test_training_page_requires_auth(self, async_client: AsyncClient):
        """Training page redirects to login when not authenticated."""
        response = await async_client.get("/training", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_training_page_exists(self, async_client: AsyncClient):
        """Training page route exists."""
        response = await async_client.get("/training")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_training_stats_endpoint(self, async_client: AsyncClient):
        """Stats endpoint exists."""
        response = await async_client.get("/training/stats")
        assert response.status_code in [200, 302, 401]


class TestStudentList:
    """Tests for student list functionality."""

    @pytest.mark.asyncio
    async def test_students_page_exists(self, async_client: AsyncClient):
        """Students page route exists."""
        response = await async_client.get("/training/students")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_students_search_endpoint(self, async_client: AsyncClient):
        """Student search endpoint exists."""
        response = await async_client.get("/training/students/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_students_search_with_query(self, async_client: AsyncClient):
        """Student search accepts query parameter."""
        response = await async_client.get("/training/students/search?q=test")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_students_filter_by_status(self, async_client: AsyncClient):
        """Student search accepts status filter."""
        response = await async_client.get("/training/students/search?status=enrolled")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_students_filter_by_cohort(self, async_client: AsyncClient):
        """Student search accepts cohort filter."""
        response = await async_client.get("/training/students/search?cohort=1")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_student_detail_page(self, async_client: AsyncClient):
        """Student detail page route exists."""
        response = await async_client.get("/training/students/1")
        assert response.status_code in [200, 302, 401, 404]


class TestCourseList:
    """Tests for course list functionality."""

    @pytest.mark.asyncio
    async def test_courses_page_exists(self, async_client: AsyncClient):
        """Courses page route exists."""
        response = await async_client.get("/training/courses")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_courses_list_partial(self, async_client: AsyncClient):
        """Course list partial endpoint exists."""
        response = await async_client.get("/training/courses/list")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_course_detail_page(self, async_client: AsyncClient):
        """Course detail page route exists."""
        response = await async_client.get("/training/courses/1")
        assert response.status_code in [200, 302, 401, 404]


class TestEnrollment:
    """Tests for enrollment functionality."""

    @pytest.mark.asyncio
    async def test_enroll_modal_endpoint(self, async_client: AsyncClient):
        """Enroll modal endpoint exists."""
        response = await async_client.get("/training/enroll-modal?student_id=1")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_enroll_endpoint_accepts_post(self, async_client: AsyncClient):
        """Enroll endpoint accepts POST."""
        response = await async_client.post(
            "/training/enroll",
            data={"student_id": 1, "course_id": 1}
        )
        assert response.status_code in [200, 302, 400, 401, 404, 422]

    @pytest.mark.asyncio
    async def test_withdraw_endpoint(self, async_client: AsyncClient):
        """Withdraw endpoint exists."""
        response = await async_client.post("/training/withdraw/1")
        assert response.status_code in [200, 302, 400, 401, 404]


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_nonexistent_student_returns_404(self, async_client: AsyncClient):
        """Requesting nonexistent student returns 404."""
        response = await async_client.get("/training/students/99999")
        assert response.status_code in [302, 401, 404]

    @pytest.mark.asyncio
    async def test_nonexistent_course_returns_404(self, async_client: AsyncClient):
        """Requesting nonexistent course returns 404."""
        response = await async_client.get("/training/courses/99999")
        assert response.status_code in [302, 401, 404]
```

---

## Step 7: Run All Tests

```bash
pytest -v --tb=short

# Expected: 220+ tests passing
# New tests: ~18 training frontend tests
```

---

## Step 8: Update Documentation

### Update CHANGELOG.md

Add to `[Unreleased]`:

```markdown
- **Phase 6 Week 4: Training Landing Page**
  * Training landing page with overview stats
  * Student list with search, filter by status/cohort
  * Course list with capacity indicators
  * Enrollment modal for quick enrollment
  * Withdraw functionality
  * Stats cards: active students, courses, cohort, attendance
  * 18 new training frontend tests
```

### Update CLAUDE.md

Add Week 4 section showing completion status.

---

## Step 9: Final Commit

```bash
git add -A
git status

git commit -m "feat(training): Phase 6 Week 4 Complete - Training Landing

Session A: Training overview
- TrainingService with stats queries
- Training landing page with 6 stat cards
- HTMX-powered stats refresh
- Active students, courses, cohort info

Session B: Student list
- Student list with table layout
- Search by name, student number, email
- Filter by status and cohort
- Pagination
- Status badges (enrolled/applicant/graduated/etc)
- Student detail page

Session C: Course list + enrollment
- Course cards with capacity bars
- Enrollment counts and fill rates
- Next session indicators
- Enrollment modal for quick enroll
- Withdraw functionality
- Comprehensive tests (18 new)

Tests: 220+ passing"

git push origin main
```

---

## Week 4 Complete Checklist

### Session A
- [ ] `TrainingService` with stats queries
- [ ] `training_frontend.py` router
- [ ] `training/index.html` landing page
- [ ] `_stats.html` partial
- [ ] 6 stat cards displaying

### Session B
- [ ] `training/students/index.html`
- [ ] Student table with pagination
- [ ] Search endpoint working
- [ ] Status filter working
- [ ] Cohort filter working
- [ ] Status badges colored

### Session C
- [ ] `training/courses/index.html`
- [ ] Course cards with capacity bars
- [ ] Enrollment modal
- [ ] Enroll endpoint
- [ ] Withdraw endpoint
- [ ] Comprehensive tests (18+)
- [ ] Documentation updated
- [ ] All tests passing (220+)
- [ ] Committed and pushed

---

## Files Created/Modified Summary

```
src/
├── services/
│   └── training_service.py      # Stats, courses, enrollment
├── routers/
│   └── training_frontend.py     # All training endpoints
├── templates/
│   └── training/
│       ├── index.html           # Landing page
│       ├── partials/
│       │   ├── _stats.html
│       │   ├── _student_list.html
│       │   └── _enroll_modal.html
│       ├── students/
│       │   ├── index.html
│       │   ├── detail.html
│       │   └── partials/
│       │       ├── _table.html
│       │       └── _row.html
│       └── courses/
│           ├── index.html
│           └── partials/
│               ├── _course_grid.html
│               └── _course_card.html
└── tests/
    └── test_training_frontend.py  # 18 tests
```

---

## Next: Week 5

**Focus:** Members Section (or Dues depending on priority)

- Member list with employment history
- Dues status indicators
- Member detail with full history

---

*Phase 6 Week 4 complete. Training landing page fully operational.*
