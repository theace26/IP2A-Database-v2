# Dues Tracking Guide

This guide covers the implementation and usage of the Phase 4 Dues Tracking System.

## Overview

The dues tracking system manages member financial obligations through four interconnected components:

1. **Dues Rates** - Classification-based pricing
2. **Dues Periods** - Monthly billing cycles
3. **Dues Payments** - Payment records and tracking
4. **Dues Adjustments** - Waivers, credits, and corrections

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

## API Reference

See [docs/reference/dues-api.md](../reference/dues-api.md) for complete API documentation.

## Testing

Run dues tests:

```bash
pytest src/tests/test_dues.py -v
```

The test suite covers:
- Rate CRUD with unique date handling
- Period management with year/month uniqueness
- Payment lifecycle
- Adjustment approval workflow

## Related Documentation

- [ADR-008: Dues Tracking System Design](../decisions/ADR-008-dues-tracking-system.md)
- [API Reference](../reference/dues-api.md)
- [CHANGELOG](../../CHANGELOG.md) - Phase 4 changes
