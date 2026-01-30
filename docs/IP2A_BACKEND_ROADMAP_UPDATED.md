# IP2A Database - Backend Development Roadmap

> **Purpose:** Master roadmap for backend development with timelines, milestones, and acceptance criteria.
> **Created:** January 27, 2026
> **Last Updated:** January 29, 2026
> **For:** Claude Code implementation sessions
> **Time Budget:** 5-10 hours/week (estimates include 50% buffer)

---

## Executive Summary

| Phase | Focus | Duration | Hours | Status |
|-------|-------|----------|-------|--------|
| Phase 0 | Documentation & Structure | Week 1 | 5-8 hrs | ✅ Complete |
| Phase 1 | Foundation (Auth + Files) | Weeks 2-10 | 55-70 hrs | ✅ Complete |
| Phase 2 | Union Ops + Training | Weeks 11-18 | 55-70 hrs | ✅ Complete |
| Phase 3 | Documents (S3/MinIO) | Weeks 19-22 | 20-30 hrs | ✅ Complete |
| Phase 4 | Dues Tracking | Weeks 23-27 | 35-45 hrs | ✅ Complete |
| Phase 5 | Access DB Migration | TBD | 45-70 hrs | ⬜ Blocked (Awaiting Approval) |
| **Phase 6** | **Frontend Build** | **Weeks 28-40** | **60-80 hrs** | **🟡 In Progress** |
| Phase 7 | Production Hardening | Weeks 41-44 | 25-35 hrs | ⬜ Pending |

**Total Estimated Timeline:** 44 weeks (~11 months)
**Total Estimated Hours:** 300-410 hours

**Note on Phase 5:** This phase is intentionally blocked until the Access DB owner approves. Phases 1-4 serve as proof-of-concept. Phase 5 begins only after demo and approval.

---

## Technology Decisions (Confirmed)

| Component | Choice | ADR |
|-----------|--------|-----|
| Database | PostgreSQL 16 | ADR-001 |
| Backend Framework | FastAPI + SQLAlchemy | — |
| Frontend | Jinja2 + HTMX + Alpine.js + DaisyUI | ADR-002 |
| Authentication | JWT (access + refresh tokens) + HTTP-only cookies | ADR-003 |
| File Storage | MinIO (dev) / B2 or S3 (prod) | ADR-004 |
| CSS Framework | Tailwind CSS + DaisyUI | ADR-005 |
| Background Jobs | Abstract TaskService (FastAPI now, Celery-ready) | ADR-006 |
| Email | SendGrid | — |
| Observability | Grafana + Loki + Promtail (Docker) | ADR-007 |
| Audit Logging | PostgreSQL-based, role-filtered, NLRA compliant | ADR-008 |
| Deployment | Union server (Phase 1-4) → Cloud (Phase 7+) | — |

### Audit Logging Strategy

**CRITICAL: All member information changes MUST be audited for NLRA compliance.**

We use a **two-tier logging architecture**:

1. **Business Audit Trail (PostgreSQL `audit_logs` table)**
   - Legal compliance, accountability, "who did what"
   - 7-year retention (NLRA requirement)
   - Immutable (database triggers prevent UPDATE/DELETE)
   - Role-based access with field-level redaction
   - Archived to S3 Glacier after 3 years

2. **Technical/System Logs (Grafana + Loki)**
   - Operations, debugging, performance monitoring
   - 30-90 day retention
   - For sysadmin/developer use only

**Tables requiring mandatory audit:**
- `members` - All member data changes
- `member_notes` - Staff notes on members
- `member_employments` - Employment history
- `students` - Training program participants
- `users` - System user accounts
- `dues_payments` - Financial transactions
- `grievances` - Legal/labor relations
- `benevolence_applications` - Financial assistance

### Observability Strategy
- Development: Console/file logs (structured JSON)
- Production: Grafana + Loki + Promtail stack (all Docker-based, portable)
- Error tracking: Sentry free tier (added in Phase 7)

---

## Phase 6: Frontend Build (Weeks 28-40)

**Goal:** Complete, usable web interface for all backend functionality.

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

---

