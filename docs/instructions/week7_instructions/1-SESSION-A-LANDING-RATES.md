# Session A: Dues Landing Page + Rates Management

**Duration:** 2-3 hours
**Prerequisites:** v0.7.5, 259 tests passing

---

## Objectives

1. Create DuesFrontendService with stats methods
2. Create dues_frontend router
3. Build dues landing page with overview stats
4. Build rates management interface

---

## Pre-flight Checks

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show 259 passed
```

---

## Task 1: Create DuesFrontendService

**File:** `src/services/dues_frontend_service.py`

```python
"""Dues frontend service for stats and queries."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, and_
from sqlalchemy.orm import Session

from src.db.enums import (
    AdjustmentStatus,
    DuesPaymentStatus,
    DuesAdjustmentType,
    DuesPaymentMethod,
    MemberClassification,
)
from src.models.dues_rate import DuesRate
from src.models.dues_period import DuesPeriod
from src.models.dues_payment import DuesPayment
from src.models.dues_adjustment import DuesAdjustment
from src.models.member import Member


class DuesFrontendService:
    """Service for dues management frontend pages."""

    def __init__(self, db: Session):
        self.db = db

    # ─────────────────────────────────────────────────────────────────
    # Overview Stats
    # ─────────────────────────────────────────────────────────────────

    def get_overview_stats(self) -> dict:
        """Get stats for dues landing page."""
        today = date.today()
        year_start = date(today.year, 1, 1)

        # Total collected YTD
        collected_ytd = self.db.execute(
            select(func.coalesce(func.sum(DuesPayment.amount_paid), Decimal("0")))
            .where(DuesPayment.payment_date >= year_start)
            .where(DuesPayment.status == DuesPaymentStatus.PAID)
        ).scalar()

        # Total expected YTD (from closed periods this year)
        expected_ytd = self.db.execute(
            select(func.coalesce(func.sum(DuesPayment.amount_due), Decimal("0")))
            .join(DuesPeriod)
            .where(DuesPeriod.period_year == today.year)
        ).scalar()

        # Collection rate
        collection_rate = (
            float(collected_ytd / expected_ytd * 100)
            if expected_ytd and expected_ytd > 0
            else 0.0
        )

        # Pending adjustments count
        pending_adjustments = self.db.execute(
            select(func.count(DuesAdjustment.id))
            .where(DuesAdjustment.status == AdjustmentStatus.PENDING)
        ).scalar() or 0

        # Overdue payments count
        overdue_count = self.db.execute(
            select(func.count(DuesPayment.id))
            .where(DuesPayment.status == DuesPaymentStatus.OVERDUE)
        ).scalar() or 0

        # Active rates count
        active_rates = self.db.execute(
            select(func.count(DuesRate.id))
            .where(DuesRate.effective_date <= today)
            .where(
                (DuesRate.end_date.is_(None)) | (DuesRate.end_date >= today)
            )
        ).scalar() or 0

        return {
            "collected_ytd": collected_ytd,
            "expected_ytd": expected_ytd,
            "collection_rate": round(collection_rate, 1),
            "pending_adjustments": pending_adjustments,
            "overdue_count": overdue_count,
            "active_rates": active_rates,
        }

    def get_current_period(self) -> Optional[dict]:
        """Get current open period with collection stats."""
        today = date.today()

        period = self.db.execute(
            select(DuesPeriod)
            .where(DuesPeriod.period_year == today.year)
            .where(DuesPeriod.period_month == today.month)
            .where(DuesPeriod.is_closed == False)
        ).scalar_one_or_none()

        if not period:
            return None

        # Get payment stats for this period
        stats = self.db.execute(
            select(
                func.count(DuesPayment.id).label("total"),
                func.count(DuesPayment.id).filter(
                    DuesPayment.status == DuesPaymentStatus.PAID
                ).label("paid"),
                func.coalesce(func.sum(DuesPayment.amount_due), Decimal("0")).label("total_due"),
                func.coalesce(func.sum(DuesPayment.amount_paid), Decimal("0")).label("total_paid"),
            )
            .where(DuesPayment.period_id == period.id)
        ).one()

        collection_pct = (
            float(stats.total_paid / stats.total_due * 100)
            if stats.total_due and stats.total_due > 0
            else 0.0
        )

        return {
            "id": period.id,
            "year": period.period_year,
            "month": period.period_month,
            "month_name": date(period.period_year, period.period_month, 1).strftime("%B"),
            "due_date": period.due_date,
            "grace_period_end": period.grace_period_end,
            "total_members": stats.total,
            "paid_count": stats.paid,
            "total_due": stats.total_due,
            "total_paid": stats.total_paid,
            "collection_pct": round(collection_pct, 1),
        }

    def get_recent_payments(self, limit: int = 5) -> list[dict]:
        """Get recent payments for activity feed."""
        payments = self.db.execute(
            select(DuesPayment)
            .where(DuesPayment.payment_date.isnot(None))
            .order_by(DuesPayment.payment_date.desc())
            .limit(limit)
        ).scalars().all()

        return [
            {
                "id": p.id,
                "member_id": p.member_id,
                "member_name": p.member.full_name if p.member else "Unknown",
                "amount": p.amount_paid,
                "method": p.payment_method.value if p.payment_method else None,
                "date": p.payment_date,
            }
            for p in payments
        ]

    # ─────────────────────────────────────────────────────────────────
    # Rates Management
    # ─────────────────────────────────────────────────────────────────

    def list_rates(
        self,
        classification: Optional[MemberClassification] = None,
        active_only: bool = False,
    ) -> list[DuesRate]:
        """List rates with optional filters."""
        query = select(DuesRate).order_by(
            DuesRate.classification,
            DuesRate.effective_date.desc(),
        )

        if classification:
            query = query.where(DuesRate.classification == classification)

        if active_only:
            today = date.today()
            query = query.where(DuesRate.effective_date <= today).where(
                (DuesRate.end_date.is_(None)) | (DuesRate.end_date >= today)
            )

        return list(self.db.execute(query).scalars().all())

    def get_rates_by_classification(self) -> dict[str, list[DuesRate]]:
        """Get rates grouped by classification."""
        rates = self.list_rates()
        grouped = {}
        for rate in rates:
            key = rate.classification.value
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(rate)
        return grouped

    def get_rate(self, rate_id: int) -> Optional[DuesRate]:
        """Get single rate by ID."""
        return self.db.get(DuesRate, rate_id)

    def is_rate_current(self, rate: DuesRate) -> bool:
        """Check if rate is currently active."""
        today = date.today()
        if rate.effective_date > today:
            return False
        if rate.end_date and rate.end_date < today:
            return False
        return True

    # ─────────────────────────────────────────────────────────────────
    # Badge Helpers
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_payment_status_badge_class(status: DuesPaymentStatus) -> str:
        """Get badge class for payment status."""
        mapping = {
            DuesPaymentStatus.PENDING: "badge-warning",
            DuesPaymentStatus.PAID: "badge-success",
            DuesPaymentStatus.PARTIAL: "badge-info",
            DuesPaymentStatus.OVERDUE: "badge-error",
            DuesPaymentStatus.WAIVED: "badge-ghost",
        }
        return mapping.get(status, "badge-ghost")

    @staticmethod
    def get_adjustment_status_badge_class(status: AdjustmentStatus) -> str:
        """Get badge class for adjustment status."""
        mapping = {
            AdjustmentStatus.PENDING: "badge-warning",
            AdjustmentStatus.APPROVED: "badge-success",
            AdjustmentStatus.DENIED: "badge-error",
        }
        return mapping.get(status, "badge-ghost")

    @staticmethod
    def get_adjustment_type_badge_class(adj_type: DuesAdjustmentType) -> str:
        """Get badge class for adjustment type."""
        mapping = {
            DuesAdjustmentType.WAIVER: "badge-info",
            DuesAdjustmentType.CREDIT: "badge-success",
            DuesAdjustmentType.HARDSHIP: "badge-warning",
            DuesAdjustmentType.CORRECTION: "badge-secondary",
            DuesAdjustmentType.OTHER: "badge-ghost",
        }
        return mapping.get(adj_type, "badge-ghost")

    @staticmethod
    def get_classification_badge_class(classification: MemberClassification) -> str:
        """Get badge class for member classification."""
        mapping = {
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
        return mapping.get(classification, "badge-ghost")

    @staticmethod
    def format_currency(amount: Optional[Decimal]) -> str:
        """Format decimal as currency string."""
        if amount is None:
            return "$0.00"
        return f"${amount:,.2f}"
```

---

## Task 2: Create Dues Frontend Router

**File:** `src/routers/dues_frontend.py`

```python
"""Dues management frontend routes."""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.enums import MemberClassification
from src.routers.dependencies.auth_cookie import require_auth
from src.services.dues_frontend_service import DuesFrontendService
from src.services.dues_rate_service import DuesRateService
from src.schemas.dues_rate import DuesRateCreate, DuesRateUpdate

router = APIRouter(prefix="/dues", tags=["dues-frontend"])
templates = Jinja2Templates(directory="src/templates")


# ─────────────────────────────────────────────────────────────────────
# Landing Page
# ─────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def dues_landing(
    request: Request,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Dues management landing page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)
    stats = service.get_overview_stats()
    current_period = service.get_current_period()
    recent_payments = service.get_recent_payments(limit=5)

    return templates.TemplateResponse(
        "dues/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "current_period": current_period,
            "recent_payments": recent_payments,
            "format_currency": service.format_currency,
        },
    )


# ─────────────────────────────────────────────────────────────────────
# Rates Management
# ─────────────────────────────────────────────────────────────────────

@router.get("/rates", response_class=HTMLResponse)
async def rates_list(
    request: Request,
    classification: Optional[str] = Query(None),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Rates list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)

    # Parse classification filter
    class_filter = None
    if classification:
        try:
            class_filter = MemberClassification(classification)
        except ValueError:
            pass

    rates = service.list_rates(classification=class_filter)
    rates_grouped = service.get_rates_by_classification()

    return templates.TemplateResponse(
        "dues/rates/index.html",
        {
            "request": request,
            "user": current_user,
            "rates": rates,
            "rates_grouped": rates_grouped,
            "classifications": list(MemberClassification),
            "selected_classification": classification,
            "service": service,
        },
    )


@router.get("/rates/search", response_class=HTMLResponse)
async def rates_search(
    request: Request,
    classification: Optional[str] = Query(None),
    active_only: bool = Query(False),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """HTMX endpoint for rates table."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)

    class_filter = None
    if classification:
        try:
            class_filter = MemberClassification(classification)
        except ValueError:
            pass

    rates = service.list_rates(classification=class_filter, active_only=active_only)

    return templates.TemplateResponse(
        "dues/rates/partials/_table.html",
        {
            "request": request,
            "rates": rates,
            "service": service,
        },
    )


