# Dues Tracking Guide

> **Document Created:** January 27, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.1
> **Status:** Active — Implementation Guide
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Overview

The dues tracking system manages member financial obligations through four interconnected components. This module was implemented as Phase 4 (backend, Weeks 10–11) with the frontend delivered in Phase 6 Week 10. Payment processing via Stripe was integrated in Week 16.

| Component | Status | Phase |
|-----------|--------|-------|
| **Dues Rates** — Classification-based pricing | ✅ Complete | Phase 4 |
| **Dues Periods** — Monthly billing cycles | ✅ Complete | Phase 4 |
| **Dues Payments** — Payment records and tracking | ✅ Complete | Phase 4 |
| **Dues Adjustments** — Waivers, credits, corrections | ✅ Complete | Phase 4 |
| **Stripe Integration** — Online payment processing | ✅ Complete | Phase 6 Week 16 |
| **Frontend UI** — Full management interface | ✅ Complete | Phase 6 Week 10 |

---

## Quick Start

### 1. Set Up Rates

Before tracking payments, establish rates for each member classification:

```python
# Seed data creates default rates
from src.seed.dues_seed import seed_dues_rates

# Or via API
POST /dues-rates/
{
    "classification": "journeyman",
    "monthly_amount": "75.00",
    "effective_date": "2026-01-01",
    "description": "Standard journeyman rate"
}
```

**Default Rate Schedule:**

| Classification | Monthly Amount |
|---------------|----------------|
| apprentice_1  | $35.00 |
| apprentice_2  | $40.00 |
| apprentice_3  | $45.00 |
| apprentice_4  | $50.00 |
| apprentice_5  | $55.00 |
| journeyman    | $75.00 |
| foreman       | $85.00 |
| retiree       | $25.00 |
| honorary      | $0.00 |

### 2. Create Billing Periods

Generate monthly billing periods:

```python
# Generate all 12 periods for a year
POST /dues-periods/generate/2026

# Or create individual periods
POST /dues-periods/
{
    "period_year": 2026,
    "period_month": 1,
    "due_date": "2026-01-01",
    "grace_period_end": "2026-01-15"
}
```

### 3. Record Payments

Create payment records for members:

```python
# Create payment record
POST /dues-payments/
{
    "member_id": 123,
    "period_id": 1,
    "amount_due": "75.00"
}

# Record actual payment
POST /dues-payments/{payment_id}/record
{
    "amount_paid": "75.00",
    "payment_method": "check",
    "check_number": "1234"
}
```

Online payments are processed via Stripe Checkout Sessions. When a member pays online, the Stripe webhook automatically records the payment and updates the status. See [ADR-009](../decisions/ADR-009-payment-processing.md) for the Stripe integration architecture.

### 4. Handle Adjustments

Process waivers and credits:

```python
# Request adjustment
POST /dues-adjustments/
{
    "member_id": 123,
    "adjustment_type": "hardship",
    "amount": "-25.00",
    "reason": "Financial hardship - reduced rate requested"
}

# Approve adjustment
POST /dues-adjustments/{id}/approve
{
    "approved": true,
    "approved_by_id": 1
}
```

---

## Data Models

### DuesRate

Defines monthly dues amounts by member classification.

```python
class DuesRate:
    id: int
    classification: MemberClassification  # apprentice_1, journeyman, etc.
    monthly_amount: Decimal              # e.g., 75.00
    effective_date: date                 # When rate becomes active
    end_date: Optional[date]             # When rate expires (null = current)
    description: Optional[str]           # Rate description
```

**Key Features:**

- Unique constraint on (classification, effective_date)
- Historical rates preserved with end_date
- Get current rate: `GET /dues-rates/current/{classification}`
- Get rate for specific date: `GET /dues-rates/for-date/{classification}?target_date=2026-01-15`

### DuesPeriod

Represents a monthly billing cycle.

```python
class DuesPeriod:
    id: int
    period_year: int                     # 2026
    period_month: int                    # 1-12
    due_date: date                       # Payment due date
    grace_period_end: date               # End of grace period
    is_closed: bool                      # Period closed for modifications
    closed_at: Optional[datetime]        # When closed
    closed_by_id: Optional[int]          # Who closed it
```

**Key Features:**

- Unique constraint on (period_year, period_month)
- Generate entire year: `POST /dues-periods/generate/{year}`
- Close period: `POST /dues-periods/{id}/close`
- Get by month: `GET /dues-periods/by-month/{year}/{month}`

### DuesPayment

Tracks member payment records.

```python
class DuesPayment:
    id: int
    member_id: int                       # FK to members
    period_id: int                       # FK to dues_periods
    amount_due: Decimal                  # Amount owed
    amount_paid: Decimal                 # Amount received (default 0)
    status: DuesPaymentStatus            # pending, paid, partial, overdue, waived
    payment_method: Optional[DuesPaymentMethod]
    payment_date: Optional[date]
    check_number: Optional[str]
    notes: Optional[str]
```

**Payment Statuses:**

| Status | Description |
|--------|-------------|
| pending | Payment not yet received |
| paid | Full payment received |
| partial | Partial payment received |
| overdue | Past grace period, unpaid |
| waived | Payment waived via adjustment |

**Key Features:**

- Unique constraint on (member_id, period_id)
- Record payment: `POST /dues-payments/{id}/record`
- Update overdue: `POST /dues-payments/update-overdue`
- Member summary: `GET /dues-payments/member/{member_id}/summary`

