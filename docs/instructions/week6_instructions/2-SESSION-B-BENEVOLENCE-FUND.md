# Phase 6 Week 6 - Session B: Benevolence Fund

**Document:** 2 of 4
**Estimated Time:** 2-3 hours
**Focus:** Benevolence requests list, status workflow, detail page with payments

---

## Objective

Create the Benevolence Fund management UI:
- Requests list with status workflow badges
- Filter by status and request type
- Request detail with payment history
- Status progression display
- HTMX live search

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show ~238+ passed
```

---

## Step 1: Add Benevolence Methods to Service (30 min)

Add to `src/services/operations_frontend_service.py`:

```python
    # ============================================================
    # Benevolence Methods (Add after SALTing methods)
    # ============================================================

    async def get_benevolence_stats(self) -> dict:
        """Get benevolence fund stats for list page."""
        total = await self.db.execute(
            select(func.count(BenevolenceRequest.id))
        )
        total = total.scalar() or 0

        pending = await self._count_benevolence_by_status(BenevolenceStatus.PENDING)
        approved = await self._count_benevolence_by_status(BenevolenceStatus.APPROVED)
        paid = await self._count_benevolence_by_status(BenevolenceStatus.PAID)
        denied = await self._count_benevolence_by_status(BenevolenceStatus.DENIED)

        # Total approved amount YTD
        year_start = date(date.today().year, 1, 1)
        approved_stmt = select(func.sum(BenevolenceRequest.amount_approved)).where(
            and_(
                BenevolenceRequest.status.in_([BenevolenceStatus.APPROVED, BenevolenceStatus.PAID, BenevolenceStatus.CLOSED]),
                func.date(BenevolenceRequest.reviewed_at) >= year_start
            )
        )
        approved_amount = (await self.db.execute(approved_stmt)).scalar() or Decimal("0.00")

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "paid": paid,
            "denied": denied,
            "approved_amount_ytd": approved_amount,
            "paid_amount_ytd": await self._benevolence_amount_ytd(),
        }

    async def search_benevolence_requests(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        request_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[BenevolenceRequest], int, int]:
        """Search benevolence requests with filters."""
        stmt = select(BenevolenceRequest).options(
            selectinload(BenevolenceRequest.member),
            selectinload(BenevolenceRequest.reviewed_by),
        )

        # Search by member name or reason
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.join(BenevolenceRequest.member).where(
                or_(
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    func.concat(Member.first_name, ' ', Member.last_name).ilike(search_term),
                    BenevolenceRequest.reason.ilike(search_term),
                )
            )

        # Filter by status
        if status and status != "all":
            try:
                status_enum = BenevolenceStatus(status)
                stmt = stmt.where(BenevolenceRequest.status == status_enum)
            except ValueError:
                pass

        # Filter by type
        if request_type and request_type != "all":
            try:
                type_enum = BenevolenceType(request_type)
                stmt = stmt.where(BenevolenceRequest.request_type == type_enum)
            except ValueError:
                pass

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Sort and paginate
        stmt = stmt.order_by(BenevolenceRequest.created_at.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(stmt)
        requests = list(result.unique().scalars().all())

        total_pages = (total + per_page - 1) // per_page

        return requests, total, total_pages

    async def get_benevolence_request_by_id(self, request_id: int) -> Optional[BenevolenceRequest]:
        """Get a benevolence request with all relationships."""
        stmt = select(BenevolenceRequest).options(
            selectinload(BenevolenceRequest.member),
            selectinload(BenevolenceRequest.reviewed_by),
            selectinload(BenevolenceRequest.payments).selectinload(BenevolencePayment.processed_by),
        ).where(BenevolenceRequest.id == request_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def get_benevolence_status_badge_class(status: BenevolenceStatus) -> str:
        """Get DaisyUI badge class for benevolence status."""
        mapping = {
            BenevolenceStatus.PENDING: "badge-warning",
            BenevolenceStatus.APPROVED: "badge-info",
            BenevolenceStatus.DENIED: "badge-error",
            BenevolenceStatus.PAID: "badge-success",
            BenevolenceStatus.CLOSED: "badge-ghost",
        }
        return mapping.get(status, "badge-ghost")

    @staticmethod
    def get_benevolence_type_badge_class(request_type: BenevolenceType) -> str:
        """Get DaisyUI badge class for request type."""
        mapping = {
            BenevolenceType.HARDSHIP: "badge-warning",
            BenevolenceType.FUNERAL: "badge-neutral",
            BenevolenceType.MEDICAL: "badge-error",
            BenevolenceType.DISASTER: "badge-info",
            BenevolenceType.OTHER: "badge-ghost",
        }
        return mapping.get(request_type, "badge-ghost")
```

---

## Step 2: Add Benevolence Routes (25 min)

Add to `src/routers/operations_frontend.py`:

```python
# Add imports at top
from src.db.enums import (
    SaltingStatus, BenevolenceStatus, BenevolenceType,
    GrievanceStatus, GrievanceCategory
)

# Add routes after SALTing routes

# ============================================================
# Benevolence Routes
# ============================================================

@router.get("/benevolence", response_class=HTMLResponse)
async def benevolence_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render benevolence requests list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    stats = await service.get_benevolence_stats()
    all_statuses = [s.value for s in BenevolenceStatus]
    all_types = [t.value for t in BenevolenceType]

    return templates.TemplateResponse(
        "operations/benevolence/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "all_statuses": all_statuses,
            "all_types": all_types,
            "get_status_badge_class": service.get_benevolence_status_badge_class,
            "get_type_badge_class": service.get_benevolence_type_badge_class,
        }
    )


@router.get("/benevolence/search", response_class=HTMLResponse)
async def benevolence_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    request_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
):
    """HTMX partial: Benevolence table body."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = OperationsFrontendService(db)
    requests, total, total_pages = await service.search_benevolence_requests(
        query=q,
        status=status,
        request_type=request_type,
        page=page,
    )

    return templates.TemplateResponse(
        "operations/benevolence/partials/_table.html",
        {
            "request": request,
            "requests": requests,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "status_filter": status or "all",
            "type_filter": request_type or "all",
            "get_status_badge_class": service.get_benevolence_status_badge_class,
            "get_type_badge_class": service.get_benevolence_type_badge_class,
        }
    )


@router.get("/benevolence/{request_id}", response_class=HTMLResponse)
async def benevolence_detail_page(
    request: Request,
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render benevolence request detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    benevolence_request = await service.get_benevolence_request_by_id(request_id)

    if not benevolence_request:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Benevolence request not found"},
            status_code=404
        )

    all_statuses = [s.value for s in BenevolenceStatus]

    return templates.TemplateResponse(
        "operations/benevolence/detail.html",
        {
            "request": request,
            "user": current_user,
            "benevolence_request": benevolence_request,
            "all_statuses": all_statuses,
            "get_status_badge_class": service.get_benevolence_status_badge_class,
            "get_type_badge_class": service.get_benevolence_type_badge_class,
        }
    )
```

---

## Step 3: Create Benevolence List Page (25 min)

Create `src/templates/operations/benevolence/index.html`:

```html
{% extends "base.html" %}

{% block title %}Benevolence Fund - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/operations">Operations</a></li>
            <li>Benevolence Fund</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold">Benevolence Fund</h1>
            <p class="text-base-content/60">Member assistance and support requests</p>
        </div>
        <button class="btn btn-primary">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
            New Request
        </button>
    </div>

    <!-- Stats Cards -->
    <div class="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div class="stat">
            <div class="stat-title">Total Requests</div>
            <div class="stat-value">{{ stats.total }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Pending Review</div>
            <div class="stat-value text-warning">{{ stats.pending }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Approved</div>
            <div class="stat-value text-info">{{ stats.approved }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Paid</div>
            <div class="stat-value text-success">{{ stats.paid }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Paid YTD</div>
            <div class="stat-value text-primary">${{ "{:,.0f}".format(stats.paid_amount_ytd) }}</div>
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
                            placeholder="Search by member name or reason..."
                            class="input input-bordered w-full pl-10"
                            hx-get="/operations/benevolence/search"
                            hx-trigger="input changed delay:300ms, search"
                            hx-target="#table-container"
                            hx-include="[name='status'], [name='request_type']"
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
                        hx-get="/operations/benevolence/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='request_type']"
                    >
                        <option value="all">All Status</option>
                        {% for status in all_statuses %}
                        <option value="{{ status }}">{{ status | title }}</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Type Filter -->
                <div class="w-full lg:w-48">
                    <select
                        name="request_type"
                        class="select select-bordered w-full"
                        hx-get="/operations/benevolence/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='status']"
                    >
                        <option value="all">All Types</option>
                        {% for type in all_types %}
                        <option value="{{ type }}">{{ type | title }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- Requests Table -->
    <div class="card bg-base-100 shadow overflow-hidden">
        <div
            id="table-container"
            hx-get="/operations/benevolence/search"
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

## Step 4: Create Benevolence Table Partial (20 min)

Create `src/templates/operations/benevolence/partials/_table.html`:

```html
{# Benevolence requests table #}

<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr class="bg-base-200">
                <th>Member</th>
                <th>Type</th>
                <th>Requested</th>
                <th>Approved</th>
                <th>Status</th>
                <th>Submitted</th>
                <th class="w-24">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% if requests %}
                {% for req in requests %}
                <tr class="hover">
                    <!-- Member -->
                    <td>
                        <div class="flex items-center gap-2">
                            <div class="avatar placeholder">
                                <div class="bg-neutral text-neutral-content rounded-full w-8">
                                    <span class="text-xs">
                                        {{ req.member.first_name[0] | upper if req.member else '?' }}{{ req.member.last_name[0] | upper if req.member else '' }}
                                    </span>
                                </div>
                            </div>
                            <div>
                                <div class="font-bold">
                                    {{ req.member.first_name if req.member else 'N/A' }} {{ req.member.last_name if req.member else '' }}
                                </div>
                                <div class="text-xs text-base-content/60">
                                    {{ req.member.card_id if req.member else '' }}
                                </div>
                            </div>
                        </div>
                    </td>

                    <!-- Type -->
                    <td>
                        <span class="badge {{ get_type_badge_class(req.request_type) }} badge-sm">
                            {{ req.request_type.value | title }}
                        </span>
                    </td>

                    <!-- Amount Requested -->
                    <td>
                        <span class="font-mono">${{ "{:,.2f}".format(req.amount_requested) }}</span>
                    </td>

                    <!-- Amount Approved -->
                    <td>
                        {% if req.amount_approved %}
                        <span class="font-mono text-success">${{ "{:,.2f}".format(req.amount_approved) }}</span>
                        {% else %}
                        <span class="text-base-content/40">—</span>
                        {% endif %}
                    </td>

                    <!-- Status -->
                    <td>
                        <span class="badge {{ get_status_badge_class(req.status) }}">
                            {{ req.status.value | title }}
                        </span>
                    </td>

                    <!-- Submitted Date -->
                    <td>
                        {{ req.created_at.strftime('%b %d, %Y') }}
                    </td>

                    <!-- Actions -->
                    <td>
                        <a href="/operations/benevolence/{{ req.id }}" class="btn btn-ghost btn-sm">
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
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                        </svg>
                        <p class="text-lg">No benevolence requests found</p>
                    </div>
                </td>
            </tr>
            {% endif %}
        </tbody>
    </table>
</div>

{% if requests %}
<!-- Pagination -->
<div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-base-200">
    <div class="text-sm text-base-content/60">
        Showing {{ ((current_page - 1) * 20) + 1 }} - {{ ((current_page - 1) * 20) + requests|length }} of {{ total }}
    </div>

    <div class="join">
        {% if current_page > 1 %}
        <button
            class="join-item btn btn-sm"
            hx-get="/operations/benevolence/search?page={{ current_page - 1 }}&q={{ query }}&status={{ status_filter }}&request_type={{ type_filter }}"
            hx-target="#table-container"
        >«</button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">«</button>
        {% endif %}

        <button class="join-item btn btn-sm btn-active">{{ current_page }}</button>

        {% if current_page < total_pages %}
        <button
            class="join-item btn btn-sm"
            hx-get="/operations/benevolence/search?page={{ current_page + 1 }}&q={{ query }}&status={{ status_filter }}&request_type={{ type_filter }}"
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

## Step 5: Create Benevolence Detail Page (30 min)

Create `src/templates/operations/benevolence/detail.html`:

```html
{% extends "base.html" %}

{% block title %}Benevolence Request #{{ benevolence_request.id }} - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/operations">Operations</a></li>
            <li><a href="/operations/benevolence">Benevolence</a></li>
            <li>Request #{{ benevolence_request.id }}</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
            <div class="flex items-center gap-3">
                <h1 class="text-2xl font-bold">
                    {{ benevolence_request.member.first_name if benevolence_request.member else 'Unknown' }}
                    {{ benevolence_request.member.last_name if benevolence_request.member else '' }}
                </h1>
                <span class="badge {{ get_status_badge_class(benevolence_request.status) }} badge-lg">
                    {{ benevolence_request.status.value | title }}
                </span>
            </div>
            <p class="text-base-content/60 mt-1">
                {{ benevolence_request.request_type.value | title }} Request #{{ benevolence_request.id }}
            </p>
        </div>
        <div class="flex gap-2">
            <a href="/operations/benevolence" class="btn btn-ghost">← Back</a>
            {% if benevolence_request.status.value == 'pending' %}
            <button class="btn btn-success">Approve</button>
            <button class="btn btn-error btn-outline">Deny</button>
            {% elif benevolence_request.status.value == 'approved' %}
            <button class="btn btn-primary">Record Payment</button>
            {% endif %}
        </div>
    </div>

    <!-- Status Workflow -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title text-lg">Request Status</h2>
            <ul class="steps steps-horizontal w-full mt-4">
                <li class="step step-primary">Submitted</li>
                <li class="step {{ 'step-primary' if benevolence_request.status.value in ['approved', 'paid', 'closed'] else 'step-warning' if benevolence_request.status.value == 'pending' else 'step-error' if benevolence_request.status.value == 'denied' else '' }}">
                    {{ 'Approved' if benevolence_request.status.value != 'denied' else 'Denied' }}
                </li>
                <li class="step {{ 'step-primary' if benevolence_request.status.value in ['paid', 'closed'] else '' }}">Paid</li>
                <li class="step {{ 'step-primary' if benevolence_request.status.value == 'closed' else '' }}">Closed</li>
            </ul>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Content -->
        <div class="lg:col-span-2 space-y-6">
            <!-- Request Details -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Request Details</h2>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <div>
                            <label class="text-sm text-base-content/60">Request Type</label>
                            <p>
                                <span class="badge {{ get_type_badge_class(benevolence_request.request_type) }}">
                                    {{ benevolence_request.request_type.value | title }}
                                </span>
                            </p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Amount Requested</label>
                            <p class="font-bold text-lg">${{ "{:,.2f}".format(benevolence_request.amount_requested) }}</p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Amount Approved</label>
                            <p class="font-bold text-lg {{ 'text-success' if benevolence_request.amount_approved else '' }}">
                                {% if benevolence_request.amount_approved %}
                                ${{ "{:,.2f}".format(benevolence_request.amount_approved) }}
                                {% else %}
                                <span class="text-base-content/40">Pending</span>
                                {% endif %}
                            </p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Reviewed By</label>
                            <p>
                                {% if benevolence_request.reviewed_by %}
                                {{ benevolence_request.reviewed_by.email }}
                                {% else %}
                                <span class="text-base-content/40">Not reviewed</span>
                                {% endif %}
                            </p>
                        </div>
                    </div>

                    <div class="mt-4">
                        <label class="text-sm text-base-content/60">Reason</label>
                        <p class="mt-1 whitespace-pre-wrap bg-base-200 p-4 rounded-lg">{{ benevolence_request.reason }}</p>
                    </div>

                    {% if benevolence_request.notes %}
                    <div class="mt-4">
                        <label class="text-sm text-base-content/60">Review Notes</label>
                        <p class="mt-1 whitespace-pre-wrap">{{ benevolence_request.notes }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Payment History -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <div class="flex items-center justify-between">
                        <h2 class="card-title">Payment History</h2>
                        {% if benevolence_request.status.value == 'approved' %}
                        <button class="btn btn-sm btn-primary">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                            </svg>
                            Add Payment
                        </button>
                        {% endif %}
                    </div>

                    {% if benevolence_request.payments %}
                    <div class="overflow-x-auto mt-4">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Amount</th>
                                    <th>Method</th>
                                    <th>Check #</th>
                                    <th>Processed By</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for payment in benevolence_request.payments %}
                                <tr>
                                    <td>{{ payment.payment_date.strftime('%b %d, %Y') }}</td>
                                    <td class="font-mono text-success">${{ "{:,.2f}".format(payment.amount) }}</td>
                                    <td>{{ payment.payment_method }}</td>
                                    <td>{{ payment.check_number or '—' }}</td>
                                    <td>{{ payment.processed_by.email if payment.processed_by else 'N/A' }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                            <tfoot>
                                <tr class="font-bold">
                                    <td>Total Paid</td>
                                    <td class="font-mono text-success">
                                        ${{ "{:,.2f}".format(benevolence_request.payments | sum(attribute='amount')) }}
                                    </td>
                                    <td colspan="3"></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                    {% else %}
                    <div class="text-center py-8 text-base-content/50">
                        <p>No payments recorded</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
            <!-- Member Info -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Member Information</h2>
                    {% if benevolence_request.member %}
                    <div class="space-y-3 text-sm mt-2">
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Name</span>
                            <span class="font-medium">
                                {{ benevolence_request.member.first_name }} {{ benevolence_request.member.last_name }}
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Card ID</span>
                            <span class="font-mono">{{ benevolence_request.member.card_id or '—' }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Email</span>
                            <span>{{ benevolence_request.member.email or '—' }}</span>
                        </div>
                    </div>
                    <div class="mt-4">
                        <a href="/members/{{ benevolence_request.member.id }}" class="btn btn-outline btn-sm btn-block">
                            View Member Profile
                        </a>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Timeline -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Timeline</h2>
                    <div class="space-y-3 text-sm mt-2">
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Submitted</span>
                            <span>{{ benevolence_request.created_at.strftime('%b %d, %Y') }}</span>
                        </div>
                        {% if benevolence_request.reviewed_at %}
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Reviewed</span>
                            <span>{{ benevolence_request.reviewed_at.strftime('%b %d, %Y') }}</span>
                        </div>
                        {% endif %}
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Last Updated</span>
                            <span>{{ benevolence_request.updated_at.strftime('%b %d, %Y') }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 6: Commit Session B

```bash
git add -A
git status

git commit -m "feat(operations): Phase 6 Week 6 Session B - Benevolence Fund

- Add benevolence methods to OperationsFrontendService
- Add benevolence routes (list, search, detail)
- Benevolence requests list with status badges
- Status workflow visualization (steps component)
- Request detail with payment history table
- Filter by status (pending/approved/denied/paid/closed)
- Filter by type (hardship/funeral/medical/disaster/other)
- HTMX live search

Stats: total, pending, approved, paid, denied, YTD amounts"

git push origin main
```

---

## Session B Checklist

- [ ] Added benevolence methods to service
- [ ] Added benevolence routes to router
- [ ] Created `operations/benevolence/index.html`
- [ ] Created `operations/benevolence/detail.html`
- [ ] Created `operations/benevolence/partials/_table.html`
- [ ] Status workflow steps display
- [ ] Payment history table
- [ ] Search and filters working
- [ ] Committed changes

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

*Session B complete. Proceed to Session C for Grievance Tracking.*
