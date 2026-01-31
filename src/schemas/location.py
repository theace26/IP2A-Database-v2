"""
Location Pydantic schemas - aligned with src/models/location.py

Model fields:
- id, name, address, capacity
- relationships: cohorts, instructor_hours
"""

from pydantic import BaseModel
from typing import List, Optional


# ------------------------------------------------------------
# Base Schema (shared fields - matches model exactly)
# ------------------------------------------------------------
class LocationBase(BaseModel):
    name: str
    address: str
    capacity: Optional[int] = None


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class LocationCreate(LocationBase):
    """Used when creating a new location."""

    pass


# ------------------------------------------------------------
# Update Schema (PATCH) - all fields optional
# ------------------------------------------------------------
class LocationUpdate(BaseModel):
    """Fields allowed to change on update."""

    name: Optional[str] = None
    address: Optional[str] = None
    capacity: Optional[int] = None


# ------------------------------------------------------------
# Response Schema (GET)
# ------------------------------------------------------------
class LocationRead(LocationBase):
    id: int

    # Relationship IDs for reference
    cohort_ids: List[int] = []

    class Config:
        from_attributes = True
