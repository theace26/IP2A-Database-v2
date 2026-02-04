# Audit API Reference

> **Document Created:** February 3, 2026
> **Last Updated:** February 3, 2026
> **Version:** v0.9.4-alpha
> **Status:** Implemented (Week 11) — Phase 7 Expansion Planned
> **Related ADRs:** [ADR-008](../decisions/ADR-008-audit-logging.md), [ADR-012](../decisions/ADR-012-audit-logging-strategy.md)

---

## Overview

The audit system provides NLRA-compliant, immutable logging of all changes to member-related data. It enforces a 7-year retention requirement with role-based access controls and sensitive field redaction.

**Architecture:** Two-tier design — business audit trail (PostgreSQL `audit_logs` table) for compliance, plus technical/system logs (Sentry + structured JSON logging) for operations.

---

## Architecture Components

| Component | Location | Purpose |
|-----------|----------|---------|
| AuditLog model | `src/models/audit_log.py` | SQLAlchemy ORM model for `audit_logs` table |
| AuditService | `src/services/audit_service.py` | Write-side: logging create/read/update/delete operations |
| AuditFrontendService | `src/services/audit_frontend_service.py` | Read-side: role-filtered queries, redaction, stats |
| AuditPermission | `src/core/permissions.py` | Permission enum and role-to-permission mapping |
| Audit Frontend Router | `src/routers/audit_frontend.py` | UI endpoints at `/admin/audit-logs/*` |
| Audit Middleware | `src/middleware/audit_middleware.py` | Request context injection (user, IP, timestamp) |
| Immutability Triggers | Migration `h3c4d5e6f7g8` | PostgreSQL BEFORE UPDATE/DELETE triggers |

---

## Frontend Endpoints

All endpoints require authentication via HTTP-only cookie. Access is restricted by role.

### `GET /admin/audit-logs`

**Purpose:** Main audit viewer page with stats dashboard and filter controls.

**Access:** Admin, Officer

**Response:** HTML page with:
- Stats cards: total logs, logs this week, logs today
- Filter controls: table, action, date range, search query
- Paginated results table (loaded via HTMX)

---

### `GET /admin/audit-logs/search`

**Purpose:** HTMX endpoint returning filtered, paginated audit log rows.

**Access:** Admin, Officer, Staff (scope limited by role)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table` | string | Filter by table name (e.g., `members`, `dues_payments`) |
| `action` | string | Filter by action type (`CREATE`, `READ`, `UPDATE`, `DELETE`) |
| `date_from` | date | Start of date range |
| `date_to` | date | End of date range |
| `q` | string | Search query (matches record fields, user info) |
| `page` | int | Page number (default: 1) |
| `per_page` | int | Results per page (default: 25) |

**Response:** HTML partial (`_audit_table.html`) — paginated table with action badges.

**Role Scoping:**
- **Staff:** See only own actions (`VIEW_OWN`)
- **Officer:** See member and user actions (`VIEW_MEMBERS`, `VIEW_USERS`)
- **Admin:** See all actions (`VIEW_ALL`)

---

### `GET /admin/audit-logs/detail/{log_id}`

**Purpose:** Detailed view of a single audit log entry with before/after value comparison.

**Access:** Admin, Officer (Staff can view own entries only)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `log_id` | int | Audit log entry ID |

**Response:** HTML page with:
- Timestamp, user, action, table, record ID
- JSON diff view: old values vs. new values (for UPDATE actions)
- Sensitive fields redacted for non-admin users

---

### `GET /admin/audit-logs/export`

**Purpose:** CSV export of audit logs matching current filters.

**Access:** Admin only (`EXPORT` permission)

**Query Parameters:** Same as `/admin/audit-logs/search`

**Response:** `text/csv` file download with headers:
- `id`, `timestamp`, `user_id`, `username`, `action`, `table_name`, `record_id`, `old_values`, `new_values`, `ip_address`

**Note:** Sensitive fields are NOT redacted in admin CSV exports — these are compliance records.

---

### `GET /admin/audit-logs/entity/{table_name}/{record_id}`

**Purpose:** Inline audit history for a specific entity. Used on member detail pages via HTMX.

**Access:** Admin, Officer, Staff (scope limited by role)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table_name` | string | Source table (e.g., `members`, `students`) |
| `record_id` | int | Record primary key |

