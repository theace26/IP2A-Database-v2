# Phase 6 Week 6: Union Operations Frontend

**Created:** January 29, 2026
**Estimated Time:** 8-10 hours (3-4 sessions)
**Prerequisites:** Week 5 complete (Members Landing, ~238 tests passing, v0.7.4)

---

## Overview

Week 6 builds the Union Operations section - the heart of organizing activities. This includes SALTing (Strategic Approach to Labor Targeting), Benevolence Fund management, and Grievance tracking.

| Session | Focus | Time |
|---------|-------|------|
| A | SALTing Activities | 2-3 hrs |
| B | Benevolence Fund | 2-3 hrs |
| C | Grievance Tracking | 2-3 hrs |
| D | Tests + Documentation + ADRs | 2 hrs |

---

## Week 6 Objectives

### Must Have (MVP)
- [ ] Union Operations landing page with section links
- [ ] SALTing activities list with employer/score display
- [ ] SALTing activity detail with log timeline
- [ ] Benevolence requests list with status workflow
- [ ] Benevolence request detail with payments
- [ ] Grievance list with step indicators
- [ ] Grievance detail with step timeline
- [ ] 20+ new tests
- [ ] Updated CHANGELOG.md
- [ ] Updated IP2A_MILESTONE_CHECKLIST.md
- [ ] Updated CLAUDE.md
- [ ] Session log created

### Nice to Have
- [ ] Quick action modals for status updates
- [ ] Filter by date range
- [ ] Export to CSV
- [ ] ADR for Union Operations UI patterns

---

## Architecture Overview

### Page Structure

```
/operations                    → Union Operations landing (links to all 3)
/operations/salting            → SALTing list
/operations/salting/{id}       → SALTing detail with logs
/operations/benevolence        → Benevolence requests list
/operations/benevolence/{id}   → Request detail with payments
/operations/grievances         → Grievance list
/operations/grievances/{id}    → Grievance detail with steps
```

### Component Hierarchy

```
templates/
└── operations/
    ├── index.html                    # Operations landing
    ├── salting/
    │   ├── index.html                # SALTing list
    │   ├── detail.html               # Activity detail
    │   └── partials/
    │       ├── _table.html           # Activity table
    │       ├── _row.html             # Activity row
    │       └── _log_timeline.html    # Activity logs
    ├── benevolence/
    │   ├── index.html                # Requests list
    │   ├── detail.html               # Request detail
    │   └── partials/
    │       ├── _table.html           # Requests table
    │       ├── _row.html             # Request row
    │       └── _payments.html        # Payment history
    └── grievances/
        ├── index.html                # Grievance list
        ├── detail.html               # Grievance detail
        └── partials/
            ├── _table.html           # Grievance table
            ├── _row.html             # Grievance row
            └── _steps_timeline.html  # Steps timeline
```

### New Files Summary

| File | Purpose |
|------|---------|
| `src/services/operations_frontend_service.py` | Stats + queries for all 3 modules |
| `src/routers/operations_frontend.py` | Operations page routes |
| `src/templates/operations/**/*.html` | All templates listed above |
| `src/tests/test_operations_frontend.py` | Frontend tests |

---

## Data Model Reference

### SALTing Models

```python
class SaltingActivity(Base):
    __tablename__ = "salting_activities"

    id: int
    employer_id: int                  # FK to Organization
    organizer_id: int                 # FK to Member (who's organizing)
    status: SaltingStatus             # PLANNING, ACTIVE, PAUSED, COMPLETED, ABANDONED
    score: int                        # 1-5 (employer receptiveness)
    target_workers: int | None
    notes: str | None
    started_at: date
    completed_at: date | None
    created_at: datetime
    updated_at: datetime

    # Relationships
    employer: Organization
    organizer: Member
    logs: list[SaltingLog]

class SaltingLog(Base):
    __tablename__ = "salting_logs"

    id: int
    activity_id: int                  # FK to SaltingActivity
    logged_by_id: int                 # FK to User
    action: str                       # e.g., "Contact made", "Meeting scheduled"
    notes: str | None
    logged_at: datetime

    # Relationships
    activity: SaltingActivity
    logged_by: User

class SaltingStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
```

### Benevolence Models

```python
class BenevolenceRequest(Base):
    __tablename__ = "benevolence_requests"

    id: int
    member_id: int                    # FK to Member (requesting member)
    request_type: BenevolenceType     # HARDSHIP, FUNERAL, MEDICAL, DISASTER, OTHER
    status: BenevolenceStatus         # PENDING, APPROVED, DENIED, PAID, CLOSED
    amount_requested: Decimal
    amount_approved: Decimal | None
    reason: str
    supporting_docs: str | None       # JSON list of document IDs
    reviewed_by_id: int | None        # FK to User
    reviewed_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # Relationships
    member: Member
    reviewed_by: User | None
    payments: list[BenevolencePayment]

class BenevolencePayment(Base):
    __tablename__ = "benevolence_payments"

    id: int
    request_id: int                   # FK to BenevolenceRequest
    amount: Decimal
    payment_method: str               # CHECK, DIRECT_DEPOSIT, CASH
    payment_date: date
    check_number: str | None
    processed_by_id: int              # FK to User
    notes: str | None
    created_at: datetime

    # Relationships
    request: BenevolenceRequest
    processed_by: User

class BenevolenceType(str, Enum):
    HARDSHIP = "hardship"
    FUNERAL = "funeral"
    MEDICAL = "medical"
    DISASTER = "disaster"
    OTHER = "other"

class BenevolenceStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"
    CLOSED = "closed"
```

### Grievance Models

