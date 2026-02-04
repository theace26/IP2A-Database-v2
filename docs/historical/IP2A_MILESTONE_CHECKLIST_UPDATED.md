# IP2A Milestone Checklist (Quick Reference)

> **Print this or keep it open during sessions**
> Last Updated: January 29, 2026

---

## Current Focus: Phase 6 Frontend (Week 10 - Dues UI → Week 11 - Audit Trail)

### Legend: ✅ Done | 🟡 In Progress | ⬜ Pending

---

## Backend Phases: ALL COMPLETE ✅

| Phase | Description | Models | Endpoints | Tests | Status |
|-------|-------------|--------|-----------|-------|--------|
| Phase 0 | Documentation & Structure | - | - | - | ✅ Done |
| Phase 1 | Auth (JWT, RBAC, Registration) | 4 | 13 | 52 | ✅ Done |
| Phase 2a | Union Ops (SALT, Benevolence, Grievance) | 5 | 27 | 31 | ✅ Done |
| Phase 2b | Training (Students, Courses, Grades) | 7 | ~35 | 33 | ✅ Done |
| Phase 3 | Documents (S3/MinIO) | 1 | 8 | 11 | ✅ Done |
| Phase 4 | Dues Tracking | 4 | ~35 | 21 | ✅ Done |
| **Total** | **Backend Complete** | **25** | **~120** | **165** | **✅ Done** |

---

## Phase 6: Frontend Build

### Weeks 1-9: COMPLETE ✅

| Week | Focus | Tests Added | Status |
|------|-------|-------------|--------|
| 1 | Setup + Login | 12 | ✅ v0.7.0 |
| 2 | Auth Cookies + Dashboard | 10 | ✅ v0.7.1 |
| 3 | Staff Management | 18 | ✅ v0.7.2 |
| 4 | Training Landing | 19 | ✅ v0.7.3 |
| 5 | Members Landing | 15 | ✅ v0.7.4 |
| 6 | Union Operations | 21 | ✅ v0.7.5 |
| 8 | Reports & Export | 30 | ✅ v0.7.6 |
| 9 | Documents Frontend | 6 | ✅ v0.7.7 |

---

### Week 10: Dues UI (IN PROGRESS)

| Task | Status |
|------|--------|
| DuesFrontendService with stats and badge helpers | ✅ Done |
| Dues landing page with current period display | ✅ Done |
| Stats cards (MTD, YTD, overdue, pending) | ✅ Done |
| Quick action cards for rates/periods/payments/adjustments | ✅ Done |
| Rates list page with HTMX filtering | ✅ Done |
| Rates table partial with status badges | ✅ Done |
| Sidebar navigation with Dues dropdown | ✅ Done |
| 19 new dues frontend tests | ✅ Done |
| Periods management page | ⬜ Pending |
| Payments list and recording | ⬜ Pending |
| Adjustments workflow | ⬜ Pending |

**Current Version:** v0.7.8 (Week 10 Session A Complete)

---

### Week 11: Audit Trail & Member History UI ⬜ NEXT

**Goal:** Complete audit trail for all member changes with role-based access.

**CRITICAL COMPLIANCE:** All member information changes MUST be audited (NLRA 7-year requirement).

#### 11.1 Database Completeness

| Task | Est. | Status |
|------|------|--------|
| Add immutability trigger to `audit_logs` table | 1 hr | ⬜ |
| Create `member_notes` table and model | 2 hrs | ⬜ |
| Add `member_notes` to `AUDITED_TABLES` | 15 min | ⬜ |
| Create MemberNoteService (CRUD) | 1 hr | ⬜ |
| Create member notes router | 1 hr | ⬜ |
| Tests for member notes (unit + integration) | 1 hr | ⬜ |

**Migration Required:**
```sql
-- MUST ADD: Immutability trigger
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_immutable
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_modification();
```

#### 11.2 Audit RBAC Permissions

| Task | Est. | Status |
|------|------|--------|
| Define audit permission constants in `permissions.py` | 30 min | ⬜ |
| Add permissions to Role model/seeder | 30 min | ⬜ |
| Create `AuditFrontendService` with role filtering | 2 hrs | ⬜ |
| Add field-level redaction (SSN, bank info) | 1 hr | ⬜ |
| Tests for role-based audit access | 1 hr | ⬜ |

**Permission Matrix:**
| Role | Permissions |
|------|-------------|
| Staff | `audit:view_own` (only entities they touched) |
| Organizer | `audit:view_own` + `audit:view_members` |
| Officer | `audit:view_members` + `audit:view_users` |
| Admin | `audit:view_all` + `audit:view_users` + `audit:export` |

**Fields to Redact for Non-Admin:**
- `ssn`, `social_security`
- `bank_account`, `routing_number`
- `password_hash`, `token_hash`

#### 11.3 Audit Trail UI

| Task | Est. | Status |
|------|------|--------|
| Audit log list page (`/admin/audit-logs`) | 2 hrs | ⬜ |
| HTMX search/filter (date, user, entity, action) | 1 hr | ⬜ |
| Audit log detail view (old/new diff) | 1 hr | ⬜ |
| Sidebar nav entry under Admin section | 15 min | ⬜ |
| Export button (CSV/JSON for authorized roles) | 1 hr | ⬜ |
| Tests for audit UI | 1 hr | ⬜ |

#### 11.4 Inline History on Entity Pages

| Task | Est. | Status |
|------|------|--------|
| Create `_audit_history.html` partial (reusable) | 1 hr | ⬜ |
| Add "Recent Activity" to member detail page | 30 min | ⬜ |
| Add "Recent Activity" to student detail page | 30 min | ⬜ |
| Add "Recent Activity" to grievance detail page | 30 min | ⬜ |
| HTMX endpoint `/audit/entity/{type}/{id}` | 1 hr | ⬜ |

