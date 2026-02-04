# ADR-011: Dues Frontend Patterns

> **Document Created:** 2026-01-30
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented — Dues UI patterns established and in production

## Status
Implemented

## Date
January 2026

## Context
The dues management module required consistent UI patterns across four related areas:
- Rates management (configuration)
- Periods management (billing cycles)
- Payments tracking (transactions)
- Adjustments workflow (approvals)

Each area has different interaction patterns but needed visual consistency with the rest of the application, particularly the Operations module patterns established in ADR-010.

## Decision
We established the following patterns for the dues frontend:

### 1. Single Service Pattern
Following ADR-010, a single `DuesFrontendService` handles all dues-related UI logic:
- Stats aggregation for landing page
- Badge class helpers for status visualization
- Currency and date formatting
- Query methods with filtering support

### 2. Landing Page Dashboard
The dues landing page provides:
- Current period prominently displayed with days until due
- Four stat cards (MTD collected, YTD collected, overdue count, pending adjustments)
- Quick action cards linking to submodules
- Consistent with other module landing pages (Members, Training, Operations)

### 3. Modal Workflows
Alpine.js modals used for in-page actions:
- Record Payment: amount, method, check number, notes
- Close Period: confirmation with notes
- Approve/Deny Adjustment: decision selection with notes

Benefits:
- No page navigation for common actions
- Form state managed by Alpine.js
- HTMX submission updates parent table

### 4. Filter Include Pattern
All list pages use consistent HTMX filtering:
```html
<input
    hx-get="/dues/payments/search"
    hx-trigger="input changed delay:300ms"
    hx-target="#table-container"
    hx-include="[name='period_id'], [name='status']"
/>
```

### 5. Status Badge Consistency
Badge colors follow semantic meaning:
- Success (green): paid, approved, active
- Warning (yellow): pending, in grace period
- Error (red): overdue, denied, past grace
- Ghost (gray): waived, closed, expired
- Info (blue): partial, future

### 6. Currency Display
All monetary values:
- Use `format_currency()` helper
- Display with `font-mono` class for alignment
- Color-coded: green for credits, red for debits

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| DuesFrontendService | ✅ | 10 | ~400 lines, 4 submodule support |
| Dues landing page dashboard | ✅ | 10 | Stats cards + quick actions |
| Rates management UI | ✅ | 10 | List with classification display |
| Periods management UI | ✅ | 10 | Detail page, close period modal |
| Payments tracking UI | ✅ | 10 | Record payment modal, member view |
| Adjustments workflow UI | ✅ | 10 | Approve/deny modal, detail page |
| HTMX filter/search (all pages) | ✅ | 10 | Consistent `hx-include` pattern |
| Badge helper methods | ✅ | 10 | Semantic color mapping |
| Currency formatting helpers | ✅ | 10 | `format_currency()` + `font-mono` |
| Stripe "Pay Dues" button | ✅ | 11 | Initiates Checkout Session (ADR-013) |
| Dues analytics charts | ✅ | 19 | Chart.js integration on dashboard |
| 37 dues frontend tests | ✅ | 10 | Full page + partial + modal coverage |

## Consequences

### Benefits
- Consistent UX across all dues submodules
- Modal workflows reduce page loads
- Clear visual status indicators
- Reusable badge and formatting helpers
- Pattern consistency with Operations module (ADR-010)

### Tradeoffs
- Service file is large (~400 lines)
- Multiple modal definitions in templates
- More complex template partials

### Alternatives Considered
1. **Separate pages for each action** — Rejected, too many page loads
2. **Client-side only modals** — Rejected, need server validation
3. **Inline editing** — Rejected, too complex for financial data

## Related ADRs
- ADR-002: Frontend Stack (HTMX + DaisyUI)
- ADR-005: CSS Framework (Tailwind + DaisyUI components)
- ADR-008: Dues Tracking System Design (data model)
- ADR-010: Operations Frontend Patterns (established the combined service pattern)
- ADR-013: Stripe Payment Integration (online payment flow)

## Files

```
src/services/dues_frontend_service.py
src/routers/dues_frontend.py
src/templates/dues/
├── index.html
├── rates/
│   ├── index.html
│   └── partials/_table.html
├── periods/
│   ├── index.html
│   ├── detail.html
│   └── partials/_table.html
├── payments/
│   ├── index.html
│   ├── member.html
│   └── partials/_table.html
└── adjustments/
    ├── index.html
    ├── detail.html
    └── partials/_table.html
src/tests/test_dues_frontend.py
```

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-01-30 — original decision record)
