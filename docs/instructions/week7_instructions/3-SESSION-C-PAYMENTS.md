# Session C: Payments Interface

**Duration:** 2-3 hours
**Prerequisites:** Session B complete (periods management)

---

## Objectives

1. Add payment methods to DuesFrontendService
2. Build payments list page with period/status filters
3. Implement record payment modal
4. Add payment method selection
5. Add batch update overdue functionality

---

## Pre-flight Checks

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Verify tests passing
```

---

## Task 1: Add Payment Methods to Service

**File:** `src/services/dues_frontend_service.py` - Add these methods:

```python
    # ─────────────────────────────────────────────────────────────────
    # Payments Management
    # ─────────────────────────────────────────────────────────────────

    def list_payments(
        self,
        period_id: Optional[int] = None,
        member_id: Optional[int] = None,
        status: Optional[DuesPaymentStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[DuesPayment], int]:
        """List payments with optional filters. Returns (payments, total_count)."""
        query = select(DuesPayment).join(Member).join(DuesPeriod)

        # Build filter conditions
        conditions = []
        if period_id:
            conditions.append(DuesPayment.period_id == period_id)
        if member_id:
            conditions.append(DuesPayment.member_id == member_id)
        if status:
            conditions.append(DuesPayment.status == status)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                (Member.first_name.ilike(search_term)) |
                (Member.last_name.ilike(search_term)) |
                (Member.member_number.ilike(search_term))
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Order by period (newest first), then member name
        query = query.order_by(
            DuesPeriod.period_year.desc(),
            DuesPeriod.period_month.desc(),
            Member.last_name,
            Member.first_name,
        )

        # Get total count
        count_query = select(func.count(DuesPayment.id)).join(Member).join(DuesPeriod)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = self.db.execute(count_query).scalar() or 0

        # Apply pagination
        query = query.offset(skip).limit(limit)
        payments = list(self.db.execute(query).scalars().all())

        return payments, total

    def get_payment(self, payment_id: int) -> Optional[DuesPayment]:
        """Get single payment by ID."""
        return self.db.get(DuesPayment, payment_id)

    def get_payment_with_details(self, payment_id: int) -> Optional[dict]:
        """Get payment with member and period details."""
        payment = self.get_payment(payment_id)
        if not payment:
            return None

        return {
            "id": payment.id,
            "member": payment.member,
            "period": payment.period,
            "amount_due": payment.amount_due,
            "amount_paid": payment.amount_paid or Decimal("0"),
            "status": payment.status,
            "payment_method": payment.payment_method,
            "payment_date": payment.payment_date,
            "check_number": payment.check_number,
            "notes": payment.notes,
            "balance": payment.amount_due - (payment.amount_paid or Decimal("0")),
        }

    def get_member_payment_history(
        self,
        member_id: int,
        limit: int = 12,
    ) -> list[DuesPayment]:
        """Get recent payment history for a member."""
        payments = self.db.execute(
            select(DuesPayment)
            .join(DuesPeriod)
            .where(DuesPayment.member_id == member_id)
            .order_by(
                DuesPeriod.period_year.desc(),
                DuesPeriod.period_month.desc(),
            )
            .limit(limit)
        ).scalars().all()
        return list(payments)

    def get_unpaid_members_for_period(
        self,
        period_id: int,
        search: Optional[str] = None,
    ) -> list[dict]:
        """Get members with unpaid dues for a period."""
        query = (
            select(DuesPayment)
            .join(Member)
            .where(DuesPayment.period_id == period_id)
            .where(DuesPayment.status.in_([
                DuesPaymentStatus.PENDING,
                DuesPaymentStatus.OVERDUE,
                DuesPaymentStatus.PARTIAL,
            ]))
            .order_by(Member.last_name, Member.first_name)
        )

        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Member.first_name.ilike(search_term)) |
                (Member.last_name.ilike(search_term)) |
                (Member.member_number.ilike(search_term))
            )

        payments = self.db.execute(query).scalars().all()

        return [
            {
                "payment_id": p.id,
                "member_id": p.member_id,
                "member_name": p.member.full_name,
                "member_number": p.member.member_number,
                "amount_due": p.amount_due,
                "amount_paid": p.amount_paid or Decimal("0"),
                "balance": p.amount_due - (p.amount_paid or Decimal("0")),
                "status": p.status,
            }
            for p in payments
        ]

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

