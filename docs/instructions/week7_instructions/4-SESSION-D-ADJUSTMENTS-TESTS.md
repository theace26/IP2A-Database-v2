# Session D: Adjustments Workflow + Tests

**Duration:** 2-3 hours
**Prerequisites:** Session C complete (payments interface)

---

## Objectives

1. Add adjustment methods to DuesFrontendService
2. Build adjustments list and pending queue pages
3. Implement approve/deny workflow
4. Write comprehensive tests (20+)
5. Update documentation

---

## Pre-flight Checks

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Verify tests passing
```

---

## Task 1: Add Adjustment Methods to Service

**File:** `src/services/dues_frontend_service.py` - Add these methods:

```python
    # ─────────────────────────────────────────────────────────────────
    # Adjustments Management
    # ─────────────────────────────────────────────────────────────────

    def list_adjustments(
        self,
        member_id: Optional[int] = None,
        status: Optional[AdjustmentStatus] = None,
        adj_type: Optional[DuesAdjustmentType] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[DuesAdjustment], int]:
        """List adjustments with optional filters. Returns (adjustments, total_count)."""
        query = select(DuesAdjustment).join(Member)

        conditions = []
        if member_id:
            conditions.append(DuesAdjustment.member_id == member_id)
        if status:
            conditions.append(DuesAdjustment.status == status)
        if adj_type:
            conditions.append(DuesAdjustment.adjustment_type == adj_type)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(DuesAdjustment.created_at.desc())

        # Get total count
        count_query = select(func.count(DuesAdjustment.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = self.db.execute(count_query).scalar() or 0

        query = query.offset(skip).limit(limit)
        adjustments = list(self.db.execute(query).scalars().all())

        return adjustments, total

    def list_pending_adjustments(self) -> list[DuesAdjustment]:
        """List all pending adjustments ordered by date."""
        return list(
            self.db.execute(
                select(DuesAdjustment)
                .join(Member)
                .where(DuesAdjustment.status == AdjustmentStatus.PENDING)
                .order_by(DuesAdjustment.created_at.asc())
            ).scalars().all()
        )

    def get_adjustment(self, adjustment_id: int) -> Optional[DuesAdjustment]:
        """Get single adjustment by ID."""
        return self.db.get(DuesAdjustment, adjustment_id)

    def get_adjustment_with_details(self, adjustment_id: int) -> Optional[dict]:
        """Get adjustment with related details."""
        adjustment = self.get_adjustment(adjustment_id)
        if not adjustment:
            return None

        return {
            "id": adjustment.id,
            "member": adjustment.member,
            "payment": adjustment.payment,
            "adjustment_type": adjustment.adjustment_type,
            "amount": adjustment.amount,
            "reason": adjustment.reason,
            "status": adjustment.status,
            "requested_by": adjustment.requested_by,
            "approved_by": adjustment.approved_by,
            "approval_notes": adjustment.approval_notes,
            "created_at": adjustment.created_at,
            "approved_at": adjustment.approved_at,
        }

    def get_pending_count(self) -> int:
        """Get count of pending adjustments."""
        return self.db.execute(
            select(func.count(DuesAdjustment.id))
            .where(DuesAdjustment.status == AdjustmentStatus.PENDING)
        ).scalar() or 0

    def get_adjustment_stats(self) -> dict:
        """Get adjustment statistics."""
        today = date.today()
        year_start = date(today.year, 1, 1)

        pending = self.db.execute(
            select(func.count(DuesAdjustment.id))
            .where(DuesAdjustment.status == AdjustmentStatus.PENDING)
        ).scalar() or 0

        approved_ytd = self.db.execute(
            select(func.count(DuesAdjustment.id))
            .where(DuesAdjustment.status == AdjustmentStatus.APPROVED)
            .where(DuesAdjustment.approved_at >= year_start)
        ).scalar() or 0

        denied_ytd = self.db.execute(
            select(func.count(DuesAdjustment.id))
            .where(DuesAdjustment.status == AdjustmentStatus.DENIED)
            .where(DuesAdjustment.approved_at >= year_start)
        ).scalar() or 0

        total_adjusted_ytd = self.db.execute(
            select(func.coalesce(func.sum(DuesAdjustment.amount), Decimal("0")))
            .where(DuesAdjustment.status == AdjustmentStatus.APPROVED)
            .where(DuesAdjustment.approved_at >= year_start)
        ).scalar() or Decimal("0")

        return {
            "pending": pending,
            "approved_ytd": approved_ytd,
            "denied_ytd": denied_ytd,
            "total_adjusted_ytd": total_adjusted_ytd,
        }
```

---

## Task 2: Add Adjustment Routes to Router

**File:** `src/routers/dues_frontend.py` - Add these routes:

```python
from src.services.dues_adjustment_service import DuesAdjustmentService

# ─────────────────────────────────────────────────────────────────────
# Adjustments Management
# ─────────────────────────────────────────────────────────────────────

@router.get("/adjustments", response_class=HTMLResponse)
async def adjustments_list(
    request: Request,
    status: Optional[str] = Query(None),
    adj_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Adjustments list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)

    # Parse filters
    status_filter = None
    if status:
        try:
            status_filter = AdjustmentStatus(status)
        except ValueError:
            pass

    type_filter = None
    if adj_type:
        try:
            type_filter = DuesAdjustmentType(adj_type)
        except ValueError:
            pass

    per_page = 25
    skip = (page - 1) * per_page
    adjustments, total = service.list_adjustments(
        status=status_filter,
        adj_type=type_filter,
        skip=skip,
        limit=per_page,
    )

    total_pages = (total + per_page - 1) // per_page
    stats = service.get_adjustment_stats()

    return templates.TemplateResponse(
        "dues/adjustments/index.html",
        {
            "request": request,
            "user": current_user,
            "adjustments": adjustments,
            "statuses": list(AdjustmentStatus),
            "adjustment_types": list(DuesAdjustmentType),
            "selected_status": status,
            "selected_type": adj_type,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "stats": stats,
            "service": service,
        },
    )


@router.get("/adjustments/pending", response_class=HTMLResponse)
async def adjustments_pending(
    request: Request,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Pending adjustments queue page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)
    adjustments = service.list_pending_adjustments()

    return templates.TemplateResponse(
        "dues/adjustments/pending.html",
        {
            "request": request,
            "user": current_user,
            "adjustments": adjustments,
            "service": service,
        },
    )


@router.get("/adjustments/search", response_class=HTMLResponse)
async def adjustments_search(
    request: Request,
    status: Optional[str] = Query(None),
    adj_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """HTMX endpoint for adjustments table."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)

    status_filter = None
    if status:
        try:
            status_filter = AdjustmentStatus(status)
        except ValueError:
            pass

    type_filter = None
    if adj_type:
        try:
            type_filter = DuesAdjustmentType(adj_type)
        except ValueError:
            pass

    per_page = 25
    skip = (page - 1) * per_page
    adjustments, total = service.list_adjustments(
        status=status_filter,
        adj_type=type_filter,
        skip=skip,
        limit=per_page,
    )

    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        "dues/adjustments/partials/_table.html",
        {
            "request": request,
            "adjustments": adjustments,
            "page": page,
            "total_pages": total_pages,
            "service": service,
        },
    )


@router.get("/adjustments/{adjustment_id}/action-modal", response_class=HTMLResponse)
async def adjustment_action_modal(
    request: Request,
    adjustment_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get approve/deny modal content."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)
    adjustment = service.get_adjustment_with_details(adjustment_id)

    if not adjustment:
        return HTMLResponse("<div class='alert alert-error'>Adjustment not found</div>")

    return templates.TemplateResponse(
        "dues/adjustments/partials/_action_modal.html",
        {
            "request": request,
            "adjustment": adjustment,
            "service": service,
        },
    )


@router.post("/adjustments/{adjustment_id}/approve", response_class=HTMLResponse)
async def adjustment_approve(
    request: Request,
    adjustment_id: int,
    notes: Optional[str] = Form(None),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Approve an adjustment."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    try:
        adj_service = DuesAdjustmentService(db)
        adj_service.approve_adjustment(
            adjustment_id=adjustment_id,
            approved=True,
            approved_by_id=current_user.get("id"),
            notes=notes,
        )
        db.commit()

        return HTMLResponse(
            '<div class="alert alert-success" hx-swap-oob="true" id="flash-message">'
            '<span>Adjustment approved</span></div>',
            headers={"HX-Trigger": "adjustmentsUpdated"},
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400,
        )


@router.post("/adjustments/{adjustment_id}/deny", response_class=HTMLResponse)
async def adjustment_deny(
    request: Request,
    adjustment_id: int,
    notes: Optional[str] = Form(None),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Deny an adjustment."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    try:
        adj_service = DuesAdjustmentService(db)
        adj_service.approve_adjustment(
            adjustment_id=adjustment_id,
            approved=False,
            approved_by_id=current_user.get("id"),
            notes=notes,
        )
        db.commit()

        return HTMLResponse(
            '<div class="alert alert-info" hx-swap-oob="true" id="flash-message">'
            '<span>Adjustment denied</span></div>',
            headers={"HX-Trigger": "adjustmentsUpdated"},
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400,
        )
```

---

## Task 3: Create Adjustments Templates

**File:** `src/templates/dues/adjustments/index.html`

```html
{% extends "base.html" %}

{% block title %}Dues Adjustments - IP2A{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs mb-4">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues Management</a></li>
            <li>Adjustments</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold">Dues Adjustments</h1>
            <p class="text-base-content/70">Manage dues waivers, credits, and corrections</p>
        </div>
        {% if stats.pending > 0 %}
        <a href="/dues/adjustments/pending" class="btn btn-warning">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ stats.pending }} Pending
        </a>
        {% endif %}
    </div>

    <!-- Flash Message Container -->
    <div id="flash-message"></div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="stat bg-base-100 rounded-lg shadow p-4">
            <div class="stat-title text-sm">Pending</div>
            <div class="stat-value text-warning text-2xl">{{ stats.pending }}</div>
        </div>
        <div class="stat bg-base-100 rounded-lg shadow p-4">
            <div class="stat-title text-sm">Approved YTD</div>
            <div class="stat-value text-success text-2xl">{{ stats.approved_ytd }}</div>
        </div>
        <div class="stat bg-base-100 rounded-lg shadow p-4">
            <div class="stat-title text-sm">Denied YTD</div>
            <div class="stat-value text-error text-2xl">{{ stats.denied_ytd }}</div>
        </div>
        <div class="stat bg-base-100 rounded-lg shadow p-4">
            <div class="stat-title text-sm">Total Adjusted YTD</div>
            <div class="stat-value text-2xl">${{ "%.2f" | format(stats.total_adjusted_ytd) }}</div>
        </div>
    </div>

    <!-- Filters -->
    <div class="card bg-base-100 shadow mb-6">
        <div class="card-body py-4">
            <div class="flex flex-wrap gap-4 items-end">
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Status</span>
                    </label>
                    <select
                        name="status"
                        class="select select-bordered select-sm w-32"
                        hx-get="/dues/adjustments/search"
                        hx-target="#adjustments-table"
                        hx-include="[name='adj_type']"
                    >
                        <option value="">All Status</option>
                        {% for s in statuses %}
                        <option value="{{ s.value }}" {% if selected_status == s.value %}selected{% endif %}>
                            {{ s.value | title }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Type</span>
                    </label>
                    <select
                        name="adj_type"
                        class="select select-bordered select-sm w-40"
                        hx-get="/dues/adjustments/search"
                        hx-target="#adjustments-table"
                        hx-include="[name='status']"
                    >
                        <option value="">All Types</option>
                        {% for t in adjustment_types %}
                        <option value="{{ t.value }}" {% if selected_type == t.value %}selected{% endif %}>
                            {{ t.value | title }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <div class="text-sm text-base-content/70 self-end pb-2">
                    {{ total }} adjustment{% if total != 1 %}s{% endif %}
                </div>
            </div>
        </div>
    </div>

    <!-- Adjustments Table -->
    <div id="adjustments-table" hx-trigger="adjustmentsUpdated from:body" hx-get="/dues/adjustments/search" hx-include="[name='status'], [name='adj_type']">
        {% include "dues/adjustments/partials/_table.html" %}
    </div>
</div>

<!-- Action Modal -->
<dialog id="action-modal" class="modal">
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

**File:** `src/templates/dues/adjustments/pending.html`

```html
{% extends "base.html" %}

{% block title %}Pending Adjustments - IP2A{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs mb-4">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues Management</a></li>
            <li><a href="/dues/adjustments">Adjustments</a></li>
            <li>Pending Review</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold">Pending Adjustments</h1>
            <p class="text-base-content/70">{{ adjustments | length }} adjustment{% if adjustments | length != 1 %}s{% endif %} awaiting review</p>
        </div>
        <a href="/dues/adjustments" class="btn btn-ghost btn-sm">
            ← Back to All
        </a>
    </div>

    <!-- Flash Message Container -->
    <div id="flash-message"></div>

    <!-- Pending Queue -->
    <div id="pending-queue" hx-trigger="adjustmentsUpdated from:body" hx-get="/dues/adjustments/pending" hx-select="#pending-queue" hx-swap="outerHTML">
        {% if adjustments %}
        <div class="space-y-4">
            {% for adj in adjustments %}
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <div class="flex justify-between items-start">
                        <div>
                            <h3 class="font-bold">{{ adj.member.full_name }}</h3>
                            <p class="text-sm text-base-content/70">{{ adj.member.member_number }}</p>
                        </div>
                        <div class="flex gap-2">
                            <span class="badge {{ service.get_adjustment_type_badge_class(adj.adjustment_type) }}">
                                {{ adj.adjustment_type.value | title }}
                            </span>
                            <span class="badge badge-warning">Pending</span>
                        </div>
                    </div>

                    <div class="divider my-2"></div>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <span class="text-base-content/70">Amount:</span>
                            <span class="font-bold ml-1">
                                {% if adj.amount >= 0 %}
                                <span class="text-success">+${{ "%.2f" | format(adj.amount) }}</span>
                                {% else %}
                                <span class="text-error">-${{ "%.2f" | format(adj.amount | abs) }}</span>
                                {% endif %}
                            </span>
                        </div>
                        <div>
                            <span class="text-base-content/70">Requested:</span>
                            <span class="ml-1">{{ adj.created_at.strftime('%b %d, %Y') }}</span>
                        </div>
                        {% if adj.payment %}
                        <div>
                            <span class="text-base-content/70">Period:</span>
                            <span class="ml-1">{{ adj.payment.period.period_year }}-{{ '%02d' | format(adj.payment.period.period_month) }}</span>
                        </div>
                        {% endif %}
                        {% if adj.requested_by %}
                        <div>
                            <span class="text-base-content/70">By:</span>
                            <span class="ml-1">{{ adj.requested_by.email }}</span>
                        </div>
                        {% endif %}
                    </div>

                    <div class="bg-base-200 rounded p-3 mt-2">
                        <span class="text-sm text-base-content/70">Reason:</span>
                        <p class="mt-1">{{ adj.reason }}</p>
                    </div>

                    <div class="card-actions justify-end mt-4">
                        <button
                            class="btn btn-error btn-sm"
                            hx-post="/dues/adjustments/{{ adj.id }}/deny"
                            hx-swap="none"
                            hx-confirm="Deny this adjustment request?"
                        >
                            Deny
                        </button>
                        <button
                            class="btn btn-success btn-sm"
                            hx-get="/dues/adjustments/{{ adj.id }}/action-modal"
                            hx-target="#modal-content"
                            hx-swap="innerHTML"
                            onclick="document.getElementById('action-modal').showModal()"
                        >
                            Approve
                        </button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="card bg-base-100 shadow">
            <div class="card-body text-center py-12">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-success mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 class="text-xl font-bold">All Caught Up!</h3>
                <p class="text-base-content/70">No pending adjustments to review.</p>
            </div>
        </div>
        {% endif %}
    </div>
</div>

<!-- Action Modal -->
<dialog id="action-modal" class="modal">
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

**File:** `src/templates/dues/adjustments/partials/_table.html`

```html
<div class="card bg-base-100 shadow">
    <div class="card-body p-0">
        <div class="overflow-x-auto">
            <table class="table">
                <thead>
                    <tr>
                        <th>Member</th>
                        <th>Type</th>
                        <th>Amount</th>
                        <th>Reason</th>
                        <th>Status</th>
                        <th>Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for adj in adjustments %}
                    <tr class="hover">
                        <td>
                            <div class="font-medium">{{ adj.member.full_name }}</div>
                            <div class="text-xs text-base-content/50">{{ adj.member.member_number }}</div>
                        </td>
                        <td>
                            <span class="badge {{ service.get_adjustment_type_badge_class(adj.adjustment_type) }} badge-sm">
                                {{ adj.adjustment_type.value | title }}
                            </span>
                        </td>
                        <td class="font-mono">
                            {% if adj.amount >= 0 %}
                            <span class="text-success">+${{ "%.2f" | format(adj.amount) }}</span>
                            {% else %}
                            <span class="text-error">-${{ "%.2f" | format(adj.amount | abs) }}</span>
                            {% endif %}
                        </td>
                        <td class="max-w-xs truncate" title="{{ adj.reason }}">
                            {{ adj.reason[:50] }}{% if adj.reason | length > 50 %}...{% endif %}
                        </td>
                        <td>
                            <span class="badge {{ service.get_adjustment_status_badge_class(adj.status) }} badge-sm">
                                {{ adj.status.value | title }}
                            </span>
                        </td>
                        <td>{{ adj.created_at.strftime('%b %d, %Y') }}</td>
                        <td>
                            {% if adj.status.value == 'pending' %}
                            <button
                                class="btn btn-ghost btn-xs"
                                hx-get="/dues/adjustments/{{ adj.id }}/action-modal"
                                hx-target="#modal-content"
                                hx-swap="innerHTML"
                                onclick="document.getElementById('action-modal').showModal()"
                            >
                                Review
                            </button>
                            {% else %}
                            <span class="text-xs text-base-content/50">
                                {% if adj.approved_by %}
                                by {{ adj.approved_by.email | truncate(15) }}
                                {% endif %}
                            </span>
                            {% endif %}
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="7" class="text-center py-8 text-base-content/50">
                            No adjustments found
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
                    hx-get="/dues/adjustments/search?page={{ page - 1 }}"
                    hx-target="#adjustments-table"
                    hx-include="[name='status'], [name='adj_type']"
                >
                    «
                </button>
                {% endif %}

                <button class="join-item btn btn-sm btn-active">{{ page }}</button>

                {% if page < total_pages %}
                <button
                    class="join-item btn btn-sm"
                    hx-get="/dues/adjustments/search?page={{ page + 1 }}"
                    hx-target="#adjustments-table"
                    hx-include="[name='status'], [name='adj_type']"
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

**File:** `src/templates/dues/adjustments/partials/_action_modal.html`

```html
<h3 class="font-bold text-lg mb-4">Approve Adjustment</h3>

<!-- Adjustment Details -->
<div class="bg-base-200 rounded-lg p-4 mb-4">
    <div class="flex justify-between items-start mb-2">
        <div>
            <div class="font-medium">{{ adjustment.member.full_name }}</div>
            <div class="text-sm text-base-content/70">{{ adjustment.member.member_number }}</div>
        </div>
        <span class="badge {{ service.get_adjustment_type_badge_class(adjustment.adjustment_type) }}">
            {{ adjustment.adjustment_type.value | title }}
        </span>
    </div>

    <div class="divider my-2"></div>

    <div class="grid grid-cols-2 gap-2 text-sm">
        <div>
            <span class="text-base-content/70">Amount:</span>
            <span class="font-bold ml-1">
                {% if adjustment.amount >= 0 %}
                <span class="text-success">+${{ "%.2f" | format(adjustment.amount) }}</span>
                {% else %}
                <span class="text-error">-${{ "%.2f" | format(adjustment.amount | abs) }}</span>
                {% endif %}
            </span>
        </div>
        <div>
            <span class="text-base-content/70">Requested:</span>
            <span class="ml-1">{{ adjustment.created_at.strftime('%b %d, %Y') }}</span>
        </div>
    </div>

    <div class="mt-3">
        <span class="text-sm text-base-content/70">Reason:</span>
        <p class="mt-1 text-sm">{{ adjustment.reason }}</p>
    </div>
</div>

<form hx-post="/dues/adjustments/{{ adjustment.id }}/approve" hx-swap="none">
    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Approval Notes (optional)</span>
        </label>
        <textarea
            name="notes"
            class="textarea textarea-bordered"
            placeholder="Add notes about this approval..."
            rows="2"
        ></textarea>
    </div>

    <div class="modal-action">
        <button type="button" class="btn" onclick="document.getElementById('action-modal').close()">
            Cancel
        </button>
        <button
            type="button"
            class="btn btn-error"
            hx-post="/dues/adjustments/{{ adjustment.id }}/deny"
            hx-swap="none"
            hx-include="[name='notes']"
            onclick="document.getElementById('action-modal').close()"
        >
            Deny
        </button>
        <button type="submit" class="btn btn-success" onclick="document.getElementById('action-modal').close()">
            Approve
        </button>
    </div>
</form>
```

---

## Task 4: Create Comprehensive Tests

**File:** `src/tests/test_dues_frontend.py`

```python
"""Tests for dues frontend routes."""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from src.main import app
from src.db.session import get_db
from src.models.user import User
from src.core.security import create_access_token


@pytest.fixture
def auth_cookies(db: Session):
    """Create auth cookies for testing."""
    user = db.query(User).filter(User.email == "admin@ip2a.org").first()
    if not user:
        pytest.skip("Admin user not found in test database")

    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return {"access_token": token}


class TestDuesLanding:
    """Tests for dues landing page."""

    @pytest.mark.asyncio
    async def test_dues_landing_requires_auth(self):
        """Test that dues landing requires authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/dues")
            assert response.status_code in [302, 303, 307]

    @pytest.mark.asyncio
    async def test_dues_landing_loads(self, auth_cookies):
        """Test that dues landing page loads with auth."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues")
            assert response.status_code == 200
            assert "Dues Management" in response.text

    @pytest.mark.asyncio
    async def test_dues_landing_shows_stats(self, auth_cookies):
        """Test that landing shows stats cards."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues")
            assert "Collected YTD" in response.text
            assert "collection rate" in response.text.lower()


class TestDuesRates:
    """Tests for dues rates management."""

    @pytest.mark.asyncio
    async def test_rates_list_requires_auth(self):
        """Test that rates list requires authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/dues/rates")
            assert response.status_code in [302, 303, 307]

    @pytest.mark.asyncio
    async def test_rates_list_loads(self, auth_cookies):
        """Test that rates list page loads."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/rates")
            assert response.status_code == 200
            assert "Dues Rates" in response.text

    @pytest.mark.asyncio
    async def test_rates_search_htmx(self, auth_cookies):
        """Test HTMX rates search endpoint."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/rates/search")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rates_filter_by_classification(self, auth_cookies):
        """Test filtering rates by classification."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/rates/search?classification=journeyman")
            assert response.status_code == 200


