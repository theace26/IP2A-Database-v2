# Session A: Dues Landing + Rates Management

**Duration:** 2-3 hours
**Goal:** Dues landing page with stats + rates management UI

---

## Prerequisites

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Verify 259 passing
```

---

## Task 1: Create DuesFrontendService

Create `src/services/dues_frontend_service.py`:

```python
"""Frontend service for dues management UI."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from src.db.models import DuesRate, DuesPeriod, DuesPayment, DuesAdjustment, Member
from src.db.enums import (
    MemberClassification,
    DuesPaymentStatus,
    DuesPaymentMethod,
    DuesAdjustmentType,
    AdjustmentStatus,
)


class DuesFrontendService:
    """Service for dues frontend operations."""

    # Classification badge colors (matches member badges)
    CLASSIFICATION_COLORS = {
        MemberClassification.JOURNEYMAN: "badge-primary",
        MemberClassification.APPRENTICE_1: "badge-secondary",
        MemberClassification.APPRENTICE_2: "badge-secondary",
        MemberClassification.APPRENTICE_3: "badge-secondary",
        MemberClassification.APPRENTICE_4: "badge-secondary",
        MemberClassification.APPRENTICE_5: "badge-secondary",
        MemberClassification.FOREMAN: "badge-accent",
        MemberClassification.RETIREE: "badge-ghost",
        MemberClassification.HONORARY: "badge-ghost",
    }

    # Payment status badge colors
    PAYMENT_STATUS_COLORS = {
        DuesPaymentStatus.PENDING: "badge-warning",
        DuesPaymentStatus.PAID: "badge-success",
        DuesPaymentStatus.PARTIAL: "badge-info",
        DuesPaymentStatus.OVERDUE: "badge-error",
        DuesPaymentStatus.WAIVED: "badge-ghost",
    }

    # Adjustment status badge colors
    ADJUSTMENT_STATUS_COLORS = {
        AdjustmentStatus.PENDING: "badge-warning",
        AdjustmentStatus.APPROVED: "badge-success",
        AdjustmentStatus.DENIED: "badge-error",
    }

    # Adjustment type badge colors
    ADJUSTMENT_TYPE_COLORS = {
        DuesAdjustmentType.WAIVER: "badge-info",
        DuesAdjustmentType.CREDIT: "badge-success",
        DuesAdjustmentType.HARDSHIP: "badge-warning",
        DuesAdjustmentType.CORRECTION: "badge-secondary",
        DuesAdjustmentType.OTHER: "badge-ghost",
    }

    @staticmethod
    def get_classification_badge_class(classification: MemberClassification) -> str:
        """Get badge class for member classification."""
        return DuesFrontendService.CLASSIFICATION_COLORS.get(
            classification, "badge-ghost"
        )

    @staticmethod
    def get_payment_status_badge_class(status: DuesPaymentStatus) -> str:
        """Get badge class for payment status."""
        return DuesFrontendService.PAYMENT_STATUS_COLORS.get(status, "badge-ghost")

    @staticmethod
    def get_adjustment_status_badge_class(status: AdjustmentStatus) -> str:
        """Get badge class for adjustment status."""
        return DuesFrontendService.ADJUSTMENT_STATUS_COLORS.get(status, "badge-ghost")

    @staticmethod
    def get_adjustment_type_badge_class(adj_type: DuesAdjustmentType) -> str:
        """Get badge class for adjustment type."""
        return DuesFrontendService.ADJUSTMENT_TYPE_COLORS.get(adj_type, "badge-ghost")

    @staticmethod
    def get_landing_stats(db: Session) -> dict:
        """Get stats for dues landing page."""
        today = date.today()
        current_month_start = today.replace(day=1)
        current_year_start = today.replace(month=1, day=1)

        # Current period
        current_period = (
            db.query(DuesPeriod)
            .filter(
                and_(
                    DuesPeriod.is_closed == False,
                    DuesPeriod.due_date <= today,
                )
            )
            .order_by(DuesPeriod.due_date.desc())
            .first()
        )

        # If no open period with past due date, get next upcoming
        if not current_period:
            current_period = (
                db.query(DuesPeriod)
                .filter(DuesPeriod.is_closed == False)
                .order_by(DuesPeriod.due_date.asc())
                .first()
            )

        # MTD collections
        mtd_collected = (
            db.query(func.coalesce(func.sum(DuesPayment.amount_paid), Decimal("0")))
            .filter(
                and_(
                    DuesPayment.payment_date >= current_month_start,
                    DuesPayment.payment_date <= today,
                )
            )
            .scalar()
        )

        # YTD collections
        ytd_collected = (
            db.query(func.coalesce(func.sum(DuesPayment.amount_paid), Decimal("0")))
            .filter(
                and_(
                    DuesPayment.payment_date >= current_year_start,
                    DuesPayment.payment_date <= today,
                )
            )
            .scalar()
        )

        # Overdue count
        overdue_count = (
            db.query(func.count(DuesPayment.id))
            .filter(DuesPayment.status == DuesPaymentStatus.OVERDUE)
            .scalar()
        )

        # Pending adjustments
        pending_adjustments = (
            db.query(func.count(DuesAdjustment.id))
            .filter(DuesAdjustment.status == AdjustmentStatus.PENDING)
            .scalar()
        )

        # Active rates count
        active_rates = (
            db.query(func.count(DuesRate.id))
            .filter(
                and_(
                    DuesRate.effective_date <= today,
                    (DuesRate.end_date == None) | (DuesRate.end_date >= today),
                )
            )
            .scalar()
        )

        # Days until due (if current period exists)
        days_until_due = None
        if current_period and current_period.due_date >= today:
            days_until_due = (current_period.due_date - today).days

        return {
            "current_period": current_period,
            "days_until_due": days_until_due,
            "mtd_collected": mtd_collected,
            "ytd_collected": ytd_collected,
            "overdue_count": overdue_count,
            "pending_adjustments": pending_adjustments,
            "active_rates": active_rates,
        }

    @staticmethod
    def get_rates_grouped_by_classification(
        db: Session, active_only: bool = True
    ) -> dict:
        """Get rates grouped by classification."""
        today = date.today()

        query = db.query(DuesRate)

        if active_only:
            query = query.filter(
                and_(
                    DuesRate.effective_date <= today,
                    (DuesRate.end_date == None) | (DuesRate.end_date >= today),
                )
            )

        rates = query.order_by(
            DuesRate.classification, DuesRate.effective_date.desc()
        ).all()

        # Group by classification
        grouped = {}
        for rate in rates:
            classification = rate.classification
            if classification not in grouped:
                grouped[classification] = []
            grouped[classification].append(rate)

        return grouped

    @staticmethod
    def get_all_rates(
        db: Session,
        classification: Optional[MemberClassification] = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DuesRate], int]:
        """Get all rates with optional filtering."""
        today = date.today()

        query = db.query(DuesRate)

        if classification:
            query = query.filter(DuesRate.classification == classification)

        if active_only:
            query = query.filter(
                and_(
                    DuesRate.effective_date <= today,
                    (DuesRate.end_date == None) | (DuesRate.end_date >= today),
                )
            )

        total = query.count()

        rates = (
            query.order_by(DuesRate.classification, DuesRate.effective_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return rates, total

    @staticmethod
    def format_currency(amount: Optional[Decimal]) -> str:
        """Format decimal as currency string."""
        if amount is None:
            return "$0.00"
        return f"${amount:,.2f}"

    @staticmethod
    def format_period_name(period: DuesPeriod) -> str:
        """Format period as readable name (e.g., 'January 2026')."""
        month_names = [
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        return f"{month_names[period.period_month]} {period.period_year}"
```

---

## Task 2: Create Dues Frontend Router

Create `src/routers/dues_frontend.py`:

```python
"""Frontend routes for dues management."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.enums import MemberClassification
from src.dependencies.auth_cookie import get_current_user_from_cookie
from src.db.models import User
from src.services.dues_frontend_service import DuesFrontendService

