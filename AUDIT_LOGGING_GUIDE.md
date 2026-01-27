# Audit Logging Implementation Guide

## Overview

The IP2A Database v2 includes comprehensive audit logging that tracks **ALL** access and modifications to user-related data, including:

- **READ**: Viewing individual records
- **BULK_READ**: Listing/searching records
- **CREATE**: Creating new records
- **UPDATE**: Modifying existing records
- **DELETE**: Deleting/soft-deleting records

This provides a complete audit trail for compliance, security, and debugging.

---

## Architecture

### Components

1. **AuditLog Model** ([src/models/audit_log.py](src/models/audit_log.py))
   - Immutable database table storing all audit events
   - Captures: table_name, record_id, action, old/new values, who, when, where

2. **Audit Service** ([src/services/audit_service.py](src/services/audit_service.py))
   - Functions for logging each action type
   - Automatic serialization and change detection
   - Configurable table filtering

3. **Audit Context Middleware** ([src/middleware/audit_context.py](src/middleware/audit_context.py))
   - Captures user, IP address, user-agent from requests
   - Stores in context variables for audit logging
   - Automatically clears after each request

---

## Quick Start

### 1. Enable Middleware (Already Done)

The `AuditContextMiddleware` is registered in [src/main.py](src/main.py):

```python
from src.middleware import AuditContextMiddleware

app.add_middleware(AuditContextMiddleware)
```

### 2. Add Audit Logging to a Router

See [src/routers/members_audited.py](src/routers/members_audited.py) for a complete example.

**Pattern:**

```python
from src.services import audit_service
from src.middleware import get_audit_context

# In your endpoint:
@router.get("/{id}")
def read_record(id: int, db: Session = Depends(get_db)):
    record = get_record(db, id)
    if not record:
        raise HTTPException(status_code=404)

    # Convert to dict for logging
    record_dict = {
        "id": record.id,
        "name": record.name,
        # ... other fields
    }

    # Log READ action
    audit_context = get_audit_context()
    audit_service.log_read(
        db=db,
        table_name="your_table",
        record_id=record.id,
        record_data=record_dict,
        **audit_context
    )

    return record
```

---

## Logging Actions

### 1. Log READ (View Single Record)

```python
from src.services import audit_service
from src.middleware import get_audit_context

# After retrieving record
audit_context = get_audit_context()
audit_service.log_read(
    db=db,
    table_name="members",
    record_id=member.id,
    record_data=member_to_dict(member),  # Optional
    **audit_context
)
```

**When to Use:**
- GET `/resource/{id}` endpoints
- Any time a single record is viewed
- Includes: user profile views, detail pages, API lookups

### 2. Log BULK_READ (List/Search Records)

```python
# After retrieving list
members = list_members(db, skip, limit)

audit_context = get_audit_context()
audit_service.log_bulk_read(
    db=db,
    table_name="members",
    record_count=len(members),
    filters={"skip": skip, "limit": limit, "status": "active"},
    **audit_context
)
```

**When to Use:**
- GET `/resource/` list endpoints
- Search/filter operations
- Export/report generation

### 3. Log CREATE (New Record)

```python
# After creating record
member = create_member(db, data)

audit_context = get_audit_context()
audit_service.log_create(
    db=db,
    table_name="members",
    record_id=member.id,
    new_values=member_to_dict(member),
    **audit_context
)
```

**When to Use:**
- POST endpoints creating new records
- Bulk imports
- API integrations creating data

### 4. Log UPDATE (Modify Record)

```python
# Get old state BEFORE update
old_member = get_member(db, member_id)
old_values = member_to_dict(old_member)

# Perform update
updated_member = update_member(db, member_id, data)
new_values = member_to_dict(updated_member)

# Log UPDATE
audit_context = get_audit_context()
audit_service.log_update(
    db=db,
    table_name="members",
    record_id=member_id,
    old_values=old_values,
    new_values=new_values,
    **audit_context
)
```

**When to Use:**
- PUT/PATCH endpoints modifying records
- Status changes
- Profile updates
- Batch updates

**Important:** The service automatically detects which fields changed!

### 5. Log DELETE (Remove Record)

```python
# Get current state BEFORE deletion
member = get_member(db, member_id)
old_values = member_to_dict(member)

# Perform deletion
delete_member(db, member_id)

# Log DELETE
audit_context = get_audit_context()
audit_service.log_delete(
    db=db,
    table_name="members",
    record_id=member_id,
    old_values=old_values,
    **audit_context
)
```

**When to Use:**
- DELETE endpoints
- Soft deletes (setting is_deleted=true)
- Hard deletes
- Bulk deletions

---

## Helper Functions

### Converting Models to Dicts

Create a helper function for each audited model:

```python
def member_to_dict(member) -> dict:
    """Convert Member object to dict for audit logging."""
    return {
        "id": member.id,
        "member_number": member.member_number,
        "first_name": member.first_name,
        "last_name": member.last_name,
        # ... all relevant fields
        "status": member.status.value if member.status else None,
        "created_at": member.created_at,
        "updated_at": member.updated_at,
    }
```

**Tips:**
- Include all fields you want in the audit trail
- Handle enums by calling `.value`
- Handle None values gracefully
- Include timestamps for context

---

## Audited Tables

The following tables are automatically audited (configured in `audit_service.py`):

- `members` - Union members
- `students` - Training program students
- `instructors` - Training instructors
- `users` - System users
- `organization_contacts` - Organization contacts
- `organizations` - Employers, unions, training partners
- `member_employments` - Employment history
- `credentials` - Certifications
- `jatc_applications` - Apprenticeship applications

**To Add a Table:**

Edit [src/services/audit_service.py](src/services/audit_service.py):

```python
AUDITED_TABLES = {
    "members",
    "students",
    # ... existing tables ...
    "your_new_table",  # Add here
}
```

---

## Retrieving Audit Trail

### Query Audit Logs

```python
from src.services.audit_service import get_audit_trail
from datetime import datetime, timedelta

# Get all changes to a specific record
logs = get_audit_trail(
    db=db,
    table_name="members",
    record_id=123,
    limit=50
)

# Get all actions by a user
logs = get_audit_trail(
    db=db,
    changed_by="user@example.com",
    start_date=datetime.now() - timedelta(days=7),
    limit=100
)

# Get all READ operations
logs = get_audit_trail(
    db=db,
    action="READ",
    start_date=datetime.now() - timedelta(hours=24),
    limit=100
)
```

### Audit Log API

See [src/routers/audit_logs.py](src/routers/audit_logs.py) for API endpoints:

- `GET /audit-logs/` - List all audit logs
- `GET /audit-logs/{id}` - Get specific audit log
- `GET /audit-logs/table/{table_name}` - Logs for a table
- `GET /audit-logs/record/{table}/{record_id}` - Logs for a specific record

---

## Authentication Integration

### Current Implementation

The middleware extracts user from:
1. `X-User-ID` header (recommended for authenticated requests)
2. `Authorization` header (JWT bearer tokens)
3. Session cookies (if implemented)
4. Falls back to "anonymous"

### Integration with Your Auth System

Edit [src/middleware/audit_context.py](src/middleware/audit_context.py):

```python
def _extract_user_from_request(request: Request) -> str:
    """Extract user identifier from request."""

    # Your auth integration here
    if hasattr(request.state, "user"):
        return request.state.user.email  # or user.id

    # JWT decoding
    if "authorization" in request.headers:
        token = request.headers["authorization"].replace("Bearer ", "")
        payload = decode_jwt(token)  # Your JWT decode function
        return payload.get("sub") or payload.get("email")

    return "anonymous"
```

### Setting User Manually

For testing or special cases:

```python
from src.middleware.audit_context import _audit_user

# Set user for this request
_audit_user.set("admin@example.com")

# Your audit logging here
audit_service.log_create(...)
```

---

## Best Practices

### 1. Always Log After Success

Only log audit events AFTER the operation succeeds:

```python
# ✅ CORRECT
member = create_member(db, data)  # Create first
audit_service.log_create(...)      # Then log

# ❌ WRONG
audit_service.log_create(...)      # Don't log before operation
member = create_member(db, data)  # Operation might fail!
```

### 2. Capture Old State for Updates/Deletes

Always retrieve the old state BEFORE modifying:

```python
# ✅ CORRECT
old_member = get_member(db, id)   # Get old state first
old_values = member_to_dict(old_member)
updated_member = update_member(db, id, data)  # Then update
new_values = member_to_dict(updated_member)
audit_service.log_update(..., old_values=old_values, new_values=new_values)
```

### 3. Don't Log System Operations

Avoid logging automated system operations (backups, cleanup, etc.):

```python
# For system operations, set changed_by explicitly
audit_service.log_delete(
    ...,
    changed_by="SYSTEM",
    notes="Automated cleanup job"
)
```

### 4. Use Meaningful Notes

Add context when helpful:

```python
audit_service.log_update(
    ...,
    notes=f"Status changed from {old_status} to {new_status} via bulk operation"
)
```

### 5. Handle Sensitive Data

Don't log passwords or sensitive fields:

```python
def user_to_dict(user) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        # "password": user.password,  # ❌ Don't log passwords!
        "name": user.name,
    }
```

---

## Performance Considerations

### Audit Log Volume

With READ tracking enabled, audit logs grow quickly:

| Activity | Logs per Day | Estimate |
|----------|--------------|----------|
| 100 users viewing 50 records each | 5,000 | ~150K/month |
| 10 users making 20 changes each | 200 | ~6K/month |
| API integrations | Variable | ~50K/month |

**Total:** Expect 200K-500K audit logs per month for active system.