### Week 11: Audit Trail & Member History UI

**Goal:** Complete audit trail visibility for authorized users, with role-based access control.

**Time Estimate:** 8-12 hours
**Dependency:** Week 10 complete

#### 11.1 Database Completeness

| Task | Est. | Notes |
|------|------|-------|
| Add immutability trigger to `audit_logs` table | 1 hr | Prevent UPDATE/DELETE at DB level |
| Create `member_notes` table and model | 2 hrs | Staff notes with audit integration |
| Add `member_notes` to `AUDITED_TABLES` | 15 min | Automatic audit of note changes |
| Create member notes service (CRUD) | 1 hr | Standard service layer pattern |
| Create member notes router | 1 hr | REST endpoints |
| Tests for member notes | 1 hr | Unit + integration |

**Immutability Trigger (CRITICAL):**
```sql
-- Migration: add_audit_immutability_trigger.py
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable. UPDATE and DELETE operations are prohibited.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_immutable
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_modification();

-- Belt and suspenders: revoke at application user level
REVOKE UPDATE, DELETE ON audit_logs FROM ip2a_app_user;
```

**Member Notes Model:**
```python
# src/models/member_note.py
class MemberNote(Base):
    __tablename__ = "member_notes"
    
    id: int (PK)
    member_id: int (FK to members)
    note_text: str (Text, not null)
    visibility: str  # 'staff_only', 'officers', 'all_authorized'
    created_by: int (FK to users)
    created_at: datetime
    updated_at: datetime
    is_deleted: bool (soft delete)
```

#### 11.2 Audit RBAC Permissions

| Task | Est. | Notes |
|------|------|-------|
| Define audit permission constants | 30 min | `audit:view_own`, `audit:view_all`, etc. |
| Add permissions to Role model/seeder | 30 min | Map to existing roles |
| Create `AuditFrontendService` with role filtering | 2 hrs | Query with redaction logic |
| Add field-level redaction for sensitive data | 1 hr | SSN, bank info masked by role |
| Tests for role-based access | 1 hr | Verify proper filtering |

**Permission Matrix:**
```python
class AuditPermissions:
    VIEW_OWN_ENTITY_HISTORY = "audit:view_own"      # Staff: entities they touched
    VIEW_ALL_MEMBER_AUDITS = "audit:view_members"   # Organizers: all member changes
    VIEW_ALL_AUDITS = "audit:view_all"              # Admin: everything
    VIEW_USER_ACTIVITY = "audit:view_users"         # Security: login/access tracking
    EXPORT_AUDITS = "audit:export"                  # Compliance: download reports

# Role mapping
ROLE_PERMISSIONS = {
    "staff": ["audit:view_own"],
    "organizer": ["audit:view_own", "audit:view_members"],
    "officer": ["audit:view_members", "audit:view_users"],
    "admin": ["audit:view_all", "audit:view_users", "audit:export"],
}
```

**Redaction Rules:**
```python
SENSITIVE_FIELDS = {
    "ssn", "social_security", "bank_account", "routing_number",
    "password_hash", "token_hash"
}

def redact_for_role(values: dict, role: str) -> dict:
    """Redact sensitive fields based on user role."""
    if role == "admin":
        return values  # Admins see everything
    
    if values is None:
        return None
    
    redacted = {}
    for key, val in values.items():
        if key in SENSITIVE_FIELDS:
            redacted[key] = "[REDACTED]"
        else:
            redacted[key] = val
    return redacted
```

#### 11.3 Audit Trail UI

| Task | Est. | Notes |
|------|------|-------|
| Audit log list page with filters | 2 hrs | Table, date range, user, action type |
| HTMX search/filter for audit logs | 1 hr | 300ms debounce, live results |
| Audit log detail view | 1 hr | Show old/new values diff |
| Sidebar nav entry for Audit Logs | 15 min | Under Admin section |
| Tests for audit UI | 1 hr | Authorization + display |

**Audit List Page Features:**
- Filter by: date range, user, entity type, action type
- Columns: timestamp, user, action, entity, summary
- Click to expand: full old/new values (with redaction)
- Export button (for authorized roles)

