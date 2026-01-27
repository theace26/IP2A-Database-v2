"""Audit logging service for tracking all user record access and changes."""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
import json

from src.models.audit_log import AuditLog


class AuditAction:
    """Audit action constants."""
    READ = "READ"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    BULK_READ = "BULK_READ"  # For list/search operations


# Tables that should be audited (user-related data)
AUDITED_TABLES = {
    "members",
    "students",
    "instructors",
    "users",
    "organization_contacts",
    "organizations",
    "member_employments",
    "credentials",
    "jatc_applications",
}


def should_audit_table(table_name: str) -> bool:
    """Check if a table should be audited."""
    return table_name in AUDITED_TABLES


def log_read(
    db: Session,
    table_name: str,
    record_id: int,
    record_data: Optional[Dict[str, Any]] = None,
    changed_by: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[AuditLog]:
    """
    Log a READ operation (viewing a record).

    Args:
        db: Database session
        table_name: Table being read from
        record_id: ID of record being viewed
        record_data: Optional snapshot of data being viewed
        changed_by: User performing the read
        ip_address: IP address of requester
        user_agent: User agent string
        notes: Additional notes

    Returns:
        AuditLog record or None if table not audited
    """
    if not should_audit_table(table_name):
        return None

    audit_log = AuditLog(
        table_name=table_name,
        record_id=str(record_id),
        action=AuditAction.READ,
        old_values=None,
        new_values=_serialize_for_audit(record_data) if record_data else None,
        changed_fields=None,
        changed_by=changed_by or "anonymous",
        ip_address=ip_address,
        user_agent=user_agent,
        notes=notes or f"Viewed {table_name} record {record_id}",
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def log_bulk_read(
    db: Session,
    table_name: str,
    record_count: int,
    filters: Optional[Dict[str, Any]] = None,
    changed_by: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Optional[AuditLog]:
    """
    Log a BULK_READ operation (listing/searching records).

    Args:
        db: Database session
        table_name: Table being queried
        record_count: Number of records returned
        filters: Search/filter criteria applied
        changed_by: User performing the search
        ip_address: IP address of requester
        user_agent: User agent string

    Returns:
        AuditLog record or None if table not audited
    """
    if not should_audit_table(table_name):
        return None

    notes = f"Listed {record_count} {table_name} records"
    if filters:
        notes += f" with filters: {json.dumps(filters, default=str)}"

    audit_log = AuditLog(
        table_name=table_name,
        record_id="BULK",
        action=AuditAction.BULK_READ,
        old_values=None,
        new_values=_serialize_for_audit({"record_count": record_count, "filters": filters}),
        changed_fields=None,
        changed_by=changed_by or "anonymous",
        ip_address=ip_address,
        user_agent=user_agent,
        notes=notes,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def log_create(
    db: Session,
    table_name: str,
    record_id: int,
    new_values: Dict[str, Any],
    changed_by: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[AuditLog]:
    """
    Log a CREATE operation (new record).

    Args:
        db: Database session
        table_name: Table where record was created
        record_id: ID of new record
        new_values: Data of new record
        changed_by: User who created the record
        ip_address: IP address of requester
        user_agent: User agent string
        notes: Additional notes

    Returns:
        AuditLog record or None if table not audited
    """
    if not should_audit_table(table_name):
        return None

    audit_log = AuditLog(
        table_name=table_name,
        record_id=str(record_id),
        action=AuditAction.CREATE,
        old_values=None,
        new_values=_serialize_for_audit(new_values),
        changed_fields=list(new_values.keys()),
        changed_by=changed_by or "anonymous",
        ip_address=ip_address,
        user_agent=user_agent,
        notes=notes or f"Created {table_name} record {record_id}",
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def log_update(
    db: Session,
    table_name: str,
    record_id: int,
    old_values: Dict[str, Any],
    new_values: Dict[str, Any],
    changed_by: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[AuditLog]:
    """
    Log an UPDATE operation (modified record).

    Args:
        db: Database session
        table_name: Table where record was updated
        record_id: ID of updated record
        old_values: Previous state of record
        new_values: New state of record
        changed_by: User who updated the record
        ip_address: IP address of requester
        user_agent: User agent string
        notes: Additional notes

    Returns:
        AuditLog record or None if table not audited
    """
    if not should_audit_table(table_name):
        return None

    # Calculate changed fields
    changed_fields = _get_changed_fields(old_values, new_values)

    if not changed_fields:
        # No actual changes - skip logging
        return None

    audit_log = AuditLog(
        table_name=table_name,
        record_id=str(record_id),
        action=AuditAction.UPDATE,
        old_values=_serialize_for_audit(old_values),
        new_values=_serialize_for_audit(new_values),
        changed_fields=changed_fields,
        changed_by=changed_by or "anonymous",
        ip_address=ip_address,
        user_agent=user_agent,
        notes=notes or f"Updated {table_name} record {record_id}: {', '.join(changed_fields)}",
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def log_delete(
    db: Session,
    table_name: str,
    record_id: int,
    old_values: Dict[str, Any],
    changed_by: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[AuditLog]:
    """
    Log a DELETE operation (removed/soft-deleted record).

    Args:
        db: Database session
        table_name: Table where record was deleted
        record_id: ID of deleted record
        old_values: State of record before deletion
        changed_by: User who deleted the record
        ip_address: IP address of requester
        user_agent: User agent string
        notes: Additional notes

    Returns:
        AuditLog record or None if table not audited
    """
    if not should_audit_table(table_name):
        return None

    audit_log = AuditLog(
        table_name=table_name,
        record_id=str(record_id),
        action=AuditAction.DELETE,
        old_values=_serialize_for_audit(old_values),
        new_values=None,
        changed_fields=list(old_values.keys()),
        changed_by=changed_by or "anonymous",
        ip_address=ip_address,
        user_agent=user_agent,
        notes=notes or f"Deleted {table_name} record {record_id}",
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def _get_changed_fields(old_values: Dict[str, Any], new_values: Dict[str, Any]) -> List[str]:
    """
    Compare old and new values to identify changed fields.

    Args:
        old_values: Previous state
        new_values: New state

    Returns:
        List of field names that changed
    """
    changed = []

    # Check all fields in new_values
    for key, new_val in new_values.items():
        old_val = old_values.get(key)

        # Handle datetime comparison
        if isinstance(new_val, datetime) and isinstance(old_val, datetime):
            # Consider datetimes equal if within 1 second (to handle microsecond differences)
            if abs((new_val - old_val).total_seconds()) > 1:
                changed.append(key)
        elif new_val != old_val:
            changed.append(key)

    return changed


def _serialize_for_audit(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Serialize data for JSON storage in audit log.

    Handles datetime objects and other non-JSON-serializable types.

    Args:
        data: Dictionary to serialize

    Returns:
        JSON-serializable dictionary
    """
    if data is None:
        return None

    serialized = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, (int, float, str, bool, type(None))):
            serialized[key] = value
        else:
            # Convert to string for complex types
            serialized[key] = str(value)

    return serialized


def get_audit_trail(
    db: Session,
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    changed_by: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> List[AuditLog]:
    """
    Retrieve audit trail with filters.

    Args:
        db: Database session
        table_name: Filter by table name
        record_id: Filter by record ID
        changed_by: Filter by user
        action: Filter by action type
        start_date: Filter records after this date
        end_date: Filter records before this date
        limit: Maximum number of records to return

    Returns:
        List of audit log records
    """
    query = db.query(AuditLog)

    if table_name:
        query = query.filter(AuditLog.table_name == table_name)

    if record_id:
        query = query.filter(AuditLog.record_id == str(record_id))

    if changed_by:
        query = query.filter(AuditLog.changed_by == changed_by)

    if action:
        query = query.filter(AuditLog.action == action)

    if start_date:
        query = query.filter(AuditLog.changed_at >= start_date)

    if end_date:
        query = query.filter(AuditLog.changed_at <= end_date)

    query = query.order_by(AuditLog.changed_at.desc())
    query = query.limit(limit)

    return query.all()
