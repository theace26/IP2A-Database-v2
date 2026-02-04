# ADR-008: Dues Tracking System Design

> **Document Created:** 2026-01-28
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented — 4-model dues system live with Stripe payment integration

## Status
**Implemented** — January 28–30, 2026 (Weeks 10–11). Stripe online payments added in Week 11 (ADR-013).

## Context

The IP2A system requires a comprehensive dues tracking system to manage member financial obligations. Union members pay monthly dues based on their classification (apprentice levels, journeyman, foreman, retiree, honorary). The system needs to:

1. Track different dues rates by member classification
2. Manage billing periods (monthly)
3. Record payments and track payment status
4. Handle adjustments, waivers, and credits with approval workflows
5. Support multiple payment methods (including online via Stripe)
6. Track overdue payments

## Decision

We will implement a **4-model dues tracking system** with the following architecture:

### Models

1. **DuesRate** — Classification-based rate management
   - Links rate amounts to MemberClassification enum
   - Supports effective dates for rate changes over time
   - Optional end dates for historical rates

2. **DuesPeriod** — Monthly billing period management
   - Year/month unique constraint
   - Due date and grace period tracking
   - Period close functionality with audit trail

3. **DuesPayment** — Payment record tracking
   - Links members to periods
   - Tracks amount due, paid, and balance
   - Payment status workflow (pending → paid/partial/overdue/waived)
   - Multiple payment method support (including Stripe card/ACH)

4. **DuesAdjustment** — Waivers, credits, and corrections
   - Approval workflow (pending → approved/denied)
   - Links to specific payments (optional)
   - Audit trail for approver and timestamps

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| DuesRate model + CRUD + API | ✅ | 10 | Classification-based rate management |
| DuesPeriod model + CRUD + API | ✅ | 10 | Year generation, close period |
| DuesPayment model + CRUD + API | ✅ | 10 | Full payment lifecycle |
| DuesAdjustment model + CRUD + API | ✅ | 10 | Approval workflow |
| Dues enums (4 enums) | ✅ | 10 | `src/db/enums/` |
| Dues frontend UI | ✅ | 10 | Landing page, rates, periods, payments, adjustments (ADR-011) |
| Stripe online payments | ✅ | 11 | Checkout Sessions + webhooks (ADR-013) |
| Audit logging for dues | ✅ | 11 | NLRA-compliant immutable logs (ADR-012) |
| Analytics (dues metrics) | ✅ | 19 | Chart.js dues analytics dashboard |
| 37 dues-specific tests | ✅ | 10 | CRUD, lifecycle, workflow |
| 25 Stripe payment tests | ✅ | 11 | Checkout, webhooks, reconciliation |

### Enums

| Enum | Values | Purpose |
|------|--------|---------|
| DuesPaymentStatus | pending, paid, partial, overdue, waived | Payment state tracking |
| DuesPaymentMethod | cash, check, credit_card, debit_card, bank_transfer, payroll_deduction, stripe_card, stripe_ach | Payment type (extended for Stripe) |
| DuesAdjustmentType | waiver, credit, hardship, correction, other | Adjustment categories |
| AdjustmentStatus | pending, approved, denied | Approval workflow states |

### Key Design Decisions

1. **Classification-based rates** rather than flat rates
   - Different member types pay different amounts
   - Apprentices have graduated rates (1–5)
   - Retirees and honorary members have reduced/zero rates

2. **Nullable user references** for testing
   - `requested_by_id` and `approved_by_id` are nullable
   - Allows testing without creating users
   - In production, these are populated via authentication

3. **Soft approval workflow** for adjustments
   - All adjustments start as "pending"
   - Require explicit approval/denial
   - Stores approver and timestamp for audit

4. **Period-based billing** not continuous
   - Each month is a discrete billing period
   - Supports batch period generation for entire years
   - Periods can be closed to prevent modifications

5. **Stripe integration** (added Week 11)
   - Members can pay online via Stripe Checkout Sessions
   - Webhook confirms payment and creates DuesPayment record
   - ACH bank transfers available at lower fee (0.8% vs 2.9% card)
   - See ADR-013 for full Stripe architecture

## Alternatives Considered

### Alternative 1: Single Dues Table
**Rejected** — Would require complex queries for rate lookups and wouldn't support rate history.

### Alternative 2: Invoice-based System
**Rejected** — Over-engineered for monthly union dues. Invoice systems are better suited for variable billing amounts.

### Alternative 3: Subscription Model
**Rejected** — Subscription patterns assume recurring automated billing. Union dues are often paid via check or payroll deduction with manual recording. (Note: Stripe subscriptions may be added in a future phase for members who prefer auto-pay.)

## Consequences

### Positive
- Clear separation of concerns (rates, periods, payments, adjustments)
- Full audit trail for financial transactions (enhanced by ADR-012)
- Flexible rate management with effective dates
- Supports all common payment methods plus online Stripe payments
- Approval workflow provides accountability for adjustments
- Analytics dashboard provides real-time dues collection visibility (Week 19)

### Negative
- More tables to maintain (4 vs 1–2)
- Requires period generation before payment recording
- Adjustment workflow adds complexity for simple waivers

### Risks
- **Period collision:** Unique constraint on year/month requires careful handling in tests
- **Rate lookup complexity:** Finding the correct rate for a date requires effective_date filtering
- **Stripe fee costs:** 2.9% card / 0.8% ACH — mitigated by promoting ACH option

## API Endpoints (~35 total)
- `/dues-rates/` — Rate CRUD, get current/for-date by classification
- `/dues-periods/` — Period CRUD, generate year, close period
- `/dues-payments/` — Payment CRUD, record payment, update overdue
- `/dues-adjustments/` — Adjustment CRUD, approve/deny workflow

## Database Schema
```
dues_rates (id, classification, monthly_amount, effective_date, end_date, description)
dues_periods (id, period_year, period_month, due_date, grace_period_end, is_closed, closed_at, closed_by_id)
dues_payments (id, member_id, period_id, amount_due, amount_paid, status, payment_method, payment_date, notes)
dues_adjustments (id, member_id, payment_id, adjustment_type, amount, reason, requested_by_id, approved_by_id, approved_at, status)
```

## References
- ADR-011: Dues Frontend Patterns
- ADR-012: Audit Logging Architecture
- ADR-013: Stripe Payment Integration
- [CHANGELOG.md](../../CHANGELOG.md) — Phase 4 and Week 10–11 changes
- [docs/guides/dues-tracking.md](../guides/dues-tracking.md) — Implementation guide
- Models: `src/models/dues_{rate,period,payment,adjustment}.py`
- Services: `src/services/dues_service.py`
- Frontend service: `src/services/dues_frontend_service.py`
- Router: `src/routers/dues.py`
- Frontend router: `src/routers/dues_frontend.py`
- Templates: `src/templates/dues/`
- Tests: `src/tests/test_dues*.py`

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-01-28 — original design with implementation details)
