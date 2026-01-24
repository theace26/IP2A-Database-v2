from pydantic import BaseModel
from typing import Optional
from datetime import date


# ------------------------------------------------------------
# Base Schema
# ------------------------------------------------------------
class ToolIssuedBase(BaseModel):
    tool_name: str
    quantity: int = 1
    date_issued: date
    notes: Optional[str] = None
    student_id: int
    receipt_path: Optional[str] = None


# ------------------------------------------------------------
# Create Schema
# ------------------------------------------------------------
class ToolIssuedCreate(ToolIssuedBase):
    pass


# ------------------------------------------------------------
# Update Schema
# ------------------------------------------------------------
class ToolIssuedUpdate(BaseModel):
    tool_name: Optional[str] = None
    quantity: Optional[int] = None
    date_issued: Optional[date] = None
    notes: Optional[str] = None
    student_id: Optional[int] = None
    receipt_path: Optional[str] = None


# ------------------------------------------------------------
# Read Schema
# ------------------------------------------------------------
class ToolIssuedRead(ToolIssuedBase):
    id: int

    class Config:
        from_attributes = True
