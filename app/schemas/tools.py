from pydantic import BaseModel
from datetime import date
from typing import Optional

# ------------------------------------------------------------
# Base Schema
# ------------------------------------------------------------
class ToolIssuedBase(BaseModel):
    tool_name: str
    condition: Optional[str] = None
    date_issued: Optional[date] = None
    student_id: int  # FK → Student

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
    condition: Optional[str] = None
    date_issued: Optional[date] = None
    student_id: Optional[int] = None

# ------------------------------------------------------------
# Read Schema
# ------------------------------------------------------------
class ToolIssuedRead(ToolIssuedBase):
    id: int

    class Config:
        from_attributes = True
