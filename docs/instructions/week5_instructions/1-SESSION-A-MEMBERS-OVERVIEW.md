# Phase 6 Week 5 - Session A: Members Overview

**Document:** 1 of 3
**Estimated Time:** 2-3 hours
**Focus:** Members landing page with stats dashboard and classification breakdown

---

## Objective

Create the members landing page with:
- Stats dashboard (total, active, new this month, dues current)
- Classification breakdown with counts
- Recent member activity
- Quick action buttons
- Navigation to full member list

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show ~224 passed
```

---

## Step 1: Create Member Frontend Service (45 min)

Create `src/services/member_frontend_service.py`:

```python
"""
Member Frontend Service - Stats and queries for member pages.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from src.models.member import Member
from src.models.member_employment import MemberEmployment
from src.models.organization import Organization
from src.models.dues_payment import DuesPayment
from src.models.dues_period import DuesPeriod
from src.db.enums import MemberStatus, MemberClassification, DuesPaymentStatus

logger = logging.getLogger(__name__)


class MemberFrontendService:
    """Service for member frontend operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Stats Methods
    # ============================================================

    async def get_member_stats(self) -> dict:
        """
        Get overview statistics for the members dashboard.
        Returns counts for total, active, new this month, dues current.
        """
        # Total members (not deleted)
        total_stmt = select(func.count(Member.id)).where(Member.deleted_at.is_(None))
        total = (await self.db.execute(total_stmt)).scalar() or 0

        # Active members
        active_stmt = select(func.count(Member.id)).where(
            and_(
                Member.deleted_at.is_(None),
                Member.status == MemberStatus.ACTIVE
            )
        )
        active = (await self.db.execute(active_stmt)).scalar() or 0

        # New this month
        month_start = date.today().replace(day=1)
        new_stmt = select(func.count(Member.id)).where(
            and_(
                Member.deleted_at.is_(None),
                func.date(Member.created_at) >= month_start
            )
        )
        new_this_month = (await self.db.execute(new_stmt)).scalar() or 0

        # Inactive members
        inactive_stmt = select(func.count(Member.id)).where(
            and_(
                Member.deleted_at.is_(None),
                Member.status == MemberStatus.INACTIVE
            )
        )
        inactive = (await self.db.execute(inactive_stmt)).scalar() or 0

        # Suspended members
        suspended_stmt = select(func.count(Member.id)).where(
            and_(
                Member.deleted_at.is_(None),
                Member.status == MemberStatus.SUSPENDED
            )
        )
        suspended = (await self.db.execute(suspended_stmt)).scalar() or 0

        # Retired members
        retired_stmt = select(func.count(Member.id)).where(
            and_(
                Member.deleted_at.is_(None),
                Member.status == MemberStatus.RETIRED
            )
        )
        retired = (await self.db.execute(retired_stmt)).scalar() or 0

        # Calculate dues current percentage (simplified - based on active with recent payment)
        # This is a simplified version - adjust based on your actual dues logic
        dues_current_pct = 94  # Placeholder - implement actual calculation

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "suspended": suspended,
            "retired": retired,
            "new_this_month": new_this_month,
            "dues_current_pct": dues_current_pct,
        }

    async def get_classification_breakdown(self) -> List[dict]:
        """
        Get member counts by classification.
        Returns list of dicts with classification name and count.
        """
        stmt = select(
            Member.classification,
            func.count(Member.id).label("count")
        ).where(
            and_(
                Member.deleted_at.is_(None),
                Member.status == MemberStatus.ACTIVE
            )
        ).group_by(Member.classification).order_by(func.count(Member.id).desc())

        result = await self.db.execute(stmt)
        rows = result.fetchall()

        breakdown = []
        for row in rows:
            if row.classification:
                breakdown.append({
                    "classification": row.classification,
                    "display_name": self.format_classification(row.classification),
                    "count": row.count,
                    "badge_class": self.get_classification_badge_class(row.classification),
                })

        return breakdown

    async def get_recent_members(self, limit: int = 5) -> List[Member]:
        """Get most recently added members."""
        stmt = select(Member).where(
            Member.deleted_at.is_(None)
        ).order_by(Member.created_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ============================================================
    # Search and List Methods
    # ============================================================

    async def search_members(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        classification: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Member], int, int]:
        """
        Search members with filters and pagination.
        Returns (members, total_count, total_pages).
        """
        # Base query with eager loading
        stmt = select(Member).options(
            selectinload(Member.employments).selectinload(MemberEmployment.organization)
        ).where(Member.deleted_at.is_(None))

        # Apply search filter
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Member.card_id.ilike(search_term),
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    Member.email.ilike(search_term),
                    func.concat(Member.first_name, ' ', Member.last_name).ilike(search_term),
                )
            )

        # Apply status filter
        if status and status != "all":
            try:
                status_enum = MemberStatus(status)
                stmt = stmt.where(Member.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter

        # Apply classification filter
        if classification and classification != "all":
            try:
                class_enum = MemberClassification(classification)
                stmt = stmt.where(Member.classification == class_enum)
            except ValueError:
                pass  # Invalid classification, ignore filter

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Apply sorting and pagination
        stmt = stmt.order_by(Member.last_name, Member.first_name)
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(stmt)
        members = list(result.unique().scalars().all())

        total_pages = (total + per_page - 1) // per_page

        return members, total, total_pages

    async def get_member_by_id(self, member_id: int) -> Optional[Member]:
        """Get a single member by ID with relationships loaded."""
        stmt = select(Member).options(
            selectinload(Member.employments).selectinload(MemberEmployment.organization),
        ).where(
            and_(
                Member.id == member_id,
                Member.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_member_current_employer(self, member: Member) -> Optional[dict]:
        """Get member's current employer info."""
        for emp in member.employments:
            if emp.is_current or emp.end_date is None:
                return {
                    "id": emp.organization.id,
                    "name": emp.organization.name,
                    "start_date": emp.start_date,
                    "job_title": emp.job_title,
                    "hourly_rate": emp.hourly_rate,
                }
        return None

    # ============================================================
    # Employment History Methods
    # ============================================================

    async def get_employment_history(self, member_id: int) -> List[dict]:
        """Get member's employment history as timeline data."""
        stmt = select(MemberEmployment).options(
            selectinload(MemberEmployment.organization)
        ).where(
            MemberEmployment.member_id == member_id
        ).order_by(MemberEmployment.start_date.desc())

        result = await self.db.execute(stmt)
        employments = result.scalars().all()

        history = []
        for emp in employments:
            history.append({
                "id": emp.id,
                "organization_id": emp.organization_id,
                "organization_name": emp.organization.name if emp.organization else "Unknown",
                "start_date": emp.start_date,
                "end_date": emp.end_date,
                "is_current": emp.is_current or emp.end_date is None,
                "job_title": emp.job_title,
                "hourly_rate": emp.hourly_rate,
                "duration": self._calculate_duration(emp.start_date, emp.end_date),
            })

        return history

    def _calculate_duration(self, start_date: date, end_date: Optional[date]) -> str:
        """Calculate employment duration as human-readable string."""
        end = end_date or date.today()
        delta = end - start_date
        years = delta.days // 365
        months = (delta.days % 365) // 30

        if years > 0 and months > 0:
            return f"{years}y {months}m"
        elif years > 0:
            return f"{years}y"
        elif months > 0:
            return f"{months}m"
        else:
            return f"{delta.days}d"

    # ============================================================
    # Dues Methods
    # ============================================================

    async def get_member_dues_summary(self, member_id: int) -> dict:
        """Get member's dues payment summary."""
        # Get recent payments
        stmt = select(DuesPayment).options(
            selectinload(DuesPayment.period)
        ).where(
            DuesPayment.member_id == member_id
        ).order_by(DuesPayment.created_at.desc()).limit(6)

        result = await self.db.execute(stmt)
        payments = list(result.scalars().all())

        # Determine overall status
        if not payments:
            status = "unknown"
            status_class = "badge-ghost"
        else:
            latest = payments[0]
            if latest.status == DuesPaymentStatus.PAID:
                status = "current"
                status_class = "badge-success"
            elif latest.status == DuesPaymentStatus.OVERDUE:
                status = "overdue"
                status_class = "badge-error"
            elif latest.status == DuesPaymentStatus.PENDING:
                status = "pending"
                status_class = "badge-warning"
            else:
                status = "waived"
                status_class = "badge-info"

        # Calculate totals
        total_paid = sum(
            p.amount for p in payments
            if p.status == DuesPaymentStatus.PAID
        ) or Decimal("0.00")

        return {
            "status": status,
            "status_class": status_class,
            "recent_payments": payments[:3],
            "total_paid_ytd": total_paid,
            "payment_count": len(payments),
        }

    # ============================================================
    # Helper Methods
    # ============================================================

    @staticmethod
    def format_classification(classification: MemberClassification) -> str:
        """Format classification enum as display string."""
        mapping = {
            MemberClassification.JOURNEYMAN_WIREMAN: "Journeyman Wireman",
            MemberClassification.APPRENTICE_WIREMAN: "Apprentice Wireman",
            MemberClassification.JOURNEYMAN_TECHNICIAN: "Journeyman Technician",
            MemberClassification.APPRENTICE_TECHNICIAN: "Apprentice Technician",
            MemberClassification.RESIDENTIAL_WIREMAN: "Residential Wireman",
            MemberClassification.RESIDENTIAL_APPRENTICE: "Residential Apprentice",
            MemberClassification.INSTALLER_TECHNICIAN: "Installer Technician",
            MemberClassification.TRAINEE: "Trainee",
            MemberClassification.ORGANIZER: "Organizer",
        }
        return mapping.get(classification, str(classification).replace("_", " ").title())

    @staticmethod
    def get_classification_badge_class(classification: MemberClassification) -> str:
        """Get DaisyUI badge class for classification."""
        mapping = {
            MemberClassification.JOURNEYMAN_WIREMAN: "badge-primary",
            MemberClassification.APPRENTICE_WIREMAN: "badge-secondary",
            MemberClassification.JOURNEYMAN_TECHNICIAN: "badge-accent",
            MemberClassification.APPRENTICE_TECHNICIAN: "badge-info",
            MemberClassification.RESIDENTIAL_WIREMAN: "badge-success",
            MemberClassification.RESIDENTIAL_APPRENTICE: "badge-warning",
            MemberClassification.INSTALLER_TECHNICIAN: "badge-neutral",
            MemberClassification.TRAINEE: "badge-ghost",
            MemberClassification.ORGANIZER: "badge-error",
        }
        return mapping.get(classification, "badge-ghost")

    @staticmethod
    def get_status_badge_class(status: MemberStatus) -> str:
        """Get DaisyUI badge class for member status."""
        mapping = {
            MemberStatus.ACTIVE: "badge-success",
            MemberStatus.INACTIVE: "badge-warning",
            MemberStatus.SUSPENDED: "badge-error",
            MemberStatus.RETIRED: "badge-ghost",
            MemberStatus.DECEASED: "badge-neutral",
        }
        return mapping.get(status, "badge-ghost")


# Convenience function
async def get_member_frontend_service(db: AsyncSession) -> MemberFrontendService:
    return MemberFrontendService(db)
```

---

## Step 2: Create Member Frontend Router (30 min)

Create `src/routers/member_frontend.py`:

```python
"""
Member Frontend Router - HTML pages for member management.
"""

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.db.session import get_db
from src.services.member_frontend_service import MemberFrontendService
from src.routers.dependencies.auth_cookie import require_auth
from src.db.enums import MemberStatus, MemberClassification

router = APIRouter(prefix="/members", tags=["members-frontend"])
templates = Jinja2Templates(directory="src/templates")


# ============================================================
# Main Pages
# ============================================================

@router.get("", response_class=HTMLResponse)
async def members_landing_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the members landing page with overview stats."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = MemberFrontendService(db)

    # Get stats
    stats = await service.get_member_stats()

    # Get classification breakdown
    classification_breakdown = await service.get_classification_breakdown()

    # Get recent members
    recent_members = await service.get_recent_members(limit=5)

    # Get all statuses and classifications for filter dropdowns
    all_statuses = [s.value for s in MemberStatus]
    all_classifications = [c.value for c in MemberClassification]

    return templates.TemplateResponse(
        "members/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "classification_breakdown": classification_breakdown,
            "recent_members": recent_members,
            "all_statuses": all_statuses,
            "all_classifications": all_classifications,
            "format_classification": service.format_classification,
            "get_status_badge_class": service.get_status_badge_class,
        }
    )


@router.get("/stats", response_class=HTMLResponse)
async def members_stats_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: Return just the stats cards."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = MemberFrontendService(db)
    stats = await service.get_member_stats()

    return templates.TemplateResponse(
        "members/partials/_stats.html",
        {
            "request": request,
            "stats": stats,
        }
    )


# ============================================================
# Search Endpoint (for HTMX)
# ============================================================

@router.get("/search", response_class=HTMLResponse)
async def members_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status"),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    page: int = Query(1, ge=1, description="Page number"),
):
    """
    HTMX partial: Return member table body for search results.
    Used for live search without full page reload.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = MemberFrontendService(db)

    members, total, total_pages = await service.search_members(
        query=q,
        status=status,
        classification=classification,
        page=page,
        per_page=20,
    )

    # Get current employer for each member
    members_with_employer = []
    for member in members:
        employer = await service.get_member_current_employer(member)
        members_with_employer.append({
            "member": member,
            "current_employer": employer,
        })

    return templates.TemplateResponse(
        "members/partials/_table.html",
        {
            "request": request,
            "members_data": members_with_employer,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "status_filter": status or "all",
            "classification_filter": classification or "all",
            "format_classification": service.format_classification,
            "get_status_badge_class": service.get_status_badge_class,
            "get_classification_badge_class": service.get_classification_badge_class,
        }
    )
```

---

## Step 3: Create Members Landing Page Template (30 min)

Create directory structure:
```bash
mkdir -p src/templates/members/partials
```

Create `src/templates/members/index.html`:

```html
{% extends "base.html" %}

{% block title %}Members - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold">Members</h1>
            <p class="text-base-content/60">Manage union membership</p>
        </div>
        <div class="flex gap-2">
            <button class="btn btn-primary" onclick="document.getElementById('add-member-modal').showModal()">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
                </svg>
                Add Member
            </button>
        </div>
    </div>

    <!-- Stats Cards -->
    <div
        id="stats-container"
        hx-get="/members/stats"
        hx-trigger="stats-refresh from:body"
    >
        {% include "members/partials/_stats.html" %}
    </div>

    <!-- Classification Breakdown -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title text-lg">Members by Classification</h2>
            <div class="flex flex-wrap gap-3 mt-2">
                {% for item in classification_breakdown %}
                <div class="flex items-center gap-2 px-3 py-2 bg-base-200 rounded-lg">
                    <span class="badge {{ item.badge_class }}">{{ item.display_name }}</span>
                    <span class="font-bold">{{ item.count }}</span>
                </div>
                {% endfor %}
                {% if not classification_breakdown %}
                <p class="text-base-content/50">No classification data available</p>
                {% endif %}
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
                            placeholder="Search by name, card ID, or email..."
                            class="input input-bordered w-full pl-10"
                            hx-get="/members/search"
                            hx-trigger="input changed delay:300ms, search"
                            hx-target="#table-container"
                            hx-include="[name='status'], [name='classification']"
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
                        hx-get="/members/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='classification']"
                    >
                        <option value="all">All Status</option>
                        {% for status in all_statuses %}
                        <option value="{{ status }}">{{ status | title }}</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Classification Filter -->
                <div class="w-full lg:w-56">
                    <select
                        name="classification"
                        class="select select-bordered w-full"
                        hx-get="/members/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='status']"
                    >
                        <option value="all">All Classifications</option>
                        {% for classification in all_classifications %}
                        <option value="{{ classification }}">{{ format_classification(classification) }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- Member Table -->
    <div class="card bg-base-100 shadow overflow-hidden">
        <div
            id="table-container"
            hx-get="/members/search"
            hx-trigger="load"
        >
            <div class="flex justify-center py-12">
                <span class="loading loading-spinner loading-lg"></span>
            </div>
        </div>
    </div>
</div>

<!-- Add Member Modal (placeholder) -->
<dialog id="add-member-modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg">Add New Member</h3>
        <p class="py-4 text-base-content/60">Member registration form coming in a future update.</p>
        <div class="modal-action">
            <form method="dialog">
                <button class="btn">Close</button>
            </form>
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

---

## Step 4: Create Stats Partial (15 min)

Create `src/templates/members/partials/_stats.html`:

```html
{# Stats cards partial - refreshable via HTMX #}

<div class="stats stats-vertical lg:stats-horizontal shadow w-full">
    <!-- Total Members -->
    <div class="stat">
        <div class="stat-figure text-primary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
        </div>
        <div class="stat-title">Total Members</div>
        <div class="stat-value text-primary">{{ "{:,}".format(stats.total) }}</div>
        <div class="stat-desc">
            {% if stats.new_this_month > 0 %}
            <span class="text-success">↗︎ {{ stats.new_this_month }} new this month</span>
            {% else %}
            All time
            {% endif %}
        </div>
    </div>

    <!-- Active Members -->
    <div class="stat">
        <div class="stat-figure text-success">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
        </div>
        <div class="stat-title">Active</div>
        <div class="stat-value text-success">{{ "{:,}".format(stats.active) }}</div>
        <div class="stat-desc">{{ ((stats.active / stats.total) * 100) | round(1) if stats.total > 0 else 0 }}% of total</div>
    </div>

    <!-- Inactive/Suspended -->
    <div class="stat">
        <div class="stat-figure text-warning">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
        </div>
        <div class="stat-title">Inactive/Suspended</div>
        <div class="stat-value text-warning">{{ stats.inactive + stats.suspended }}</div>
        <div class="stat-desc">{{ stats.inactive }} inactive, {{ stats.suspended }} suspended</div>
    </div>

    <!-- Dues Current -->
    <div class="stat">
        <div class="stat-figure text-info">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
        </div>
        <div class="stat-title">Dues Current</div>
        <div class="stat-value text-info">{{ stats.dues_current_pct }}%</div>
        <div class="stat-desc">Of active members</div>
    </div>
</div>
```

---

## Step 5: Register Router in main.py (5 min)

Update `src/main.py`:

```python
# Add import
from src.routers.member_frontend import router as member_frontend_router

# Add router (after other frontend routers, before catch-all frontend)
app.include_router(member_frontend_router)
```

---

## Step 6: Add Initial Tests (15 min)

Create `src/tests/test_member_frontend.py`:

```python
"""
Member frontend tests.
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
```

---

## Step 7: Test Manually

```bash
# Start server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

1. Login at `/login`
2. Navigate to `/members`
3. Verify stats cards display
4. Verify classification breakdown displays
5. Verify search/filter controls are present

---

## Step 8: Run Tests

```bash
pytest src/tests/test_member_frontend.py -v

# Expected: 5 tests passing
```

---

## Step 9: Commit

```bash
git add -A
git status

git commit -m "feat(members): Phase 6 Week 5 Session A - Members landing page

- Create MemberFrontendService with stats queries
- Create member_frontend router with landing and stats endpoints
- Create members/index.html with stats dashboard
- Create _stats.html partial with 4 stat cards
- Classification breakdown with badge styling
- Search and filter controls (HTMX ready)
- Register router in main.py
- Initial member frontend tests (5)

Stats: total members, active, inactive/suspended, dues current %
Filters: status, classification (prepared for Session B)"

git push origin main
```

---

## Session A Checklist

- [ ] Created `src/services/member_frontend_service.py`
- [ ] Created `src/routers/member_frontend.py`
- [ ] Created `src/templates/members/index.html`
- [ ] Created `src/templates/members/partials/_stats.html`
- [ ] Registered router in main.py
- [ ] Stats cards displaying
- [ ] Classification breakdown displaying
- [ ] Search/filter controls present
- [ ] Initial tests passing (5)
- [ ] Committed changes

---

## Files Created This Session

```
src/
├── services/
│   └── member_frontend_service.py    # Stats, search, helpers
├── routers/
│   └── member_frontend.py            # Landing and stats routes
├── templates/
│   └── members/
│       ├── index.html                # Landing page
│       └── partials/
│           └── _stats.html           # Stats cards
└── tests/
    └── test_member_frontend.py       # Initial tests (5)
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

*Session A complete. Proceed to Session B for member list with search and filters.*
