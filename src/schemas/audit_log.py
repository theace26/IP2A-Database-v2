"""AuditLog schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class AuditLogRead(BaseModel):
    """Schema for reading an audit log entry (read-only)."""

    id: int
    table_name: str = Field(..., max_length=100)
    record_id: str = Field(..., max_length=50)
    action: str = Field(..., max_length=10)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None  # List of field names that changed
    changed_by: Optional[str] = Field(None, max_length=100)
    changed_at: datetime
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None

    class Config:
        from_attributes = True