```python
class Grievance(Base):
    __tablename__ = "grievances"

    id: int
    grievance_number: str             # Auto-generated: GRV-2026-0001
    member_id: int                    # FK to Member (filing member)
    employer_id: int                  # FK to Organization
    filed_by_id: int                  # FK to User (staff who filed)
    status: GrievanceStatus           # FILED, STEP_1, STEP_2, STEP_3, STEP_4, RESOLVED, WITHDRAWN
    current_step: int                 # 1-4
    category: GrievanceCategory       # CONTRACT, SAFETY, DISCRIMINATION, TERMINATION, OTHER
    description: str
    resolution: str | None
    filed_at: date
    resolved_at: date | None
    created_at: datetime
    updated_at: datetime

    # Relationships
    member: Member
    employer: Organization
    filed_by: User
    steps: list[GrievanceStep]

class GrievanceStep(Base):
    __tablename__ = "grievance_steps"

    id: int
    grievance_id: int                 # FK to Grievance
    step_number: int                  # 1-4
    status: StepStatus                # PENDING, IN_PROGRESS, COMPLETED, ESCALATED
    started_at: date
    completed_at: date | None
    outcome: str | None               # e.g., "Denied - escalating to Step 2"
    notes: str | None
    handled_by_id: int                # FK to User
    created_at: datetime

    # Relationships
    grievance: Grievance
    handled_by: User

class GrievanceStatus(str, Enum):
    FILED = "filed"
    STEP_1 = "step_1"
    STEP_2 = "step_2"
    STEP_3 = "step_3"
    STEP_4 = "step_4"           # Arbitration
    RESOLVED = "resolved"
    WITHDRAWN = "withdrawn"

class GrievanceCategory(str, Enum):
    CONTRACT = "contract"
    SAFETY = "safety"
    DISCRIMINATION = "discrimination"
    TERMINATION = "termination"
    OTHER = "other"
```

---

## UI Patterns

### SALTing Score Display (1-5)
```html
<!-- Score badges -->
<div class="rating rating-sm">
    {% for i in range(1, 6) %}
    <span class="mask mask-star-2 {{ 'bg-warning' if i <= activity.score else 'bg-base-300' }}"></span>
    {% endfor %}
</div>
<span class="text-sm ml-2">{{ activity.score }}/5</span>
```

### Benevolence Status Workflow
```
PENDING → APPROVED → PAID → CLOSED
    ↓
  DENIED → CLOSED
```

### Grievance Step Progress
```html
<ul class="steps steps-horizontal w-full">
    <li class="step {{ 'step-primary' if grievance.current_step >= 1 else '' }}">Step 1</li>
    <li class="step {{ 'step-primary' if grievance.current_step >= 2 else '' }}">Step 2</li>
    <li class="step {{ 'step-primary' if grievance.current_step >= 3 else '' }}">Step 3</li>
    <li class="step {{ 'step-primary' if grievance.current_step >= 4 else '' }}">Arbitration</li>
</ul>
```

---

## HTMX Patterns

### Live Search (consistent with previous weeks)
```html
<input
    type="search"
    name="q"
    hx-get="/operations/salting/search"
    hx-trigger="input changed delay:300ms, search"
    hx-target="#table-container"
    hx-include="[name='status'], [name='score']"
/>
```

### Status Update (inline)
```html
<select
    name="status"
    hx-post="/operations/salting/{{ activity.id }}/status"
    hx-trigger="change"
    hx-swap="outerHTML"
    class="select select-bordered select-sm"
>
    {% for status in all_statuses %}
    <option value="{{ status }}" {{ 'selected' if activity.status.value == status }}>
        {{ status | title }}
    </option>
    {% endfor %}
</select>
```

---

## Documentation Requirements

### MUST Update (Every Session)
1. **CHANGELOG.md** - Add features under `[Unreleased]`
2. **IP2A_MILESTONE_CHECKLIST.md** - Check off completed tasks
3. **Session Log** - Create `docs/reports/session-logs/2026-01-XX-phase6-week6.md`

### MUST Update (End of Week)
1. **CLAUDE.md** - Update current status and next steps
2. **README.md** (docs/) - Update version and component status
3. **docs/guides/** - If new patterns introduced

### SHOULD Create (If Applicable)
1. **ADR** - If significant architectural decisions made
   - Example: ADR-009 for Union Operations UI patterns
   - Example: ADR-010 for HTMX partial loading strategy

---

## Session Breakdown

### Session A: SALTing Activities (Document 1)
- Create OperationsFrontendService
- Create operations_frontend router
- Operations landing page
- SALTing list with score display
- SALTing detail with log timeline
- Filter by status and score

### Session B: Benevolence Fund (Document 2)
- Benevolence requests list
- Status workflow display
- Request detail with payments
- Filter by status and type

### Session C: Grievance Tracking (Document 3)
- Grievance list with step indicators
- Grievance detail with step timeline
- Step progress component
- Filter by status and category

### Session D: Tests + Documentation (Document 4)
- Comprehensive test suite (20+ tests)
- Update all documentation
- Create session log
- Tag release v0.7.5

---

## Success Criteria

Week 6 is complete when:
- [ ] Operations landing page displays with section cards
- [ ] SALTing list shows activities with score visualization
- [ ] SALTing detail shows log timeline
- [ ] Benevolence list shows requests with status
- [ ] Benevolence detail shows payment history
- [ ] Grievance list shows cases with step progress
- [ ] Grievance detail shows step timeline
- [ ] All HTMX interactions work
- [ ] All tests pass (258+ total, ~93 frontend)
- [ ] Documentation fully updated
- [ ] Session log created
- [ ] v0.7.5 tagged

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

---

*Proceed to Document 1 (Session A) to begin SALTing Activities implementation.*
