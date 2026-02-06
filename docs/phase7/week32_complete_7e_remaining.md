# Claude Code Instruction: Week 32 — Complete Sub-Phase 7e (Remaining Items)

**Source:** Spoke 2 → Claude Code
**Date:** February 5, 2026
**Priority:** 🔴 HIGH
**Estimated Time:** 5 hours
**Branch:** develop
**Risk Level:** LOW — extends existing patterns, no schema changes
**Prerequisite:** Weeks 20-27 complete, v0.9.8-alpha, Dispatch.bid bug fixed (Week 30)

---

## Context

Sub-Phase 7e (Frontend UI) is 90% complete. Weeks 26-27 built the core referral and dispatch UIs — 28 routes, 11 pages, 15 HTMX partials. Three items remain before 7e can be marked DONE:

1. **Exemption Management UI** — CRUD interface for member exemptions (Rule #14)
2. **Reports Navigation Dashboard** — Landing page shell for the 78 reports coming in 7f/7g
3. **Check Mark Tracking UI Refinement** — Enhanced check mark display and recording (Rule #10)

Completing these unblocks the reports sub-phases (7f/7g) which are the bulk of remaining Phase 7 work.

---

## Pre-Flight Checklist

- [ ] `git checkout develop && git pull origin develop`
- [ ] `docker-compose up -d`
- [ ] `pytest -v --tb=short` — verify baseline (~519 passing, 92.7%+ rate)
- [ ] Read `CLAUDE.md` for current state
- [ ] Confirm Dispatch.bid bug is fixed (Week 30 fix: `foreign_keys=[bid_id]` on `Dispatch.bid` relationship)
- [ ] Verify existing dispatch frontend tests pass: `pytest src/tests/test_dispatch_frontend.py -v --tb=short`

---

## Task 1: Exemption Management UI (~2 hrs)

### What This Is

Business Rule #14 defines exempt statuses: military, union business, salting, medical, jury duty. Exempt members are temporarily removed from dispatch obligations without penalty. The enforcement page from Week 27 has a placeholder section for exemptions. This task builds the full CRUD interface.

### Files to Create

| File | Purpose |
|------|---------|
| `src/templates/dispatch/exemptions.html` | Exemption list page with search/filter |
| `src/templates/dispatch/exemption_detail.html` | Single exemption detail/edit view |
| `src/templates/dispatch/partials/_exemptions_table.html` | HTMX partial for exemption list |
| `src/templates/dispatch/partials/_exemption_create_modal.html` | Create new exemption modal |
| `src/templates/dispatch/partials/_exemption_edit_modal.html` | Edit existing exemption modal |

### Files to Modify

| File | Change |
|------|--------|
| `src/routers/dispatch_frontend.py` | Add 4 routes: list, detail, create, deactivate |
| `src/services/dispatch_frontend_service.py` | Add exemption helper methods (stats, badge formatting) |
| `src/templates/dispatch/enforcement.html` | Replace placeholder exemption section with link to full exemption page |
| `src/templates/components/_sidebar.html` | Add "Exemptions" link under Dispatch section |
| `src/tests/test_dispatch_frontend.py` | Add exemption route tests |

### Implementation Details

**Routes to add in `dispatch_frontend.py`:**

```python
@router.get("/dispatch/exemptions", name="dispatch_exemptions")
# List all exemptions with search by member name, filter by type and status
# Uses DispatchFrontendService.get_exemption_stats() for summary cards
# Renders exemptions.html

@router.get("/dispatch/exemptions/{exemption_id}", name="dispatch_exemption_detail")
# Single exemption detail with edit form
# Renders exemption_detail.html

@router.post("/dispatch/exemptions/create", name="dispatch_exemption_create")
# Create new exemption — Staff+ only
# Accepts: member_id, exemption_type, start_date, end_date (optional), reason
# Redirects to exemption detail on success

@router.post("/dispatch/exemptions/{exemption_id}/deactivate", name="dispatch_exemption_deactivate")
# Deactivate (soft-end) an exemption — Staff+ only
# Sets end_date to now, updates status
# Returns HTMX partial or redirects
```

**DispatchFrontendService methods to add:**

```python
def get_exemption_stats(self, db: Session) -> dict:
    """Returns: total_active, by_type counts, expiring_soon (within 7 days)"""

def format_exemption_badge(self, exemption_type: str) -> dict:
    """Returns: {'text': '...', 'class': 'badge-...'} for DaisyUI badge styling"""
    # military → badge-info, union_business → badge-primary,
    # salting → badge-warning, medical → badge-error, jury_duty → badge-secondary
```

**Exemption types** (from Business Rule #14): `MILITARY`, `UNION_BUSINESS`, `SALTING`, `MEDICAL`, `JURY_DUTY`

Check the existing enum in `src/db/enums/phase7_enums.py` — if `ExemptionType` exists, use it. If not, create it.

**Template patterns to follow:**
- List page: mirror `src/templates/dispatch/enforcement.html` layout — DaisyUI cards for stats, table below
- HTMX search: 300ms debounce, `hx-get` to partials endpoint, `hx-target` to table container
- Modal pattern: follow `src/templates/dispatch/partials/_resign_modal.html` structure
- Badge styling: use DaisyUI `badge badge-{variant}` classes

**Audit requirement:** Creating and deactivating exemptions MUST be audit-logged. The service layer should call `audit_service.log_create()` and `audit_service.log_update()` respectively.

### Tests Required (4 minimum)

```python
# In test_dispatch_frontend.py

def test_exemptions_page_loads(auth_client):
    """GET /dispatch/exemptions returns 200"""

def test_exemptions_page_requires_auth(client):
    """GET /dispatch/exemptions without auth returns 302 to login"""

def test_exemption_detail_page_loads(auth_client, sample_exemption):
    """GET /dispatch/exemptions/{id} returns 200"""

def test_exemption_create_requires_staff(member_client):
    """POST /dispatch/exemptions/create with member role returns 403"""
```

---

## Task 2: Reports Navigation Dashboard (~2 hrs)

### What This Is

A landing page for all referral/dispatch reports. This is the **navigation shell** — actual report generation comes in Week 33+. The page organizes the 78 reports into priority-based categories with clear "available" vs "coming soon" states.

### Files to Create

| File | Purpose |
|------|---------|
| `src/templates/dispatch/reports_landing.html` | Reports navigation dashboard |
| `src/templates/dispatch/partials/_report_category_card.html` | Reusable category card partial |

### Files to Modify

| File | Change |
|------|--------|
| `src/routers/dispatch_frontend.py` | Add 1 route for reports landing |
| `src/services/dispatch_frontend_service.py` | Add `get_report_categories()` method |
| `src/templates/components/_sidebar.html` | Add "Reports" link under Dispatch section |
| `src/tests/test_dispatch_frontend.py` | Add reports landing test |

### Implementation Details

**Route to add in `dispatch_frontend.py`:**

```python
@router.get("/dispatch/reports", name="dispatch_reports")
# Reports navigation dashboard
# Uses DispatchFrontendService.get_report_categories() for category data
# Renders reports_landing.html
```

**DispatchFrontendService method:**

```python
def get_report_categories(self) -> list[dict]:
    """Returns report categories with availability status.
    
    Each category: {
        'name': 'Out-of-Work Lists',
        'icon': 'clipboard-list',  # Heroicon name
        'priority': 'P0',
        'description': 'Daily operational lists for dispatch staff',
        'reports': [
            {'name': 'Out-of-Work List (by Book)', 'available': False, 'url': None},
            {'name': 'Out-of-Work Summary', 'available': False, 'url': None},
            ...
        ],
        'total': 4,
        'available_count': 0,
    }
    """
```

**Report categories (from `LABORPOWER_REFERRAL_REPORTS_INVENTORY.md`):**

| Category | Priority | Report Count | Initial State |
|----------|----------|-------------|---------------|
| Out-of-Work Lists | P0 | 4 | Coming Soon |
| Dispatch Operations | P0 | 5 | Coming Soon |
| Registration Reports | P0/P1 | 4 | Coming Soon |
| Employer Reports | P0/P1 | 3 | Coming Soon |
| Check Marks & Enforcement | P1 | 4 | Coming Soon |
| Member Activity | P1 | 5 | Coming Soon |
| Analytics & Trends | P2 | 5 | Coming Soon |
| Projections & Ad-Hoc | P3 | 3 | Coming Soon |

**Template layout:**
- Grid of DaisyUI cards (2 columns on desktop, 1 on mobile)
- Each card shows: category name, icon, priority badge, description, report count, progress bar (available/total)
- "Coming Soon" reports shown in muted text with lock icon
- Available reports get blue link styling and download icons
- Header area: total reports available vs total planned, last generation timestamp

**As reports are built in Weeks 33+, the `available` flag and `url` will be populated. This is the scaffold.**

### Tests Required (2 minimum)

```python
def test_dispatch_reports_landing_loads(auth_client):
    """GET /dispatch/reports returns 200"""

def test_dispatch_reports_landing_requires_auth(client):
    """GET /dispatch/reports without auth returns 302"""
```

---

## Task 3: Check Mark Tracking UI Refinement (~1 hr)

### What This Is

Business Rule #10: Members get check marks when they decline dispatch. 2 allowed per area book. 3rd = rolled off that book. The Week 27 enforcement page shows check marks in a table. This task adds:

1. Per-member check mark history view
2. Visual 2-of-3 progress indicator
3. "Record Check Mark" action modal for staff

### Files to Create

| File | Purpose |
|------|---------|
| `src/templates/dispatch/partials/_checkmark_history.html` | Member check mark history partial |
| `src/templates/dispatch/partials/_checkmark_record_modal.html` | Staff action: record new check mark |
| `src/templates/dispatch/partials/_checkmark_progress.html` | Visual progress indicator (reusable) |

### Files to Modify

| File | Change |
|------|--------|
| `src/routers/dispatch_frontend.py` | Add 2 routes: check mark history partial, record check mark action |
| `src/services/dispatch_frontend_service.py` | Add `get_member_checkmark_summary()` method |
| `src/templates/dispatch/enforcement.html` | Integrate progress indicators into existing check mark table |
| `src/tests/test_dispatch_frontend.py` | Add check mark UI tests |

### Implementation Details

**Routes to add in `dispatch_frontend.py`:**

```python
@router.get("/dispatch/checkmarks/{member_id}/history", name="dispatch_checkmark_history")
# HTMX partial: returns check mark history for a specific member across all books
# Used in enforcement page expansion or member detail integration

@router.post("/dispatch/checkmarks/record", name="dispatch_checkmark_record")
# Staff+ action: record a new check mark
# Accepts: member_id, book_id, reason, dispatch_id (optional)
# Validates: member is registered on that book, not at 3 already
# Returns: updated HTMX partial
```

**Progress indicator pattern (`_checkmark_progress.html`):**

```html
<!-- Visual: 3 circles, filled based on check mark count -->
<!-- 0 checks: ○ ○ ○ (all gray) -->
<!-- 1 check:  ● ○ ○ (1 yellow) -->
<!-- 2 checks: ● ● ○ (2 orange — warning state) -->
<!-- 3 checks: ● ● ● (3 red — rolled off) -->
<!-- Use DaisyUI badge or custom SVG circles -->
<!-- Accepts: count (0-3), book_name -->
```

This partial should be reusable anywhere a member's check mark status needs to display (enforcement page, member detail, registration detail).

**DispatchFrontendService method:**

```python
def get_member_checkmark_summary(self, db: Session, member_id: int) -> list[dict]:
    """Returns check marks per book for a member.
    
    Each entry: {
        'book_id': 1,
        'book_name': 'WIRE SEATTLE',
        'count': 2,
        'max_allowed': 2,
        'at_limit': True,
        'history': [
            {'date': '...', 'reason': '...', 'dispatch_id': ...},
            ...
        ]
    }
    """
```

**Record Check Mark modal fields:**
- Member (searchable dropdown or ID input)
- Book (dropdown filtered to member's active registrations)
- Reason (text area)
- Associated dispatch (optional, dropdown of member's recent dispatches)
- Warning display: "This member has X of 2 check marks on this book. Recording another will result in roll-off."

**Audit requirement:** Recording a check mark is a high-impact action. MUST be audit-logged with full context (who recorded, reason, associated dispatch).

### Tests Required (4 minimum)

```python
def test_checkmark_history_loads(auth_client, sample_member_with_checkmarks):
    """GET /dispatch/checkmarks/{member_id}/history returns 200"""

def test_checkmark_history_requires_auth(client):
    """Unauthenticated request returns 302"""

def test_checkmark_record_requires_staff(member_client):
    """POST /dispatch/checkmarks/record with member role returns 403"""

def test_checkmark_record_action(staff_client, sample_registration):
    """POST /dispatch/checkmarks/record creates check mark and returns updated partial"""
```

---

## Anti-Patterns (DO NOT)

- Do NOT modify Phase 7 models (ReferralBook, BookRegistration, etc.) — they are locked unless a bug is found
- Do NOT modify `src/main.py` or `conftest.py` without documenting in session summary for Hub handoff
- Do NOT create new database models — all models needed for these tasks already exist
- Do NOT skip audit logging on exemption and check mark mutations
- Do NOT use `commit()` in test fixtures — use `flush()` for transaction isolation
- Do NOT change existing test assertions unless the test is objectively wrong
- Do NOT add new Alembic migrations — these are UI-only changes using existing schema

---

## Success Criteria

- [ ] Exemption Management UI: list, detail, create, deactivate — all functional
- [ ] Reports Navigation Dashboard: renders all 8 categories with correct report counts
- [ ] Check Mark Progress: visual indicator renders correctly for 0, 1, 2, 3 check marks
- [ ] Record Check Mark modal: staff can record, validation prevents 4th check mark
- [ ] Minimum 10 new tests passing
- [ ] No regression in existing tests (baseline ~519 passing)
- [ ] All new routes accessible from sidebar navigation
- [ ] Audit logging active on all mutating operations

---

## End-of-Session (MANDATORY)

- [ ] `pytest -v` — verify green (or document new failures with context)
- [ ] `ruff check . --fix && ruff format .`
- [ ] `git add -A && git commit -m "feat(phase7): Week 32 — complete 7e remaining (exemptions, reports nav, check marks)"`
- [ ] `git push origin develop`
- [ ] Update `CLAUDE.md` — version bump to v0.9.9-alpha, update test counts, mark 7e COMPLETE
- [ ] Update `CHANGELOG.md` — add v0.9.9-alpha entry
- [ ] Create session log: `docs/reports/session-logs/2026-XX-XX-week32-7e-complete.md`
- [ ] Update `docs/IP2A_MILESTONE_CHECKLIST.md` — mark remaining 7e tasks as Done
- [ ] If `_sidebar.html` was modified, note in session summary for Hub handoff

---

## Session Reminders

> **Member ≠ Student.** Members are IBEW union members in the referral system. Students are pre-apprenticeship program participants. Phase 7 models FK to `members`, NOT `students`.

> **Book ≠ Contract.** Books are out-of-work registration lists. Contracts are collective bargaining agreements. The mapping is NOT 1:1. 3 books have NO contract code.

> **APN = DECIMAL(10,2).** Integer part is Excel serial date. Decimal part is secondary sort key. NEVER truncate to INTEGER.

> **Audit.** `registrations`, `dispatches`, and `check_marks` tables MUST be in AUDITED_TABLES. Exemption and check mark mutations require audit logging.

---

*Week 32 Instruction — Spoke 2: Operations*
*UnionCore (IP2A-Database-v2) — February 5, 2026*
