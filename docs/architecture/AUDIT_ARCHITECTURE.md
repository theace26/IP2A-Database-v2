# Audit Architecture

> **Document Created:** February 3, 2026 (Batch 4b — reconstructed from project references)
> **Last Updated:** February 3, 2026
> **Version:** 1.0
> **Status:** ✅ Implemented (Week 11) — **Verify against actual implementation**
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1-19)

> **⚠️ Note:** This document was NOT updated from an existing source file — it was reconstructed from ADR-012, the continuity document, and project state references. It should be verified against the actual audit implementation in `src/` before being treated as authoritative. If the original `AUDIT_ARCHITECTURE.md` is found, merge this content with it.

---

## Related Documents

| Document | Location | Relationship |
|----------|----------|-------------|
| ADR-012 Audit Logging | `docs/decisions/ADR-012-audit-logging.md` | Architecture decision record for audit system |
| System Overview | `docs/architecture/SYSTEM_OVERVIEW.md` | Overall system architecture context |
| Authentication Architecture | `docs/architecture/AUTHENTICATION_ARCHITECTURE.md` | Auth events that generate audit entries |
| Phase 7 Referral & Dispatch Plan | `docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` | Phase 7 audit integration requirements |
| Phase 7 Implementation Plan v2 | `docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` | Phase 7 audit integration requirements |

---

## Implementation Status

| Component | Status | Shipped In | Notes |
|-----------|--------|-----------|-------|
| Audit log model | ✅ Complete | Week 11 | ORM model for audit entries |
| Immutability trigger | ✅ Complete | Week 11 | PostgreSQL trigger prevents UPDATE/DELETE |
| NLRA 7-year retention | ✅ Complete | Week 11 | Compliance with labor law record-keeping |
| Structured logging | ✅ Complete | Week 16 | Application-level structured logging (Sentry) |
| Audit API endpoints | ✅ Complete | Week 11 | Query/search audit records |
| Audit UI | ✅ Complete | Week 11 | Admin-facing audit log viewer |
| Phase 7 dispatch audit | 🔜 Planned | Phase 7 | Dispatch/registration actions must integrate |

---

## Overview

The IP2A audit system provides an immutable record of all significant data changes in the application. It is designed to meet NLRA (National Labor Relations Act) 7-year record retention requirements for union operations.

The system operates at two levels:

1. **Database-level immutability** — A PostgreSQL trigger prevents any `UPDATE` or `DELETE` operations on the audit log table. Once an audit entry is written, it cannot be modified or removed. This is the compliance backbone.

2. **Application-level logging** — Structured logging via Sentry (shipped Week 16) captures operational events, errors, and performance data. This supplements the audit log with runtime context.

---

## Architecture

### Core Principles

1. **Immutability** — Audit records are append-only. The PostgreSQL trigger enforces this at the database level, independent of application code. Even direct SQL access cannot modify audit entries without disabling the trigger (which requires superuser privileges).

2. **Completeness** — All significant data changes must be logged. This includes creates, updates, and deletes on core business entities (members, dues, organizations, training records, and — with Phase 7 — dispatch and registration actions).

3. **Attribution** — Every audit entry records who made the change (`user_id`), when it happened (`created_at`), and what changed (`entity_type`, `entity_id`, `action`, `old_value`, `new_value`).

4. **Queryability** — Audit records are indexed for efficient querying by entity, user, date range, and action type. The admin UI provides search and filter capabilities.

### Data Model

> **Verify:** The field names and types below are inferred from ADR-012 and project references. Check against the actual model in `src/models/`.

```python
# src/models/audit_log.py (VERIFY AGAINST ACTUAL IMPLEMENTATION)

class AuditLog(Base):
    """
    Immutable audit trail for all significant data changes.
    Protected by PostgreSQL trigger preventing UPDATE/DELETE.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    
    # What changed
    entity_type = Column(String(100), nullable=False, index=True)  # "Member", "DuesPayment", etc.
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False)                     # "create", "update", "delete"
    
    # Change details
    old_value = Column(JSON)                                        # Previous state (null for creates)
    new_value = Column(JSON)                                        # New state (null for deletes)
    
    # Attribution
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    ip_address = Column(String(45))                                 # IPv4 or IPv6
    
    # Context
    description = Column(Text)                                      # Human-readable summary
    
    # Timestamp (immutable — set once on creation)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
```

### Immutability Trigger

```sql
-- PostgreSQL trigger preventing modification of audit records (VERIFY AGAINST ACTUAL)
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log records cannot be modified or deleted (NLRA 7-year compliance)';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_immutability_trigger
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_modification();
```

### Retention Policy

- **Minimum retention:** 7 years (NLRA compliance)
- **Current policy:** Indefinite retention (no automated purge)
- **Future consideration:** Archive to cold storage after 7 years if table size becomes a concern. Must maintain queryability for compliance requests.

---

## Integration Points

