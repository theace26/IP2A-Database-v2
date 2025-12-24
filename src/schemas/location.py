from pydantic import BaseModel
from typing import Optional


# ------------------------------------------------------------
# Base Schema (shared fields)
# ------------------------------------------------------------
class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


# ------------------------------------------------------------
# Create Schema (POST)
# ------------------------------------------------------------
class LocationCreate(LocationBase):
    """Used when creating a new training or class location."""
    pass


# ------------------------------------------------------------
# Update Schema (PATCH)
# ------------------------------------------------------------
class LocationUpdate(BaseModel):
    """Allows partial update of a location."""
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


# ------------------------------------------------------------
# Response Schema (GET)
# ------------------------------------------------------------
class LocationRead(LocationBase):
    id: int

    class Config:
        from_attributes = True