class TestDuesPeriods:
    """Tests for dues periods management."""

    @pytest.mark.asyncio
    async def test_periods_list_requires_auth(self):
        """Test that periods list requires authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/dues/periods")
            assert response.status_code in [302, 303, 307]

    @pytest.mark.asyncio
    async def test_periods_list_loads(self, auth_cookies):
        """Test that periods list page loads."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/periods")
            assert response.status_code == 200
            assert "Dues Periods" in response.text

    @pytest.mark.asyncio
    async def test_periods_search_htmx(self, auth_cookies):
        """Test HTMX periods search endpoint."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/periods/search")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_periods_filter_by_year(self, auth_cookies):
        """Test filtering periods by year."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/periods/search?year=2026")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_periods_filter_by_status(self, auth_cookies):
        """Test filtering periods by status."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/periods/search?status=open")
            assert response.status_code == 200


class TestDuesPayments:
    """Tests for dues payments management."""

    @pytest.mark.asyncio
    async def test_payments_list_requires_auth(self):
        """Test that payments list requires authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/dues/payments")
            assert response.status_code in [302, 303, 307]

    @pytest.mark.asyncio
    async def test_payments_list_loads(self, auth_cookies):
        """Test that payments list page loads."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/payments")
            assert response.status_code == 200
            assert "Dues Payments" in response.text

    @pytest.mark.asyncio
    async def test_payments_search_htmx(self, auth_cookies):
        """Test HTMX payments search endpoint."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/payments/search")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_payments_filter_by_status(self, auth_cookies):
        """Test filtering payments by status."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/payments/search?status=pending")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_payments_search_by_member(self, auth_cookies):
        """Test searching payments by member name."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/payments/search?q=test")
            assert response.status_code == 200


