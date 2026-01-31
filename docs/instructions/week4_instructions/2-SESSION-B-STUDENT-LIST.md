# Phase 6 Week 4 - Session B: Student List

**Document:** 2 of 3
**Estimated Time:** 2-3 hours
**Focus:** Student list with search, filters, and status badges

---

## Objective

Create the student list page with:
- Table displaying all students
- Live search (name, student number, email)
- Filter by status and cohort
- Status badges with appropriate colors
- Pagination
- Link to student detail (nice to have)

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show 210+ passed
```

---

## Step 1: Create Student List Page (30 min)

Create `src/templates/training/students/index.html`:

```html
{% extends "base.html" %}

{% block title %}Students - Training - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/training">Training</a></li>
            <li>Students</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold">Students</h1>
            <p class="text-base-content/60">Manage pre-apprenticeship students</p>
        </div>
        <div class="flex gap-2">
            <button class="btn btn-primary" onclick="alert('Student registration coming soon!')">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
                </svg>
                Add Student
            </button>
        </div>
    </div>

    <!-- Stats Summary -->
    <div class="stats stats-vertical sm:stats-horizontal shadow w-full">
        <div class="stat">
            <div class="stat-title">Total</div>
            <div class="stat-value text-primary">{{ total }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Active</div>
            <div class="stat-value text-success">
                {{ students | selectattr('status.value', 'equalto', 'active') | list | length }}
            </div>
        </div>
        <div class="stat">
            <div class="stat-title">Graduated</div>
            <div class="stat-value text-info">
                {{ students | selectattr('status.value', 'equalto', 'graduated') | list | length }}
            </div>
        </div>
    </div>

    <!-- Search and Filters -->
    <div class="card bg-base-100 shadow">
        <div class="card-body p-4">
            <div class="flex flex-col lg:flex-row gap-4">
                <!-- Search Input -->
                <div class="flex-1">
                    <div class="relative">
                        <input
                            type="search"
                            name="q"
                            value="{{ query }}"
                            placeholder="Search by name, student number, or email..."
                            class="input input-bordered w-full pl-10"
                            hx-get="/training/students/search"
                            hx-trigger="input changed delay:300ms, search"
                            hx-target="#table-container"
                            hx-include="[name='status'], [name='cohort']"
                            hx-indicator="#search-spinner"
                        />
                        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-base-content/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                        <span id="search-spinner" class="loading loading-spinner loading-sm absolute right-3 top-1/2 -translate-y-1/2 htmx-indicator"></span>
                    </div>
                </div>

                <!-- Status Filter -->
                <div class="w-full lg:w-48">
                    <select
                        name="status"
                        class="select select-bordered w-full"
                        hx-get="/training/students/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='cohort']"
                    >
                        <option value="all" {% if status_filter == 'all' %}selected{% endif %}>All Status</option>
                        <option value="active" {% if status_filter == 'active' %}selected{% endif %}>Active</option>
                        <option value="graduated" {% if status_filter == 'graduated' %}selected{% endif %}>Graduated</option>
                        <option value="dropped" {% if status_filter == 'dropped' %}selected{% endif %}>Dropped</option>
                        <option value="suspended" {% if status_filter == 'suspended' %}selected{% endif %}>Suspended</option>
                        <option value="on_leave" {% if status_filter == 'on_leave' %}selected{% endif %}>On Leave</option>
                    </select>
                </div>

                <!-- Cohort Filter -->
                <div class="w-full lg:w-48">
                    <select
                        name="cohort"
                        class="select select-bordered w-full"
                        hx-get="/training/students/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='status']"
                    >
                        <option value="" {% if not cohort_filter %}selected{% endif %}>All Cohorts</option>
                        {% for cohort in cohorts %}
                        <option value="{{ cohort.id }}" {% if cohort_filter == cohort.id %}selected{% endif %}>
                            {{ cohort.name }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- Student Table -->
    <div class="card bg-base-100 shadow overflow-hidden">
        <div id="table-container">
            {% include "training/students/partials/_table.html" %}
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 2: Create Student Table Partial (25 min)

Create `src/templates/training/students/partials/_table.html`:

```html
{# Student table partial - updated via HTMX search #}

<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr class="bg-base-200">
                <th>Student</th>
                <th>Student #</th>
                <th>Status</th>
                <th>Cohort</th>
                <th>Enrolled</th>
                <th class="w-24">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% if students %}
                {% for student in students %}
                {% include "training/students/partials/_row.html" %}
                {% endfor %}
            {% else %}
            <tr>
                <td colspan="6" class="text-center py-8">
                    <div class="text-base-content/50">
                        <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
                        </svg>
                        <p>No students found</p>
                        {% if query %}
                        <p class="text-sm">Try adjusting your search or filters</p>
                        {% endif %}
                    </div>
                </td>
            </tr>
            {% endif %}
        </tbody>
    </table>
</div>

{% if students %}
<!-- Pagination -->
<div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-base-200">
    <div class="text-sm text-base-content/60">
        Showing {{ ((current_page - 1) * 20) + 1 }} - {{ ((current_page - 1) * 20) + students|length }} of {{ total }} students
    </div>

    <div class="join">
        {% if current_page > 1 %}
        <button
            class="join-item btn btn-sm"
            hx-get="/training/students/search?page={{ current_page - 1 }}&q={{ query }}&status={{ status_filter }}&cohort={{ cohort_filter or '' }}"
            hx-target="#table-container"
        >
            «
        </button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">«</button>
        {% endif %}

        {% for p in range(1, total_pages + 1) %}
            {% if p == current_page %}
            <button class="join-item btn btn-sm btn-active">{{ p }}</button>
            {% elif p == 1 or p == total_pages or (p >= current_page - 2 and p <= current_page + 2) %}
            <button
                class="join-item btn btn-sm"
                hx-get="/training/students/search?page={{ p }}&q={{ query }}&status={{ status_filter }}&cohort={{ cohort_filter or '' }}"
                hx-target="#table-container"
            >
                {{ p }}
            </button>
            {% elif p == current_page - 3 or p == current_page + 3 %}
            <button class="join-item btn btn-sm btn-disabled">...</button>
            {% endif %}
        {% endfor %}

        {% if current_page < total_pages %}
        <button
            class="join-item btn btn-sm"
            hx-get="/training/students/search?page={{ current_page + 1 }}&q={{ query }}&status={{ status_filter }}&cohort={{ cohort_filter or '' }}"
            hx-target="#table-container"
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

---

## Step 3: Create Student Row Partial (15 min)

Create `src/templates/training/students/partials/_row.html`:

```html
{# Single student row #}

<tr class="hover" id="student-row-{{ student.id }}">
    <td>
        <div class="flex items-center gap-3">
            <div class="avatar placeholder">
                <div class="bg-neutral text-neutral-content rounded-full w-10">
                    <span class="text-sm">
                        {{ student.first_name[0] | upper }}{{ student.last_name[0] | upper }}
                    </span>
                </div>
            </div>
            <div>
                <div class="font-bold">{{ student.first_name }} {{ student.last_name }}</div>
                <div class="text-sm text-base-content/60">{{ student.email }}</div>
            </div>
        </div>
    </td>
    <td>
        <span class="font-mono text-sm">{{ student.student_number }}</span>
    </td>
    <td>
        <span class="badge {{ get_status_badge(student.status) }} badge-sm">
            {{ student.status.value | replace('_', ' ') | title }}
        </span>
    </td>
    <td>
        {% if student.cohort %}
        <span class="text-sm">{{ student.cohort.name }}</span>
        {% else %}
        <span class="text-sm text-base-content/50">None</span>
        {% endif %}
    </td>
    <td>
        <span class="text-sm">{{ student.enrollment_date.strftime('%b %d, %Y') }}</span>
    </td>
    <td>
        <div class="flex gap-1">
            <a href="/training/students/{{ student.id }}" class="btn btn-ghost btn-sm" title="View Details">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
            </a>
            <div class="dropdown dropdown-end">
                <label tabindex="0" class="btn btn-ghost btn-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/>
                    </svg>
                </label>
                <ul tabindex="0" class="dropdown-content z-[1] menu menu-sm p-2 shadow-lg bg-base-100 rounded-box w-48">
                    <li>
                        <a href="/training/students/{{ student.id }}">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                            View Details
                        </a>
                    </li>
                    <li>
                        <a onclick="alert('Edit coming soon!')">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                            </svg>
                            Edit Student
                        </a>
                    </li>
                    <li>
                        <a onclick="alert('Enrollment coming soon!')">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                            </svg>
                            Enroll in Course
                        </a>
                    </li>
                    {% if student.status.value == 'active' %}
                    <div class="divider my-1"></div>
                    <li>
                        <a class="text-warning" onclick="alert('Status change coming soon!')">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                            </svg>
                            Mark Dropped
                        </a>
                    </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </td>
</tr>
```

---

## Step 4: Create Student Detail Page (Optional - Nice to Have) (20 min)

Create `src/templates/training/students/detail.html`:

```html
{% extends "base.html" %}

{% block title %}{{ student.first_name }} {{ student.last_name }} - Students - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/training">Training</a></li>
            <li><a href="/training/students">Students</a></li>
            <li>{{ student.first_name }} {{ student.last_name }}</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="flex items-center gap-4">
            <div class="avatar placeholder">
                <div class="bg-neutral text-neutral-content rounded-full w-16">
                    <span class="text-xl">
                        {{ student.first_name[0] | upper }}{{ student.last_name[0] | upper }}
                    </span>
                </div>
            </div>
            <div>
                <h1 class="text-2xl font-bold">{{ student.first_name }} {{ student.last_name }}</h1>
                <p class="text-base-content/60">{{ student.student_number }}</p>
            </div>
        </div>
        <span class="badge {{ get_status_badge(student.status) }} badge-lg">
            {{ student.status.value | replace('_', ' ') | title }}
        </span>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Info -->
        <div class="lg:col-span-2 space-y-6">
            <!-- Contact Info -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Contact Information</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="label"><span class="label-text text-base-content/60">Email</span></label>
                            <p class="font-medium">{{ student.email }}</p>
                        </div>
                        <div>
                            <label class="label"><span class="label-text text-base-content/60">Phone</span></label>
                            <p class="font-medium">{{ student.phone or 'Not provided' }}</p>
                        </div>
                        <div>
                            <label class="label"><span class="label-text text-base-content/60">Date of Birth</span></label>
                            <p class="font-medium">
                                {% if student.date_of_birth %}
                                {{ student.date_of_birth.strftime('%B %d, %Y') }}
                                {% else %}
                                Not provided
                                {% endif %}
                            </p>
                        </div>
                        <div>
                            <label class="label"><span class="label-text text-base-content/60">Cohort</span></label>
                            <p class="font-medium">{{ student.cohort.name if student.cohort else 'None' }}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Enrollments -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Course Enrollments</h2>
                    {% if student.enrollments %}
                    <div class="overflow-x-auto">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Course</th>
                                    <th>Status</th>
                                    <th>Grade</th>
                                    <th>Enrolled</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for enrollment in student.enrollments %}
                                <tr>
                                    <td>
                                        <div class="font-medium">{{ enrollment.course.code }}</div>
                                        <div class="text-sm text-base-content/60">{{ enrollment.course.name }}</div>
                                    </td>
                                    <td>
                                        <span class="badge {{ get_enrollment_badge(enrollment.status) }} badge-sm">
                                            {{ enrollment.status.value | title }}
                                        </span>
                                    </td>
                                    <td>{{ enrollment.grade or '-' }}</td>
                                    <td>{{ enrollment.enrolled_at.strftime('%b %d, %Y') }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <p class="text-base-content/50 text-center py-4">No course enrollments</p>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
            <!-- Dates -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Program Dates</h2>
                    <div class="space-y-3">
                        <div>
                            <label class="label"><span class="label-text text-base-content/60">Enrolled</span></label>
                            <p class="font-medium">{{ student.enrollment_date.strftime('%B %d, %Y') }}</p>
                        </div>
                        <div>
                            <label class="label"><span class="label-text text-base-content/60">Expected Graduation</span></label>
                            <p class="font-medium">
                                {% if student.expected_graduation %}
                                {{ student.expected_graduation.strftime('%B %d, %Y') }}
                                {% else %}
                                Not set
                                {% endif %}
                            </p>
                        </div>
                        {% if student.actual_graduation %}
                        <div>
                            <label class="label"><span class="label-text text-base-content/60">Graduated</span></label>
                            <p class="font-medium text-success">{{ student.actual_graduation.strftime('%B %d, %Y') }}</p>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>

            <!-- Notes -->
            {% if student.notes %}
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Notes</h2>
                    <p class="text-sm">{{ student.notes }}</p>
                </div>
            </div>
            {% endif %}

            <!-- Actions -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Actions</h2>
                    <div class="space-y-2">
                        <button class="btn btn-outline btn-block" onclick="alert('Coming soon!')">
                            Edit Student
                        </button>
                        <button class="btn btn-outline btn-block" onclick="alert('Coming soon!')">
                            Enroll in Course
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 5: Add Student Detail Route (10 min)

Add to `src/routers/training_frontend.py`:

```python
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
            status_code=404
        )

    return templates.TemplateResponse(
        "training/students/detail.html",
        {
            "request": request,
            "user": current_user,
            "student": student,
            "get_status_badge": TrainingFrontendService.get_status_badge_class,
            "get_enrollment_badge": TrainingFrontendService.get_enrollment_badge_class,
        }
    )
```

---

## Step 6: Test Manually

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

1. Login and go to `/training/students`
2. Verify student table displays
3. Test search - type in search box
4. Test filters - change status/cohort dropdowns
5. Test pagination - click page numbers
6. Click on a student to view detail page

---

## Step 7: Add More Tests

Update `src/tests/test_training_frontend.py`:

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
    async def test_students_page_requires_auth(self, async_client: AsyncClient):
        """Students page should require authentication."""
        response = await async_client.get("/training/students", follow_redirects=False)
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_students_search_exists(self, async_client: AsyncClient):
        """Students search endpoint should exist."""
        response = await async_client.get("/training/students/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_students_search_with_query(self, async_client: AsyncClient):
        """Students search accepts query parameter."""
        response = await async_client.get("/training/students/search?q=john")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_students_search_with_status(self, async_client: AsyncClient):
        """Students search accepts status filter."""
        response = await async_client.get("/training/students/search?status=active")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_students_search_with_pagination(self, async_client: AsyncClient):
        """Students search accepts page parameter."""
        response = await async_client.get("/training/students/search?page=2")
        assert response.status_code in [200, 302, 401]


class TestStudentDetail:
    """Tests for student detail page."""

    @pytest.mark.asyncio
    async def test_student_detail_exists(self, async_client: AsyncClient):
        """Student detail page route should exist."""
        response = await async_client.get("/training/students/1")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_student_detail_requires_auth(self, async_client: AsyncClient):
        """Student detail page should require authentication."""
        response = await async_client.get("/training/students/1", follow_redirects=False)
        assert response.status_code in [302, 401, 404]


class TestCourseList:
    """Tests for course list page."""

    @pytest.mark.asyncio
    async def test_courses_page_exists(self, async_client: AsyncClient):
        """Courses page route should exist."""
        response = await async_client.get("/training/courses")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_courses_page_requires_auth(self, async_client: AsyncClient):
        """Courses page should require authentication."""
        response = await async_client.get("/training/courses", follow_redirects=False)
        assert response.status_code in [302, 401]
```

---

## Step 8: Run Tests

```bash
pytest -v --tb=short

# Expected: 217+ tests passing (210 + 7 new)
```

---

## Step 9: Commit

```bash
git add -A
git status

git commit -m "feat(training): Phase 6 Week 4 Session B - Student list

- Create students/index.html list page
- Create _table.html and _row.html partials
- HTMX live search with 300ms debounce
- Filter by status (active/graduated/dropped/etc)
- Filter by cohort
- Status badges with color coding
- Pagination component
- Student detail page (basic)
- 7 new tests (217 total)

Student list features:
- Search by name, student number, email
- Color-coded status badges
- Action dropdown per row
- Stats summary at top"

git push origin main
```

---

## Session B Checklist

- [ ] Created `training/students/index.html`
- [ ] Created `training/students/partials/_table.html`
- [ ] Created `training/students/partials/_row.html`
- [ ] Created `training/students/detail.html`
- [ ] Added student detail route
- [ ] HTMX search working
- [ ] Status filter working
- [ ] Cohort filter working
- [ ] Pagination working
- [ ] Status badges colored correctly
- [ ] Tests passing
- [ ] Committed changes

---

## Files Created This Session

```
src/
├── templates/
│   └── training/
│       └── students/
│           ├── index.html           # List page
│           ├── detail.html          # Detail page
│           └── partials/
│               ├── _table.html      # Table with pagination
│               └── _row.html        # Student row
└── tests/
    └── test_training_frontend.py    # Updated (12 tests now)
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

*Session B complete. Proceed to Session C for course list and enrollment actions.*
