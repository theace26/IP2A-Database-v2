# Phase 6 Week 6 - Session A: SALTing Activities

**Document:** 1 of 4
**Estimated Time:** 2-3 hours
**Focus:** Operations landing page and SALTing activities list/detail

---

## Objective

Create the Union Operations foundation and SALTing activities UI:
- Operations landing page with section cards
- SALTing list with employer and score display
- SALTing detail with activity logs
- Filter by status and score
- HTMX live search

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show ~238 passed
```

---

## Step 1: Create Operations Frontend Service (45 min)

Create `src/services/operations_frontend_service.py`:

```python
"""
Operations Frontend Service - Stats and queries for union operations pages.
Covers SALTing, Benevolence, and Grievances.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from src.models.salting_activity import SaltingActivity
from src.models.salting_log import SaltingLog
from src.models.benevolence_request import BenevolenceRequest
from src.models.benevolence_payment import BenevolencePayment
from src.models.grievance import Grievance
from src.models.grievance_step import GrievanceStep
from src.models.organization import Organization
from src.models.member import Member
from src.models.user import User
from src.db.enums import (
    SaltingStatus, BenevolenceStatus, BenevolenceType,
    GrievanceStatus, GrievanceCategory
)

logger = logging.getLogger(__name__)


class OperationsFrontendService:
    """Service for union operations frontend pages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Overview Stats
    # ============================================================

    async def get_operations_overview(self) -> dict:
        """Get overview stats for all three operations modules."""
        # SALTing stats
        salting_active = await self._count_salting_by_status(SaltingStatus.ACTIVE)
        salting_total = await self._count_salting_total()

        # Benevolence stats
        benevolence_pending = await self._count_benevolence_by_status(BenevolenceStatus.PENDING)
        benevolence_ytd = await self._benevolence_amount_ytd()

        # Grievance stats
        grievances_open = await self._count_grievances_open()
        grievances_total = await self._count_grievances_total()

        return {
            "salting": {
                "active": salting_active,
                "total": salting_total,
            },
            "benevolence": {
                "pending": benevolence_pending,
                "ytd_amount": benevolence_ytd,
            },
            "grievances": {
                "open": grievances_open,
                "total": grievances_total,
            },
        }

    async def _count_salting_by_status(self, status: SaltingStatus) -> int:
        stmt = select(func.count(SaltingActivity.id)).where(
            SaltingActivity.status == status
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def _count_salting_total(self) -> int:
        stmt = select(func.count(SaltingActivity.id))
        return (await self.db.execute(stmt)).scalar() or 0

    async def _count_benevolence_by_status(self, status: BenevolenceStatus) -> int:
        stmt = select(func.count(BenevolenceRequest.id)).where(
            BenevolenceRequest.status == status
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def _benevolence_amount_ytd(self) -> Decimal:
        year_start = date(date.today().year, 1, 1)
        stmt = select(func.sum(BenevolencePayment.amount)).where(
            BenevolencePayment.payment_date >= year_start
        )
        return (await self.db.execute(stmt)).scalar() or Decimal("0.00")

    async def _count_grievances_open(self) -> int:
        open_statuses = [
            GrievanceStatus.FILED, GrievanceStatus.STEP_1,
            GrievanceStatus.STEP_2, GrievanceStatus.STEP_3,
            GrievanceStatus.STEP_4
        ]
        stmt = select(func.count(Grievance.id)).where(
            Grievance.status.in_(open_statuses)
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def _count_grievances_total(self) -> int:
        stmt = select(func.count(Grievance.id))
        return (await self.db.execute(stmt)).scalar() or 0

    # ============================================================
    # SALTing Methods
    # ============================================================

    async def get_salting_stats(self) -> dict:
        """Get SALTing-specific stats for the list page."""
        total = await self._count_salting_total()
        active = await self._count_salting_by_status(SaltingStatus.ACTIVE)
        planning = await self._count_salting_by_status(SaltingStatus.PLANNING)
        completed = await self._count_salting_by_status(SaltingStatus.COMPLETED)

        # Average score of active campaigns
        avg_stmt = select(func.avg(SaltingActivity.score)).where(
            SaltingActivity.status == SaltingStatus.ACTIVE
        )
        avg_score = (await self.db.execute(avg_stmt)).scalar() or 0

        return {
            "total": total,
            "active": active,
            "planning": planning,
            "completed": completed,
            "avg_score": round(float(avg_score), 1),
        }

    async def search_salting_activities(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        score: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[SaltingActivity], int, int]:
        """Search SALTing activities with filters."""
        stmt = select(SaltingActivity).options(
            selectinload(SaltingActivity.employer),
            selectinload(SaltingActivity.organizer),
        )

        # Search by employer name or notes
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.join(SaltingActivity.employer).where(
                or_(
                    Organization.name.ilike(search_term),
                    SaltingActivity.notes.ilike(search_term),
                )
            )

        # Filter by status
        if status and status != "all":
            try:
                status_enum = SaltingStatus(status)
                stmt = stmt.where(SaltingActivity.status == status_enum)
            except ValueError:
                pass

        # Filter by score
        if score and score > 0:
            stmt = stmt.where(SaltingActivity.score == score)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Apply sorting and pagination
        stmt = stmt.order_by(SaltingActivity.updated_at.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(stmt)
        activities = list(result.unique().scalars().all())

        total_pages = (total + per_page - 1) // per_page

        return activities, total, total_pages

    async def get_salting_activity_by_id(self, activity_id: int) -> Optional[SaltingActivity]:
        """Get a single SALTing activity with all relationships."""
        stmt = select(SaltingActivity).options(
            selectinload(SaltingActivity.employer),
            selectinload(SaltingActivity.organizer),
            selectinload(SaltingActivity.logs).selectinload(SaltingLog.logged_by),
        ).where(SaltingActivity.id == activity_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_recent_salting_activities(self, limit: int = 5) -> List[SaltingActivity]:
        """Get most recently updated SALTing activities."""
        stmt = select(SaltingActivity).options(
            selectinload(SaltingActivity.employer),
        ).order_by(SaltingActivity.updated_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ============================================================
    # Helper Methods
    # ============================================================

    @staticmethod
    def get_salting_status_badge_class(status: SaltingStatus) -> str:
        """Get DaisyUI badge class for SALTing status."""
        mapping = {
            SaltingStatus.PLANNING: "badge-info",
            SaltingStatus.ACTIVE: "badge-success",
            SaltingStatus.PAUSED: "badge-warning",
            SaltingStatus.COMPLETED: "badge-primary",
            SaltingStatus.ABANDONED: "badge-ghost",
        }
        return mapping.get(status, "badge-ghost")

    @staticmethod
    def get_score_class(score: int) -> str:
        """Get color class based on score (1-5)."""
        if score >= 4:
            return "text-success"
        elif score >= 3:
            return "text-warning"
        else:
            return "text-error"


# Convenience function
async def get_operations_frontend_service(db: AsyncSession) -> OperationsFrontendService:
    return OperationsFrontendService(db)
```

---

## Step 2: Create Operations Frontend Router (30 min)

Create `src/routers/operations_frontend.py`:

```python
"""
Operations Frontend Router - HTML pages for union operations.
Covers SALTing, Benevolence, and Grievances.
"""

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.db.session import get_db
from src.services.operations_frontend_service import OperationsFrontendService
from src.routers.dependencies.auth_cookie import require_auth
from src.db.enums import SaltingStatus

router = APIRouter(prefix="/operations", tags=["operations-frontend"])
templates = Jinja2Templates(directory="src/templates")


# ============================================================
# Operations Landing
# ============================================================

@router.get("", response_class=HTMLResponse)
async def operations_landing_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the union operations landing page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    overview = await service.get_operations_overview()

    return templates.TemplateResponse(
        "operations/index.html",
        {
            "request": request,
            "user": current_user,
            "overview": overview,
        }
    )


# ============================================================
# SALTing Routes
# ============================================================

@router.get("/salting", response_class=HTMLResponse)
async def salting_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render SALTing activities list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    stats = await service.get_salting_stats()
    all_statuses = [s.value for s in SaltingStatus]

    return templates.TemplateResponse(
        "operations/salting/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "all_statuses": all_statuses,
            "get_status_badge_class": service.get_salting_status_badge_class,
        }
    )


@router.get("/salting/search", response_class=HTMLResponse)
async def salting_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    score: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
):
    """HTMX partial: SALTing table body."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = OperationsFrontendService(db)
    activities, total, total_pages = await service.search_salting_activities(
        query=q,
        status=status,
        score=score,
        page=page,
    )

    return templates.TemplateResponse(
        "operations/salting/partials/_table.html",
        {
            "request": request,
            "activities": activities,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "status_filter": status or "all",
            "score_filter": score or 0,
            "get_status_badge_class": service.get_salting_status_badge_class,
            "get_score_class": service.get_score_class,
        }
    )


@router.get("/salting/{activity_id}", response_class=HTMLResponse)
async def salting_detail_page(
    request: Request,
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render SALTing activity detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    activity = await service.get_salting_activity_by_id(activity_id)

    if not activity:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "SALTing activity not found"},
            status_code=404
        )

    all_statuses = [s.value for s in SaltingStatus]

    return templates.TemplateResponse(
        "operations/salting/detail.html",
        {
            "request": request,
            "user": current_user,
            "activity": activity,
            "all_statuses": all_statuses,
            "get_status_badge_class": service.get_salting_status_badge_class,
            "get_score_class": service.get_score_class,
        }
    )
```

---

## Step 3: Create Operations Landing Page (20 min)

Create directory structure:
```bash
mkdir -p src/templates/operations/salting/partials
mkdir -p src/templates/operations/benevolence/partials
mkdir -p src/templates/operations/grievances/partials
```

Create `src/templates/operations/index.html`:

```html
{% extends "base.html" %}

{% block title %}Union Operations - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Page Header -->
    <div>
        <h1 class="text-2xl font-bold">Union Operations</h1>
        <p class="text-base-content/60">Organizing activities, benevolence fund, and grievance tracking</p>
    </div>

    <!-- Module Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- SALTing Card -->
        <div class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow">
            <div class="card-body">
                <div class="flex items-center gap-3">
                    <div class="p-3 bg-primary/10 rounded-lg">
                        <svg class="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                        </svg>
                    </div>
                    <div>
                        <h2 class="card-title">SALTing Activities</h2>
                        <p class="text-sm text-base-content/60">Strategic organizing campaigns</p>
                    </div>
                </div>

                <div class="stats stats-vertical shadow mt-4">
                    <div class="stat py-2">
                        <div class="stat-title text-xs">Active Campaigns</div>
                        <div class="stat-value text-lg text-primary">{{ overview.salting.active }}</div>
                    </div>
                    <div class="stat py-2">
                        <div class="stat-title text-xs">Total</div>
                        <div class="stat-value text-lg">{{ overview.salting.total }}</div>
                    </div>
                </div>

                <div class="card-actions justify-end mt-4">
                    <a href="/operations/salting" class="btn btn-primary">
                        View Activities
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                        </svg>
                    </a>
                </div>
            </div>
        </div>

        <!-- Benevolence Card -->
        <div class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow">
            <div class="card-body">
                <div class="flex items-center gap-3">
                    <div class="p-3 bg-secondary/10 rounded-lg">
                        <svg class="w-8 h-8 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                        </svg>
                    </div>
                    <div>
                        <h2 class="card-title">Benevolence Fund</h2>
                        <p class="text-sm text-base-content/60">Member assistance program</p>
                    </div>
                </div>

                <div class="stats stats-vertical shadow mt-4">
                    <div class="stat py-2">
                        <div class="stat-title text-xs">Pending Requests</div>
                        <div class="stat-value text-lg text-secondary">{{ overview.benevolence.pending }}</div>
                    </div>
                    <div class="stat py-2">
                        <div class="stat-title text-xs">Paid YTD</div>
                        <div class="stat-value text-lg">${{ "{:,.2f}".format(overview.benevolence.ytd_amount) }}</div>
                    </div>
                </div>

                <div class="card-actions justify-end mt-4">
                    <a href="/operations/benevolence" class="btn btn-secondary">
                        View Requests
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                        </svg>
                    </a>
                </div>
            </div>
        </div>

        <!-- Grievances Card -->
        <div class="card bg-base-100 shadow-lg hover:shadow-xl transition-shadow">
            <div class="card-body">
                <div class="flex items-center gap-3">
                    <div class="p-3 bg-accent/10 rounded-lg">
                        <svg class="w-8 h-8 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                    </div>
                    <div>
                        <h2 class="card-title">Grievances</h2>
                        <p class="text-sm text-base-content/60">Contract enforcement</p>
                    </div>
                </div>

                <div class="stats stats-vertical shadow mt-4">
                    <div class="stat py-2">
                        <div class="stat-title text-xs">Open Cases</div>
                        <div class="stat-value text-lg text-accent">{{ overview.grievances.open }}</div>
                    </div>
                    <div class="stat py-2">
                        <div class="stat-title text-xs">Total Filed</div>
                        <div class="stat-value text-lg">{{ overview.grievances.total }}</div>
                    </div>
                </div>

                <div class="card-actions justify-end mt-4">
                    <a href="/operations/grievances" class="btn btn-accent">
                        View Grievances
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                        </svg>
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 4: Create SALTing List Page (25 min)

Create `src/templates/operations/salting/index.html`:

```html
{% extends "base.html" %}

{% block title %}SALTing Activities - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/operations">Operations</a></li>
            <li>SALTing Activities</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold">SALTing Activities</h1>
            <p class="text-base-content/60">Strategic Approach to Labor Targeting campaigns</p>
        </div>
        <button class="btn btn-primary">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
            New Campaign
        </button>
    </div>

    <!-- Stats Cards -->
    <div class="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div class="stat">
            <div class="stat-title">Total Campaigns</div>
            <div class="stat-value">{{ stats.total }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Active</div>
            <div class="stat-value text-success">{{ stats.active }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Planning</div>
            <div class="stat-value text-info">{{ stats.planning }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Completed</div>
            <div class="stat-value text-primary">{{ stats.completed }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Avg Score</div>
            <div class="stat-value">{{ stats.avg_score }}/5</div>
        </div>
    </div>

    <!-- Search and Filters -->
    <div class="card bg-base-100 shadow">
        <div class="card-body p-4">
            <div class="flex flex-col lg:flex-row gap-4">
                <!-- Search -->
                <div class="flex-1">
                    <div class="relative">
                        <input
                            type="search"
                            name="q"
                            placeholder="Search by employer name..."
                            class="input input-bordered w-full pl-10"
                            hx-get="/operations/salting/search"
                            hx-trigger="input changed delay:300ms, search"
                            hx-target="#table-container"
                            hx-include="[name='status'], [name='score']"
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
                        hx-get="/operations/salting/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='score']"
                    >
                        <option value="all">All Status</option>
                        {% for status in all_statuses %}
                        <option value="{{ status }}">{{ status | title }}</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Score Filter -->
                <div class="w-full lg:w-40">
                    <select
                        name="score"
                        class="select select-bordered w-full"
                        hx-get="/operations/salting/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='status']"
                    >
                        <option value="0">All Scores</option>
                        <option value="5">★★★★★ (5)</option>
                        <option value="4">★★★★☆ (4)</option>
                        <option value="3">★★★☆☆ (3)</option>
                        <option value="2">★★☆☆☆ (2)</option>
                        <option value="1">★☆☆☆☆ (1)</option>
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- Activity Table -->
    <div class="card bg-base-100 shadow overflow-hidden">
        <div
            id="table-container"
            hx-get="/operations/salting/search"
            hx-trigger="load"
        >
            <div class="flex justify-center py-12">
                <span class="loading loading-spinner loading-lg"></span>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 5: Create SALTing Table Partial (20 min)

Create `src/templates/operations/salting/partials/_table.html`:

```html
{# SALTing activities table - updated via HTMX #}

<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr class="bg-base-200">
                <th>Employer</th>
                <th>Organizer</th>
                <th>Status</th>
                <th>Score</th>
                <th>Target</th>
                <th>Started</th>
                <th class="w-24">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% if activities %}
                {% for activity in activities %}
                <tr class="hover">
                    <!-- Employer -->
                    <td>
                        <div class="font-bold">{{ activity.employer.name if activity.employer else 'Unknown' }}</div>
                    </td>

                    <!-- Organizer -->
                    <td>
                        <div class="flex items-center gap-2">
                            <div class="avatar placeholder">
                                <div class="bg-neutral text-neutral-content rounded-full w-8">
                                    <span class="text-xs">
                                        {{ activity.organizer.first_name[0] | upper if activity.organizer else '?' }}{{ activity.organizer.last_name[0] | upper if activity.organizer else '' }}
                                    </span>
                                </div>
                            </div>
                            <span class="text-sm">
                                {{ activity.organizer.first_name if activity.organizer else 'N/A' }} {{ activity.organizer.last_name if activity.organizer else '' }}
                            </span>
                        </div>
                    </td>

                    <!-- Status -->
                    <td>
                        <span class="badge {{ get_status_badge_class(activity.status) }}">
                            {{ activity.status.value | title }}
                        </span>
                    </td>

                    <!-- Score (1-5 stars) -->
                    <td>
                        <div class="flex items-center gap-1">
                            <div class="rating rating-sm rating-half">
                                {% for i in range(1, 6) %}
                                <span class="mask mask-star-2 {{ 'bg-warning' if i <= activity.score else 'bg-base-300' }}"></span>
                                {% endfor %}
                            </div>
                            <span class="text-sm {{ get_score_class(activity.score) }}">{{ activity.score }}</span>
                        </div>
                    </td>

                    <!-- Target Workers -->
                    <td>
                        {{ activity.target_workers or '—' }}
                    </td>

                    <!-- Started Date -->
                    <td>
                        {{ activity.started_at.strftime('%b %d, %Y') if activity.started_at else '—' }}
                    </td>

                    <!-- Actions -->
                    <td>
                        <a href="/operations/salting/{{ activity.id }}" class="btn btn-ghost btn-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                        </a>
                    </td>
                </tr>
                {% endfor %}
            {% else %}
            <tr>
                <td colspan="7" class="text-center py-12">
                    <div class="text-base-content/50">
                        <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                        </svg>
                        <p class="text-lg">No SALTing activities found</p>
                        {% if query %}
                        <p class="text-sm mt-1">Try adjusting your search or filters</p>
                        {% endif %}
                    </div>
                </td>
            </tr>
            {% endif %}
        </tbody>
    </table>
</div>

{% if activities %}
<!-- Pagination -->
<div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-base-200">
    <div class="text-sm text-base-content/60">
        Showing {{ ((current_page - 1) * 20) + 1 }} - {{ ((current_page - 1) * 20) + activities|length }} of {{ total }}
    </div>

    <div class="join">
        {% if current_page > 1 %}
        <button
            class="join-item btn btn-sm"
            hx-get="/operations/salting/search?page={{ current_page - 1 }}&q={{ query }}&status={{ status_filter }}&score={{ score_filter }}"
            hx-target="#table-container"
        >«</button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">«</button>
        {% endif %}

        <button class="join-item btn btn-sm btn-active">{{ current_page }}</button>

        {% if current_page < total_pages %}
        <button
            class="join-item btn btn-sm"
            hx-get="/operations/salting/search?page={{ current_page + 1 }}&q={{ query }}&status={{ status_filter }}&score={{ score_filter }}"
            hx-target="#table-container"
        >»</button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">»</button>
        {% endif %}
    </div>
</div>
{% endif %}
```

---

## Step 6: Create SALTing Detail Page (25 min)

Create `src/templates/operations/salting/detail.html`:

```html
{% extends "base.html" %}

{% block title %}{{ activity.employer.name if activity.employer else 'SALTing Activity' }} - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/operations">Operations</a></li>
            <li><a href="/operations/salting">SALTing</a></li>
            <li>{{ activity.employer.name if activity.employer else 'Activity' }}</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
            <div class="flex items-center gap-3">
                <h1 class="text-2xl font-bold">{{ activity.employer.name if activity.employer else 'Unknown Employer' }}</h1>
                <span class="badge {{ get_status_badge_class(activity.status) }} badge-lg">
                    {{ activity.status.value | title }}
                </span>
            </div>
            <p class="text-base-content/60 mt-1">SALTing Campaign #{{ activity.id }}</p>
        </div>
        <div class="flex gap-2">
            <a href="/operations/salting" class="btn btn-ghost">← Back</a>
            <button class="btn btn-primary">Edit Campaign</button>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Content -->
        <div class="lg:col-span-2 space-y-6">
            <!-- Campaign Info -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Campaign Information</h2>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <div>
                            <label class="text-sm text-base-content/60">Employer</label>
                            <p class="font-medium">{{ activity.employer.name if activity.employer else 'Unknown' }}</p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Lead Organizer</label>
                            <p class="font-medium">
                                {{ activity.organizer.first_name if activity.organizer else 'N/A' }}
                                {{ activity.organizer.last_name if activity.organizer else '' }}
                            </p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Target Workers</label>
                            <p class="font-medium">{{ activity.target_workers or 'Not specified' }}</p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Score</label>
                            <div class="flex items-center gap-2">
                                <div class="rating rating-md">
                                    {% for i in range(1, 6) %}
                                    <span class="mask mask-star-2 {{ 'bg-warning' if i <= activity.score else 'bg-base-300' }}"></span>
                                    {% endfor %}
                                </div>
                                <span class="font-bold {{ get_score_class(activity.score) }}">{{ activity.score }}/5</span>
                            </div>
                        </div>
                    </div>

                    {% if activity.notes %}
                    <div class="mt-4">
                        <label class="text-sm text-base-content/60">Notes</label>
                        <p class="mt-1 whitespace-pre-wrap">{{ activity.notes }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Activity Log Timeline -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <div class="flex items-center justify-between">
                        <h2 class="card-title">Activity Log</h2>
                        <button class="btn btn-sm btn-primary">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                            </svg>
                            Add Entry
                        </button>
                    </div>

                    {% if activity.logs %}
                    <ul class="timeline timeline-vertical mt-4">
                        {% for log in activity.logs | sort(attribute='logged_at', reverse=True) %}
                        <li>
                            {% if not loop.first %}
                            <hr class="bg-primary"/>
                            {% endif %}
                            <div class="timeline-start text-sm text-base-content/60">
                                {{ log.logged_at.strftime('%b %d') }}<br>
                                {{ log.logged_at.strftime('%I:%M %p') }}
                            </div>
                            <div class="timeline-middle">
                                <svg class="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                                </svg>
                            </div>
                            <div class="timeline-end timeline-box">
                                <div class="font-bold">{{ log.action }}</div>
                                {% if log.notes %}
                                <p class="text-sm text-base-content/70 mt-1">{{ log.notes }}</p>
                                {% endif %}
                                <div class="text-xs text-base-content/50 mt-2">
                                    by {{ log.logged_by.email if log.logged_by else 'Unknown' }}
                                </div>
                            </div>
                            {% if not loop.last %}
                            <hr class="bg-primary"/>
                            {% endif %}
                        </li>
                        {% endfor %}
                    </ul>
                    {% else %}
                    <div class="text-center py-8 text-base-content/50">
                        <p>No activity logs yet</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
            <!-- Status Card -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Status</h2>
                    <select class="select select-bordered w-full mt-2">
                        {% for status in all_statuses %}
                        <option value="{{ status }}" {{ 'selected' if activity.status.value == status }}>
                            {{ status | title }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
            </div>

            <!-- Timeline Card -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Timeline</h2>
                    <div class="space-y-3 text-sm mt-2">
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Started</span>
                            <span>{{ activity.started_at.strftime('%b %d, %Y') if activity.started_at else '—' }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Completed</span>
                            <span>{{ activity.completed_at.strftime('%b %d, %Y') if activity.completed_at else '—' }}</span>
                        </div>
                        <div class="divider my-2"></div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Created</span>
                            <span>{{ activity.created_at.strftime('%b %d, %Y') }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Updated</span>
                            <span>{{ activity.updated_at.strftime('%b %d, %Y') }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Quick Actions</h2>
                    <div class="space-y-2 mt-2">
                        <button class="btn btn-outline btn-block btn-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
                            Schedule Meeting
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

## Step 7: Register Router in main.py (5 min)

Update `src/main.py`:

```python
# Add import
from src.routers.operations_frontend import router as operations_frontend_router

# Add router (after member_frontend, before catch-all frontend)
app.include_router(operations_frontend_router)
```

---

## Step 8: Test Manually

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

1. Login at `/login`
2. Navigate to `/operations` - verify landing page
3. Click "View Activities" - verify SALTing list
4. Click on an activity - verify detail page
5. Test search and filters

---

## Step 9: Commit Session A

```bash
git add -A
git status

git commit -m "feat(operations): Phase 6 Week 6 Session A - SALTing Activities

- Create OperationsFrontendService with stats queries
- Create operations_frontend router
- Operations landing page with module cards
- SALTing list with score visualization (1-5 stars)
- SALTing detail with activity log timeline
- Filter by status and score
- HTMX live search

Stats: total, active, planning, completed, avg score
Filters: status (5 options), score (1-5)"

git push origin main
```

---

## Session A Checklist

- [ ] Created `src/services/operations_frontend_service.py`
- [ ] Created `src/routers/operations_frontend.py`
- [ ] Created `src/templates/operations/index.html`
- [ ] Created `src/templates/operations/salting/index.html`
- [ ] Created `src/templates/operations/salting/detail.html`
- [ ] Created `src/templates/operations/salting/partials/_table.html`
- [ ] Registered router in main.py
- [ ] Operations landing displays
- [ ] SALTing list with scores
- [ ] SALTing detail with log timeline
- [ ] Search and filters working
- [ ] Committed changes

---

*Session A complete. Proceed to Session B for Benevolence Fund management.*