### DuesAdjustment

Handles waivers, credits, and corrections.

```python
class DuesAdjustment:
    id: int
    member_id: int                       # FK to members
    payment_id: Optional[int]            # FK to specific payment (optional)
    adjustment_type: DuesAdjustmentType  # waiver, credit, hardship, correction
    amount: Decimal                      # Positive = credit, Negative = charge
    reason: str                          # Justification
    status: AdjustmentStatus             # pending, approved, denied
    requested_by_id: Optional[int]       # Who requested
    approved_by_id: Optional[int]        # Who approved/denied
    approved_at: Optional[datetime]      # When approved/denied
```

**Adjustment Types:**

| Type | Description |
|------|-------------|
| waiver | Full or partial dues waiver |
| credit | Credit from overpayment |
| hardship | Reduced rate for financial hardship |
| correction | Billing error correction |
| other | Other adjustment |

**Approval Workflow:**

1. Create adjustment (status = `pending`)
2. Review pending: `GET /dues-adjustments/pending`
3. Approve: `POST /dues-adjustments/{id}/approve` with `{"approved": true}`
4. Or deny: `POST /dues-adjustments/{id}/approve` with `{"approved": false}`

---

## Common Workflows

### Monthly Billing Cycle

```bash
# 1. Ensure period exists
POST /dues-periods/
{"period_year": 2026, "period_month": 2, "due_date": "2026-02-01", "grace_period_end": "2026-02-15"}

# 2. Generate dues for all members (if batch endpoint exists)
# Or create individual payment records

# 3. After grace period, mark overdue
POST /dues-payments/update-overdue

# 4. Close period when complete
POST /dues-periods/{id}/close
{"closed_by_id": 1}
```

### Processing a Hardship Request

```bash
# 1. Member requests hardship reduction
POST /dues-adjustments/
{
    "member_id": 123,
    "adjustment_type": "hardship",
    "amount": "-50.00",
    "reason": "Unemployment - requesting 50% reduction"
}

# 2. Officer reviews pending adjustments
GET /dues-adjustments/pending

# 3. Approve the request
POST /dues-adjustments/{id}/approve
{
    "approved": true,
    "approved_by_id": 1,
    "notes": "Approved for 6 months per policy"
}
```

### Rate Change

```bash
# 1. Create new rate with future effective date
POST /dues-rates/
{
    "classification": "journeyman",
    "monthly_amount": "80.00",
    "effective_date": "2027-01-01",
    "description": "2027 rate increase"
}

# 2. Optionally set end date on current rate
PUT /dues-rates/{current_rate_id}
{
    "end_date": "2026-12-31"
}
```

---

## API Reference

See [docs/reference/dues-api.md](../reference/dues-api.md) for complete API documentation.

---

## Testing

Run dues tests:

```bash
pytest src/tests/test_dues.py -v
```

The test suite covers:

- Rate CRUD with unique date handling
- Period management with year/month uniqueness
- Payment lifecycle (pending → paid/partial/overdue/waived)
- Adjustment approval workflow
- Stripe webhook processing

---

## Frontend Usage (Phase 6 Week 10)

The dues management frontend provides a complete UI for managing all dues operations, built with Jinja2 + HTMX + Alpine.js + DaisyUI.

### Accessing the Dues Module

Navigate to `/dues` from the main dashboard or sidebar menu.

### Landing Page (`/dues`)

- Current period display with days until due
- Stats cards: MTD collected, YTD collected, overdue count, pending adjustments
- Quick action cards linking to submodules

### Rates Management (`/dues/rates`)

- List all rates by classification
- Filter by classification type
- Toggle to show only active rates
- View rate history with effective dates

### Periods Management (`/dues/periods`)

- List all billing periods by year
- Filter by year and status (open/closed)
- Generate 12 periods for a year via modal
- View period details with payment summary
- Close periods with notes

### Payments (`/dues/payments`)

- Search payments by member name or number
- Filter by period and status
- Record payments via modal (amount, method, check number, notes)
- View member payment history with balance summary
- Online payments processed via Stripe Checkout Sessions

### Adjustments (`/dues/adjustments`)

- List all adjustments with status/type filters
- View adjustment details
- Approve or deny pending adjustments via modal
- Add review notes

### Frontend Architecture

See [ADR-011: Dues Frontend Patterns](../decisions/ADR-011-dues-frontend-patterns.md) for implementation details. The frontend follows the project-wide patterns established in [ADR-010: Frontend Architecture](../decisions/ADR-010-frontend-architecture.md).

---

## Related Documentation

| Document | Location |
|----------|----------|
| ADR-008: Dues Tracking System Design | `/docs/decisions/ADR-008-dues-tracking-system.md` |
| ADR-009: Payment Processing (Stripe) | `/docs/decisions/ADR-009-payment-processing.md` |
| ADR-011: Dues Frontend Patterns | `/docs/decisions/ADR-011-dues-frontend-patterns.md` |
| API Reference | `/docs/reference/dues-api.md` |
| CHANGELOG | `/CHANGELOG.md` — Phase 4 (backend) and Phase 6 Week 10 (frontend) |
| Coding Standards | `/docs/standards/coding-standards.md` |

---

> **End-of-Session Rule:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

*Document Version: 1.1*
*Last Updated: February 3, 2026*