**Response:** HTML partial (`_audit_history.html`) — DaisyUI timeline-vertical layout with color-coded action indicators.

---

## Service Layer API

### Write-Side: `audit_service.py`

These functions are called from service layer code when data changes occur. They are NOT HTTP endpoints — they're internal Python functions.

```python
from src.services import audit_service
from src.middleware import get_audit_context

# Log a create operation
audit_service.log_create(
    db=db,
    table_name="members",
    record_id=record.id,
    new_values=record_to_dict(record),
    **get_audit_context()
)

# Log an update operation
audit_service.log_update(
    db=db,
    table_name="members",
    record_id=record.id,
    old_values=old_dict,
    new_values=new_dict,
    **get_audit_context()
)

# Log a delete operation
audit_service.log_delete(
    db=db,
    table_name="members",
    record_id=record.id,
    old_values=record_to_dict(record),
    **get_audit_context()
)

# Log a read operation (for sensitive data access)
audit_service.log_read(
    db=db,
    table_name="members",
    record_id=record.id,
    **get_audit_context()
)
```

### Read-Side: `audit_frontend_service.py`

Handles role-filtered queries and sensitive field redaction for the UI layer.

- Determines user's primary role (highest privilege) for filtering
- Applies `redact_sensitive_fields()` for non-admin users
- Computes stats (total, this week, today)
- Supports filtering by table, action, date range, search query

---

## AUDITED_TABLES

All tables in this list trigger automatic audit logging when records are created, updated, or deleted.

### Current (v0.9.4-alpha)

| Table | Tracked Actions | Since |
|-------|-----------------|-------|
| `members` | READ, CREATE, UPDATE, DELETE | Phase 2 |
| `member_notes` | CREATE, UPDATE, DELETE | Week 11 |
| `member_employments` | CREATE, UPDATE, DELETE | Phase 2 |
| `students` | READ, CREATE, UPDATE, DELETE | Phase 2 |
| `users` | CREATE, UPDATE, DELETE | Phase 1 |
| `dues_payments` | CREATE, UPDATE, DELETE | Phase 4 |
| `grievances` | All actions | Phase 2 |
| `benevolence_applications` | All actions | Phase 2 |

### Phase 7 Additions (Planned)

| Table | Tracked Actions | Why |
|-------|-----------------|-----|
| `registrations` | All actions | Out-of-work book entries — dispatch ordering integrity |
| `dispatches` | All actions | Referral transactions — complete chain of custody |
| `check_marks` | All actions | Penalty system — member rights protection |

**Location:** `AUDITED_TABLES` list in `src/services/audit_service.py`

---

## Permissions Model

Defined in `src/core/permissions.py`:

### AuditPermission Enum

| Permission | Description |
|------------|-------------|
| `VIEW_OWN` | See only your own actions |
| `VIEW_MEMBERS` | See actions on member-related tables |
| `VIEW_USERS` | See actions on user account tables |
| `VIEW_ALL` | See all audit log entries |
| `EXPORT` | Export audit logs as CSV |

### Role-to-Permission Mapping

| Role | Permissions |
|------|-------------|
| **Staff** | `VIEW_OWN` |
| **Organizer** | `VIEW_OWN` |
| **Instructor** | `VIEW_OWN` |
| **Officer** | `VIEW_OWN`, `VIEW_MEMBERS`, `VIEW_USERS` |
| **Admin** | `VIEW_OWN`, `VIEW_MEMBERS`, `VIEW_USERS`, `VIEW_ALL`, `EXPORT` |

---

## Sensitive Field Redaction

Non-admin users see `[REDACTED]` for these field patterns in old/new values:

- Social Security Numbers (`ssn`, `social_security`)
- Passwords and hashes (`password`, `hashed_password`)
- Bank account information (`bank_account`, `routing_number`)
- API keys and tokens (`api_key`, `secret`, `token`)

**Implementation:** `redact_sensitive_fields()` in `audit_frontend_service.py`

**Exception:** Admin CSV exports include unredacted values for compliance purposes.

---

## Data Model

