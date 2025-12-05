from pydantic import BaseModel
from typing import Optional
from datetime import date

# ------------------------------------------------------------
# Base Schema
# ------------------------------------------------------------
class CredentialBase(BaseModel):
    credential_name: str
    issuing_org: Optional[str] = None
    issue_date: date
    expiration_date: Optional[date] = None
    certificate_number: Optional[str] = None
    notes: Optional[str] = None
    student_id: int

# ------------------------------------------------------------
# Create Schema
# ------------------------------------------------------------
class CredentialCreate(CredentialBase):
    pass

# ------------------------------------------------------------
# Update Schema
# ------------------------------------------------------------
class CredentialUpdate(BaseModel):
    credential_name: Optional[str] = None
    issuing_org: Optional[str] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    certificate_number: Optional[str] = None
    notes: Optional[str] = None
    student_id: Optional[int] = None

# ------------------------------------------------------------
# Read Schema
# ------------------------------------------------------------
class CredentialRead(CredentialBase):
    id: int

    class Config:
        from_attributes = True