#### 11.4 Inline History on Entity Pages

| Task | Est. | Notes |
|------|------|-------|
| Create `_audit_history.html` partial | 1 hr | Reusable HTMX component |
| Add to member detail page | 30 min | "Recent Activity" section |
| Add to student detail page | 30 min | Same pattern |
| Add to grievance detail page | 30 min | Same pattern |
| HTMX endpoint for entity history | 1 hr | `/audit/entity/{type}/{id}` |

**Inline History Component:**
```html
<!-- templates/components/_audit_history.html -->
<div class="card bg-base-100 shadow-sm">
    <div class="card-body">
        <h3 class="card-title text-lg">Recent Activity</h3>
        <div hx-get="/audit/entity/{{ entity_type }}/{{ entity_id }}"
             hx-trigger="load"
             hx-swap="innerHTML">
            <span class="loading loading-spinner"></span>
        </div>
        <div class="card-actions justify-end">
            <a href="/admin/audit-logs?entity_type={{ entity_type }}&entity_id={{ entity_id }}"
               class="btn btn-sm btn-ghost">
                View Full History →
            </a>
        </div>
    </div>
</div>
```

#### 11.5 Member Notes UI

| Task | Est. | Notes |
|------|------|-------|
| Notes section on member detail page | 1 hr | List existing notes |
| Add note modal/form | 1 hr | HTMX submit |
| Visibility selector (staff/officers/all) | 30 min | Dropdown in form |
| Notes filtered by user permission | 30 min | Service layer filtering |
| Tests for notes UI | 1 hr | CRUD + visibility |

