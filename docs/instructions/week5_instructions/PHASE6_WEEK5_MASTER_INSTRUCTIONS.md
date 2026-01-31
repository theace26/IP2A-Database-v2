# Phase 6 Week 5: Members Landing Page

**Created:** January 29, 2026
**Estimated Time:** 6-8 hours (3 sessions)
**Prerequisites:** Week 4 complete (Training Landing, ~224 tests passing)

---

## Overview

Week 5 builds the Members section - the core of union operations management.

| Session | Focus | Time |
|---------|-------|------|
| A | Members overview + stats dashboard | 2-3 hrs |
| B | Member list with search/filters | 2-3 hrs |
| C | Member detail + employment history + tests | 2-3 hrs |

---

## Week 5 Objectives

### Must Have (MVP)
- [ ] Members landing page with overview stats
- [ ] Total members count with status breakdown
- [ ] Members by classification chart/badges
- [ ] Recent activity (new members, status changes)
- [ ] Member list with search (name, card ID, email)
- [ ] Filter by status and classification
- [ ] Member detail page with contact info
- [ ] Employment history timeline
- [ ] Dues status indicator (current/overdue/exempt)
- [ ] Classification badge with color coding
- [ ] 15+ new tests

### Nice to Have
- [ ] Quick edit modal for member info
- [ ] Link member to user account
- [ ] Export member roster to CSV
- [ ] Dues payment quick entry

---

## Architecture Overview

### Page Structure

```
/members                  → Members landing page (overview + list)
/members/search           → HTMX partial (table body only)
/members/{id}             → Member detail page
/members/{id}/edit        → HTMX partial (edit modal)
/members/{id}/employment  → HTMX partial (employment history)
/members/{id}/dues        → HTMX partial (dues summary)
```

### Component Hierarchy

```
templates/
└── members/
    ├── index.html              # Main landing page
    ├── detail.html             # Full detail page
    └── partials/
        ├── _stats.html         # Stats cards
        ├── _table.html         # Member table with pagination
        ├── _row.html           # Single member row
        ├── _employment.html    # Employment history section
        ├── _dues_summary.html  # Dues status section
        └── _edit_modal.html    # Quick edit modal
```

### New Files Summary

| File | Purpose |
|------|---------|
| `src/services/member_frontend_service.py` | Member stats + queries |
| `src/routers/member_frontend.py` | Member page routes |
| `src/templates/members/index.html` | Landing page |
| `src/templates/members/detail.html` | Detail page |
| `src/templates/members/partials/*.html` | HTMX partials |
| `src/tests/test_member_frontend.py` | Frontend tests |

---

## Data Model Reference

### Member Model (Key Fields)

```python
class Member(Base):
    __tablename__ = "members"

    id: int
    card_id: str                  # Union card number (unique)
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    zip_code: str | None

    status: MemberStatus          # ACTIVE, INACTIVE, SUSPENDED, RETIRED, DECEASED
    classification: MemberClassification  # JOURNEYMAN, APPRENTICE, etc.

    hire_date: date | None
    termination_date: date | None

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None   # Soft delete

    # Relationships
    employments: list[MemberEmployment]
    dues_payments: list[DuesPayment]
    user: User | None             # Linked user account
```

### MemberStatus Enum

```python
class MemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    RETIRED = "retired"
    DECEASED = "deceased"
```

### MemberClassification Enum

```python
class MemberClassification(str, Enum):
    JOURNEYMAN_WIREMAN = "journeyman_wireman"
    APPRENTICE_WIREMAN = "apprentice_wireman"
    JOURNEYMAN_TECHNICIAN = "journeyman_technician"
    APPRENTICE_TECHNICIAN = "apprentice_technician"
    RESIDENTIAL_WIREMAN = "residential_wireman"
    RESIDENTIAL_APPRENTICE = "residential_apprentice"
    INSTALLER_TECHNICIAN = "installer_technician"
    TRAINEE = "trainee"
    ORGANIZER = "organizer"
```

### MemberEmployment Model

```python
class MemberEmployment(Base):
    __tablename__ = "member_employments"

    id: int
    member_id: int                # FK to Member
    organization_id: int          # FK to Organization (employer)

    start_date: date
    end_date: date | None         # Null = currently employed

    job_title: str | None
    hourly_rate: Decimal | None
    is_current: bool

    created_at: datetime
    updated_at: datetime

    # Relationships
    member: Member
    organization: Organization
```

### DuesPayment Model (Key Fields for Display)

```python
class DuesPayment(Base):
    __tablename__ = "dues_payments"

    id: int
    member_id: int
    period_id: int                # FK to DuesPeriod
    amount: Decimal
    status: DuesPaymentStatus     # PENDING, PAID, OVERDUE, WAIVED
    payment_date: date | None

    # Relationships
    member: Member
    period: DuesPeriod
```