router = APIRouter(prefix="/dues", tags=["dues-frontend"])


def get_templates(request: Request):
    """Get templates from app state."""
    return request.app.state.templates


@router.get("", response_class=HTMLResponse)
async def dues_landing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Dues management landing page."""
    templates = get_templates(request)
    stats = DuesFrontendService.get_landing_stats(db)

    return templates.TemplateResponse(
        "dues/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
        },
    )


@router.get("/rates", response_class=HTMLResponse)
async def rates_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Dues rates list page."""
    templates = get_templates(request)

    # Get all classifications for filter dropdown
    classifications = list(MemberClassification)

    # Initial load - get all rates grouped
    grouped_rates = DuesFrontendService.get_rates_grouped_by_classification(
        db, active_only=False
    )

    return templates.TemplateResponse(
        "dues/rates/index.html",
        {
            "request": request,
            "user": current_user,
            "grouped_rates": grouped_rates,
            "classifications": classifications,
            "get_badge_class": DuesFrontendService.get_classification_badge_class,
            "format_currency": DuesFrontendService.format_currency,
        },
    )


@router.get("/rates/search", response_class=HTMLResponse)
async def rates_search(
    request: Request,
    classification: Optional[str] = Query(None),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """HTMX endpoint for rates table filtering."""
    templates = get_templates(request)

    # Parse classification if provided
    classification_enum = None
    if classification:
        try:
            classification_enum = MemberClassification(classification)
        except ValueError:
            pass

    rates, total = DuesFrontendService.get_all_rates(
        db,
        classification=classification_enum,
        active_only=active_only,
    )

    return templates.TemplateResponse(
        "dues/rates/partials/_table.html",
        {
            "request": request,
            "rates": rates,
            "total": total,
            "get_badge_class": DuesFrontendService.get_classification_badge_class,
            "format_currency": DuesFrontendService.format_currency,
            "today": date.today(),
        },
    )
```

---

## Task 3: Create Dues Landing Template

Create `src/templates/dues/index.html`:

```html
{% extends "base.html" %}

{% block title %}Dues Management - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li>Dues Management</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center">
        <div>
            <h1 class="text-2xl font-bold">Dues Management</h1>
            <p class="text-base-content/70">Track rates, periods, payments, and adjustments</p>
        </div>
    </div>

    <!-- Current Period Card -->
    {% if stats.current_period %}
    <div class="card bg-primary text-primary-content">
        <div class="card-body">
            <div class="flex justify-between items-center">
                <div>
                    <h2 class="card-title">Current Period</h2>
                    <p class="text-2xl font-bold">{{ format_period_name(stats.current_period) }}</p>
                </div>
                <div class="text-right">
                    {% if stats.days_until_due is not none %}
                        {% if stats.days_until_due > 0 %}
                        <p class="text-sm opacity-80">Due in</p>
                        <p class="text-3xl font-bold">{{ stats.days_until_due }} days</p>
                        {% elif stats.days_until_due == 0 %}
                        <p class="text-sm opacity-80">Due</p>
                        <p class="text-3xl font-bold">Today</p>
                        {% else %}
                        <p class="text-sm opacity-80">Overdue by</p>
                        <p class="text-3xl font-bold">{{ stats.days_until_due|abs }} days</p>
                        {% endif %}
                    {% else %}
                    <p class="text-sm opacity-80">Grace period ends</p>
                    <p class="text-lg">{{ stats.current_period.grace_period_end.strftime('%b %d, %Y') }}</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- MTD Collected -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-success">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <div class="stat-title">Collected MTD</div>
            <div class="stat-value text-success">{{ format_currency(stats.mtd_collected) }}</div>
            <div class="stat-desc">This month</div>
        </div>

        <!-- YTD Collected -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-primary">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
            </div>
            <div class="stat-title">Collected YTD</div>
            <div class="stat-value text-primary">{{ format_currency(stats.ytd_collected) }}</div>
            <div class="stat-desc">Year to date</div>
        </div>

        <!-- Overdue -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-error">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <div class="stat-title">Overdue</div>
            <div class="stat-value {% if stats.overdue_count > 0 %}text-error{% endif %}">{{ stats.overdue_count }}</div>
            <div class="stat-desc">Members with overdue payments</div>
        </div>

        <!-- Pending Adjustments -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-warning">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
            </div>
            <div class="stat-title">Pending Adjustments</div>
            <div class="stat-value {% if stats.pending_adjustments > 0 %}text-warning{% endif %}">{{ stats.pending_adjustments }}</div>
            <div class="stat-desc">Awaiting approval</div>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <a href="/dues/rates" class="card bg-base-100 shadow hover:shadow-lg transition-shadow cursor-pointer">
            <div class="card-body items-center text-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-primary mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <h3 class="font-semibold">Dues Rates</h3>
                <p class="text-sm text-base-content/70">{{ stats.active_rates }} active rates</p>
            </div>
        </a>

        <a href="/dues/periods" class="card bg-base-100 shadow hover:shadow-lg transition-shadow cursor-pointer">
            <div class="card-body items-center text-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-secondary mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <h3 class="font-semibold">Periods</h3>
                <p class="text-sm text-base-content/70">Manage billing periods</p>
            </div>
        </a>

        <a href="/dues/payments" class="card bg-base-100 shadow hover:shadow-lg transition-shadow cursor-pointer">
            <div class="card-body items-center text-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-success mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <h3 class="font-semibold">Payments</h3>
                <p class="text-sm text-base-content/70">Record & track payments</p>
            </div>
        </a>

        <a href="/dues/adjustments" class="card bg-base-100 shadow hover:shadow-lg transition-shadow cursor-pointer">
            <div class="card-body items-center text-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-warning mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                <h3 class="font-semibold">Adjustments</h3>
                <p class="text-sm text-base-content/70">Waivers & credits</p>
            </div>
        </a>
    </div>
</div>
{% endblock %}
```

---

## Task 4: Create Rates List Template

Create directory and file `src/templates/dues/rates/index.html`:

```html
{% extends "base.html" %}

{% block title %}Dues Rates - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues</a></li>
            <li>Rates</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center">
        <div>
            <h1 class="text-2xl font-bold">Dues Rates</h1>
            <p class="text-base-content/70">Monthly dues rates by member classification</p>
        </div>
    </div>

    <!-- Filters -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <div class="flex flex-wrap gap-4 items-end">
                <!-- Classification Filter -->
                <div class="form-control w-full max-w-xs">
                    <label class="label">
                        <span class="label-text">Classification</span>
                    </label>
                    <select
                        name="classification"
                        class="select select-bordered"
                        hx-get="/dues/rates/search"
                        hx-trigger="change"
                        hx-target="#rates-table"
                        hx-include="[name='active_only']"
                    >
                        <option value="">All Classifications</option>
                        {% for c in classifications %}
                        <option value="{{ c.value }}">{{ c.value.replace('_', ' ').title() }}</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Active Only Toggle -->
                <div class="form-control">
                    <label class="label cursor-pointer gap-2">
                        <span class="label-text">Active only</span>
                        <input
                            type="checkbox"
                            name="active_only"
                            value="true"
                            class="checkbox checkbox-primary"
                            hx-get="/dues/rates/search"
                            hx-trigger="change"
                            hx-target="#rates-table"
                            hx-include="[name='classification']"
                        />
                    </label>
                </div>
            </div>
        </div>
    </div>

    <!-- Rates Table -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <div id="rates-table">
                {% include "dues/rates/partials/_table.html" %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Task 5: Create Rates Table Partial

Create `src/templates/dues/rates/partials/_table.html`:

```html
{% if rates is defined %}
    {% set rate_list = rates %}
{% else %}
    {% set rate_list = [] %}
    {% for classification, class_rates in grouped_rates.items() %}
        {% for rate in class_rates %}
            {% set _ = rate_list.append(rate) %}
        {% endfor %}
    {% endfor %}
{% endif %}

{% if rate_list %}
<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr>
                <th>Classification</th>
                <th>Monthly Amount</th>
                <th>Effective Date</th>
                <th>End Date</th>
                <th>Status</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            {% for rate in rate_list %}
            <tr>
                <td>
                    <span class="badge {{ get_badge_class(rate.classification) }}">
                        {{ rate.classification.value.replace('_', ' ').title() }}
                    </span>
                </td>
                <td class="font-mono">{{ format_currency(rate.monthly_amount) }}</td>
                <td>{{ rate.effective_date.strftime('%b %d, %Y') }}</td>
                <td>
                    {% if rate.end_date %}
                    {{ rate.end_date.strftime('%b %d, %Y') }}
                    {% else %}
                    <span class="text-base-content/50">—</span>
                    {% endif %}
                </td>
                <td>
                    {% if rate.end_date and rate.end_date < today %}
                    <span class="badge badge-ghost">Expired</span>
                    {% elif rate.effective_date > today %}
                    <span class="badge badge-info">Future</span>
                    {% else %}
                    <span class="badge badge-success">Active</span>
                    {% endif %}
                </td>
                <td class="max-w-xs truncate">{{ rate.description or '—' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% if total is defined %}
<div class="mt-4 text-sm text-base-content/70">
    Showing {{ rate_list|length }} of {{ total }} rates
</div>
{% endif %}
{% else %}
<div class="text-center py-8 text-base-content/50">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
    <p>No rates found</p>
</div>
{% endif %}
```

---

## Task 6: Register Router and Create Template Directory

Update `src/main.py` to include the dues frontend router:

```python
# Add import at top with other routers
from src.routers.dues_frontend import router as dues_frontend_router

# Add router registration with other frontend routers
app.include_router(dues_frontend_router)
```

Create the template directory structure:

```bash
mkdir -p src/templates/dues/rates/partials
mkdir -p src/templates/dues/periods/partials
mkdir -p src/templates/dues/payments/partials
mkdir -p src/templates/dues/adjustments/partials
```

---

## Task 7: Update Sidebar Navigation

Update `src/templates/components/sidebar.html` to add Dues menu:

Find the Operations menu section and add after it:

```html
<!-- Dues Management -->
<li>
    <details {% if request.url.path.startswith('/dues') %}open{% endif %}>
        <summary>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Dues
        </summary>
        <ul>
            <li><a href="/dues" class="{% if request.url.path == '/dues' %}active{% endif %}">Overview</a></li>
            <li><a href="/dues/rates" class="{% if '/dues/rates' in request.url.path %}active{% endif %}">Rates</a></li>
            <li><a href="/dues/periods" class="{% if '/dues/periods' in request.url.path %}active{% endif %}">Periods</a></li>
            <li><a href="/dues/payments" class="{% if '/dues/payments' in request.url.path %}active{% endif %}">Payments</a></li>
            <li><a href="/dues/adjustments" class="{% if '/dues/adjustments' in request.url.path %}active{% endif %}">Adjustments</a></li>
        </ul>
    </details>
</li>
```

---

## Task 8: Add Basic Tests

Add to test file (will be expanded in Session D):

Create `src/tests/test_dues_frontend.py`:

```python
"""Tests for dues frontend routes."""

import pytest
from fastapi.testclient import TestClient


class TestDuesLanding:
    """Tests for dues landing page."""

    def test_dues_landing_requires_auth(self, client: TestClient):
        """Dues landing requires authentication."""
        response = client.get("/dues")
        assert response.status_code in [302, 401, 403]

    def test_dues_landing_authenticated(self, authenticated_client: TestClient):
        """Dues landing loads for authenticated users."""
        response = authenticated_client.get("/dues")
        assert response.status_code == 200
        assert b"Dues Management" in response.content

    def test_dues_landing_shows_stats(self, authenticated_client: TestClient):
        """Dues landing shows stats cards."""
        response = authenticated_client.get("/dues")
        assert response.status_code == 200
        assert b"Collected MTD" in response.content
        assert b"Collected YTD" in response.content
        assert b"Overdue" in response.content


class TestDuesRates:
    """Tests for dues rates page."""

    def test_rates_list_requires_auth(self, client: TestClient):
        """Rates list requires authentication."""
        response = client.get("/dues/rates")
        assert response.status_code in [302, 401, 403]

    def test_rates_list_authenticated(self, authenticated_client: TestClient):
        """Rates list loads for authenticated users."""
        response = authenticated_client.get("/dues/rates")
        assert response.status_code == 200
        assert b"Dues Rates" in response.content
```

---

## Verification

```bash
# Run tests
pytest src/tests/test_dues_frontend.py -v

# Test manually
# 1. Navigate to /dues - should see landing page with stats
# 2. Navigate to /dues/rates - should see rates table
# 3. Filter by classification - table should update via HTMX
# 4. Toggle active only - table should filter

# Commit
git add -A
git commit -m "feat(dues-ui): add dues landing and rates management

- Add DuesFrontendService with stats and badge helpers
- Add dues frontend router with landing and rates routes
- Add dues landing template with stats cards and quick actions
- Add rates list with classification filter and active toggle
- Add HTMX-powered rates table partial
- Update sidebar navigation with Dues menu
- Add initial dues frontend tests"
```

---

## Session A Complete

**Created:**
- `src/services/dues_frontend_service.py`
- `src/routers/dues_frontend.py`
- `src/templates/dues/index.html`
- `src/templates/dues/rates/index.html`
- `src/templates/dues/rates/partials/_table.html`
- `src/tests/test_dues_frontend.py` (5 tests)

**Modified:**
- `src/main.py` (router registration)
- `src/templates/components/sidebar.html` (Dues menu)

**Next:** Session B - Periods Management