### Optimization Tips

1. **Partition the audit_logs table** by month (PostgreSQL 12+):
   ```sql
   CREATE TABLE audit_logs_2026_01 PARTITION OF audit_logs
   FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
   ```

2. **Add retention policy** (delete old logs):
   ```sql
   DELETE FROM audit_logs
   WHERE changed_at < NOW() - INTERVAL '2 years';
   ```

3. **Archive old logs** to cold storage (S3, etc.)

4. **Index optimization**:
   ```sql
   CREATE INDEX idx_audit_logs_changed_at
   ON audit_logs(changed_at DESC);

   CREATE INDEX idx_audit_logs_table_record
   ON audit_logs(table_name, record_id);
   ```

---

## Compliance & Security

### GDPR / Data Privacy

Audit logs may contain personal data. Ensure:

- Logs are encrypted at rest
- Access is restricted to authorized personnel
- Retention policies comply with regulations
- Right to erasure requests handled properly

### Immutability

The AuditLog table should be **append-only**:

```sql
-- Revoke UPDATE and DELETE permissions
REVOKE UPDATE, DELETE ON audit_logs FROM your_app_user;
GRANT INSERT, SELECT ON audit_logs TO your_app_user;
```

### Security Monitoring

Monitor for suspicious patterns:

```sql
-- Excessive READ operations by a user
SELECT changed_by, COUNT(*) as read_count
FROM audit_logs
WHERE action = 'READ'
  AND changed_at > NOW() - INTERVAL '1 hour'
GROUP BY changed_by
HAVING COUNT(*) > 100;

-- Bulk deletions
SELECT changed_by, table_name, COUNT(*) as delete_count
FROM audit_logs
WHERE action = 'DELETE'
  AND changed_at > NOW() - INTERVAL '1 hour'
GROUP BY changed_by, table_name
HAVING COUNT(*) > 10;
```

---

## Testing

### Manual Testing

```bash
# Start API server
./ip2adb run

# Make some requests with user header
curl -H "X-User-ID: testuser@example.com" \
     http://localhost:8000/members/1

# Check audit logs
./ip2adb audit-logs --table members --limit 10
```

### Automated Testing

```python
def test_audit_logging(client, db):
    # Create a member
    response = client.post(
        "/members/",
        json={"member_number": "12345", "first_name": "John", "last_name": "Doe"},
        headers={"X-User-ID": "testuser@example.com"}
    )

    # Verify audit log was created
    logs = get_audit_trail(db, table_name="members", action="CREATE")
    assert len(logs) > 0
    assert logs[0].changed_by == "testuser@example.com"
    assert logs[0].record_id == str(response.json()["id"])
```

---

## Troubleshooting

### Audit Logs Not Being Created

1. **Check middleware is registered**:
   ```python
   # In src/main.py
   app.add_middleware(AuditContextMiddleware)
   ```

2. **Verify table is in AUDITED_TABLES**:
   ```python
   # In src/services/audit_service.py
   AUDITED_TABLES = {"members", ...}
   ```

3. **Check database connection**:
   ```python
   # Audit logs require a separate db.commit()
   audit_service.log_create(db, ...)  # Commits internally
   ```

### User Always Shows as "anonymous"

1. **Add X-User-ID header** to requests:
   ```bash
   curl -H "X-User-ID: user@example.com" ...
   ```

2. **Integrate with auth system** (see Authentication Integration above)

3. **Check middleware order** (AuditContextMiddleware should be first):
   ```python
   app.add_middleware(AuditContextMiddleware)  # Must be before auth
   app.add_middleware(AuthMiddleware)
   ```

### Performance Issues

1. **Add indexes** (see Performance Considerations)
2. **Implement partitioning**
3. **Review query patterns** (avoid full table scans)
4. **Consider async logging** for high-volume systems

---

## Migration Plan

To roll out audit logging across all routers:

1. **Phase 1:** Test on a single router (members_audited.py)
2. **Phase 2:** Update high-priority routers (members, students, organizations)
3. **Phase 3:** Update remaining user-related routers
4. **Phase 4:** Monitor log volume and performance
5. **Phase 5:** Implement partitioning/archiving if needed

**Estimated Effort:** 30-60 minutes per router (with helper functions)

---

## Future Enhancements

- **Dashboard:** Web UI for viewing/searching audit logs
- **Alerts:** Real-time notifications for suspicious activity
- **Export:** CSV/JSON export for compliance reports
- **Integration:** Webhook notifications to SIEM systems
- **ML:** Anomaly detection for security monitoring

---

## Support

For questions or issues:
- Review this guide and [src/routers/members_audited.py](src/routers/members_audited.py) example
- Check [src/services/audit_service.py](src/services/audit_service.py) for available functions
- Test with curl or Postman to verify behavior

---

**Last Updated:** 2026-01-27
**Version:** 1.0
