# Dues Tracking API Reference

> **Document Created:** January 28, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.1
> **Status:** Active — Implemented (Phase 4)
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)
> **Related ADRs:** [ADR-009](../decisions/ADR-009-dues-tracking-system.md)

Quick reference for Phase 4 Dues Tracking API endpoints.

> **Context:** All endpoints are served via Flask Blueprints. The dues system integrates
> with Stripe for payment processing (Checkout Sessions + Webhooks). See the
> [Dues Tracking Guide](../guides/dues-tracking.md) for business logic and workflows.

---

## Dues Rates

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/dues-rates/` | Create new rate |
| GET | `/dues-rates/` | List all rates |
| GET | `/dues-rates/{id}` | Get rate by ID |
| GET | `/dues-rates/current/{classification}` | Get current active rate |
| GET | `/dues-rates/for-date/{classification}?target_date=` | Get rate for specific date |
| PUT | `/dues-rates/{id}` | Update rate |
| DELETE | `/dues-rates/{id}` | Delete rate |

### Create Rate
```bash
POST /dues-rates/
Content-Type: application/json

{
    "classification": "journeyman",  # Required: apprentice_1-5, journeyman, foreman, retiree, honorary
    "monthly_amount": "75.00",       # Required: Decimal string
    "effective_date": "2026-01-01",  # Required: YYYY-MM-DD
    "end_date": null,                # Optional: YYYY-MM-DD
    "description": "Standard rate"   # Optional
}
```

### Get Current Rate
```bash
GET /dues-rates/current/journeyman
# Returns the active rate for the classification (effective_date <= today, no end_date or end_date >= today)
```

---

## Dues Periods

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/dues-periods/` | Create new period |
| POST | `/dues-periods/generate/{year}` | Generate all 12 periods for year |
| GET | `/dues-periods/` | List all periods |
| GET | `/dues-periods/{id}` | Get period by ID |
| GET | `/dues-periods/current` | Get current open period |
| GET | `/dues-periods/by-month/{year}/{month}` | Get period by year/month |
| PUT | `/dues-periods/{id}` | Update period |
| POST | `/dues-periods/{id}/close` | Close a period |

### Create Period
```bash
POST /dues-periods/
Content-Type: application/json

{
    "period_year": 2026,              # Required: int
    "period_month": 1,                # Required: 1-12
    "due_date": "2026-01-01",         # Required: YYYY-MM-DD
    "grace_period_end": "2026-01-15"  # Required: YYYY-MM-DD
}
```

### Generate Year
```bash
POST /dues-periods/generate/2026
# Creates 12 periods for the year with default due dates (1st) and grace periods (15th)
```

### Close Period
```bash
POST /dues-periods/{id}/close
Content-Type: application/json

{
    "closed_by_id": 1,  # Optional: User ID who closed
    "notes": "..."      # Optional: Close notes
}
```

---

## Dues Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/dues-payments/` | Create payment record |
| GET | `/dues-payments/` | List all payments |
| GET | `/dues-payments/{id}` | Get payment by ID |
| GET | `/dues-payments/member/{member_id}` | Get member's payments |
| GET | `/dues-payments/period/{period_id}` | Get period's payments |
| GET | `/dues-payments/member/{member_id}/summary` | Get member dues summary |
| PUT | `/dues-payments/{id}` | Update payment |
| POST | `/dues-payments/{id}/record` | Record payment received |
| POST | `/dues-payments/update-overdue` | Batch update overdue status |
| DELETE | `/dues-payments/{id}` | Delete payment |

### Create Payment Record
```bash
POST /dues-payments/
Content-Type: application/json

{
    "member_id": 123,       # Required: FK to members
    "period_id": 1,         # Required: FK to dues_periods
    "amount_due": "75.00"   # Required: Decimal string
}
```

### Record Payment
```bash
POST /dues-payments/{id}/record
Content-Type: application/json

{
    "amount_paid": "75.00",        # Required
    "payment_method": "check",     # Optional: cash, check, credit_card, debit_card, bank_transfer, payroll_deduction
    "payment_date": "2026-01-10",  # Optional: defaults to today
    "check_number": "1234",        # Optional
    "notes": "..."                 # Optional
}
```

> **Stripe Integration:** Online payments processed via Stripe Checkout Sessions
> create payment records automatically via webhook callbacks. Manual payment recording
> (above) is for in-person transactions (cash, check, etc.).

### Payment Statuses
| Status | Description |
|--------|-------------|
| `pending` | Not yet paid |
| `paid` | Fully paid (amount_paid >= amount_due) |
| `partial` | Partially paid (0 < amount_paid < amount_due) |
| `overdue` | Past grace period, not fully paid |
| `waived` | Waived via adjustment |

---

## Dues Adjustments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/dues-adjustments/` | Create adjustment request |
| GET | `/dues-adjustments/` | List all adjustments |
| GET | `/dues-adjustments/pending` | List pending adjustments |
| GET | `/dues-adjustments/{id}` | Get adjustment by ID |
| GET | `/dues-adjustments/member/{member_id}` | Get member's adjustments |
| POST | `/dues-adjustments/{id}/approve` | Approve or deny adjustment |
| DELETE | `/dues-adjustments/{id}` | Delete pending adjustment |

### Create Adjustment
```bash
POST /dues-adjustments/
Content-Type: application/json

{
    "member_id": 123,            # Required: FK to members
    "payment_id": null,          # Optional: FK to specific payment
    "adjustment_type": "waiver", # Required: waiver, credit, hardship, correction, other
    "amount": "-25.00",          # Required: Positive = credit to member, Negative = charge
    "reason": "Hardship request" # Required: Justification text
}
# Note: requested_by_id is passed as query param, not in body
```

### Approve/Deny Adjustment
```bash
POST /dues-adjustments/{id}/approve
Content-Type: application/json

{
    "approved": true,       # Required: true = approve, false = deny
    "approved_by_id": 1,    # Optional: User ID who approved/denied
    "notes": "..."          # Optional: Approval notes
}
```

### Adjustment Types
| Type | Description |
|------|-------------|
| `waiver` | Full or partial dues waiver |
| `credit` | Credit from overpayment |
| `hardship` | Reduced rate for financial hardship |
| `correction` | Billing error correction |
| `other` | Other adjustment type |

### Adjustment Statuses
| Status | Description |
|--------|-------------|
| `pending` | Awaiting approval |
| `approved` | Approved by authorized user |
| `denied` | Denied by authorized user |

---

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (validation error) |
| 404 | Not found |
| 409 | Conflict (unique constraint violation) |
| 422 | Unprocessable entity (validation error) |

## Query Parameters

### List Endpoints
Most list endpoints support:
- `skip` — Offset for pagination (default: 0)
- `limit` — Max results (default: 100)

### Rates List
- `classification` — Filter by classification
- `active_only` — If true, only current rates

### Periods List
- `year` — Filter by year
- `is_closed` — Filter by closed status

---

## Cross-References

| Document | Location |
|----------|----------|
| Dues Tracking Guide | `/docs/guides/dues-tracking.md` |
| ADR-009: Dues Tracking System | `/docs/decisions/ADR-009-dues-tracking-system.md` |
| Audit API Reference | `/docs/reference/audit-api.md` |
| Phase 2 Quick Reference | `/docs/reference/phase2-quick-reference.md` |
| Stripe Integration | See ADR-009 for webhook flow |

---

## 📄 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

---

*Document Version: 1.1*
*Last Updated: February 3, 2026*
