# ADR-011: Dues Frontend Patterns

## Status
Accepted

## Date
January 2026

## Context
The dues management module required consistent UI patterns across four related areas:
- Rates management (configuration)
- Periods management (billing cycles)
- Payments tracking (transactions)
- Adjustments workflow (approvals)

Each area has different interaction patterns but needed visual consistency with the rest of the application.

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

## Consequences

### Benefits
- Consistent UX across all dues submodules
- Modal workflows reduce page loads
- Clear visual status indicators
- Reusable badge and formatting helpers

### Tradeoffs
- Service file is large (~400 lines)
- Multiple modal definitions in templates
- More complex template partials

### Alternatives Considered
1. **Separate pages for each action** - Rejected, too many page loads
2. **Client-side only modals** - Rejected, need server validation
3. **Inline editing** - Rejected, too complex for financial data

## Related ADRs
- ADR-002: Frontend Stack (HTMX + DaisyUI)
- ADR-008: Dues Tracking System Design
- ADR-010: Operations Frontend Patterns

## Files Created
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
