# Session B: Periods Management

**Duration:** 2-3 hours
**Prerequisites:** Session A complete (landing + rates)

---

## Objectives

1. Add period methods to DuesFrontendService
2. Build periods list page with filters
3. Implement generate year workflow
4. Implement close period workflow
5. Create period detail page

---

## Pre-flight Checks

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Verify tests passing
```

---

## Task 1: Add Period Methods to Service

**File:** `src/services/dues_frontend_service.py` - Add these methods:

```python
    # ─────────────────────────────────────────────────────────────────
    # Periods Management
    # ─────────────────────────────────────────────────────────────────

    def list_periods(
        self,
        year: Optional[int] = None,
        is_closed: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[DuesPeriod], int]:
        """List periods with optional filters. Returns (periods, total_count)."""
        query = select(DuesPeriod).order_by(
            DuesPeriod.period_year.desc(),
            DuesPeriod.period_month.desc(),
        )

        if year is not None:
            query = query.where(DuesPeriod.period_year == year)

        if is_closed is not None:
            query = query.where(DuesPeriod.is_closed == is_closed)

        # Get total count
        count_query = select(func.count(DuesPeriod.id))
        if year is not None:
            count_query = count_query.where(DuesPeriod.period_year == year)
        if is_closed is not None:
            count_query = count_query.where(DuesPeriod.is_closed == is_closed)
        total = self.db.execute(count_query).scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(limit)
        periods = list(self.db.execute(query).scalars().all())

        return periods, total

    def get_period(self, period_id: int) -> Optional[DuesPeriod]:
        """Get single period by ID."""
        return self.db.get(DuesPeriod, period_id)

    def get_period_stats(self, period_id: int) -> dict:
        """Get detailed stats for a period."""
        period = self.get_period(period_id)
        if not period:
            return {}

        stats = self.db.execute(
            select(
                func.count(DuesPayment.id).label("total"),
                func.count(DuesPayment.id).filter(
                    DuesPayment.status == DuesPaymentStatus.PAID
                ).label("paid"),
                func.count(DuesPayment.id).filter(
                    DuesPayment.status == DuesPaymentStatus.PENDING
                ).label("pending"),
                func.count(DuesPayment.id).filter(
                    DuesPayment.status == DuesPaymentStatus.OVERDUE
                ).label("overdue"),
                func.count(DuesPayment.id).filter(
                    DuesPayment.status == DuesPaymentStatus.PARTIAL
                ).label("partial"),
                func.count(DuesPayment.id).filter(
                    DuesPayment.status == DuesPaymentStatus.WAIVED
                ).label("waived"),
                func.coalesce(func.sum(DuesPayment.amount_due), Decimal("0")).label("total_due"),
                func.coalesce(func.sum(DuesPayment.amount_paid), Decimal("0")).label("total_paid"),
            )
            .where(DuesPayment.period_id == period_id)
        ).one()

        collection_pct = (
            float(stats.total_paid / stats.total_due * 100)
            if stats.total_due and stats.total_due > 0
            else 0.0
        )

        return {
            "total_members": stats.total,
            "paid": stats.paid,
            "pending": stats.pending,
            "overdue": stats.overdue,
            "partial": stats.partial,
            "waived": stats.waived,
            "total_due": stats.total_due,
            "total_paid": stats.total_paid,
            "collection_pct": round(collection_pct, 1),
            "outstanding": stats.total_due - stats.total_paid,
        }

    def get_available_years(self) -> list[int]:
        """Get list of years that have periods."""
        years = self.db.execute(
            select(DuesPeriod.period_year)
            .distinct()
            .order_by(DuesPeriod.period_year.desc())
        ).scalars().all()
        return list(years)

    def get_period_payment_breakdown(self, period_id: int) -> dict:
        """Get payment status breakdown for a period."""
        breakdown = {}
        for status in DuesPaymentStatus:
            count = self.db.execute(
                select(func.count(DuesPayment.id))
                .where(DuesPayment.period_id == period_id)
                .where(DuesPayment.status == status)
            ).scalar() or 0
            breakdown[status.value] = count
        return breakdown
```

---

## Task 2: Add Period Routes to Router

**File:** `src/routers/dues_frontend.py` - Add these routes:

```python
from src.services.dues_period_service import DuesPeriodService

# ─────────────────────────────────────────────────────────────────────
# Periods Management
# ─────────────────────────────────────────────────────────────────────

