"""AuditLog service for business logic (read-only)."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.audit_log import AuditLog


def get_audit_log(db: Session, log_id: int) -> Optional[AuditLog]:
    """Get audit log by ID."""
    return db.query(AuditLog).filter(AuditLog.id == log_id).first()


def list_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> List[AuditLog]:
    """List audit logs with pagination."""
    return db.query(AuditLog).order_by(AuditLog.changed_at.desc()).offset(skip).limit(limit).all()


def list_audit_logs_by_table(
    db: Session, table_name: str, skip: int = 0, limit: int = 100
) -> List[AuditLog]:
    """List audit logs for a specific table."""
    return (
        db.query(AuditLog)
        .filter(AuditLog.table_name == table_name)
        .order_by(AuditLog.changed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_audit_logs_by_record(
    db: Session, table_name: str, record_id: str
) -> List[AuditLog]:
    """List all audit logs for a specific record."""
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.table_name == table_name,
            AuditLog.record_id == record_id
        )
        .order_by(AuditLog.changed_at.desc())
        .all()
    )