## Task 2: Add Payment Routes to Router

**File:** `src/routers/dues_frontend.py` - Add these routes:

```python
from src.services.dues_payment_service import DuesPaymentService
from src.schemas.dues_payment import DuesPaymentRecord

# ─────────────────────────────────────────────────────────────────────
# Payments Management
# ─────────────────────────────────────────────────────────────────────

@router.get("/payments", response_class=HTMLResponse)
async def payments_list(
    request: Request,
    period_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Payments list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)

    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = DuesPaymentStatus(status)
        except ValueError:
            pass

    per_page = 25
    skip = (page - 1) * per_page
    payments, total = service.list_payments(
        period_id=period_id,
        status=status_filter,
        search=q,
        skip=skip,
        limit=per_page,
    )

    total_pages = (total + per_page - 1) // per_page

    # Get periods for filter dropdown
    periods, _ = service.list_periods(limit=24)

    return templates.TemplateResponse(
        "dues/payments/index.html",
        {
            "request": request,
            "user": current_user,
            "payments": payments,
            "periods": periods,
            "statuses": list(DuesPaymentStatus),
            "payment_methods": list(DuesPaymentMethod),
            "selected_period": period_id,
            "selected_status": status,
            "search_query": q,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "service": service,
        },
    )


@router.get("/payments/search", response_class=HTMLResponse)
async def payments_search(
    request: Request,
    period_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """HTMX endpoint for payments table."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)

    status_filter = None
    if status:
        try:
            status_filter = DuesPaymentStatus(status)
        except ValueError:
            pass

    per_page = 25
    skip = (page - 1) * per_page
    payments, total = service.list_payments(
        period_id=period_id,
        status=status_filter,
        search=q,
        skip=skip,
        limit=per_page,
    )

    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        "dues/payments/partials/_table.html",
        {
            "request": request,
            "payments": payments,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "service": service,
        },
    )


@router.get("/payments/{payment_id}/record-modal", response_class=HTMLResponse)
async def payment_record_modal(
    request: Request,
    payment_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get record payment modal content."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)
    payment = service.get_payment_with_details(payment_id)

    if not payment:
        return HTMLResponse("<div class='alert alert-error'>Payment not found</div>")

    return templates.TemplateResponse(
        "dues/payments/partials/_record_modal.html",
        {
            "request": request,
            "payment": payment,
            "payment_methods": list(DuesPaymentMethod),
            "service": service,
        },
    )


@router.post("/payments/{payment_id}/record", response_class=HTMLResponse)
async def payment_record(
    request: Request,
    payment_id: int,
    amount_paid: str = Form(...),
    payment_method: str = Form(...),
    payment_date: Optional[str] = Form(None),
    check_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Record a payment."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    try:
        payment_service = DuesPaymentService(db)
        record_data = DuesPaymentRecord(
            amount_paid=Decimal(amount_paid),
            payment_method=DuesPaymentMethod(payment_method),
            payment_date=date.fromisoformat(payment_date) if payment_date else date.today(),
            check_number=check_number if check_number else None,
            notes=notes if notes else None,
        )
        payment_service.record_payment(payment_id, record_data)
        db.commit()

        return HTMLResponse(
            '<div class="alert alert-success" hx-swap-oob="true" id="flash-message">'
            '<span>Payment recorded successfully</span></div>',
            headers={"HX-Trigger": "paymentsUpdated"},
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400,
        )


@router.post("/payments/update-overdue", response_class=HTMLResponse)
async def payments_update_overdue(
    request: Request,
    period_id: Optional[int] = Form(None),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Batch update overdue payments."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    try:
        payment_service = DuesPaymentService(db)
        count = payment_service.update_overdue_payments(period_id)
        db.commit()

        return HTMLResponse(
            f'<div class="alert alert-success" hx-swap-oob="true" id="flash-message">'
            f'<span>Updated {count} payment(s) to overdue status</span></div>',
            headers={"HX-Trigger": "paymentsUpdated"},
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400,
        )


@router.get("/payments/member/{member_id}", response_class=HTMLResponse)
async def member_payment_history(
    request: Request,
    member_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Get member's payment history (HTMX partial)."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DuesFrontendService(db)
    payments = service.get_member_payment_history(member_id, limit=12)

    return templates.TemplateResponse(
        "dues/payments/partials/_member_history.html",
        {
            "request": request,
            "payments": payments,
            "service": service,
        },
    )
```