#### 11.5 Member Notes UI

| Task | Est. | Status |
|------|------|--------|
| Notes section on member detail page | 1 hr | ⬜ |
| Add note modal/form with HTMX submit | 1 hr | ⬜ |
| Visibility selector (staff_only/officers/all) | 30 min | ⬜ |
| Notes filtered by user permission | 30 min | ⬜ |
| Tests for notes UI | 1 hr | ⬜ |

#### Week 11 Acceptance Criteria

- [ ] `audit_logs` table has immutability trigger (test UPDATE/DELETE fails)
- [ ] `member_notes` table exists with model/service/router
- [ ] Member notes automatically appear in audit trail
- [ ] Audit log list page works with role-based filtering
- [ ] Sensitive fields show `[REDACTED]` for non-admin
- [ ] Member detail page shows notes section (visibility filtered)
- [ ] Member detail page shows "Recent Activity" inline
- [ ] Export button visible only for authorized roles
- [ ] All tests passing

**Target:** +15-20 new tests → ~165-170 frontend tests total

---

### Week 12: Settings & Profile ⬜

| Task | Status |
|------|--------|
| User profile page (view own info) | ⬜ |
| Password change form | ⬜ |
| System settings page (admin only) | ⬜ |
| Email notification preferences | ⬜ |

---

## Quick Stats

| Metric | Current | After Week 11 |
|--------|---------|---------------|
| Total Tests | ~312 | ~330 |
| Backend Tests | 165 | 165 |
| Frontend Tests | 149 | ~165 |
| API Endpoints | ~130 | ~135 |
| ORM Models | 25 | 26 (+member_notes) |
| ADRs | 10 | 11 (+ADR-008 Audit) |
| Version | v0.7.8 | v0.7.9 |

---

## Version History

| Version | Date | Milestone |
|---------|------|-----------|
| v0.7.9 | TBD | Phase 6 Week 11 - Audit Trail & History UI |
| v0.7.8 | 2026-01-29 | Phase 6 Week 10 - Dues UI (Session A) |
| v0.7.7 | 2026-01-29 | Phase 6 Week 9 - Documents Frontend |
| v0.7.6 | 2026-01-29 | Phase 6 Week 8 - Reports & Export |
| v0.7.5 | 2026-01-29 | Phase 6 Week 6 - Union Operations |
| v0.7.4 | 2026-01-29 | Phase 6 Week 5 - Members Landing |
| v0.7.3 | 2026-01-29 | Phase 6 Week 4 - Training Landing |
| v0.7.2 | 2026-01-29 | Phase 6 Week 3 - Staff Management |
| v0.7.1 | 2026-01-29 | Phase 6 Week 2 - Auth cookies + Dashboard |
| v0.7.0 | 2026-01-28 | Phase 4 Complete (Backend milestone) |

---

## Commands Cheat Sheet

```bash
# Start dev environment
docker-compose up -d

# Run all tests
pytest -v

# Run frontend tests only
pytest src/tests/test_frontend.py -v

# Run audit-related tests
pytest src/tests/test_audit*.py -v

# Run member notes tests
pytest src/tests/test_member_notes*.py -v

# Check code quality
ruff check . --fix && ruff format .

# Database migration
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Test audit immutability (should fail!)
# psql: UPDATE audit_logs SET notes = 'test' WHERE id = 1;

# Run API server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# View logs
docker-compose logs -f api
```

---

## Session Workflow

### Starting a Session
1. `git pull origin main`
2. `docker-compose up -d`
3. `pytest -v --tb=short` (verify green)
4. Check CLAUDE.md for current tasks

### Ending a Session
1. `pytest -v` (verify green)
2. `git status` (check for uncommitted changes)
3. Commit with conventional commit message
4. `git push origin main`
5. Update CLAUDE.md with session summary

### Audit-Specific Checks (Week 11)

**Before committing:**
- [ ] Any new member-related endpoint calls `audit_service.log_*`?
- [ ] New table added to `AUDITED_TABLES` if it contains user data?
- [ ] Sensitive field redaction tested?
- [ ] Immutability trigger verified?

---

## Files to Create/Modify (Week 11)

### New Files
```
src/
├── models/
│   └── member_note.py          # MemberNote model
├── schemas/
│   └── member_note.py          # Pydantic schemas
├── services/
│   ├── member_note_service.py  # CRUD service
│   └── audit_frontend_service.py  # Role-filtered audit queries
├── routers/
│   └── member_notes.py         # REST endpoints
├── templates/
│   ├── admin/
│   │   ├── audit_logs.html     # Audit log list page
│   │   └── _audit_row.html     # HTMX partial for table row
│   ├── components/
│   │   └── _audit_history.html # Reusable inline history
│   └── members/
│       └── _notes_section.html # Notes partial for member detail
└── tests/
    ├── test_member_notes.py    # Unit tests
    └── test_audit_ui.py        # Frontend tests
```

### Modified Files
```
src/
├── services/
│   └── audit_service.py        # Add member_notes to AUDITED_TABLES
├── templates/
│   ├── members/
│   │   └── detail.html         # Add notes + history sections
│   ├── students/
│   │   └── detail.html         # Add history section
│   └── components/
│       └── _sidebar.html       # Add Audit Logs nav item
└── alembic/versions/
    └── xxx_add_audit_immutability.py  # New migration
```

---

*Keep this checklist updated during each session!*
