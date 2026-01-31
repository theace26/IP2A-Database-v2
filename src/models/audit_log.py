"""AuditLog model - immutable audit trail for legal compliance."""

from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from src.db.base import Base


class AuditLog(Base):
    """
    Immutable audit log for tracking all database changes.

    IMPORTANT: This table should have NO updates or deletes allowed.
    Configure PostgreSQL to REVOKE UPDATE, DELETE on this table.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # What changed
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # READ, CREATE, UPDATE, DELETE, BULK_READ

    # Change details
    old_values = Column(JSONB, nullable=True)  # Previous state
    new_values = Column(JSONB, nullable=True)  # New state
    changed_fields = Column(JSONB, nullable=True)  # List of fields that changed

    # Who and when
    changed_by = Column(String(100), nullable=True)  # User ID or system
    changed_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Additional context
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, table='{self.table_name}', action='{self.action}')>"
