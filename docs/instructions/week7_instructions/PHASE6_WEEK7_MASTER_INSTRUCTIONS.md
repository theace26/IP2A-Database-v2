# Phase 6 Week 7: Dues Management UI — Master Instructions

**Version:** 0.7.5 → 0.7.6
**Estimated Time:** 8-10 hours (4 sessions)
**Prerequisites:** Phase 6 Week 6 complete, 259 tests passing

---

## Overview

Week 7 implements the Dues Management frontend, providing UI for the Phase 4 backend:
- Dues rates by member classification
- Period management with generate/close workflows
- Payment recording and tracking
- Adjustment approval workflow

This completes the financial tracking vertical slice of the application.

---

## Session Breakdown

| Session | Focus | Duration | New Tests |
|---------|-------|----------|-----------|
| A | Dues Landing + Rates Management | 2-3 hrs | 5 |
| B | Periods Management | 2-3 hrs | 5 |
| C | Payments + Adjustments | 2-3 hrs | 8 |
| D | Tests + Documentation | 2 hrs | 7 |

**Total:** ~25 new tests, bringing frontend tests to ~119

---

## Architecture Decisions

### 1. DuesFrontendService Pattern
Following Week 6's `OperationsFrontendService`, create a single `DuesFrontendService` that handles:
- Stats aggregation for landing page
- Rate lookups with classification grouping
- Period queries with payment summaries
- Payment/adjustment filtering and search

### 2. Modal Workflows
Use Alpine.js modals for:
- Record payment (amount, method, check number)
- Approve/deny adjustment (with notes)
- Close period (confirmation + notes)

### 3. Stats Dashboard Pattern
Landing page mirrors other modules:
- Current period info (name, due date, days remaining)
- Collection stats (MTD, YTD, target %)
- Overdue count with severity badges
- Quick actions for common tasks

### 4. Classification Color Coding
Reuse member classification badge colors for rate display:
```python
CLASSIFICATION_COLORS = {
    "journeyman": "badge-primary",
    "apprentice_1": "badge-secondary",
    "apprentice_2": "badge-secondary",
    "apprentice_3": "badge-secondary",
    "apprentice_4": "badge-secondary",
    "apprentice_5": "badge-secondary",
    "foreman": "badge-accent",
    "retiree": "badge-ghost",
    "honorary": "badge-ghost",
}
```

---

## File Structure

```
src/
├── services/
│   └── dues_frontend_service.py      # NEW: Stats, queries, helpers
├── routers/
│   └── dues_frontend.py              # NEW: All dues UI routes
├── templates/
│   └── dues/
│       ├── index.html                # Landing page
│       ├── rates/
│       │   ├── index.html            # Rates list
│       │   └── partials/
│       │       └── _table.html       # HTMX rates table
│       ├── periods/
│       │   ├── index.html            # Periods list
│       │   ├── detail.html           # Period detail with payments
│       │   └── partials/
│       │       └── _table.html       # HTMX periods table
│       ├── payments/
│       │   ├── index.html            # Payments list (by period or member)
│       │   ├── member.html           # Single member's payment history
│       │   └── partials/
│       │       ├── _table.html       # HTMX payments table
│       │       └── _record_modal.html # Record payment modal
│       └── adjustments/
│           ├── index.html            # Adjustments list
│           ├── detail.html           # Adjustment detail
│           └── partials/
│               ├── _table.html       # HTMX adjustments table
│               └── _approve_modal.html # Approve/deny modal
└── tests/
    └── test_dues_frontend.py         # NEW: ~25 tests
```

---

## API Endpoints Reference

The backend already provides these endpoints (from Phase 4):

### Rates
- `GET /dues-rates/` - List all rates
- `GET /dues-rates/current/{classification}` - Current rate for classification
- `POST /dues-rates/` - Create rate
- `PUT /dues-rates/{id}` - Update rate

### Periods
- `GET /dues-periods/` - List periods
- `GET /dues-periods/current` - Current open period
- `GET /dues-periods/{id}` - Period detail
- `POST /dues-periods/generate/{year}` - Generate 12 periods
- `POST /dues-periods/{id}/close` - Close period

### Payments
- `GET /dues-payments/` - List payments
- `GET /dues-payments/member/{member_id}` - Member's payments
- `GET /dues-payments/period/{period_id}` - Period's payments
- `GET /dues-payments/member/{member_id}/summary` - Member summary
- `POST /dues-payments/{id}/record` - Record payment

### Adjustments
- `GET /dues-adjustments/` - List adjustments
- `GET /dues-adjustments/pending` - Pending only
- `POST /dues-adjustments/{id}/approve` - Approve/deny

---

## Routes to Implement

| Route | Method | Description |
|-------|--------|-------------|
| `/dues` | GET | Landing page with stats |
| `/dues/rates` | GET | Rates list page |
| `/dues/rates/search` | GET | HTMX rates table |
| `/dues/periods` | GET | Periods list page |
| `/dues/periods/search` | GET | HTMX periods table |
| `/dues/periods/{id}` | GET | Period detail |
| `/dues/periods/generate` | POST | Generate year (HTMX) |
| `/dues/periods/{id}/close` | POST | Close period (HTMX) |
| `/dues/payments` | GET | Payments list |
| `/dues/payments/search` | GET | HTMX payments table |
| `/dues/payments/member/{id}` | GET | Member payment history |
| `/dues/payments/{id}/record` | POST | Record payment (HTMX) |
| `/dues/adjustments` | GET | Adjustments list |
| `/dues/adjustments/search` | GET | HTMX adjustments table |
| `/dues/adjustments/{id}` | GET | Adjustment detail |
| `/dues/adjustments/{id}/approve` | POST | Approve/deny (HTMX) |

---

## Sidebar Navigation Update

Add to sidebar under existing items:

```html
<!-- Dues Management -->
<li>
    <details>
        <summary>
            <svg><!-- dollar icon --></svg>
            Dues
        </summary>
        <ul>
            <li><a href="/dues">Overview</a></li>
            <li><a href="/dues/rates">Rates</a></li>
            <li><a href="/dues/periods">Periods</a></li>
            <li><a href="/dues/payments">Payments</a></li>
            <li><a href="/dues/adjustments">Adjustments</a></li>
        </ul>
    </details>
</li>
```

---

## Git Workflow

```bash
# Start of each session
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Verify 259 passing

# After each session
git add -A
git commit -m "feat(dues-ui): [session description]"
git push origin main

# After Session D (week complete)
git tag -a v0.7.6 -m "Phase 6 Week 7: Dues Management UI"
git push origin v0.7.6
```

---

## Success Criteria

After Week 7:
- [ ] Dues landing with live stats
- [ ] Rates list grouped by classification
- [ ] Periods list with generate/close workflows
- [ ] Payment recording with method selection
- [ ] Adjustment approval workflow
- [ ] ~284 total tests (~119 frontend)
- [ ] ADR-011: Dues Frontend Patterns
- [ ] Session log complete
- [ ] v0.7.6 tagged

---

## Session Documents

1. `1-SESSION-A-DUES-LANDING-RATES.md` — Landing page + rates management
2. `2-SESSION-B-PERIODS-MANAGEMENT.md` — Periods list, generate, close
3. `3-SESSION-C-PAYMENTS-ADJUSTMENTS.md` — Payments + adjustments UI
4. `4-SESSION-D-TESTS-DOCUMENTATION.md` — Tests + documentation

---

*Execute sessions in order. Each session builds on the previous.*