### `audit_logs` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PRIMARY KEY | Auto-increment ID |
| `timestamp` | TIMESTAMP WITH TIME ZONE | When the action occurred |
| `user_id` | INTEGER (FK → users) | Who performed the action |
| `action` | VARCHAR | CREATE, READ, UPDATE, DELETE |
| `table_name` | VARCHAR | Source table name |
| `record_id` | INTEGER | Primary key of affected record |
| `old_values` | JSONB | Previous state (for UPDATE/DELETE) |
| `new_values` | JSONB | New state (for CREATE/UPDATE) |
| `ip_address` | VARCHAR | Client IP address |

### Immutability

PostgreSQL triggers prevent any modification after insertion:

- **`prevent_audit_modification` trigger function** — raises exception on UPDATE or DELETE
- **BEFORE UPDATE trigger** — blocks all UPDATE operations
- **BEFORE DELETE trigger** — blocks all DELETE operations
- **Migration:** `h3c4d5e6f7g8_add_audit_logs_immutability_trigger.py`
- **Tests:** `src/tests/test_audit_immutability.py` (4 tests)

---

## Compliance Requirements

| Requirement | Implementation |
|-------------|----------------|
| **Retention** | 7 years minimum (NLRA) |
| **Immutability** | PostgreSQL triggers prevent UPDATE/DELETE |
| **Access Control** | Role-based with 5-tier permission model |
| **Sensitive Data** | Field-level redaction for non-admin roles |
| **Archive** | Logs older than 3 years → S3 Glacier (planned) |
| **Archival Script** | `scripts/archive_audit_logs.sh` (Week 17) |

---

## UI Components

| Component | Location | Used In |
|-----------|----------|---------|
| Audit log viewer page | `src/templates/admin/audit_logs.html` | `/admin/audit-logs` |
| Audit detail page | `src/templates/admin/audit_detail.html` | `/admin/audit-logs/detail/{id}` |
| Paginated table partial | `src/templates/admin/partials/_audit_table.html` | HTMX search results |
| Inline timeline partial | `src/templates/components/_audit_history.html` | Member detail pages |
| Sidebar link | `src/templates/components/_sidebar.html` | Admin/Officer only |

---

## Adding Audit Logging to New Endpoints

When building new features that modify audited data:

1. **Verify the table is in `AUDITED_TABLES`** in `src/services/audit_service.py`
2. **Call the appropriate log function** from the service layer (not the router)
3. **Capture old values before update** — query the record before modifying it
4. **Use `get_audit_context()`** to inject user ID, IP address, timestamp
5. **Test that changes appear** in the audit trail
6. **Verify old/new values** are captured correctly

```python
# Example: Adding audit to a new service method
def update_record(self, db: Session, record_id: int, data: UpdateSchema):
    record = db.query(MyModel).get(record_id)
    old_values = record_to_dict(record)

    # Apply updates
    for key, value in data.dict(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()

    # Log the change
    audit_context = get_audit_context()
    audit_service.log_update(
        db=db,
        table_name="my_table",
        record_id=record.id,
        old_values=old_values,
        new_values=record_to_dict(record),
        **audit_context
    )

    return record
```

---

## Tests

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `src/tests/test_audit_immutability.py` | 4 | Trigger enforcement (UPDATE/DELETE blocked) |
| `src/tests/test_audit_frontend.py` | 20 | Role permissions, redaction, filtering, CSV export, inline history |
| **Total** | **24** | |

---

## 🔄 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

---

## Cross-References

| Document | Location |
|----------|----------|
| ADR-008: Audit Logging | `/docs/decisions/ADR-008-audit-logging.md` |
| ADR-012: Audit Logging Strategy | `/docs/decisions/ADR-012-audit-logging-strategy.md` |
| Audit Architecture | `/docs/architecture/AUDIT_ARCHITECTURE.md` |
| Audit Maintenance Runbook | `/docs/runbooks/audit-maintenance.md` |
| Permissions Model | `/src/core/permissions.py` |
| Coding Standards | `/docs/standards/coding-standards.md` |
| Testing Strategy | `/docs/standards/testing-strategy.md` |

---

*Document Version: 1.0*
*Last Updated: February 3, 2026*
