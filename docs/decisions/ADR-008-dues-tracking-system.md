# ADR-008: Dues Tracking System Design

## Status
**Accepted** - January 28, 2026

## Context

The IP2A system requires a comprehensive dues tracking system to manage member financial obligations. Union members pay monthly dues based on their classification (apprentice levels, journeyman, foreman, retiree, honorary). The system needs to:

1. Track different dues rates by member classification
2. Manage billing periods (monthly)
3. Record payments and track payment status
4. Handle adjustments, waivers, and credits with approval workflows
5. Support multiple payment methods
6. Track overdue payments

## Decision

We will implement a **4-model dues tracking system** with the following architecture:

### Models

1. **DuesRate** - Classification-based rate management
   - Links rate amounts to MemberClassification enum
   - Supports effective dates for rate changes over time
   - Optional end dates for historical rates

2. **DuesPeriod** - Monthly billing period management
   - Year/month unique constraint
   - Due date and grace period tracking
   - Period close functionality with audit trail

3. **DuesPayment** - Payment record tracking
   - Links members to periods
   - Tracks amount due, paid, and balance
   - Payment status workflow (pending → paid/partial/overdue/waived)
   - Multiple payment method support

4. **DuesAdjustment** - Waivers, credits, and corrections
   - Approval workflow (pending → approved/denied)
   - Links to specific payments (optional)
   - Audit trail for approver and timestamps

### Enums

| Enum | Values | Purpose |
|------|--------|---------|
| DuesPaymentStatus | pending, paid, partial, overdue, waived | Payment state tracking |
| DuesPaymentMethod | cash, check, credit_card, debit_card, bank_transfer, payroll_deduction | Payment type |
| DuesAdjustmentType | waiver, credit, hardship, correction, other | Adjustment categories |
| AdjustmentStatus | pending, approved, denied | Approval workflow states |

### Key Design Decisions

1. **Classification-based rates** rather than flat rates
   - Different member types pay different amounts
   - Apprentices have graduated rates (1-5)
   - Retirees and honorary members have reduced/zero rates

2. **Nullable user references** for testing
   - `requested_by_id` and `approved_by_id` are nullable
   - Allows testing without creating users
   - In production, these would be populated via authentication

3. **Soft approval workflow** for adjustments
   - All adjustments start as "pending"
   - Require explicit approval/denial
   - Stores approver and timestamp for audit

4. **Period-based billing** not continuous
   - Each month is a discrete billing period
   - Supports batch period generation for entire years
   - Periods can be closed to prevent modifications

## Alternatives Considered

### Alternative 1: Single Dues Table
**Rejected** - Would require complex queries for rate lookups and wouldn't support rate history.

### Alternative 2: Invoice-based System
**Rejected** - Over-engineered for monthly union dues. Invoice systems are better suited for variable billing amounts.

### Alternative 3: Subscription Model
**Rejected** - Subscription patterns assume recurring automated billing. Union dues are often paid via check or payroll deduction with manual recording.

## Consequences

### Positive
- Clear separation of concerns (rates, periods, payments, adjustments)
- Full audit trail for financial transactions
- Flexible rate management with effective dates
- Supports all common payment methods
- Approval workflow provides accountability for adjustments

### Negative
- More tables to maintain (4 vs 1-2)
- Requires period generation before payment recording
- Adjustment workflow adds complexity for simple waivers

### Risks
- **Period collision**: Unique constraint on year/month requires careful handling in tests
- **Rate lookup complexity**: Finding the correct rate for a date requires effective_date filtering

## Implementation

### API Endpoints (~35 total)
- `/dues-rates/` - Rate CRUD, get current/for-date by classification
- `/dues-periods/` - Period CRUD, generate year, close period
- `/dues-payments/` - Payment CRUD, record payment, update overdue
- `/dues-adjustments/` - Adjustment CRUD, approve/deny workflow

### Database Schema
```
dues_rates (id, classification, monthly_amount, effective_date, end_date, description)
dues_periods (id, period_year, period_month, due_date, grace_period_end, is_closed, closed_at, closed_by_id)
dues_payments (id, member_id, period_id, amount_due, amount_paid, status, payment_method, payment_date, notes)
dues_adjustments (id, member_id, payment_id, adjustment_type, amount, reason, requested_by_id, approved_by_id, approved_at, status)
```

### Test Coverage
- 21 tests covering all CRUD operations
- Rate creation with unique effective dates
- Period management with year/month uniqueness
- Payment lifecycle (create, record payment, update overdue)
- Adjustment approval workflow (create, approve, deny, delete)

## References
- [CHANGELOG.md](../../CHANGELOG.md) - Phase 4 changes
- [docs/guides/dues-tracking.md](../guides/dues-tracking.md) - Implementation guide
- [src/models/dues_*.py](../../src/models/) - Model implementations
