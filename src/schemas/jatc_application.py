from pydantic import BaseModel
from typing import Optional
from datetime import date


# ------------------------------------------------------------
# Base Schema
# ------------------------------------------------------------
class JATCApplicationBase(BaseModel):
    student_id: int
    application_date: date
    interview_date: Optional[date] = None
    status: str = "pending"
    notes: Optional[str] = None
    supporting_docs_path: Optional[str] = None


# ------------------------------------------------------------
# Create Schema
# ------------------------------------------------------------
class JATCApplicationCreate(JATCApplicationBase):
    pass


# ------------------------------------------------------------
# Update Schema
# ------------------------------------------------------------
class JATCApplicationUpdate(BaseModel):
    application_date: Optional[date] = None
    interview_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    student_id: Optional[int] = None
    supporting_docs_path: Optional[str] = None


# ------------------------------------------------------------
# Read Schema
# ------------------------------------------------------------
class JATCApplicationRead(JATCApplicationBase):
    id: int

    class Config:
        from_attributes = True