class TestDuesAdjustments:
    """Tests for dues adjustments management."""

    @pytest.mark.asyncio
    async def test_adjustments_list_requires_auth(self):
        """Test that adjustments list requires authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/dues/adjustments")
            assert response.status_code in [302, 303, 307]

    @pytest.mark.asyncio
    async def test_adjustments_list_loads(self, auth_cookies):
        """Test that adjustments list page loads."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/adjustments")
            assert response.status_code == 200
            assert "Dues Adjustments" in response.text

    @pytest.mark.asyncio
    async def test_adjustments_pending_loads(self, auth_cookies):
        """Test that pending adjustments page loads."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/adjustments/pending")
            assert response.status_code == 200
            assert "Pending" in response.text

    @pytest.mark.asyncio
    async def test_adjustments_search_htmx(self, auth_cookies):
        """Test HTMX adjustments search endpoint."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/adjustments/search")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_adjustments_filter_by_status(self, auth_cookies):
        """Test filtering adjustments by status."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/adjustments/search?status=pending")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_adjustments_filter_by_type(self, auth_cookies):
        """Test filtering adjustments by type."""
        async with AsyncClient(app=app, base_url="http://test", cookies=auth_cookies) as client:
            response = await client.get("/dues/adjustments/search?adj_type=waiver")
            assert response.status_code == 200
```

---

## Task 5: Update Documentation

### CHANGELOG.md Addition

```markdown
## [0.7.6] - 2026-01-XX

### Added
- **Phase 6 Week 7: Dues Management UI** (Complete)
  * Dues landing page with collection stats and current period card
  * Rates management with classification grouping
  * Create/edit rate modal with effective date handling
  * Periods list with collection progress bars
  * Generate year workflow (creates 12 periods)
  * Close period workflow with confirmation
  * Period detail page with status breakdown
  * Payments list with member search
  * Filter payments by period and status
  * Record payment modal with method selection
  * Batch update overdue functionality
  * Adjustments list with type/status filters
  * Pending adjustments queue
  * Approve/deny workflow with notes
  * DuesFrontendService for all dues queries
  * 23 new dues frontend tests (117 frontend total)
  * Updated sidebar navigation with Dues dropdown
```

### Session Log

Create: `docs/reports/session-logs/2026-01-XX-week7-dues-ui.md`

```markdown
# Phase 6 Week 7: Dues Management UI Session Log

**Date:** January XX, 2026
**Phase:** Frontend Phase 6 Week 7
**Duration:** 4 sessions (~10 hours)
**Version:** v0.7.6

---

## Summary

Completed Dues Management UI with full CRUD operations for rates, periods, payments, and adjustments. Added approval workflow for adjustments and batch operations for overdue payments.

---

## Sessions Completed

### Session A: Landing + Rates
| Task | Status |
|------|--------|
| Create DuesFrontendService | Done |
| Create dues_frontend router | Done |
| Dues landing page with stats | Done |
| Rates list with classification filter | Done |
| Create/edit rate modal | Done |

### Session B: Periods Management
| Task | Status |
|------|--------|
| Periods list with year/status filter | Done |
| Collection progress visualization | Done |
| Generate year modal | Done |
| Close period workflow | Done |
| Period detail page | Done |

### Session C: Payments Interface
| Task | Status |
|------|--------|
| Payments list with search | Done |
| Filter by period and status | Done |
| Record payment modal | Done |
| Payment method selection | Done |
| Batch update overdue | Done |

### Session D: Adjustments + Tests
| Task | Status |
|------|--------|
| Adjustments list with filters | Done |
| Pending adjustments queue | Done |
| Approve/deny workflow | Done |
| Comprehensive tests (23) | Done |
| Documentation updates | Done |

---

## Files Created

```
src/services/dues_frontend_service.py
src/routers/dues_frontend.py
src/templates/dues/
├── index.html
├── rates/
│   ├── index.html
│   └── partials/_table.html, _edit_modal.html
├── periods/
│   ├── index.html
│   ├── detail.html
│   └── partials/_table.html, _generate_modal.html, _close_modal.html
├── payments/
│   ├── index.html
│   └── partials/_table.html, _record_modal.html, _member_history.html
└── adjustments/
    ├── index.html
    ├── pending.html
    └── partials/_table.html, _action_modal.html
src/tests/test_dues_frontend.py (23 tests)
```

---

## Test Results

```
Frontend Tests: 117 passed
Total Tests: 282 passed
```

---

## Version

**v0.7.6** - Phase 6 Week 7 Complete
```

---

## Final Verification

```bash
# Run all tests
pytest -v --tb=short

# Verify test count increased
pytest --collect-only | grep "test session starts"

# Final commit
git add -A
git commit -m "feat(dues-ui): Week 7 Complete - Dues Management UI with tests"
git push origin main

# Tag release
git tag -a v0.7.6 -m "Phase 6 Week 7: Dues Management UI"
git push origin v0.7.6
```

---

## Week 7 Complete! 🎉

**What's Next (Week 8 Options):**
- Reports/Export (PDF/Excel generation)
- Document Management UI
- Deployment Prep (Railway/Render)
- Polish & Bug Fixes

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