---

## Task 3: Create Payments Templates

**File:** `src/templates/dues/payments/index.html`

```html
{% extends "base.html" %}

{% block title %}Dues Payments - IP2A{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs mb-4">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/dues">Dues Management</a></li>
            <li>Payments</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex justify-between items-center mb-6">
        <div>
            <h1 class="text-2xl font-bold">Dues Payments</h1>
            <p class="text-base-content/70">Record and track member dues payments</p>
        </div>
        <button
            class="btn btn-warning btn-sm"
            hx-post="/dues/payments/update-overdue"
            hx-swap="none"
            hx-confirm="Mark all pending payments past grace period as overdue?"
        >
            Update Overdue
        </button>
    </div>

    <!-- Flash Message Container -->
    <div id="flash-message"></div>

    <!-- Filters -->
    <div class="card bg-base-100 shadow mb-6">
        <div class="card-body py-4">
            <div class="flex flex-wrap gap-4 items-end">
                <!-- Search -->
                <div class="form-control flex-1 min-w-[200px]">
                    <label class="label">
                        <span class="label-text">Search</span>
                    </label>
                    <input
                        type="search"
                        name="q"
                        value="{{ search_query or '' }}"
                        placeholder="Member name or number..."
                        class="input input-bordered input-sm"
                        hx-get="/dues/payments/search"
                        hx-trigger="input changed delay:300ms, search"
                        hx-target="#payments-table"
                        hx-include="[name='period_id'], [name='status']"
                    />
                </div>

                <!-- Period Filter -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Period</span>
                    </label>
                    <select
                        name="period_id"
                        class="select select-bordered select-sm w-40"
                        hx-get="/dues/payments/search"
                        hx-target="#payments-table"
                        hx-include="[name='q'], [name='status']"
                    >
                        <option value="">All Periods</option>
                        {% for period in periods %}
                        <option value="{{ period.id }}" {% if selected_period == period.id %}selected{% endif %}>
                            {{ period.period_year }}-{{ '%02d' | format(period.period_month) }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Status Filter -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Status</span>
                    </label>
                    <select
                        name="status"
                        class="select select-bordered select-sm w-32"
                        hx-get="/dues/payments/search"
                        hx-target="#payments-table"
                        hx-include="[name='q'], [name='period_id']"
                    >
                        <option value="">All Status</option>
                        {% for s in statuses %}
                        <option value="{{ s.value }}" {% if selected_status == s.value %}selected{% endif %}>
                            {{ s.value | title }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <div class="text-sm text-base-content/70 self-end pb-2">
                    {{ total }} payment{% if total != 1 %}s{% endif %}
                </div>
            </div>
        </div>
    </div>

    <!-- Payments Table -->
    <div id="payments-table" hx-trigger="paymentsUpdated from:body" hx-get="/dues/payments/search" hx-include="[name='q'], [name='period_id'], [name='status']">
        {% include "dues/payments/partials/_table.html" %}
    </div>
</div>

<!-- Payment Modal -->
<dialog id="payment-modal" class="modal">
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

**File:** `src/templates/dues/payments/partials/_table.html`

```html
<div class="card bg-base-100 shadow">
    <div class="card-body p-0">
        <div class="overflow-x-auto">
            <table class="table">
                <thead>
                    <tr>
                        <th>Member</th>
                        <th>Period</th>
                        <th>Amount Due</th>
                        <th>Amount Paid</th>
                        <th>Status</th>
                        <th>Payment Date</th>
                        <th>Method</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for payment in payments %}
                    <tr class="hover" id="payment-row-{{ payment.id }}">
                        <td>
                            <div class="font-medium">{{ payment.member.full_name }}</div>
                            <div class="text-xs text-base-content/50">{{ payment.member.member_number }}</div>
                        </td>
                        <td>
                            <a href="/dues/periods/{{ payment.period_id }}" class="link link-hover">
                                {{ payment.period.period_year }}-{{ '%02d' | format(payment.period.period_month) }}
                            </a>
                        </td>
                        <td class="font-mono">${{ "%.2f" | format(payment.amount_due) }}</td>
                        <td class="font-mono">
                            {% if payment.amount_paid %}
                            ${{ "%.2f" | format(payment.amount_paid) }}
                            {% else %}
                            <span class="text-base-content/50">—</span>
                            {% endif %}
                        </td>
                        <td>
                            <span class="badge {{ service.get_payment_status_badge_class(payment.status) }} badge-sm">
                                {{ payment.status.value | title }}
                            </span>
                        </td>
                        <td>
                            {% if payment.payment_date %}
                            {{ payment.payment_date.strftime('%b %d, %Y') }}
                            {% else %}
                            <span class="text-base-content/50">—</span>
                            {% endif %}
                        </td>
                        <td>
                            {{ service.get_payment_method_display(payment.payment_method) }}
                        </td>
                        <td>
                            {% if payment.status != 'paid' and payment.status != 'waived' %}
                            <button
                                class="btn btn-primary btn-xs"
                                hx-get="/dues/payments/{{ payment.id }}/record-modal"
                                hx-target="#modal-content"
                                hx-swap="innerHTML"
                                onclick="document.getElementById('payment-modal').showModal()"
                            >
                                Record
                            </button>
                            {% else %}
                            <span class="text-success text-sm">✓</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="8" class="text-center py-8 text-base-content/50">
                            No payments found
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
                    hx-get="/dues/payments/search?page={{ page - 1 }}"
                    hx-target="#payments-table"
                    hx-include="[name='q'], [name='period_id'], [name='status']"
                >
                    «
                </button>
                {% endif %}

                <button class="join-item btn btn-sm btn-active">{{ page }}</button>

                {% if page < total_pages %}
                <button
                    class="join-item btn btn-sm"
                    hx-get="/dues/payments/search?page={{ page + 1 }}"
                    hx-target="#payments-table"
                    hx-include="[name='q'], [name='period_id'], [name='status']"
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