@router.get("/periods", response_class=HTMLResponse)
async def periods_list(
    request: Request,
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),  # "open" or "closed"
    page: int = Query(1, ge=1),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Periods list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)

    # Parse status filter
    is_closed = None
    if status == "open":
        is_closed = False
    elif status == "closed":
        is_closed = True

    per_page = 12
    skip = (page - 1) * per_page
    periods, total = service.list_periods(
        year=year,
        is_closed=is_closed,
        skip=skip,
        limit=per_page,
    )

    available_years = service.get_available_years()
    total_pages = (total + per_page - 1) // per_page

    # Get stats for each period
    period_stats = {}
    for period in periods:
        period_stats[period.id] = service.get_period_stats(period.id)

    return templates.TemplateResponse(
        "dues/periods/index.html",
        {
            "request": request,
            "user": current_user,
            "periods": periods,
            "period_stats": period_stats,
            "available_years": available_years,
            "selected_year": year,
            "selected_status": status,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "service": service,
        },
    )


@router.get("/periods/search", response_class=HTMLResponse)
async def periods_search(
    request: Request,
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """HTMX endpoint for periods table."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)

    is_closed = None
    if status == "open":
        is_closed = False
    elif status == "closed":
        is_closed = True

    per_page = 12
    skip = (page - 1) * per_page
    periods, total = service.list_periods(
        year=year,
        is_closed=is_closed,
        skip=skip,
        limit=per_page,
    )

    total_pages = (total + per_page - 1) // per_page

    period_stats = {}
    for period in periods:
        period_stats[period.id] = service.get_period_stats(period.id)

    return templates.TemplateResponse(
        "dues/periods/partials/_table.html",
        {
            "request": request,
            "periods": periods,
            "period_stats": period_stats,
            "page": page,
            "total_pages": total_pages,
            "service": service,
        },
    )


@router.get("/periods/{period_id}", response_class=HTMLResponse)
async def period_detail(
    request: Request,
    period_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Period detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)
    period = service.get_period(period_id)

    if not period:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Period not found"},
            status_code=404,
        )

    stats = service.get_period_stats(period_id)
    breakdown = service.get_period_payment_breakdown(period_id)

    return templates.TemplateResponse(
        "dues/periods/detail.html",
        {
            "request": request,
            "user": current_user,
            "period": period,
            "stats": stats,
            "breakdown": breakdown,
            "service": service,
        },
    )


@router.get("/periods/generate-modal", response_class=HTMLResponse)
async def periods_generate_modal(
    request: Request,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get generate year modal content."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)
    available_years = service.get_available_years()
    current_year = date.today().year

    # Suggest next year if current year exists
    suggested_year = current_year
    if current_year in available_years:
        suggested_year = current_year + 1

    return templates.TemplateResponse(
        "dues/periods/partials/_generate_modal.html",
        {
            "request": request,
            "available_years": available_years,
            "suggested_year": suggested_year,
        },
    )


@router.post("/periods/generate", response_class=HTMLResponse)
async def periods_generate(
    request: Request,
    year: int = Form(...),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Generate periods for a year."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    try:
        period_service = DuesPeriodService(db)
        periods = period_service.generate_year(year)
        db.commit()

        return HTMLResponse(
            f'<div class="alert alert-success" hx-swap-oob="true" id="flash-message">'
            f'<span>Generated {len(periods)} periods for {year}</span></div>',
            headers={"HX-Trigger": "periodsUpdated"},
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400,
        )


@router.get("/periods/{period_id}/close-modal", response_class=HTMLResponse)
async def period_close_modal(
    request: Request,
    period_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get close period modal content."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)
    period = service.get_period(period_id)
    stats = service.get_period_stats(period_id)

    if not period:
        return HTMLResponse("<div class='alert alert-error'>Period not found</div>")

    return templates.TemplateResponse(
        "dues/periods/partials/_close_modal.html",
        {
            "request": request,
            "period": period,
            "stats": stats,
            "service": service,
        },
    )


@router.post("/periods/{period_id}/close", response_class=HTMLResponse)
async def period_close(
    request: Request,
    period_id: int,
    notes: Optional[str] = Form(None),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Close a period."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    try:
        period_service = DuesPeriodService(db)
        period_service.close_period(
            period_id=period_id,
            closed_by_id=current_user.get("id"),
            notes=notes,
        )
        db.commit()

        return HTMLResponse(
            '<div class="alert alert-success" hx-swap-oob="true" id="flash-message">'
            '<span>Period closed successfully</span></div>',
            headers={"HX-Trigger": "periodsUpdated", "HX-Redirect": "/dues/periods"},
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400,
        )
```

---

## Task 3: Create Periods Templates

**File:** `src/templates/dues/periods/index.html`

```html
{% extends "base.html" %}

{% block title %}Dues Periods - IP2A{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs mb-4">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues Management</a></li>
            <li>Periods</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold">Dues Periods</h1>
            <p class="text-base-content/70">Manage monthly dues collection periods</p>
        </div>
        <button
            class="btn btn-primary"
            hx-get="/dues/periods/generate-modal"
            hx-target="#modal-content"
            hx-swap="innerHTML"
            onclick="document.getElementById('period-modal').showModal()"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Generate Year
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
                        <span class="label-text">Year</span>
                    </label>
                    <select
                        name="year"
                        class="select select-bordered select-sm w-32"
                        hx-get="/dues/periods/search"
                        hx-target="#periods-table"
                        hx-swap="innerHTML"
                        hx-include="[name='status']"
                    >
                        <option value="">All Years</option>
                        {% for y in available_years %}
                        <option value="{{ y }}" {% if selected_year == y %}selected{% endif %}>
                            {{ y }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Status</span>
                    </label>
                    <select
                        name="status"
                        class="select select-bordered select-sm w-32"
                        hx-get="/dues/periods/search"
                        hx-target="#periods-table"
                        hx-swap="innerHTML"
                        hx-include="[name='year']"
                    >
                        <option value="">All Status</option>
                        <option value="open" {% if selected_status == 'open' %}selected{% endif %}>Open</option>
                        <option value="closed" {% if selected_status == 'closed' %}selected{% endif %}>Closed</option>
                    </select>
                </div>

                <div class="text-sm text-base-content/70">
                    {{ total }} period{% if total != 1 %}s{% endif %}
                </div>
            </div>
        </div>
    </div>

    <!-- Periods Table -->
    <div id="periods-table" hx-trigger="periodsUpdated from:body" hx-get="/dues/periods/search" hx-include="[name='year'], [name='status']">
        {% include "dues/periods/partials/_table.html" %}
    </div>
</div>

<!-- Period Modal -->
<dialog id="period-modal" class="modal">
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

**File:** `src/templates/dues/periods/partials/_table.html`

```html
<div class="card bg-base-100 shadow">
    <div class="card-body p-0">
        <div class="overflow-x-auto">
            <table class="table">
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Due Date</th>
                        <th>Grace Period</th>
                        <th>Collection</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for period in periods %}
                    {% set stats = period_stats.get(period.id, {}) %}
                    <tr class="hover">
                        <td>
                            <a href="/dues/periods/{{ period.id }}" class="link link-hover font-medium">
                                {{ period.period_year }}-{{ '%02d' | format(period.period_month) }}
                            </a>
                            <div class="text-xs text-base-content/50">
                                {{ ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][period.period_month - 1] }}
                            </div>
                        </td>
                        <td>{{ period.due_date.strftime('%b %d') }}</td>
                        <td>{{ period.grace_period_end.strftime('%b %d') }}</td>
                        <td>
                            <div class="flex items-center gap-2">
                                <progress
                                    class="progress progress-success w-20"
                                    value="{{ stats.get('collection_pct', 0) }}"
                                    max="100"
                                ></progress>
                                <span class="text-sm">{{ stats.get('collection_pct', 0) }}%</span>
                            </div>
                            <div class="text-xs text-base-content/50">
                                {{ stats.get('paid', 0) }}/{{ stats.get('total_members', 0) }} paid
                            </div>
                        </td>
                        <td>
                            {% if period.is_closed %}
                            <span class="badge badge-ghost badge-sm">Closed</span>
                            {% else %}
                            <span class="badge badge-success badge-sm">Open</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="dropdown dropdown-end">
                                <label tabindex="0" class="btn btn-ghost btn-xs">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                                    </svg>
                                </label>
                                <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
                                    <li>
                                        <a href="/dues/periods/{{ period.id }}">View Details</a>
                                    </li>
                                    <li>
                                        <a href="/dues/payments?period_id={{ period.id }}">View Payments</a>
                                    </li>
                                    {% if not period.is_closed %}
                                    <li>
                                        <button
                                            hx-get="/dues/periods/{{ period.id }}/close-modal"
                                            hx-target="#modal-content"
                                            hx-swap="innerHTML"
                                            onclick="document.getElementById('period-modal').showModal()"
                                        >
                                            Close Period
                                        </button>
                                    </li>
                                    {% endif %}
                                </ul>
                            </div>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="text-center py-8 text-base-content/50">
                            No periods found
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        {% if total_pages > 1 %}
        <div class="flex justify-center py-4 border-t border-base-200">
            <div class="join">
                {% if page > 1 %}
                <button
                    class="join-item btn btn-sm"
                    hx-get="/dues/periods/search?page={{ page - 1 }}"
                    hx-target="#periods-table"
                    hx-include="[name='year'], [name='status']"
                >
                    «
                </button>
                {% endif %}

                <button class="join-item btn btn-sm btn-active">{{ page }}</button>

                {% if page < total_pages %}
                <button
                    class="join-item btn btn-sm"
                    hx-get="/dues/periods/search?page={{ page + 1 }}"
                    hx-target="#periods-table"
                    hx-include="[name='year'], [name='status']"
                >
                    »
                </button>
                {% endif %}
            </div>
        </div>
        {% endif %}
    </div>
</div>
```

**File:** `src/templates/dues/periods/partials/_generate_modal.html`

```html
<form hx-post="/dues/periods/generate" hx-swap="none">
    <h3 class="font-bold text-lg mb-4">Generate Dues Periods</h3>

    <p class="text-base-content/70 mb-4">
        This will create 12 monthly periods for the selected year with default due dates (1st of each month) and grace periods (15th of each month).
    </p>

    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Year</span>
        </label>
        <input
            type="number"
            name="year"
            value="{{ suggested_year }}"
            min="2020"
            max="2100"
            class="input input-bordered"
            required
        />
        {% if available_years %}
        <label class="label">
            <span class="label-text-alt">
                Existing years: {{ available_years | join(', ') }}
            </span>
        </label>
        {% endif %}
    </div>

    <div class="alert alert-warning mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>Periods cannot be deleted once created</span>
    </div>

    <div class="modal-action">
        <button type="button" class="btn" onclick="document.getElementById('period-modal').close()">
            Cancel
        </button>
        <button type="submit" class="btn btn-primary">
            Generate 12 Periods
        </button>
    </div>
</form>
```

**File:** `src/templates/dues/periods/partials/_close_modal.html`

```html
<form hx-post="/dues/periods/{{ period.id }}/close" hx-swap="none">
    <h3 class="font-bold text-lg mb-4">Close Period</h3>

    <div class="alert alert-info mb-4">
        <div>
            <p class="font-medium">{{ period.period_year }}-{{ '%02d' | format(period.period_month) }}</p>
            <p class="text-sm">
                {{ stats.get('paid', 0) }} paid,
                {{ stats.get('pending', 0) }} pending,
                {{ stats.get('overdue', 0) }} overdue
            </p>
        </div>
    </div>

    <p class="text-base-content/70 mb-4">
        Closing this period will:
    </p>
    <ul class="list-disc list-inside text-base-content/70 mb-4 space-y-1">
        <li>Mark the period as closed</li>
        <li>Prevent new payments from being recorded</li>
        <li>Lock the period for reporting purposes</li>
    </ul>

    {% if stats.get('pending', 0) > 0 or stats.get('overdue', 0) > 0 %}
    <div class="alert alert-warning mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>There are {{ stats.get('pending', 0) + stats.get('overdue', 0) }} unpaid members in this period</span>
    </div>
    {% endif %}

    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Notes (optional)</span>
        </label>
        <textarea
            name="notes"
            class="textarea textarea-bordered"
            placeholder="Closing notes..."
        ></textarea>
    </div>

    <div class="modal-action">
        <button type="button" class="btn" onclick="document.getElementById('period-modal').close()">
            Cancel
        </button>
        <button type="submit" class="btn btn-warning">
            Close Period
        </button>
    </div>
</form>
```

**File:** `src/templates/dues/periods/detail.html`

```html
{% extends "base.html" %}

{% block title %}Period {{ period.period_year }}-{{ '%02d' | format(period.period_month) }} - IP2A{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs mb-4">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues Management</a></li>
            <li><a href="/dues/periods">Periods</a></li>
            <li>{{ period.period_year }}-{{ '%02d' | format(period.period_month) }}</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold">
                {{ ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][period.period_month - 1] }} {{ period.period_year }}
                {% if period.is_closed %}
                <span class="badge badge-ghost ml-2">Closed</span>
                {% else %}
                <span class="badge badge-success ml-2">Open</span>
                {% endif %}
            </h1>
            <p class="text-base-content/70">
                Due: {{ period.due_date.strftime('%B %d, %Y') }} ·
                Grace ends: {{ period.grace_period_end.strftime('%B %d, %Y') }}
            </p>
        </div>
        <div class="flex gap-2">
            <a href="/dues/payments?period_id={{ period.id }}" class="btn btn-outline btn-sm">
                View Payments
            </a>
            {% if not period.is_closed %}
            <button
                class="btn btn-warning btn-sm"
                hx-get="/dues/periods/{{ period.id }}/close-modal"
                hx-target="#modal-content"
                hx-swap="innerHTML"
                onclick="document.getElementById('period-modal').showModal()"
            >
                Close Period
            </button>
            {% endif %}
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-title">Total Members</div>
            <div class="stat-value">{{ stats.total_members }}</div>
        </div>
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-title">Collected</div>
            <div class="stat-value text-success">${{ "%.2f" | format(stats.total_paid) }}</div>
            <div class="stat-desc">of ${{ "%.2f" | format(stats.total_due) }}</div>
        </div>
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-title">Collection Rate</div>
            <div class="stat-value">{{ stats.collection_pct }}%</div>
        </div>
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-title">Outstanding</div>
            <div class="stat-value text-error">${{ "%.2f" | format(stats.outstanding) }}</div>
        </div>
    </div>

    <!-- Collection Progress -->
    <div class="card bg-base-100 shadow mb-6">
        <div class="card-body">
            <h2 class="card-title">Collection Progress</h2>
            <div class="mb-4">
                <div class="flex justify-between mb-2">
                    <span>{{ stats.collection_pct }}% collected</span>
                    <span>${{ "%.2f" | format(stats.total_paid) }} / ${{ "%.2f" | format(stats.total_due) }}</span>
                </div>
                <progress
                    class="progress progress-success w-full h-4"
                    value="{{ stats.collection_pct }}"
                    max="100"
                ></progress>
            </div>

            <!-- Status Breakdown -->
            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div class="text-center p-3 bg-success/10 rounded">
                    <div class="text-2xl font-bold text-success">{{ stats.paid }}</div>
                    <div class="text-sm">Paid</div>
                </div>
                <div class="text-center p-3 bg-warning/10 rounded">
                    <div class="text-2xl font-bold text-warning">{{ stats.pending }}</div>
                    <div class="text-sm">Pending</div>
                </div>
                <div class="text-center p-3 bg-error/10 rounded">
                    <div class="text-2xl font-bold text-error">{{ stats.overdue }}</div>
                    <div class="text-sm">Overdue</div>
                </div>
                <div class="text-center p-3 bg-info/10 rounded">
                    <div class="text-2xl font-bold text-info">{{ stats.partial }}</div>
                    <div class="text-sm">Partial</div>
                </div>
                <div class="text-center p-3 bg-base-200 rounded">
                    <div class="text-2xl font-bold">{{ stats.waived }}</div>
                    <div class="text-sm">Waived</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Quick Actions</h2>
            <div class="flex flex-wrap gap-2">
                <a href="/dues/payments?period_id={{ period.id }}&status=pending" class="btn btn-outline btn-sm">
                    View Pending ({{ stats.pending }})
                </a>
                <a href="/dues/payments?period_id={{ period.id }}&status=overdue" class="btn btn-outline btn-error btn-sm">
                    View Overdue ({{ stats.overdue }})
                </a>
                {% if not period.is_closed %}
                <a href="/dues/payments?period_id={{ period.id }}" class="btn btn-primary btn-sm">
                    Record Payments
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Period Modal -->
<dialog id="period-modal" class="modal">
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

---

## Verification

```bash
# Run tests
pytest -v --tb=short

# Test manually
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints:
# - http://localhost:8000/dues/periods
# - http://localhost:8000/dues/periods/1 (if period exists)
# - Generate year modal
# - Close period modal
```

---

## Session Commit

```bash
git add -A
git commit -m "feat(dues-ui): Week 7 Session B - Periods management"
git push origin main
```

---

## Next Session

Session C will implement:
- Payments list by period
- Member search within payments
- Record payment modal
- Payment method selection
- Batch update overdue
