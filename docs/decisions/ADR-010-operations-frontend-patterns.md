# ADR-010: Union Operations Frontend Patterns

## Status
Accepted

## Date
January 29, 2026

## Context
The union operations module (SALTing, Benevolence, Grievances) required consistent UI patterns across three distinct but related modules. Each module has:
- List pages with search and filters
- Detail pages with comprehensive information
- Status workflows and progress indicators

## Decision
We established the following patterns for the operations frontend:

### 1. Combined Service Pattern
A single `OperationsFrontendService` handles all three modules rather than separate services. This provides:
- Shared helper methods (badge classes, formatting)
- Consistent stats query patterns
- Single import for routes
- Code reuse across modules

### 2. Status Workflow Visualization
DaisyUI `steps` component used for status progression:

**Benevolence:** Linear workflow
```
Draft -> Submitted -> Under Review -> Approved/Denied -> Paid
```

**Grievances:** Step-based progression
```
Filed -> Step 1 (Supervisor) -> Step 2 (HR) -> Step 3 (Director) -> Arbitration -> Resolution
```

### 3. Mini-Progress in Tables
Table rows show condensed step progress for at-a-glance status:
```html
<ul class="steps steps-horizontal">
    <li class="step step-primary" data-content="1"></li>
    <li class="step step-primary" data-content="2"></li>
    <li class="step" data-content="3"></li>
    <li class="step" data-content="A"></li>
</ul>
```

### 4. Badge Helper Methods
Each module has static methods for consistent badge styling:
```python
@staticmethod
def get_salting_outcome_badge_class(outcome: SALTingOutcome) -> str:
    mapping = {
        SALTingOutcome.POSITIVE: "badge-success",
        SALTingOutcome.NEUTRAL: "badge-warning",
        SALTingOutcome.NEGATIVE: "badge-error",
    }
    return mapping.get(outcome, "badge-ghost")
```

### 5. Consistent Page Structure
All list pages follow the same structure:
1. Breadcrumb navigation
2. Page header with title and action button
3. Stats cards
4. Search/filter bar
5. Table with HTMX-loaded content
6. Pagination

All detail pages follow:
1. Breadcrumb navigation
2. Header with status badges
3. Progress/workflow visualization
4. Two-column layout (main content + sidebar)
5. Related links

### 6. Filter Include Pattern
HTMX filters use `hx-include` to maintain filter state:
```html
<input
    type="search"
    name="q"
    hx-get="/operations/salting/search"
    hx-trigger="input changed delay:300ms"
    hx-target="#table-container"
    hx-include="[name='activity_type'], [name='outcome']"
/>
```

## Consequences

### Benefits
- Consistent UX across all operations modules
- Reusable patterns for future modules
- Reduced code duplication
- Clear visual status indicators
- Users can quickly understand status at a glance

### Tradeoffs
- Combined service file is larger (~500 lines)
- Badge class methods require enum imports
- More templates to maintain (14 total for operations)

### Alternatives Considered
1. **Separate services per module** - Rejected due to code duplication
2. **Generic status component** - Rejected, workflows are too different
3. **Client-side status rendering** - Rejected, adds JS complexity

## Related ADRs
- ADR-002: Frontend Stack (HTMX + DaisyUI)
- ADR-009: Migration Safety Strategy

## Files Created
```
src/services/operations_frontend_service.py
src/routers/operations_frontend.py
src/templates/operations/
├── index.html
├── salting/
│   ├── index.html
│   ├── detail.html
│   └── partials/_table.html
├── benevolence/
│   ├── index.html
│   ├── detail.html
│   └── partials/_table.html
└── grievances/
    ├── index.html
    ├── detail.html
    └── partials/_table.html
src/tests/test_operations_frontend.py (21 tests)
```