**File:** `src/templates/dues/payments/partials/_record_modal.html`

```html
<form hx-post="/dues/payments/{{ payment.id }}/record" hx-swap="none">
    <h3 class="font-bold text-lg mb-4">Record Payment</h3>

    <!-- Member Info -->
    <div class="bg-base-200 rounded-lg p-4 mb-4">
        <div class="flex justify-between items-start">
            <div>
                <div class="font-medium">{{ payment.member.full_name }}</div>
                <div class="text-sm text-base-content/70">{{ payment.member.member_number }}</div>
            </div>
            <div class="text-right">
                <div class="text-sm text-base-content/70">Period</div>
                <div class="font-medium">
                    {{ payment.period.period_year }}-{{ '%02d' | format(payment.period.period_month) }}
                </div>
            </div>
        </div>
        <div class="divider my-2"></div>
        <div class="flex justify-between text-sm">
            <span>Amount Due:</span>
            <span class="font-mono font-bold">${{ "%.2f" | format(payment.amount_due) }}</span>
        </div>
        {% if payment.amount_paid > 0 %}
        <div class="flex justify-between text-sm">
            <span>Previously Paid:</span>
            <span class="font-mono">${{ "%.2f" | format(payment.amount_paid) }}</span>
        </div>
        <div class="flex justify-between text-sm text-error">
            <span>Balance:</span>
            <span class="font-mono font-bold">${{ "%.2f" | format(payment.balance) }}</span>
        </div>
        {% endif %}
    </div>

    <!-- Amount -->
    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Amount Paid ($)</span>
        </label>
        <input
            type="number"
            name="amount_paid"
            step="0.01"
            min="0.01"
            max="{{ payment.balance }}"
            value="{{ "%.2f" | format(payment.balance) }}"
            class="input input-bordered"
            required
        />
        <label class="label">
            <span class="label-text-alt">Balance: ${{ "%.2f" | format(payment.balance) }}</span>
        </label>
    </div>

    <!-- Payment Method -->
    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Payment Method</span>
        </label>
        <select name="payment_method" class="select select-bordered" required>
            <option value="">Select Method</option>
            {% for method in payment_methods %}
            <option value="{{ method.value }}">{{ service.get_payment_method_display(method) }}</option>
            {% endfor %}
        </select>
    </div>

    <!-- Payment Date -->
    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Payment Date</span>
        </label>
        <input
            type="date"
            name="payment_date"
            value="{{ today().isoformat() if today else '' }}"
            class="input input-bordered"
        />
        <label class="label">
            <span class="label-text-alt">Leave blank for today</span>
        </label>
    </div>

    <!-- Check Number (conditional) -->
    <div class="form-control mb-4" x-data="{ showCheck: false }" x-init="$watch('$el.closest('form').querySelector('[name=payment_method]').value', val => showCheck = val === 'check')">
        <div x-show="showCheck" x-transition>
            <label class="label">
                <span class="label-text">Check Number</span>
            </label>
            <input
                type="text"
                name="check_number"
                class="input input-bordered"
                placeholder="Optional"
            />
        </div>
    </div>

    <!-- Notes -->
    <div class="form-control mb-4">
        <label class="label">
            <span class="label-text">Notes (optional)</span>
        </label>
        <textarea
            name="notes"
            class="textarea textarea-bordered"
            placeholder="Payment notes..."
            rows="2"
        ></textarea>
    </div>

    <div class="modal-action">
        <button type="button" class="btn" onclick="document.getElementById('payment-modal').close()">
            Cancel
        </button>
        <button type="submit" class="btn btn-primary">
            Record Payment
        </button>
    </div>
</form>

<script>
// Show/hide check number field based on payment method
document.querySelector('[name="payment_method"]').addEventListener('change', function() {
    const checkField = document.querySelector('[name="check_number"]').closest('.form-control > div');
    if (checkField) {
        checkField.style.display = this.value === 'check' ? 'block' : 'none';
    }
});
</script>
```