**Member Detail Page Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  MEMBER: John Smith (#1234)                                     │
├─────────────────────────────────────────────────────────────────┤
│  [Info Tab] [Employment Tab] [Dues Tab] [Notes Tab] [History]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  NOTES                                          [+ Add Note]    │
│  ─────────────────────────────────────────────────────────────  │
│  2026-01-29 @ 2:15 PM by Jane Smith (Staff Only)                │
│  "Referred to FSS - having hard time with dues"                 │
│                                                                 │
│  2026-01-28 @ 10:30 AM by Jane Smith (All Authorized)           │
│  "Called about dues inquiry, resolved"                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RECENT ACTIVITY                                [View Full →]   │
│  ─────────────────────────────────────────────────────────────  │
│  2026-01-29 @ 2:15 PM - Jane Smith created note                 │
│  2026-01-28 @ 11:00 AM - Jane Smith updated status              │
│  2026-01-27 @ 9:00 AM - Bob Admin viewed record                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Acceptance Criteria (Week 11):**
- [ ] `audit_logs` table has immutability trigger (verified with test)
- [ ] `member_notes` table created with proper model/service/router
- [ ] Member notes automatically audited (appears in audit trail)
- [ ] Audit log list page works with role-based filtering
- [ ] Sensitive fields redacted for non-admin users
- [ ] Member detail page shows notes section
- [ ] Member detail page shows recent activity inline
- [ ] Export button works for authorized roles
- [ ] All tests passing (target: +15-20 new tests)

---

### Week 12: Settings & Profile

| Task | Status |
|------|--------|
| User profile page (view own info) | ⬜ Pending |
| Password change form | ⬜ Pending |
| System settings page (admin only) | ⬜ Pending |
| Email notification preferences | ⬜ Pending |

---

## Phase 7: Production Hardening (Weeks 41-44)

**Goal:** Production-ready system with monitoring, security, and operational excellence.

### Milestone 7.1: Observability Stack (Grafana + Loki)
**Time Estimate:** 6-8 hours

| Task | Status |
|------|--------|
| Add Loki to docker-compose | ⬜ Pending |
| Add Promtail to docker-compose | ⬜ Pending |
| Add Grafana to docker-compose | ⬜ Pending |
| Configure structured JSON logging | ⬜ Pending |
| Create Grafana dashboards | ⬜ Pending |
| Set up alerting rules | ⬜ Pending |
| Document monitoring runbook | ⬜ Pending |

**Grafana Dashboards to Create:**
| Dashboard | Metrics |
|-----------|---------|
| API Health | Request rate, error rate, latency (p50/p95/p99) |
| Authentication | Login attempts, failures, lockouts |
| Background Tasks | Queue depth, success/failure rate, duration |
| Database | Query count, slow queries, connection pool |
| Business | Active users, new students, certifications expiring |
| **Audit Activity** | **Records viewed, changes made, by user, by entity** |

**Alerting Rules:**
| Alert | Condition | Action |
|-------|-----------|--------|
| High Error Rate | >5% 5xx errors in 5 min | Email + Slack |
| Auth Failures | >10 failed logins in 1 min | Email |
| Slow Queries | >5 queries over 1s in 5 min | Log |
| **Bulk Data Access** | **>100 member reads by single user in 1 hr** | **Email** |
| **Mass Deletion** | **>10 DELETE actions in 5 min** | **Email immediately** |

### Milestone 7.2: Security Hardening
**Time Estimate:** 6-8 hours

| Task | Status |
|------|--------|
| Security audit (OWASP checklist) | ⬜ Pending |
| SSL/TLS configuration | ⬜ Pending |
| Rate limiting on all public endpoints | ⬜ Pending |
| CORS properly configured | ⬜ Pending |
| CSRF protection verified | ⬜ Pending |
| **Audit log immutability verified in production** | ⬜ Pending |
| Backup automation (daily, tested restore) | ⬜ Pending |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Time availability drops | Medium | High | Realistic estimates, flexible scope |
| Technical blockers | Low | Medium | Architecture docs, fallback options |
| Scope creep | Medium | Medium | Strict phase boundaries, defer to backlog |
| Data migration issues | Medium | High | Parallel testing, rollback plan |
| Integration API changes | Low | Medium | Version pinning, adapter pattern |
| Access DB approval delayed | Medium | Low | Phase 5 is independent; system works without it |
| **Audit compliance gap** | **Low** | **High** | **Week 11 dedicated to completeness** |
| **Unauthorized data access** | **Low** | **High** | **RBAC on audit logs, monitoring alerts** |

---

## Backlog (Future Phases)

**Completed (Originally Backlogged):**
- [x] Dues tracking module - ✅ Phase 4 Complete
- [x] Grievance tracking - ✅ Phase 2 Complete
- [x] Benevolence fund - ✅ Phase 2 Complete
- [x] SALTing activities module - ✅ Phase 2 Complete

**Phase 8+ Candidates:**
- [ ] Member self-service portal (web + mobile)
- [ ] Referral/dispatch module
- [ ] Multi-local support (other IBEW locals)
- [ ] LaborPower data import (for unified reporting)
- [ ] Mobile app (native iOS/Android)
- [ ] Celery + Redis upgrade (when scheduling needed)
- [ ] Advanced audit analytics (ML anomaly detection)
- [ ] Audit log export automation (scheduled compliance reports)

**Deliberately NOT Building:**
- LaborPower replacement (use their system, sync data)
- QuickBooks replacement (integrate, don't replace)
- Custom payment processing (use Stripe/Square)

---

## Session Handoff Notes

### For Claude Code Sessions

When starting a session, check:
1. Current milestone in progress
2. Last completed task
3. Any blockers documented
4. Branch status

Typical session goal: Complete 1-2 tasks from current milestone.

### Audit-Specific Reminders

**BEFORE making changes to member-related code:**
1. Verify the table is in `AUDITED_TABLES` in `audit_service.py`
2. Ensure service layer calls appropriate `log_*` function
3. Test that changes appear in audit trail
4. Verify old/new values are captured correctly

**BEFORE deploying to production:**
1. Verify `audit_logs` immutability trigger exists
2. Test that UPDATE/DELETE on `audit_logs` fails
3. Verify role-based redaction works
4. Test audit export for compliance officer role

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-27 | Initial roadmap created |
| 1.1 | 2026-01-28 | Updated backlog - marked Phase 2 and Phase 4 items as complete |
| 1.2 | 2026-01-29 | Added Week 11 (Audit Trail & Member History UI), ADR-008, audit strategy |

---

*Document created: January 27, 2026*
*Last updated: January 29, 2026*
