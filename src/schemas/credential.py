"""
Credential Pydantic schemas - aligned with src/models/credential.py

Model fields:
- id, student_id, credential_name, issuing_org
- issue_date, expiration_date, certificate_number
- notes, attachment_path
- relationship: student
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date


# ------------------------------------------------------------
# Base Schema (shared fields - matches model exactly)
# ------------------------------------------------------------
class CredentialBase(BaseModel):
    student_id: int
    credential_name: str
    issuing_org: Optional[str] = None
    issue_date: date
    expiration_date: Optional[date] = None
    certificate_number: Optional[str] = None
    notes: Optional[str] = None
    attachment_path: Optional[str] = None


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class CredentialCreate(CredentialBase):
    """Used when creating a new credential."""

    pass


# ------------------------------------------------------------
# Update Schema (PATCH) - all fields optional
# ------------------------------------------------------------
class CredentialUpdate(BaseModel):
    """Fields allowed to change on update."""

    student_id: Optional[int] = None
    credential_name: Optional[str] = None
    issuing_org: Optional[str] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    certificate_number: Optional[str] = None
    notes: Optional[str] = None
    attachment_path: Optional[str] = None


# ------------------------------------------------------------
# Response Schema (GET)
# ------------------------------------------------------------
class CredentialRead(CredentialBase):
    id: int

    class Config:
        from_attributes = True