### Current (Weeks 1-19)

The audit system currently captures changes to:

| Entity | Actions Logged | Shipped In |
|--------|---------------|-----------|
| **User** | Login, logout, failed login, lockout, password change | Week 1 |
| **Member** | Create, update, status changes | Week 5 |
| **Organization** | Create, update | Week 6 |
| **DuesPayment** | Payment recorded, Stripe webhook events | Week 10-11 |
| **Document** | Upload, download, delete | Week 8 |
| **Training records** | Enrollment, completion, grade changes | Week 4 |
| **Settings** | Configuration changes | Week 12 |

> **⚠️ `locked_until` datetime pattern:** The User model uses a `locked_until` datetime field (NOT a boolean `is_locked`). Audit entries for account lockout should log the `locked_until` value, not a boolean.

### Phase 7 (Planned)

Phase 7 introduces high-volume dispatch operations that require audit coverage:

| Entity | Actions to Log | Priority |
|--------|---------------|----------|
| **BookRegistration** | Register, re-sign, check mark, roll-off, dispatch, restore | 🔴 CRITICAL |
| **Dispatch** | Dispatch, check-in, termination, short call restore | 🔴 CRITICAL |
| **LaborRequest** | Create, fill, cancel, expire | 🔴 CRITICAL |
| **JobBid** | Submit, accept, reject, withdraw | 🟡 HIGH |
| **MemberTransaction** | Payment recorded, void, adjustment | 🔴 CRITICAL |
| **MemberFinancial** | Balance updates, fee tracking | 🟡 HIGH |
| **MemberSkill** | Add, verify, expire | 🟢 MEDIUM |

> **Dual audit in Phase 7:** The Referral & Dispatch Plan introduces a `RegistrationActivity` model that provides referral-specific audit data for operational queries and reports. This is a domain-specific audit trail that supplements (not replaces) the global audit log. Both must fire for dispatch and registration actions:
> - **Global audit log** → NLRA compliance, immutable, 7-year retention
> - **RegistrationActivity** → Operational queries, report generation (B-17, A-11, AP-02)

### Volume Considerations

Phase 7 dispatch operations will significantly increase audit log volume. For a local with ~3,000 members:

| Operation | Est. Daily Volume | Annual Volume |
|-----------|-------------------|---------------|
| Dispatches | 10-30 | ~5,000-8,000 |
| Bid submissions | 20-50 | ~6,000-13,000 |
| Re-signs | 50-100 | ~15,000-25,000 |
| Check marks | 10-30 | ~3,000-8,000 |
| **Total new audit entries** | **~100-200/day** | **~30,000-55,000/year** |

This is manageable for PostgreSQL with proper indexing. Monitor table size after Phase 7 launch and consider partitioning by year if needed.

---

## Querying Audit Records

### Common Query Patterns

```python
# Verify these patterns against actual service implementation

# 1. All changes to a specific member
audit_service.get_by_entity("Member", member_id)

# 2. All actions by a specific user
audit_service.get_by_user(user_id, date_from, date_to)

# 3. All dispatch actions on a specific date
audit_service.get_by_entity_type("Dispatch", date_from=today, date_to=today)

# 4. All changes in a date range (compliance request)
audit_service.get_all(date_from=seven_years_ago, date_to=today)
```

### Admin UI

The audit log viewer (shipped Week 11) provides:
- Search by entity type, entity ID, user, date range
- Filter by action type (create, update, delete)
- Detail view showing old/new values as a diff
- Export to CSV (via openpyxl, Week 14)

---

## Security Considerations

1. **Trigger protection** — The immutability trigger cannot be bypassed by application code. Only a database superuser can disable it (and this itself would be logged by PostgreSQL's built-in logging).

2. **No soft deletes** — Audit records are never soft-deleted. The trigger prevents both hard and soft deletes.

3. **PII in audit records** — Audit entries may contain PII in `old_value`/`new_value` JSON fields. Access to the audit log should be restricted to admin roles. EEOC and demographics data in Phase 7 reports requires special handling.

4. **Connection pooling** — Week 16 production hardening added connection pooling. Audit writes should use the same pooled connections — do not open separate database connections for audit logging.

5. **Sentry integration** — Week 16 added Sentry for error tracking. Audit log write failures should generate Sentry alerts since they represent a compliance risk.

---

## Backup & Recovery

- **Railway backups** — Railway provides automated PostgreSQL backups. Audit data is included in these backups.
- **Manual backups** — Week 17 post-launch ops added backup scripts (`/scripts/backup/`). Audit data is included.
- **Recovery testing** — Backup restoration should verify that the immutability trigger is intact and functional after restore.

---

## 📝 End-of-Session Documentation (MANDATORY)

**Before completing ANY session:**

> Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

Document Version: 1.0
Last Updated: February 3, 2026
Previous Version: N/A (reconstructed from project references — ADR-012, continuity document, project state)
