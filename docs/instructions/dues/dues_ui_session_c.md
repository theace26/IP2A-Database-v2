# Week 10 Session C: Payments + Adjustments

**Duration:** 2-3 hours
**Goal:** Payment recording UI and adjustment approval workflow

---

## Step 1: Add Payment/Adjustment Methods to DuesFrontendService

Add these methods to `src/services/dues_frontend_service.py`:

```python
# Add these methods to the DuesFrontendService class:

    @staticmethod
    def get_all_payments(
        db: Session,
        period_id: Optional[int] = None,
        member_id: Optional[int] = None,
        status: Optional[DuesPaymentStatus] = None,
        q: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DuesPayment], int]:
        """Get all payments with optional filtering."""
        query = db.query(DuesPayment).join(DuesPayment.member, isouter=True)

        if period_id:
            query = query.filter(DuesPayment.period_id == period_id)

        if member_id:
            query = query.filter(DuesPayment.member_id == member_id)

        if status:
            query = query.filter(DuesPayment.status == status)

        if q:
            search = f"%{q}%"
            query = query.filter(
                (Member.first_name.ilike(search))
                | (Member.last_name.ilike(search))
                | (Member.member_number.ilike(search))
            )

        total = query.count()

        payments = (
            query.order_by(DuesPayment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return payments, total

    @staticmethod
    def get_member_payment_summary(db: Session, member_id: int) -> dict:
        """Get payment summary for a member."""
        payments = (
            db.query(DuesPayment)
            .filter(DuesPayment.member_id == member_id)
            .order_by(DuesPayment.created_at.desc())
            .all()
        )

        total_due = sum(p.amount_due for p in payments) if payments else Decimal("0")
        total_paid = sum(p.amount_paid or Decimal("0") for p in payments) if payments else Decimal("0")

        status_counts = {}
        for payment in payments:
            status = payment.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "payments": payments,
            "total_due": total_due,
            "total_paid": total_paid,
            "balance": total_due - total_paid,
            "status_counts": status_counts,
            "payment_count": len(payments),
        }

    @staticmethod
    def get_all_adjustments(
        db: Session,
        status: Optional[AdjustmentStatus] = None,
        adjustment_type: Optional[DuesAdjustmentType] = None,
        member_id: Optional[int] = None,
        q: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DuesAdjustment], int]:
        """Get all adjustments with optional filtering."""
        query = db.query(DuesAdjustment).join(DuesAdjustment.member, isouter=True)

        if status:
            query = query.filter(DuesAdjustment.status == status)

        if adjustment_type:
            query = query.filter(DuesAdjustment.adjustment_type == adjustment_type)

        if member_id:
            query = query.filter(DuesAdjustment.member_id == member_id)

        if q:
            search = f"%{q}%"
            query = query.filter(
                (Member.first_name.ilike(search))
                | (Member.last_name.ilike(search))
                | (Member.member_number.ilike(search))
                | (DuesAdjustment.reason.ilike(search))
            )

        total = query.count()

        adjustments = (
            query.order_by(DuesAdjustment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return adjustments, total

    @staticmethod
    def get_adjustment_detail(db: Session, adjustment_id: int) -> Optional[DuesAdjustment]:
        """Get adjustment with related data."""
        return (
            db.query(DuesAdjustment)
            .filter(DuesAdjustment.id == adjustment_id)
            .first()
        )

    @staticmethod
    def get_payment_method_display(method: Optional[DuesPaymentMethod]) -> str:
        """Get display name for payment method."""
        if not method:
            return "—"
        display_names = {
            DuesPaymentMethod.CASH: "Cash",
            DuesPaymentMethod.CHECK: "Check",
            DuesPaymentMethod.CREDIT_CARD: "Credit Card",
            DuesPaymentMethod.DEBIT_CARD: "Debit Card",
            DuesPaymentMethod.BANK_TRANSFER: "Bank Transfer",
            DuesPaymentMethod.PAYROLL_DEDUCTION: "Payroll Deduction",
        }
        return display_names.get(method, method.value)
```

---

## Step 2: Add Payment/Adjustment Routes

Add these routes to `src/routers/dues_frontend.py`:

```python
# Add to imports at top
from src.db.enums import DuesPaymentStatus, DuesPaymentMethod, DuesAdjustmentType, AdjustmentStatus
from src.db.models import Member

# Add these routes:

@router.get("/payments", response_class=HTMLResponse)
async def payments_list(
    request: Request,
    period_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Dues payments list page."""
    templates = get_templates(request)

    payments, total = DuesFrontendService.get_all_payments(db, period_id=period_id)

    # Get available periods for filter
    periods, _ = DuesFrontendService.get_all_periods(db, limit=24)

    # Get payment statuses for filter
    statuses = list(DuesPaymentStatus)

    return templates.TemplateResponse(
        "dues/payments/index.html",
        {
            "request": request,
            "user": current_user,
            "payments": payments,
            "total": total,
            "periods": periods,
            "statuses": statuses,
            "selected_period_id": period_id,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
            "get_payment_badge": DuesFrontendService.get_payment_status_badge_class,
            "get_method_display": DuesFrontendService.get_payment_method_display,
        },
    )


@router.get("/payments/search", response_class=HTMLResponse)
async def payments_search(
    request: Request,
    q: Optional[str] = Query(None),
    period_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """HTMX endpoint for payments table filtering."""
    templates = get_templates(request)

    # Parse status
    status_enum = None
    if status:
        try:
            status_enum = DuesPaymentStatus(status)
        except ValueError:
            pass

    payments, total = DuesFrontendService.get_all_payments(
        db, q=q, period_id=period_id, status=status_enum
    )

    return templates.TemplateResponse(
        "dues/payments/partials/_table.html",
        {
            "request": request,
            "payments": payments,
            "total": total,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
            "get_payment_badge": DuesFrontendService.get_payment_status_badge_class,
            "get_method_display": DuesFrontendService.get_payment_method_display,
        },
    )


@router.get("/payments/member/{member_id}", response_class=HTMLResponse)
async def member_payments(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Member payment history page."""
    templates = get_templates(request)

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "user": current_user},
            status_code=404,
        )

    summary = DuesFrontendService.get_member_payment_summary(db, member_id)

    return templates.TemplateResponse(
        "dues/payments/member.html",
        {
            "request": request,
            "user": current_user,
            "member": member,
            **summary,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
            "get_payment_badge": DuesFrontendService.get_payment_status_badge_class,
            "get_method_display": DuesFrontendService.get_payment_method_display,
        },
    )


@router.post("/payments/{payment_id}/record", response_class=HTMLResponse)
async def record_payment(
    request: Request,
    payment_id: int,
    amount_paid: str = Form(...),
    payment_method: Optional[str] = Form(None),
    check_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Record a payment."""
    from src.services.dues_payment_service import DuesPaymentService
    from decimal import Decimal, InvalidOperation

    try:
        amount = Decimal(amount_paid)
        method_enum = None
        if payment_method:
            try:
                method_enum = DuesPaymentMethod(payment_method)
            except ValueError:
                pass

        payment = DuesPaymentService.record_payment(
            db,
            payment_id=payment_id,
            amount_paid=amount,
            payment_method=method_enum,
            check_number=check_number,
            notes=notes,
        )
        db.commit()

        return RedirectResponse(
            url=f"/dues/payments?success=Payment recorded successfully",
            status_code=303,
        )
    except (InvalidOperation, Exception) as e:
        db.rollback()
        return RedirectResponse(
            url=f"/dues/payments?error={str(e)}",
            status_code=303,
        )


@router.get("/adjustments", response_class=HTMLResponse)
async def adjustments_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Dues adjustments list page."""
    templates = get_templates(request)

    adjustments, total = DuesFrontendService.get_all_adjustments(db)

    # Get filter options
    statuses = list(AdjustmentStatus)
    types = list(DuesAdjustmentType)

    return templates.TemplateResponse(
        "dues/adjustments/index.html",
        {
            "request": request,
            "user": current_user,
            "adjustments": adjustments,
            "total": total,
            "statuses": statuses,
            "types": types,
            "format_currency": DuesFrontendService.format_currency,
            "get_status_badge": DuesFrontendService.get_adjustment_status_badge_class,
            "get_type_badge": DuesFrontendService.get_adjustment_type_badge_class,
        },
    )


@router.get("/adjustments/search", response_class=HTMLResponse)
async def adjustments_search(
    request: Request,
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    adjustment_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """HTMX endpoint for adjustments table filtering."""
    templates = get_templates(request)

    # Parse enums
    status_enum = None
    if status:
        try:
            status_enum = AdjustmentStatus(status)
        except ValueError:
            pass

    type_enum = None
    if adjustment_type:
        try:
            type_enum = DuesAdjustmentType(adjustment_type)
        except ValueError:
            pass

    adjustments, total = DuesFrontendService.get_all_adjustments(
        db, q=q, status=status_enum, adjustment_type=type_enum
    )

    return templates.TemplateResponse(
        "dues/adjustments/partials/_table.html",
        {
            "request": request,
            "adjustments": adjustments,
            "total": total,
            "format_currency": DuesFrontendService.format_currency,
            "get_status_badge": DuesFrontendService.get_adjustment_status_badge_class,
            "get_type_badge": DuesFrontendService.get_adjustment_type_badge_class,
        },
    )


@router.get("/adjustments/{adjustment_id}", response_class=HTMLResponse)
async def adjustment_detail(
    request: Request,
    adjustment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Adjustment detail page."""
    templates = get_templates(request)

    adjustment = DuesFrontendService.get_adjustment_detail(db, adjustment_id)
    if not adjustment:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "user": current_user},
            status_code=404,
        )

    return templates.TemplateResponse(
        "dues/adjustments/detail.html",
        {
            "request": request,
            "user": current_user,
            "adjustment": adjustment,
            "format_currency": DuesFrontendService.format_currency,
            "get_status_badge": DuesFrontendService.get_adjustment_status_badge_class,
            "get_type_badge": DuesFrontendService.get_adjustment_type_badge_class,
        },
    )


@router.post("/adjustments/{adjustment_id}/approve", response_class=HTMLResponse)
async def approve_adjustment(
    request: Request,
    adjustment_id: int,
    approved: str = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Approve or deny an adjustment."""
    from src.services.dues_adjustment_service import DuesAdjustmentService

    try:
        is_approved = approved.lower() == "true"

        adjustment = DuesAdjustmentService.approve_adjustment(
            db,
            adjustment_id=adjustment_id,
            approved=is_approved,
            approved_by_id=current_user.id,
            notes=notes,
        )
        db.commit()

        action = "approved" if is_approved else "denied"
        return RedirectResponse(
            url=f"/dues/adjustments/{adjustment_id}?success=Adjustment {action}",
            status_code=303,
        )
    except Exception as e:
        db.rollback()
        return RedirectResponse(
            url=f"/dues/adjustments/{adjustment_id}?error={str(e)}",
            status_code=303,
        )
```