@router.get("/rates/{rate_id}/edit", response_class=HTMLResponse)
async def rate_edit_modal(
    request: Request,
    rate_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get rate edit modal content."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)
    rate = service.get_rate(rate_id)

    if not rate:
        return HTMLResponse("<div class='alert alert-error'>Rate not found</div>")

    return templates.TemplateResponse(
        "dues/rates/partials/_edit_modal.html",
        {
            "request": request,
            "rate": rate,
            "classifications": list(MemberClassification),
            "is_new": False,
        },
    )


@router.get("/rates/new", response_class=HTMLResponse)
async def rate_new_modal(
    request: Request,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get new rate modal content."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    return templates.TemplateResponse(
        "dues/rates/partials/_edit_modal.html",
        {
            "request": request,
            "rate": None,
            "classifications": list(MemberClassification),
            "is_new": True,
        },
    )


@router.post("/rates", response_class=HTMLResponse)
async def rate_create(
    request: Request,
    classification: str = Form(...),
    monthly_amount: str = Form(...),
    effective_date: str = Form(...),
    end_date: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create new rate."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    try:
        rate_service = DuesRateService(db)
        rate_data = DuesRateCreate(
            classification=MemberClassification(classification),
            monthly_amount=Decimal(monthly_amount),
            effective_date=date.fromisoformat(effective_date),
            end_date=date.fromisoformat(end_date) if end_date else None,
            description=description,
        )
        rate_service.create_rate(rate_data)
        db.commit()

        return HTMLResponse(
            '<div class="alert alert-success" hx-swap-oob="true" id="flash-message">'
            '<span>Rate created successfully</span></div>',
            headers={"HX-Trigger": "ratesUpdated"},
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400,
        )


@router.put("/rates/{rate_id}", response_class=HTMLResponse)
async def rate_update(
    request: Request,
    rate_id: int,
    monthly_amount: str = Form(...),
    effective_date: str = Form(...),
    end_date: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update existing rate."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    try:
        rate_service = DuesRateService(db)
        rate_data = DuesRateUpdate(
            monthly_amount=Decimal(monthly_amount),
            effective_date=date.fromisoformat(effective_date),
            end_date=date.fromisoformat(end_date) if end_date else None,
            description=description,
        )
        rate_service.update_rate(rate_id, rate_data)
        db.commit()

        return HTMLResponse(
            '<div class="alert alert-success" hx-swap-oob="true" id="flash-message">'
            '<span>Rate updated successfully</span></div>',
            headers={"HX-Trigger": "ratesUpdated"},
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400,
        )
```

---

## Task 3: Create Dues Landing Template

**File:** `src/templates/dues/index.html`

```html
{% extends "base.html" %}

{% block title %}Dues Management - IP2A{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs mb-4">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li>Dues Management</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold">Dues Management</h1>
            <p class="text-base-content/70">Track member dues, payments, and adjustments</p>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <!-- Collected YTD -->
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-figure text-success">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <div class="stat-title">Collected YTD</div>
            <div class="stat-value text-success">{{ format_currency(stats.collected_ytd) }}</div>
            <div class="stat-desc">{{ stats.collection_rate }}% collection rate</div>
        </div>

        <!-- Expected YTD -->
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-figure text-primary">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
            </div>
            <div class="stat-title">Expected YTD</div>
            <div class="stat-value">{{ format_currency(stats.expected_ytd) }}</div>
            <div class="stat-desc">{{ stats.active_rates }} active rates</div>
        </div>

        <!-- Overdue -->
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-figure text-error">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <div class="stat-title">Overdue</div>
            <div class="stat-value text-error">{{ stats.overdue_count }}</div>
            <div class="stat-desc">members past due</div>
        </div>

        <!-- Pending Adjustments -->
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-figure text-warning">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
            </div>
            <div class="stat-title">Pending Adjustments</div>
            <div class="stat-value text-warning">{{ stats.pending_adjustments }}</div>
            <div class="stat-desc">awaiting review</div>
        </div>
    </div>

    <!-- Two Column Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Current Period Card -->
        <div class="lg:col-span-2">
            {% if current_period %}
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">
                        Current Period: {{ current_period.month_name }} {{ current_period.year }}
                        <span class="badge badge-success">Open</span>
                    </h2>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 my-4">
                        <div>
                            <div class="text-sm text-base-content/70">Total Members</div>
                            <div class="text-xl font-bold">{{ current_period.total_members }}</div>
                        </div>
                        <div>
                            <div class="text-sm text-base-content/70">Paid</div>
                            <div class="text-xl font-bold text-success">{{ current_period.paid_count }}</div>
                        </div>
                        <div>
                            <div class="text-sm text-base-content/70">Due Date</div>
                            <div class="text-xl font-bold">{{ current_period.due_date.strftime('%b %d') }}</div>
                        </div>
                        <div>
                            <div class="text-sm text-base-content/70">Grace Period</div>
                            <div class="text-xl font-bold">{{ current_period.grace_period_end.strftime('%b %d') }}</div>
                        </div>
                    </div>

                    <!-- Collection Progress -->
                    <div class="mb-4">
                        <div class="flex justify-between mb-1">
                            <span class="text-sm">Collection Progress</span>
                            <span class="text-sm font-bold">{{ current_period.collection_pct }}%</span>
                        </div>
                        <progress
                            class="progress progress-success w-full"
                            value="{{ current_period.collection_pct }}"
                            max="100"
                        ></progress>
                        <div class="flex justify-between text-xs text-base-content/70 mt-1">
                            <span>{{ format_currency(current_period.total_paid) }} collected</span>
                            <span>{{ format_currency(current_period.total_due) }} expected</span>
                        </div>
                    </div>

                    <div class="card-actions justify-end">
                        <a href="/dues/periods/{{ current_period.id }}" class="btn btn-primary btn-sm">
                            View Period Details
                        </a>
                    </div>
                </div>
            </div>
            {% else %}
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">No Current Period</h2>
                    <p class="text-base-content/70">No dues period is currently open for this month.</p>
                    <div class="card-actions justify-end">
                        <a href="/dues/periods" class="btn btn-primary btn-sm">Manage Periods</a>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>

        <!-- Quick Links -->
        <div class="space-y-4">
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Quick Links</h2>
                    <div class="space-y-2">
                        <a href="/dues/rates" class="btn btn-ghost btn-block justify-start">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Manage Rates
                        </a>
                        <a href="/dues/periods" class="btn btn-ghost btn-block justify-start">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            Manage Periods
                        </a>
                        <a href="/dues/payments" class="btn btn-ghost btn-block justify-start">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                            Record Payments
                        </a>
                        <a href="/dues/adjustments/pending" class="btn btn-ghost btn-block justify-start">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Pending Adjustments
                            {% if stats.pending_adjustments > 0 %}
                            <span class="badge badge-warning badge-sm">{{ stats.pending_adjustments }}</span>
                            {% endif %}
                        </a>
                    </div>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Recent Payments</h2>
                    {% if recent_payments %}
                    <div class="space-y-2">
                        {% for payment in recent_payments %}
                        <div class="flex justify-between items-center py-2 border-b border-base-200 last:border-0">
                            <div>
                                <div class="font-medium text-sm">{{ payment.member_name }}</div>
                                <div class="text-xs text-base-content/70">
                                    {{ payment.date.strftime('%b %d') if payment.date else 'N/A' }}
                                    {% if payment.method %}
                                    · {{ payment.method }}
                                    {% endif %}
                                </div>
                            </div>
                            <div class="text-success font-bold">{{ format_currency(payment.amount) }}</div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <p class="text-base-content/70 text-sm">No recent payments</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Task 4: Create Rates Templates

**File:** `src/templates/dues/rates/index.html`

```html
{% extends "base.html" %}

{% block title %}Dues Rates - IP2A{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs mb-4">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues Management</a></li>
            <li>Rates</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold">Dues Rates</h1>
            <p class="text-base-content/70">Manage monthly dues rates by classification</p>
        </div>
        <button
            class="btn btn-primary"
            hx-get="/dues/rates/new"
            hx-target="#modal-content"
            hx-swap="innerHTML"
            onclick="document.getElementById('rate-modal').showModal()"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Add Rate
        </button>
    </div>

    <!-- Flash Message Container -->
    <div id="flash-message"></div>

    <!-- Filters -->
    <div class="card bg-base-100 shadow mb-6">
        <div class="card-body py-4">
            <div class="flex flex-wrap gap-4 items-end">
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Classification</span>
                    </label>
                    <select
                        name="classification"
                        class="select select-bordered select-sm w-48"
                        hx-get="/dues/rates/search"
                        hx-target="#rates-table"
                        hx-swap="innerHTML"
                        hx-include="[name='active_only']"
                    >
                        <option value="">All Classifications</option>
                        {% for c in classifications %}
                        <option value="{{ c.value }}" {% if selected_classification == c.value %}selected{% endif %}>
                            {{ c.value | replace('_', ' ') | title }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-control">
                    <label class="label cursor-pointer gap-2">
                        <input
                            type="checkbox"
                            name="active_only"
                            value="true"
                            class="checkbox checkbox-sm"
                            hx-get="/dues/rates/search"
                            hx-target="#rates-table"
                            hx-swap="innerHTML"
                            hx-include="[name='classification']"
                        />
                        <span class="label-text">Active only</span>
                    </label>
                </div>
            </div>
        </div>
    </div>

    <!-- Rates Table -->
    <div id="rates-table" hx-trigger="ratesUpdated from:body" hx-get="/dues/rates/search" hx-include="[name='classification'], [name='active_only']">
        {% include "dues/rates/partials/_table.html" %}
    </div>
</div>

<!-- Rate Modal -->
<dialog id="rate-modal" class="modal">
    <div class="modal-box">
        <div id="modal-content">
            <!-- Loaded via HTMX -->
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

**File:** `src/templates/dues/rates/partials/_table.html`

```html
<div class="card bg-base-100 shadow">
    <div class="card-body p-0">
        <div class="overflow-x-auto">
            <table class="table">
                <thead>
                    <tr>
                        <th>Classification</th>
                        <th>Monthly Amount</th>
                        <th>Effective Date</th>
                        <th>End Date</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for rate in rates %}
                    <tr class="hover">
                        <td>
                            <span class="badge {{ service.get_classification_badge_class(rate.classification) }}">
                                {{ rate.classification.value | replace('_', ' ') | title }}
                            </span>
                        </td>
                        <td class="font-mono">${{ "%.2f" | format(rate.monthly_amount) }}</td>
                        <td>{{ rate.effective_date.strftime('%b %d, %Y') }}</td>
                        <td>
                            {% if rate.end_date %}
                            {{ rate.end_date.strftime('%b %d, %Y') }}
                            {% else %}
                            <span class="text-base-content/50">—</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if service.is_rate_current(rate) %}
                            <span class="badge badge-success badge-sm">Current</span>
                            {% elif rate.effective_date > today %}
                            <span class="badge badge-info badge-sm">Future</span>
                            {% else %}
                            <span class="badge badge-ghost badge-sm">Expired</span>
                            {% endif %}
                        </td>
                        <td>
                            <button
                                class="btn btn-ghost btn-xs"
                                hx-get="/dues/rates/{{ rate.id }}/edit"
                                hx-target="#modal-content"
                                hx-swap="innerHTML"
                                onclick="document.getElementById('rate-modal').showModal()"
                            >
                                Edit
                            </button>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="text-center py-8 text-base-content/50">
                            No rates found
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
```

**File:** `src/templates/dues/rates/partials/_edit_modal.html`

```html
<form
    {% if is_new %}
    hx-post="/dues/rates"
    {% else %}
    hx-put="/dues/rates/{{ rate.id }}"
    {% endif %}
    hx-swap="none"
>
    <h3 class="font-bold text-lg mb-4">
        {% if is_new %}Add New Rate{% else %}Edit Rate{% endif %}
    </h3>

    {% if not is_new %}
    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Classification</span>
        </label>
        <input
            type="text"
            value="{{ rate.classification.value | replace('_', ' ') | title }}"
            class="input input-bordered"
            disabled
        />
        <label class="label">
            <span class="label-text-alt">Classification cannot be changed</span>
        </label>
    </div>
    {% else %}
    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Classification</span>
        </label>
        <select name="classification" class="select select-bordered" required>
            <option value="">Select Classification</option>
            {% for c in classifications %}
            <option value="{{ c.value }}">{{ c.value | replace('_', ' ') | title }}</option>
            {% endfor %}
        </select>
    </div>
    {% endif %}

    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Monthly Amount ($)</span>
        </label>
        <input
            type="number"
            name="monthly_amount"
            step="0.01"
            min="0"
            value="{{ '%.2f' | format(rate.monthly_amount) if rate else '' }}"
            class="input input-bordered"
            placeholder="75.00"
            required
        />
    </div>

    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Effective Date</span>
        </label>
        <input
            type="date"
            name="effective_date"
            value="{{ rate.effective_date.isoformat() if rate else '' }}"
            class="input input-bordered"
            required
        />
    </div>

    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">End Date (optional)</span>
        </label>
        <input
            type="date"
            name="end_date"
            value="{{ rate.end_date.isoformat() if rate and rate.end_date else '' }}"
            class="input input-bordered"
        />
        <label class="label">
            <span class="label-text-alt">Leave blank for open-ended rate</span>
        </label>
    </div>

    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Description (optional)</span>
        </label>
        <textarea
            name="description"
            class="textarea textarea-bordered"
            placeholder="Rate notes..."
        >{{ rate.description if rate and rate.description else '' }}</textarea>
    </div>

    <div class="modal-action">
        <button type="button" class="btn" onclick="document.getElementById('rate-modal').close()">
            Cancel
        </button>
        <button type="submit" class="btn btn-primary">
            {% if is_new %}Create Rate{% else %}Save Changes{% endif %}
        </button>
    </div>
</form>
```

---

## Task 5: Register Router

**File:** `src/main.py` - Add to router includes:

```python
from src.routers.dues_frontend import router as dues_frontend_router

# In the router registration section:
app.include_router(dues_frontend_router)
```

---

## Task 6: Create Template Directories

```bash
mkdir -p src/templates/dues/rates/partials
mkdir -p src/templates/dues/periods/partials
mkdir -p src/templates/dues/payments/partials
mkdir -p src/templates/dues/adjustments/partials
```

---

## Task 7: Update Sidebar Navigation

**File:** `src/templates/components/_sidebar.html` - Add Dues section:

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
            <li><a href="/dues/rates" class="{% if request.url.path.startswith('/dues/rates') %}active{% endif %}">Rates</a></li>
            <li><a href="/dues/periods" class="{% if request.url.path.startswith('/dues/periods') %}active{% endif %}">Periods</a></li>
            <li><a href="/dues/payments" class="{% if request.url.path.startswith('/dues/payments') %}active{% endif %}">Payments</a></li>
            <li><a href="/dues/adjustments" class="{% if request.url.path.startswith('/dues/adjustments') %}active{% endif %}">Adjustments</a></li>
        </ul>
    </details>
</li>
```

---

## Verification

```bash
# Run tests
pytest -v --tb=short

# Start server and test manually
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints:
# - http://localhost:8000/dues (landing)
# - http://localhost:8000/dues/rates (rates list)
```

---

## Session Commit

```bash
git add -A
git commit -m "feat(dues-ui): Week 7 Session A - Landing page and rates management"
git push origin main
```

---

## Next Session

Session B will implement:
- Periods list page
- Generate year workflow
- Close period workflow
- Period detail with payments summary

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
