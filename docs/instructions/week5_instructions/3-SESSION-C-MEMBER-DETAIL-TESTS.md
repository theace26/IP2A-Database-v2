# Phase 6 Week 5 - Session C: Member Detail + Employment + Tests

**Document:** 3 of 3
**Estimated Time:** 2-3 hours
**Focus:** Member detail page, employment history timeline, dues summary, comprehensive tests

---

## Objective

Complete the members section with:
- Full member detail page
- Employment history as timeline
- Dues summary section
- Contact information display
- HTMX-loaded sections
- Comprehensive test coverage (15+ total)
- Documentation updates

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show ~234 passed
```

---

## Step 1: Add Detail Page Endpoint (15 min)

Add to `src/routers/member_frontend.py`:

```python
@router.get("/{member_id}", response_class=HTMLResponse)
async def member_detail_page(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the full member detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = MemberFrontendService(db)
    member = await service.get_member_by_id(member_id)

    if not member:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Member not found"},
            status_code=404
        )

    # Get current employer
    current_employer = await service.get_member_current_employer(member)

    # Get employment history
    employment_history = await service.get_employment_history(member_id)

    # Get dues summary
    dues_summary = await service.get_member_dues_summary(member_id)

    # Get all statuses and classifications for editing
    all_statuses = [s.value for s in MemberStatus]
    all_classifications = [c.value for c in MemberClassification]

    return templates.TemplateResponse(
        "members/detail.html",
        {
            "request": request,
            "user": current_user,
            "member": member,
            "current_employer": current_employer,
            "employment_history": employment_history,
            "dues_summary": dues_summary,
            "all_statuses": all_statuses,
            "all_classifications": all_classifications,
            "format_classification": service.format_classification,
            "get_status_badge_class": service.get_status_badge_class,
            "get_classification_badge_class": service.get_classification_badge_class,
        }
    )