---

## Step 3: Create Payments List Template

Create `src/templates/dues/payments/index.html`:

```html
{% extends "base.html" %}

{% block title %}Dues Payments - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues</a></li>
            <li>Payments</li>
        </ul>
    </div>

    <!-- Flash Messages -->
    {% if request.query_params.get('success') %}
    <div class="alert alert-success">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ request.query_params.get('success') }}</span>
    </div>
    {% endif %}

    {% if request.query_params.get('error') %}
    <div class="alert alert-error">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ request.query_params.get('error') }}</span>
    </div>
    {% endif %}

    <!-- Page Header -->
    <div class="flex justify-between items-center">
        <div>
            <h1 class="text-2xl font-bold">Dues Payments</h1>
            <p class="text-base-content/70">Track and record member dues payments</p>
        </div>
    </div>

    <!-- Filters -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <div class="flex flex-wrap gap-4 items-end">
                <!-- Search -->
                <div class="form-control w-full max-w-xs">
                    <label class="label">
                        <span class="label-text">Search</span>
                    </label>
                    <input
                        type="search"
                        name="q"
                        placeholder="Member name or number..."
                        class="input input-bordered"
                        hx-get="/dues/payments/search"
                        hx-trigger="input changed delay:300ms"
                        hx-target="#payments-table"
                        hx-include="[name='period_id'], [name='status']"
                    />
                </div>

                <!-- Period Filter -->
                <div class="form-control w-full max-w-xs">
                    <label class="label">
                        <span class="label-text">Period</span>
                    </label>
                    <select
                        name="period_id"
                        class="select select-bordered"
                        hx-get="/dues/payments/search"
                        hx-trigger="change"
                        hx-target="#payments-table"
                        hx-include="[name='q'], [name='status']"
                    >
                        <option value="">All Periods</option>
                        {% for period in periods %}
                        <option value="{{ period.id }}" {% if selected_period_id == period.id %}selected{% endif %}>
                            {{ format_period_name(period) }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Status Filter -->
                <div class="form-control w-full max-w-xs">
                    <label class="label">
                        <span class="label-text">Status</span>
                    </label>
                    <select
                        name="status"
                        class="select select-bordered"
                        hx-get="/dues/payments/search"
                        hx-trigger="change"
                        hx-target="#payments-table"
                        hx-include="[name='q'], [name='period_id']"
                    >
                        <option value="">All Statuses</option>
                        {% for s in statuses %}
                        <option value="{{ s.value }}">{{ s.value.replace('_', ' ').title() }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- Payments Table -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <div id="payments-table">
                {% include "dues/payments/partials/_table.html" %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 4: Create Payments Table Partial

Create `src/templates/dues/payments/partials/_table.html`:

```html
{% if payments %}
<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr>
                <th>Member</th>
                <th>Period</th>
                <th>Amount Due</th>
                <th>Amount Paid</th>
                <th>Status</th>
                <th>Method</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for payment in payments %}
            <tr x-data="{ showModal: false }">
                <td>
                    {% if payment.member %}
                    <a href="/members/{{ payment.member_id }}" class="link link-hover">
                        {{ payment.member.first_name }} {{ payment.member.last_name }}
                    </a>
                    <div class="text-xs text-base-content/50">{{ payment.member.member_number or '' }}</div>
                    {% else %}
                    Member #{{ payment.member_id }}
                    {% endif %}
                </td>
                <td>
                    {% if payment.period %}
                    {{ format_period_name(payment.period) }}
                    {% else %}
                    —
                    {% endif %}
                </td>
                <td class="font-mono">{{ format_currency(payment.amount_due) }}</td>
                <td class="font-mono">{{ format_currency(payment.amount_paid) }}</td>
                <td>
                    <span class="badge {{ get_payment_badge(payment.status) }}">
                        {{ payment.status.value.replace('_', ' ').title() }}
                    </span>
                </td>
                <td>{{ get_method_display(payment.payment_method) }}</td>
                <td>
                    {% if payment.status.value not in ['paid', 'waived'] %}
                    <button class="btn btn-primary btn-sm" @click="showModal = true">
                        Record
                    </button>

                    <!-- Record Payment Modal -->
                    <div class="modal" :class="{ 'modal-open': showModal }">
                        <div class="modal-box">
                            <h3 class="font-bold text-lg">Record Payment</h3>
                            <p class="py-2 text-base-content/70">
                                {% if payment.member %}
                                {{ payment.member.first_name }} {{ payment.member.last_name }}
                                {% endif %}
                                — {{ format_currency(payment.amount_due) }} due
                            </p>

                            <form method="POST" action="/dues/payments/{{ payment.id }}/record">
                                <div class="form-control">
                                    <label class="label">
                                        <span class="label-text">Amount Paid</span>
                                    </label>
                                    <input
                                        type="number"
                                        name="amount_paid"
                                        step="0.01"
                                        min="0"
                                        value="{{ payment.amount_due }}"
                                        class="input input-bordered"
                                        required
                                    />
                                </div>

                                <div class="form-control mt-4">
                                    <label class="label">
                                        <span class="label-text">Payment Method</span>
                                    </label>
                                    <select name="payment_method" class="select select-bordered">
                                        <option value="">Select method...</option>
                                        <option value="cash">Cash</option>
                                        <option value="check">Check</option>
                                        <option value="credit_card">Credit Card</option>
                                        <option value="debit_card">Debit Card</option>
                                        <option value="bank_transfer">Bank Transfer</option>
                                        <option value="payroll_deduction">Payroll Deduction</option>
                                    </select>
                                </div>

                                <div class="form-control mt-4">
                                    <label class="label">
                                        <span class="label-text">Check Number (if applicable)</span>
                                    </label>
                                    <input
                                        type="text"
                                        name="check_number"
                                        class="input input-bordered"
                                        placeholder="Optional"
                                    />
                                </div>

                                <div class="form-control mt-4">
                                    <label class="label">
                                        <span class="label-text">Notes (optional)</span>
                                    </label>
                                    <textarea
                                        name="notes"
                                        class="textarea textarea-bordered"
                                        rows="2"
                                    ></textarea>
                                </div>

                                <div class="modal-action">
                                    <button type="button" class="btn" @click="showModal = false">Cancel</button>
                                    <button type="submit" class="btn btn-primary">Record Payment</button>
                                </div>
                            </form>
                        </div>
                        <div class="modal-backdrop" @click="showModal = false"></div>
                    </div>
                    {% else %}
                    <span class="text-base-content/50">—</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% if total is defined %}
