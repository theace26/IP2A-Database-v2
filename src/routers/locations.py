from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db

from src.schemas.location import LocationCreate, LocationUpdate, LocationRead

from src.schemas.cohort import CohortRead
from src.schemas.instructor_hours import InstructorHoursRead

from src.services import location_service
from src.services.instructor_hours_service import list_hours_by_location


router = APIRouter(prefix="/locations", tags=["Locations"])


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
@router.post("/", response_model=LocationRead, status_code=201)
def create_location(data: LocationCreate, db: Session = Depends(get_db)):
    return location_service.create_location(db, data)


# ------------------------------------------------------------
# READ (List)
# ------------------------------------------------------------
@router.get("/", response_model=List[LocationRead])
def list_locations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return location_service.list_locations(db, skip, limit)


# ------------------------------------------------------------
# READ (Single)
# ------------------------------------------------------------
@router.get("/{location_id}", response_model=LocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)):
    location = location_service.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
@router.patch("/{location_id}", response_model=LocationRead)
def update_location(
    location_id: int, data: LocationUpdate, db: Session = Depends(get_db)
):
    location = location_service.update_location(db, location_id, data)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    success = location_service.delete_location(db, location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"message": "Location deleted successfully"}


# ------------------------------------------------------------
# RELATIONSHIP ENDPOINTS — COHORTS
# ------------------------------------------------------------
@router.get("/{location_id}/cohorts", response_model=List[CohortRead])
def get_location_cohorts(location_id: int, db: Session = Depends(get_db)):
    # First confirm location exists
    location = location_service.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return (
        db.query(location.__class__)
        .filter(location.__class__.id == location_id)
        .first()
        .cohorts
    )


# ------------------------------------------------------------
# RELATIONSHIP ENDPOINTS — INSTRUCTOR HOURS
# ------------------------------------------------------------
@router.get("/{location_id}/hours", response_model=List[InstructorHoursRead])
def get_location_hours(location_id: int, db: Session = Depends(get_db)):
    # Validate location exists
    location = location_service.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return list_hours_by_location(db, location_id)
