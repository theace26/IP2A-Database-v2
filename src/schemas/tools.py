"""
ToolsIssued Pydantic schemas - aligned with src/models/tools_issued.py

Model fields:
- id, student_id, tool_name, quantity
- date_issued, notes, receipt_path
- relationship: student

NOTE: Class names use singular "ToolIssued" to match router imports
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date


# ------------------------------------------------------------
# Base Schema (shared fields - matches model exactly)
# ------------------------------------------------------------
class ToolIssuedBase(BaseModel):
    student_id: int
    tool_name: str
    quantity: int = 1
    date_issued: date
    notes: Optional[str] = None
    receipt_path: Optional[str] = None


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class ToolIssuedCreate(ToolIssuedBase):
    """Used when creating a new tools issued record."""

    pass


# ------------------------------------------------------------
# Update Schema (PATCH) - all fields optional
# ------------------------------------------------------------
class ToolIssuedUpdate(BaseModel):
    """Fields allowed to change on update."""

    student_id: Optional[int] = None
    tool_name: Optional[str] = None
    quantity: Optional[int] = None
    date_issued: Optional[date] = None
    notes: Optional[str] = None
    receipt_path: Optional[str] = None


# ------------------------------------------------------------
# Response Schema (GET)
# ------------------------------------------------------------
class ToolIssuedRead(ToolIssuedBase):
    id: int

    class Config:
        from_attributes = True