<div class="mt-4 text-sm text-base-content/70">
    Showing {{ payments|length }} of {{ total }} payments
</div>
{% endif %}
{% else %}
<div class="text-center py-8 text-base-content/50">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
    <p>No payments found</p>
</div>
{% endif %}
```

---

## Step 5: Create Member Payment History Template

Create `src/templates/dues/payments/member.html`:

```html
{% extends "base.html" %}

{% block title %}{{ member.first_name }} {{ member.last_name }} - Payment History - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues</a></li>
            <li><a href="/dues/payments">Payments</a></li>
            <li>{{ member.first_name }} {{ member.last_name }}</li>
        </ul>
    </div>

    <!-- Header -->
    <div class="flex justify-between items-start">
        <div>
            <h1 class="text-2xl font-bold">{{ member.first_name }} {{ member.last_name }}</h1>
            <p class="text-base-content/70">{{ member.member_number or 'No member number' }}</p>
        </div>
        <a href="/members/{{ member.id }}" class="btn btn-ghost">
            View Member Profile
        </a>
    </div>

    <!-- Summary Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-title">Total Due</div>
            <div class="stat-value text-lg">{{ format_currency(total_due) }}</div>
        </div>

        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-title">Total Paid</div>
            <div class="stat-value text-lg text-success">{{ format_currency(total_paid) }}</div>
        </div>

        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-title">Balance</div>
            <div class="stat-value text-lg {% if balance > 0 %}text-error{% endif %}">
                {{ format_currency(balance) }}
            </div>
        </div>

        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-title">Payments</div>
            <div class="stat-value text-lg">{{ payment_count }}</div>
        </div>
    </div>

    <!-- Status Breakdown -->
    {% if status_counts %}
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Payment Status</h2>
            <div class="flex flex-wrap gap-4">
                {% for status, count in status_counts.items() %}
                <div class="flex items-center gap-2">
                    <span class="badge {{ get_payment_badge(status) }}">{{ status.value.replace('_', ' ').title() }}</span>
                    <span class="font-semibold">{{ count }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Payment History Table -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Payment History</h2>

            {% if payments %}
            <div class="overflow-x-auto">
                <table class="table table-zebra">
                    <thead>
                        <tr>
                            <th>Period</th>
                            <th>Amount Due</th>
                            <th>Amount Paid</th>
                            <th>Status</th>
                            <th>Method</th>
                            <th>Payment Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for payment in payments %}
                        <tr>
                            <td>
                                {% if payment.period %}
                                {{ format_period_name(payment.period) }}
                                {% else %}
                                —
                                {% endif %}
                            </td>
                            <td class="font-mono">{{ format_currency(payment.amount_due) }}</td>
                            <td class="font-mono">{{ format_currency(payment.amount_paid) }}</td>
                            <td>
                                <span class="badge {{ get_payment_badge(payment.status) }}">
                                    {{ payment.status.value.replace('_', ' ').title() }}
                                </span>
                            </td>
                            <td>{{ get_method_display(payment.payment_method) }}</td>
                            <td>{{ payment.payment_date.strftime('%b %d, %Y') if payment.payment_date else '—' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="text-center py-8 text-base-content/50">
                <p>No payment history found</p>
            </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 6: Create Adjustments List Template

Create `src/templates/dues/adjustments/index.html`:

```html
{% extends "base.html" %}

{% block title %}Dues Adjustments - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues</a></li>
            <li>Adjustments</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center">
        <div>
            <h1 class="text-2xl font-bold">Dues Adjustments</h1>
            <p class="text-base-content/70">Waivers, credits, and adjustment requests</p>
        </div>
    </div>

    <!-- Filters -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <div class="flex flex-wrap gap-4 items-end">
                <!-- Search -->
                <div class="form-control w-full max-w-xs">
                    <label class="label">
                        <span class="label-text">Search</span>
                    </label>
                    <input
                        type="search"
                        name="q"
                        placeholder="Member name or reason..."
                        class="input input-bordered"
                        hx-get="/dues/adjustments/search"
                        hx-trigger="input changed delay:300ms"
                        hx-target="#adjustments-table"
                        hx-include="[name='status'], [name='adjustment_type']"
                    />
                </div>

                <!-- Status Filter -->
                <div class="form-control w-full max-w-xs">
                    <label class="label">
                        <span class="label-text">Status</span>
                    </label>
                    <select
                        name="status"
                        class="select select-bordered"
                        hx-get="/dues/adjustments/search"
                        hx-trigger="change"
                        hx-target="#adjustments-table"
                        hx-include="[name='q'], [name='adjustment_type']"
                    >
                        <option value="">All Statuses</option>
                        {% for s in statuses %}
                        <option value="{{ s.value }}">{{ s.value.title() }}</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Type Filter -->
                <div class="form-control w-full max-w-xs">
                    <label class="label">
                        <span class="label-text">Type</span>
                    </label>
                    <select
                        name="adjustment_type"
                        class="select select-bordered"
                        hx-get="/dues/adjustments/search"
                        hx-trigger="change"
                        hx-target="#adjustments-table"
                        hx-include="[name='q'], [name='status']"
                    >
                        <option value="">All Types</option>
                        {% for t in types %}
                        <option value="{{ t.value }}">{{ t.value.title() }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- Adjustments Table -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <div id="adjustments-table">
                {% include "dues/adjustments/partials/_table.html" %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 7: Create Adjustments Table Partial

Create `src/templates/dues/adjustments/partials/_table.html`:

```html
{% if adjustments %}
<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr>
                <th>Member</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for adjustment in adjustments %}
            <tr>
                <td>
                    {% if adjustment.member %}
                    <a href="/members/{{ adjustment.member_id }}" class="link link-hover">
                        {{ adjustment.member.first_name }} {{ adjustment.member.last_name }}
                    </a>
                    {% else %}
                    Member #{{ adjustment.member_id }}
                    {% endif %}
                </td>
                <td>
                    <span class="badge {{ get_type_badge(adjustment.adjustment_type) }}">
                        {{ adjustment.adjustment_type.value.title() }}
                    </span>
                </td>
                <td class="font-mono {% if adjustment.amount and adjustment.amount > 0 %}text-success{% elif adjustment.amount and adjustment.amount < 0 %}text-error{% endif %}">
                    {{ format_currency(adjustment.amount) }}
                </td>
                <td class="max-w-xs truncate">{{ adjustment.reason or '—' }}</td>
                <td>
                    <span class="badge {{ get_status_badge(adjustment.status) }}">
                        {{ adjustment.status.value.title() }}
                    </span>
                </td>
                <td>{{ adjustment.created_at.strftime('%b %d, %Y') if adjustment.created_at else '—' }}</td>
                <td>
                    <a href="/dues/adjustments/{{ adjustment.id }}" class="btn btn-ghost btn-sm">
                        View
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% if total is defined %}
<div class="mt-4 text-sm text-base-content/70">
    Showing {{ adjustments|length }} of {{ total }} adjustments