**File:** `src/templates/dues/payments/partials/_member_history.html`

```html
<!-- Member payment history partial (for use in member detail pages) -->
<div class="overflow-x-auto">
    <table class="table table-sm">
        <thead>
            <tr>
                <th>Period</th>
                <th>Due</th>
                <th>Paid</th>
                <th>Status</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody>
            {% for payment in payments %}
            <tr>
                <td>{{ payment.period.period_year }}-{{ '%02d' | format(payment.period.period_month) }}</td>
                <td class="font-mono">${{ "%.2f" | format(payment.amount_due) }}</td>
                <td class="font-mono">
                    {% if payment.amount_paid %}
                    ${{ "%.2f" | format(payment.amount_paid) }}
                    {% else %}
                    —
                    {% endif %}
                </td>
                <td>
                    <span class="badge {{ service.get_payment_status_badge_class(payment.status) }} badge-xs">
                        {{ payment.status.value | title }}
                    </span>
                </td>
                <td>
                    {% if payment.payment_date %}
                    {{ payment.payment_date.strftime('%m/%d/%y') }}
                    {% else %}
                    —
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="5" class="text-center text-base-content/50">
                    No payment history
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

---

## Verification

```bash
# Run tests
pytest -v --tb=short

# Test manually
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints:
# - http://localhost:8000/dues/payments
# - http://localhost:8000/dues/payments?period_id=1
# - http://localhost:8000/dues/payments?status=pending
# - Record payment modal
# - Update overdue button
```

---

## Session Commit

```bash
git add -A
git commit -m "feat(dues-ui): Week 7 Session C - Payments interface"
git push origin main
```

---

## Next Session

Session D will implement:
- Adjustments list page
- Pending adjustments queue
- Approve/deny workflow
- Adjustment detail
- Comprehensive tests (20+)
- ADR-011 (if needed)
- Documentation updates

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
