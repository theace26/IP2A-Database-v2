from pydantic import BaseModel
from typing import Optional


# ------------------------------------------------------------
# Base Schema
# ------------------------------------------------------------
class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    capacity: Optional[int] = None


# ------------------------------------------------------------
# Create Schema
# ------------------------------------------------------------
class LocationCreate(LocationBase):
    pass


# ------------------------------------------------------------
# Update Schema
# ------------------------------------------------------------
class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    capacity: Optional[int] = None


# ------------------------------------------------------------
# Read Schema
# ------------------------------------------------------------
class LocationRead(LocationBase):
    id: int

    class Config:
        from_attributes = True