</div>
{% endif %}
{% else %}
<div class="text-center py-8 text-base-content/50">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
    <p>No adjustments found</p>
</div>
{% endif %}
```

---

## Step 8: Create Adjustment Detail Template

Create `src/templates/dues/adjustments/detail.html`:

```html
{% extends "base.html" %}

{% block title %}Adjustment #{{ adjustment.id }} - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues</a></li>
            <li><a href="/dues/adjustments">Adjustments</a></li>
            <li>Adjustment #{{ adjustment.id }}</li>
        </ul>
    </div>

    <!-- Flash Messages -->
    {% if request.query_params.get('success') %}
    <div class="alert alert-success">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ request.query_params.get('success') }}</span>
    </div>
    {% endif %}

    {% if request.query_params.get('error') %}
    <div class="alert alert-error">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ request.query_params.get('error') }}</span>
    </div>
    {% endif %}

    <!-- Header -->
    <div class="flex justify-between items-start">
        <div>
            <h1 class="text-2xl font-bold">Adjustment #{{ adjustment.id }}</h1>
            <div class="flex gap-2 mt-2">
                <span class="badge {{ get_type_badge(adjustment.adjustment_type) }} badge-lg">
                    {{ adjustment.adjustment_type.value.title() }}
                </span>
                <span class="badge {{ get_status_badge(adjustment.status) }} badge-lg">
                    {{ adjustment.status.value.title() }}
                </span>
            </div>
        </div>

        {% if adjustment.status.value == 'pending' %}
        <div x-data="{ showModal: false }">
            <button class="btn btn-primary" @click="showModal = true">
                Review Adjustment
            </button>

            <!-- Approve/Deny Modal -->
            <div class="modal" :class="{ 'modal-open': showModal }">
                <div class="modal-box">
                    <h3 class="font-bold text-lg">Review Adjustment</h3>
                    <p class="py-2 text-base-content/70">
                        {{ adjustment.adjustment_type.value.title() }} for {{ format_currency(adjustment.amount) }}
                    </p>

                    <form method="POST" action="/dues/adjustments/{{ adjustment.id }}/approve" x-data="{ action: '' }">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Decision</span>
                            </label>
                            <div class="flex gap-4">
                                <label class="label cursor-pointer gap-2">
                                    <input type="radio" name="approved" value="true" class="radio radio-success" x-model="action" required />
                                    <span class="label-text">Approve</span>
                                </label>
                                <label class="label cursor-pointer gap-2">
                                    <input type="radio" name="approved" value="false" class="radio radio-error" x-model="action" required />
                                    <span class="label-text">Deny</span>
                                </label>
                            </div>
                        </div>

                        <div class="form-control mt-4">
                            <label class="label">
                                <span class="label-text">Notes</span>
                            </label>
                            <textarea
                                name="notes"
                                class="textarea textarea-bordered"
                                rows="3"
                                placeholder="Add review notes..."
                            ></textarea>
                        </div>

                        <div class="modal-action">
                            <button type="button" class="btn" @click="showModal = false">Cancel</button>
                            <button
                                type="submit"
                                class="btn"
                                :class="action === 'true' ? 'btn-success' : action === 'false' ? 'btn-error' : 'btn-disabled'"
                                :disabled="!action"
                            >
                                <span x-text="action === 'true' ? 'Approve' : action === 'false' ? 'Deny' : 'Select Decision'"></span>
                            </button>
                        </div>
                    </form>
                </div>
                <div class="modal-backdrop" @click="showModal = false"></div>
            </div>
        </div>
        {% endif %}
    </div>

    <!-- Details Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Main Info -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Adjustment Details</h2>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <span class="text-base-content/70">Member:</span>
                        {% if adjustment.member %}
                        <a href="/members/{{ adjustment.member_id }}" class="link link-hover block font-medium">
                            {{ adjustment.member.first_name }} {{ adjustment.member.last_name }}
                        </a>
                        {% else %}
                        <span class="block font-medium">Member #{{ adjustment.member_id }}</span>
                        {% endif %}
                    </div>

                    <div>
                        <span class="text-base-content/70">Amount:</span>
                        <span class="block font-medium font-mono {% if adjustment.amount and adjustment.amount > 0 %}text-success{% elif adjustment.amount and adjustment.amount < 0 %}text-error{% endif %}">
                            {{ format_currency(adjustment.amount) }}
                        </span>
                    </div>

                    <div class="col-span-2">
                        <span class="text-base-content/70">Reason:</span>
                        <p class="mt-1">{{ adjustment.reason or 'No reason provided' }}</p>
                    </div>

                    <div>
                        <span class="text-base-content/70">Created:</span>
                        <span class="block">{{ adjustment.created_at.strftime('%b %d, %Y %I:%M %p') if adjustment.created_at else '—' }}</span>
                    </div>

                    {% if adjustment.payment_id %}
                    <div>
                        <span class="text-base-content/70">Related Payment:</span>
                        <span class="block">Payment #{{ adjustment.payment_id }}</span>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Approval Info -->
        {% if adjustment.status.value != 'pending' %}
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Review Information</h2>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <span class="text-base-content/70">Decision:</span>
                        <span class="badge {{ get_status_badge(adjustment.status) }} mt-1">
                            {{ adjustment.status.value.title() }}
                        </span>
                    </div>

                    <div>
                        <span class="text-base-content/70">Reviewed:</span>
                        <span class="block">{{ adjustment.approved_at.strftime('%b %d, %Y %I:%M %p') if adjustment.approved_at else '—' }}</span>
                    </div>

                    {% if adjustment.approval_notes %}
                    <div class="col-span-2">
                        <span class="text-base-content/70">Notes:</span>
                        <p class="mt-1">{{ adjustment.approval_notes }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
```

---

## Step 9: Add Payment/Adjustment Tests

Add to `src/tests/test_dues_frontend.py`:

```python
class TestDuesPayments:
    """Tests for dues payments pages."""

    def test_payments_list_requires_auth(self, client: TestClient):
        """Payments list requires authentication."""
        response = client.get("/dues/payments")
        assert response.status_code in [302, 401, 403]

    def test_payments_list_authenticated(self, authenticated_client: TestClient):
        """Payments list loads for authenticated users."""
        response = authenticated_client.get("/dues/payments")
        assert response.status_code == 200
        assert b"Dues Payments" in response.content

    def test_payments_search(self, authenticated_client: TestClient):
        """Payments search endpoint works."""
        response = authenticated_client.get("/dues/payments/search")
        assert response.status_code == 200

    def test_payments_search_with_filters(self, authenticated_client: TestClient):
        """Payments search with filters works."""
        response = authenticated_client.get("/dues/payments/search?status=pending")
        assert response.status_code == 200

    def test_member_payments_not_found(self, authenticated_client: TestClient):
        """Member payments returns 404 for invalid member."""
        response = authenticated_client.get("/dues/payments/member/99999")
        assert response.status_code == 404


class TestDuesAdjustments:
    """Tests for dues adjustments pages."""

    def test_adjustments_list_requires_auth(self, client: TestClient):
        """Adjustments list requires authentication."""
        response = client.get("/dues/adjustments")
        assert response.status_code in [302, 401, 403]

    def test_adjustments_list_authenticated(self, authenticated_client: TestClient):
        """Adjustments list loads for authenticated users."""
        response = authenticated_client.get("/dues/adjustments")
        assert response.status_code == 200
        assert b"Dues Adjustments" in response.content

    def test_adjustments_search(self, authenticated_client: TestClient):
        """Adjustments search endpoint works."""
        response = authenticated_client.get("/dues/adjustments/search")
        assert response.status_code == 200

    def test_adjustment_detail_not_found(self, authenticated_client: TestClient):
        """Adjustment detail returns 404 for invalid ID."""
        response = authenticated_client.get("/dues/adjustments/99999")
        assert response.status_code == 404
```

---

## Verification

```bash
# Run tests
pytest src/tests/test_dues_frontend.py -v

# Manual testing
# 1. Navigate to /dues/payments - should see payments list
# 2. Search for member - table should filter
# 3. Click Record on a pending payment - modal should work
# 4. Navigate to /dues/adjustments - should see list
# 5. Click an adjustment - should see detail
# 6. Review a pending adjustment - approve/deny should work

# Commit
git add -A
git commit -m "feat(dues-ui): add payments and adjustments management

- Add payment and adjustment methods to DuesFrontendService
- Add payments list with search and filters
- Add member payment history page
- Add record payment modal workflow
- Add adjustments list with type/status filters
- Add adjustment detail with approve/deny workflow
- Add payments and adjustments tests"
```

---

## Session C Complete!

**Files Created:**
- `src/templates/dues/payments/index.html`
- `src/templates/dues/payments/member.html`
- `src/templates/dues/payments/partials/_table.html`
- `src/templates/dues/adjustments/index.html`
- `src/templates/dues/adjustments/detail.html`
- `src/templates/dues/adjustments/partials/_table.html`

**Files Modified:**
- `src/services/dues_frontend_service.py` (payment/adjustment methods)
- `src/routers/dues_frontend.py` (payment/adjustment routes)
- `src/tests/test_dues_frontend.py` (payment/adjustment tests)

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

**Next:** Session D - Tests + Documentation