---

## Stats to Display

### Overview Cards

| Stat | Query | Display |
|------|-------|---------|
| Total Members | `COUNT(members WHERE deleted_at IS NULL)` | "6,247 Members" |
| Active Members | `COUNT(members WHERE status='active')` | "5,892 Active" |
| New This Month | `COUNT(members WHERE created_at > month_start)` | "+23 This Month" |
| Dues Current | `COUNT(members with current dues)` | "94% Current" |

### Classification Breakdown

| Classification | Count | Display |
|----------------|-------|---------|
| Journeyman Wireman | 3,450 | Badge + count |
| Apprentice Wireman | 1,200 | Badge + count |
| ... | ... | ... |

### Member List Columns

| Column | Source |
|--------|--------|
| Card ID | `member.card_id` |
| Name | `member.first_name + last_name` |
| Classification | Badge based on `member.classification` |
| Status | Badge based on `member.status` |
| Current Employer | `member.employments[is_current=True].organization.name` |
| Dues Status | Indicator based on payment status |
| Actions | View, Edit |

---

## HTMX Patterns Used

### Live Search with Debounce
```html
<input
    type="search"
    name="q"
    hx-get="/members/search"
    hx-trigger="input changed delay:300ms, search"
    hx-target="#member-table-body"
    hx-include="[name='status'], [name='classification']"
    hx-indicator="#search-spinner"
/>
```

### Employment History Load
```html
<div
    hx-get="/members/{{ member.id }}/employment"
    hx-trigger="revealed"
    hx-swap="innerHTML"
>
    <span class="loading loading-spinner"></span>
</div>
```

### Dues Summary Refresh
```html
<div
    id="dues-summary"
    hx-get="/members/{{ member.id }}/dues"
    hx-trigger="load, dues-updated from:body"
>
    <!-- Dues info loads here -->
</div>
```

---

## DaisyUI Components Reference

### Classification Badges
```html
<span class="badge badge-primary">Journeyman Wireman</span>
<span class="badge badge-secondary">Apprentice</span>
<span class="badge badge-accent">Technician</span>
```

### Status Badges
```html
<span class="badge badge-success gap-1">
    <span class="w-2 h-2 rounded-full bg-success animate-pulse"></span>
    Active
</span>
<span class="badge badge-warning">Inactive</span>
<span class="badge badge-error">Suspended</span>
<span class="badge badge-ghost">Retired</span>
```

### Dues Status Indicator
```html
<!-- Current -->
<div class="flex items-center gap-2 text-success">
    <svg class="w-4 h-4" fill="currentColor">...</svg>
    <span>Current</span>
</div>

<!-- Overdue -->
<div class="flex items-center gap-2 text-error">
    <svg class="w-4 h-4" fill="currentColor">...</svg>
    <span>Overdue (2 months)</span>
</div>
```

### Timeline (Employment History)
```html
<ul class="timeline timeline-vertical">
    <li>
        <div class="timeline-start">2024</div>
        <div class="timeline-middle">
            <svg class="w-5 h-5">...</svg>
        </div>
        <div class="timeline-end timeline-box">
            <div class="font-bold">ABC Electric</div>
            <div class="text-sm">Jan 2024 - Present</div>
        </div>
        <hr class="bg-primary"/>
    </li>
</ul>
```

---

## Session Breakdown

### Session A: Members Overview (Document 1)
1. Create `member_frontend_service.py` with stats queries
2. Create `member_frontend.py` router
3. Create `members/index.html` landing page
4. Create `_stats.html` partial with stat cards
5. Add classification breakdown display
6. Test manually

### Session B: Member List (Document 2)
1. Create `_table.html` partial with columns
2. Create `_row.html` partial with badges
3. Add search endpoint with HTMX
4. Add status and classification filters
5. Add pagination
6. Add current employer display

### Session C: Member Detail + Tests (Document 3)
1. Create `detail.html` full page
2. Create `_employment.html` timeline partial
3. Create `_dues_summary.html` partial
4. Add employment history endpoint
5. Add dues summary endpoint
6. Write comprehensive tests (15+)
7. Update documentation

---

## Success Criteria

Week 5 is complete when:
- [ ] Members landing page displays with stats
- [ ] Classification breakdown shows counts
- [ ] Member list shows with all badges
- [ ] Search and filters work via HTMX
- [ ] Member detail shows contact info
- [ ] Employment history displays as timeline
- [ ] Dues status indicator shows correctly
- [ ] All tests pass (240+ total)
- [ ] Browser testing confirms full flow

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

*Proceed to Document 1 (Session A) to begin implementation.*