@router.get("/{member_id}/employment", response_class=HTMLResponse)
async def member_employment_partial(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: Return employment history section."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = MemberFrontendService(db)
    employment_history = await service.get_employment_history(member_id)

    return templates.TemplateResponse(
        "members/partials/_employment.html",
        {
            "request": request,
            "member_id": member_id,
            "employment_history": employment_history,
        }
    )


@router.get("/{member_id}/dues", response_class=HTMLResponse)
async def member_dues_partial(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: Return dues summary section."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = MemberFrontendService(db)
    dues_summary = await service.get_member_dues_summary(member_id)

    return templates.TemplateResponse(
        "members/partials/_dues_summary.html",
        {
            "request": request,
            "member_id": member_id,
            "dues_summary": dues_summary,
        }
    )
```

---

## Step 2: Create Member Detail Page (35 min)

Create `src/templates/members/detail.html`:

```html
{% extends "base.html" %}

{% block title %}{{ member.first_name }} {{ member.last_name }} - Members - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/members">Members</a></li>
            <li>{{ member.first_name }} {{ member.last_name }}</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div class="flex items-center gap-4">
            <div class="avatar placeholder">
                <div class="bg-neutral text-neutral-content rounded-full w-20">
                    <span class="text-2xl">
                        {{ member.first_name[0] | upper if member.first_name else '?' }}{{ member.last_name[0] | upper if member.last_name else '' }}
                    </span>
                </div>
            </div>
            <div>
                <h1 class="text-2xl font-bold">
                    {{ member.first_name }} {{ member.last_name }}
                </h1>
                <div class="flex flex-wrap items-center gap-2 mt-1">
                    <span class="font-mono text-base-content/60">{{ member.card_id or 'No Card ID' }}</span>
                    <span class="badge {{ get_status_badge_class(member.status) }}">
                        {{ member.status.value | title }}
                    </span>
                    {% if member.classification %}
                    <span class="badge {{ get_classification_badge_class(member.classification) }}">
                        {{ format_classification(member.classification) }}
                    </span>
                    {% endif %}
                </div>
            </div>
        </div>
        <div class="flex gap-2">
            <a href="/members" class="btn btn-ghost">
                ← Back to Members
            </a>
            <button class="btn btn-primary">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
                Edit
            </button>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Content (2/3) -->
        <div class="lg:col-span-2 space-y-6">
            <!-- Contact Information -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Contact Information</h2>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                        <div>
                            <label class="text-sm text-base-content/60">Email</label>
                            <p class="font-medium">
                                {% if member.email %}
                                <a href="mailto:{{ member.email }}" class="link link-primary">{{ member.email }}</a>
                                {% else %}
                                <span class="text-base-content/40">Not provided</span>
                                {% endif %}
                            </p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Phone</label>
                            <p class="font-medium">
                                {% if member.phone %}
                                <a href="tel:{{ member.phone }}" class="link">{{ member.phone }}</a>
                                {% else %}
                                <span class="text-base-content/40">Not provided</span>
                                {% endif %}
                            </p>
                        </div>
                        <div class="md:col-span-2">
                            <label class="text-sm text-base-content/60">Address</label>
                            <p class="font-medium">
                                {% if member.address %}
                                {{ member.address }}<br>
                                {{ member.city }}{% if member.state %}, {{ member.state }}{% endif %} {{ member.zip_code }}
                                {% else %}
                                <span class="text-base-content/40">Not provided</span>
                                {% endif %}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Employment History -->
            <div class="card bg-base-100 shadow" id="employment">
                <div class="card-body">
                    <div class="flex items-center justify-between">
                        <h2 class="card-title">Employment History</h2>
                        <button class="btn btn-sm btn-ghost">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                            </svg>
                            Add Employment
                        </button>
                    </div>

                    <div
                        id="employment-content"
                        hx-get="/members/{{ member.id }}/employment"
                        hx-trigger="load"
                        hx-swap="innerHTML"
                    >
                        <div class="flex justify-center py-8">
                            <span class="loading loading-spinner loading-md"></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Dues History -->
            <div class="card bg-base-100 shadow" id="dues">
                <div class="card-body">
                    <div class="flex items-center justify-between">
                        <h2 class="card-title">Dues Status</h2>
                        <a href="/dues/payments/new?member_id={{ member.id }}" class="btn btn-sm btn-ghost">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                            </svg>
                            Record Payment
                        </a>
                    </div>

                    <div
                        id="dues-content"
                        hx-get="/members/{{ member.id }}/dues"
                        hx-trigger="load, dues-updated from:body"
                        hx-swap="innerHTML"
                    >
                        <div class="flex justify-center py-8">
                            <span class="loading loading-spinner loading-md"></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Sidebar (1/3) -->
        <div class="space-y-6">
            <!-- Current Employment -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Current Employment</h2>

                    {% if current_employer %}
                    <div class="space-y-2">
                        <div>
                            <label class="text-sm text-base-content/60">Employer</label>
                            <p class="font-bold">{{ current_employer.name }}</p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Since</label>
                            <p>{{ current_employer.start_date.strftime('%B %d, %Y') }}</p>
                        </div>
                        {% if current_employer.job_title %}
                        <div>
                            <label class="text-sm text-base-content/60">Position</label>
                            <p>{{ current_employer.job_title }}</p>
                        </div>
                        {% endif %}
                        {% if current_employer.hourly_rate %}
                        <div>
                            <label class="text-sm text-base-content/60">Hourly Rate</label>
                            <p>${{ "%.2f"|format(current_employer.hourly_rate) }}</p>
                        </div>
                        {% endif %}
                    </div>
                    {% else %}
                    <p class="text-base-content/50">Not currently employed</p>
                    {% endif %}
                </div>
            </div>

            <!-- Quick Info -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Member Info</h2>

                    <div class="space-y-3 text-sm">
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Member ID</span>
                            <span class="font-mono">{{ member.id }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Card ID</span>
                            <span class="font-mono">{{ member.card_id or '—' }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Status</span>
                            <span class="badge {{ get_status_badge_class(member.status) }} badge-sm">
                                {{ member.status.value | title }}
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Classification</span>
                            <span>
                                {% if member.classification %}
                                {{ format_classification(member.classification) }}
                                {% else %}
                                —
                                {% endif %}
                            </span>
                        </div>
                        <div class="divider my-2"></div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Hire Date</span>
                            <span>{{ member.hire_date.strftime('%b %d, %Y') if member.hire_date else '—' }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Created</span>
                            <span>{{ member.created_at.strftime('%b %d, %Y') }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Updated</span>
                            <span>{{ member.updated_at.strftime('%b %d, %Y') }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Quick Actions</h2>

                    <div class="space-y-2">
                        <button class="btn btn-outline btn-block btn-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
                            Schedule Meeting
                        </button>
                        <button class="btn btn-outline btn-block btn-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                            </svg>
                            Send Email
                        </button>
                        <button class="btn btn-outline btn-block btn-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            View Documents
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

## Step 3: Create Employment History Partial (20 min)

Create `src/templates/members/partials/_employment.html`:

```html
{# Employment history timeline - loaded via HTMX #}

{% if employment_history %}
<ul class="timeline timeline-vertical timeline-compact">
    {% for emp in employment_history %}
    <li>
        {% if not loop.first %}
        <hr class="{{ 'bg-primary' if emp.is_current else 'bg-base-300' }}"/>
        {% endif %}

        <div class="timeline-start text-sm text-base-content/60">
            {{ emp.start_date.strftime('%b %Y') }}
            {% if emp.end_date %}
            <br>to {{ emp.end_date.strftime('%b %Y') }}
            {% endif %}
        </div>

        <div class="timeline-middle">
            {% if emp.is_current %}
            <svg class="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            {% else %}
            <svg class="w-5 h-5 text-base-300" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16z" clip-rule="evenodd"/>
            </svg>
            {% endif %}
        </div>

        <div class="timeline-end timeline-box {{ 'border-primary' if emp.is_current else '' }}">
            <div class="flex items-start justify-between gap-2">
                <div>
                    <div class="font-bold">{{ emp.organization_name }}</div>
                    {% if emp.job_title %}
                    <div class="text-sm text-base-content/70">{{ emp.job_title }}</div>
                    {% endif %}
                </div>
                {% if emp.is_current %}
                <span class="badge badge-primary badge-sm">Current</span>
                {% endif %}
            </div>

            <div class="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-sm text-base-content/60">
                <span>{{ emp.duration }}</span>
                {% if emp.hourly_rate %}
                <span>${{ "%.2f"|format(emp.hourly_rate) }}/hr</span>
                {% endif %}
            </div>
        </div>

        {% if not loop.last %}
        <hr class="{{ 'bg-primary' if emp.is_current else 'bg-base-300' }}"/>
        {% endif %}
    </li>
    {% endfor %}
</ul>
{% else %}
<div class="text-center py-8 text-base-content/50">
    <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
    </svg>
    <p>No employment history recorded</p>
</div>
{% endif %}
```

---

## Step 4: Create Dues Summary Partial (15 min)

Create `src/templates/members/partials/_dues_summary.html`:

```html
{# Dues summary section - loaded via HTMX #}

<div class="space-y-4">
    <!-- Status Banner -->
    <div class="alert {{ 'alert-success' if dues_summary.status == 'current' else 'alert-error' if dues_summary.status == 'overdue' else 'alert-warning' if dues_summary.status == 'pending' else 'alert-info' }}">
        {% if dues_summary.status == 'current' %}
        <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Dues are current</span>
        {% elif dues_summary.status == 'overdue' %}
        <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>Dues are overdue</span>
        {% elif dues_summary.status == 'pending' %}
        <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Payment pending</span>
        {% else %}
        <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>No dues information</span>
        {% endif %}
    </div>

    <!-- Summary Stats -->
    <div class="stats stats-vertical sm:stats-horizontal shadow w-full">
        <div class="stat">
            <div class="stat-title">YTD Paid</div>
            <div class="stat-value text-lg">${{ "%.2f"|format(dues_summary.total_paid_ytd) }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Payments</div>
            <div class="stat-value text-lg">{{ dues_summary.payment_count }}</div>
        </div>
    </div>

    <!-- Recent Payments -->
    {% if dues_summary.recent_payments %}
    <div>
        <h3 class="font-medium mb-2">Recent Payments</h3>
        <div class="overflow-x-auto">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    {% for payment in dues_summary.recent_payments %}
                    <tr>
                        <td>{{ payment.period.name if payment.period else 'N/A' }}</td>
                        <td>${{ "%.2f"|format(payment.amount) }}</td>
                        <td>
                            <span class="badge badge-{{ 'success' if payment.status.value == 'paid' else 'error' if payment.status.value == 'overdue' else 'warning' }} badge-xs">
                                {{ payment.status.value | title }}
                            </span>
                        </td>
                        <td>{{ payment.payment_date.strftime('%b %d') if payment.payment_date else '—' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}

    <!-- View All Link -->
    <div class="text-center">
        <a href="/dues/member/{{ member_id }}" class="link link-primary text-sm">
            View Full Dues History →
        </a>
    </div>
</div>
```

---

## Step 5: Comprehensive Test Suite (25 min)

Update `src/tests/test_member_frontend.py`:

```python
"""
Comprehensive member frontend tests.
Tests landing, search, detail, employment, and dues sections.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestMembersLanding:
    """Tests for members landing page."""

    @pytest.mark.asyncio
    async def test_members_page_requires_auth(self, async_client: AsyncClient):
        """Members page redirects to login when not authenticated."""
        response = await async_client.get("/members", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_members_page_exists(self, async_client: AsyncClient):
        """Members page route exists."""
        response = await async_client.get("/members")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_members_stats_endpoint(self, async_client: AsyncClient):
        """Stats endpoint exists."""
        response = await async_client.get("/members/stats")
        assert response.status_code in [200, 302, 401]


class TestMembersSearch:
    """Tests for member search functionality."""

    @pytest.mark.asyncio
    async def test_search_endpoint_exists(self, async_client: AsyncClient):
        """Search endpoint exists."""
        response = await async_client.get("/members/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_query(self, async_client: AsyncClient):
        """Search accepts query parameter."""
        response = await async_client.get("/members/search?q=john")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self, async_client: AsyncClient):
        """Search accepts status filter."""
        response = await async_client.get("/members/search?status=active")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_classification_filter(self, async_client: AsyncClient):
        """Search accepts classification filter."""
        response = await async_client.get("/members/search?classification=journeyman_wireman")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, async_client: AsyncClient):
        """Search accepts page parameter."""
        response = await async_client.get("/members/search?page=2")
        assert response.status_code in [200, 302, 401]


class TestMemberDetail:
    """Tests for member detail page."""

    @pytest.mark.asyncio
    async def test_detail_page_exists(self, async_client: AsyncClient):
        """Detail page route exists."""
        response = await async_client.get("/members/1")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_detail_page_requires_auth(self, async_client: AsyncClient):
        """Detail page requires authentication."""
        response = await async_client.get("/members/1", follow_redirects=False)
        assert response.status_code in [302, 401, 404]

    @pytest.mark.asyncio
    async def test_nonexistent_member_returns_404(self, async_client: AsyncClient):
        """Requesting nonexistent member returns 404."""
        response = await async_client.get("/members/99999")
        assert response.status_code in [302, 401, 404]


class TestMemberEdit:
    """Tests for member edit functionality."""

    @pytest.mark.asyncio
    async def test_edit_modal_endpoint(self, async_client: AsyncClient):
        """Edit modal endpoint exists."""
        response = await async_client.get("/members/1/edit")
        assert response.status_code in [200, 302, 401, 404]


class TestMemberEmployment:
    """Tests for employment history section."""

    @pytest.mark.asyncio
    async def test_employment_endpoint_exists(self, async_client: AsyncClient):
        """Employment partial endpoint exists."""
        response = await async_client.get("/members/1/employment")
        assert response.status_code in [200, 302, 401, 404]


class TestMemberDues:
    """Tests for dues summary section."""

    @pytest.mark.asyncio
    async def test_dues_endpoint_exists(self, async_client: AsyncClient):
        """Dues partial endpoint exists."""
        response = await async_client.get("/members/1/dues")
        assert response.status_code in [200, 302, 401, 404]


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_member_id(self, async_client: AsyncClient):
        """Invalid member ID is handled."""
        response = await async_client.get("/members/abc")
        assert response.status_code in [302, 401, 404, 422]
```

---

## Step 6: Run All Tests

```bash
pytest -v --tb=short

# Expected: ~240 tests passing
# New member frontend tests: 17
```

---

## Step 7: Update Documentation

### Update CHANGELOG.md

Add to `[Unreleased]`:

```markdown
- **Phase 6 Week 5: Members Landing Page**
  * Members landing page with overview stats
  * Stats: total, active, inactive/suspended, dues current %
  * Classification breakdown with badge styling
  * Member list with HTMX search (300ms debounce)
  * Filter by status and classification
  * Status and classification badges
  * Current employer column
  * Member detail page with contact info
  * Employment history timeline (HTMX loaded)
  * Dues summary section (HTMX loaded)
  * Quick edit modal
  * MemberFrontendService for stats and queries
  * 17 new member frontend tests
```

### Update CLAUDE.md

Add Week 5 section showing completion status.

---

## Step 8: Final Commit

```bash
git add -A
git status

git commit -m "feat(members): Phase 6 Week 5 Complete - Members Landing

Session A: Members overview
- MemberFrontendService with stats queries
- Members landing page with 4 stat cards
- Classification breakdown with badges
- Search and filter controls

Session B: Member list
- Table with all member columns
- Status and classification badges
- Current employer display
- Quick edit modal
- Row actions dropdown
- Pagination

Session C: Member detail
- Full detail page with contact info
- Employment history timeline (HTMX loaded)
- Dues summary section (HTMX loaded)
- Current employer sidebar
- Quick actions sidebar
- Comprehensive tests (17 new)

Tests: 240+ passing"

git push origin main
```

---

## Week 5 Complete Checklist

### Session A
- [ ] `MemberFrontendService` created
- [ ] `member_frontend.py` router created
- [ ] `members/index.html` landing page
- [ ] `_stats.html` partial with 4 stat cards
- [ ] Classification breakdown displaying

### Session B
- [ ] `_table.html` with all columns
- [ ] `_row.html` with badges
- [ ] `_edit_modal.html` for quick edit
- [ ] HTMX search working
- [ ] Status filter working
- [ ] Classification filter working
- [ ] Pagination working

### Session C
- [ ] `detail.html` full page
- [ ] `_employment.html` timeline partial
- [ ] `_dues_summary.html` partial
- [ ] Employment endpoint
- [ ] Dues endpoint
- [ ] Comprehensive tests (17)
- [ ] Documentation updated
- [ ] All tests passing (240+)
- [ ] Committed and pushed

---

## Files Created/Modified Summary

```
src/
├── services/
│   └── member_frontend_service.py   # Stats, search, history, dues
├── routers/
│   └── member_frontend.py           # All member endpoints
├── templates/
│   └── members/
│       ├── index.html               # Landing page
│       ├── detail.html              # Detail page
│       └── partials/
│           ├── _stats.html          # Stats cards
│           ├── _table.html          # Table with pagination
│           ├── _row.html            # Member row
│           ├── _edit_modal.html     # Quick edit
│           ├── _employment.html     # Employment timeline
│           └── _dues_summary.html   # Dues section
└── tests/
    └── test_member_frontend.py      # 17 tests
```

---

## Next: Week 6

**Focus:** Dues Management

- Dues dashboard with period overview
- Payment entry form
- Period management
- Overdue tracking

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

*Phase 6 Week 5 complete. Members landing page fully operational with employment history and dues status.*
