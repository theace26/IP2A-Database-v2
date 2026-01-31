"""AuditLogs router for API endpoints (read-only)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.audit_log import AuditLogRead
from src.services.audit_log_service import (
    get_audit_log,
    list_audit_logs,
    list_audit_logs_by_table,
    list_audit_logs_by_record,
)

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/{log_id}", response_model=AuditLogRead)
def read(log_id: int, db: Session = Depends(get_db)):
    """Get an audit log by ID."""
    obj = get_audit_log(db, log_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return obj


@router.get("/", response_model=List[AuditLogRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all audit logs."""
    return list_audit_logs(db, skip, limit)


@router.get("/by-table/{table_name}", response_model=List[AuditLogRead])
def list_by_table(
    table_name: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List audit logs for a specific table."""
    return list_audit_logs_by_table(db, table_name, skip, limit)


@router.get("/by-record/{table_name}/{record_id}", response_model=List[AuditLogRead])
def list_by_record(table_name: str, record_id: str, db: Session = Depends(get_db)):
    """List all audit logs for a specific record."""
    return list_audit_logs_by_record(db, table_name, record_id)
