# ADR-008: Audit Logging Architecture

## Status
Accepted

## Date
2026-01-29

## Context

IP2A Database manages sensitive member information subject to:
- **NLRA (National Labor Relations Act)** - 7-year record retention requirement
- **Union member privacy expectations** - Who accessed their data, when, why
- **Internal accountability** - Staff actions must be traceable
- **Legal discovery** - Must produce audit trail for grievances, arbitration

We need a comprehensive audit system that:
1. Tracks ALL changes to member-related data
2. Tracks who viewed sensitive records
3. Cannot be tampered with (immutable)
4. Provides role-appropriate visibility
5. Supports compliance reporting and export
6. Handles high volume without performance impact

## Decision

We implement a **two-tier logging architecture**:

### Tier 1: Business Audit Trail (PostgreSQL)

**Purpose:** Legal compliance, accountability, "who did what to whom"

**Storage:** PostgreSQL `audit_logs` table with JSONB for flexibility

**Retention:** 
- 0-3 years: Online in PostgreSQL (fast queries)
- 3-7 years: Archived to S3 Glacier (cold storage)
- 7+ years: Deleted per retention policy

**Immutability:** Enforced via database trigger preventing UPDATE/DELETE

**Schema:**
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(50) NOT NULL,
    action VARCHAR(10) NOT NULL,  -- READ, CREATE, UPDATE, DELETE, BULK_READ
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    notes TEXT
);
```

### Tier 2: Technical/System Logs (Grafana + Loki)

**Purpose:** Operations, debugging, performance monitoring

**Storage:** Loki (log aggregation) with Promtail (shipping)

**Retention:** 30-90 days (rotates automatically)

**Access:** Developers, sysadmins only (not exposed in application UI)

### Role-Based Access Control

| Role | Audit Permissions |
|------|-------------------|
| Staff | View history of entities they touched |
| Organizer | View all member audit history |
| Officer | View all member + user audit history |
| Admin | Full access, no redaction, export capability |

### Field-Level Redaction

Sensitive fields are masked for non-admin users:
- `ssn`, `social_security` → `[REDACTED]`
- `bank_account`, `routing_number` → `[REDACTED]`
- `password_hash`, `token_hash` → `[REDACTED]`

### Tables Requiring Audit

All tables containing member-related or sensitive data:
- `members` - Core member data
- `member_notes` - Staff notes on members
- `member_employments` - Work history
- `students` - Training participants
- `users` - System accounts
- `dues_payments` - Financial transactions
- `grievances` - Labor relations
- `benevolence_applications` - Financial assistance
- `credentials` - Certifications

## Consequences

### Positive
- **NLRA Compliant** - 7-year retention with archival
- **Tamper-Proof** - Database trigger prevents modification
- **Role-Appropriate** - Users see only what they're authorized for
- **Complete Trail** - Every change to member data is captured
- **Queryable** - Can answer "show me all changes to member X"
- **Exportable** - Compliance officers can generate reports

### Negative
- **Storage Growth** - Audit logs grow with usage (~200K-500K rows/month estimated)
- **Write Overhead** - Every audited operation has second INSERT
- **Query Complexity** - Role-based filtering adds logic

### Mitigations
- Partitioning by month for large tables
- Archival job moves old logs to cold storage
- Indexes on common query patterns (table_name, record_id, changed_at)

## Implementation Components

| Component | Location | Purpose |
|-----------|----------|---------|
| AuditLog model | `src/models/audit_log.py` | SQLAlchemy model |
| Audit service | `src/services/audit_service.py` | Logging functions |
| Audit context middleware | `src/middleware/audit_context.py` | Capture user/IP |
| Audit API endpoints | `src/routers/audit_logs.py` | REST access (read-only) |
| Maintenance script | `scripts/audit_maintenance.py` | Archive/delete jobs |
| Immutability trigger | Migration | Prevent UPDATE/DELETE |

## Alternatives Considered

### Option A: Application-Only Logging
- Log only in application code, no database constraint
- **Rejected:** Can be bypassed by direct database access

### Option B: PostgreSQL Audit Extension (pgAudit)
- Use PostgreSQL extension for automatic logging
- **Rejected:** Less control over what's logged, harder to query

### Option C: Event Sourcing
- Store all state changes as events, reconstruct current state
- **Rejected:** Over-engineering for our use case, complex to implement

### Option D: Third-Party Audit Service
- Use external service like Audit Board, LogRhythm
- **Rejected:** Cost, data sovereignty concerns, external dependency

## References

- [NLRA Record Retention Requirements](https://www.nlrb.gov/)
- [PostgreSQL Trigger Documentation](https://www.postgresql.org/docs/current/plpgsql-trigger.html)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

---

*This ADR documents the audit logging architecture for NLRA compliance and internal accountability.*
