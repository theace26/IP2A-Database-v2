from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db.session import get_db

from app.schemas.instructor_hours import (
    InstructorHoursCreate,
    InstructorHoursUpdate,
    InstructorHoursRead,
)

from app.services import instructor_hours_service


router = APIRouter(
    prefix="/instructor-hours",
    tags=["Instructor Hours"]
)


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------
@router.post("/", response_model=InstructorHoursRead)
def create_instructor_hours(
    data: InstructorHoursCreate,
    db: Session = Depends(get_db)
):
    return instructor_hours_service.create_instructor_hours(db, data)


# ------------------------------------------------------------
# READ (List All)
# ------------------------------------------------------------
@router.get("/", response_model=List[InstructorHoursRead])
def list_instructor_hours(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return instructor_hours_service.list_instructor_hours(db, skip, limit)


# ------------------------------------------------------------
# READ (Single)
# ------------------------------------------------------------
@router.get("/{hours_id}", response_model=InstructorHoursRead)
def get_instructor_hours(
    hours_id: int,
    db: Session = Depends(get_db)
):
    entry = instructor_hours_service.get_instructor_hours(db, hours_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Hours entry not found")
    return entry


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------
@router.patch("/{hours_id}", response_model=InstructorHoursRead)
def update_instructor_hours(
    hours_id: int,
    data: InstructorHoursUpdate,
    db: Session = Depends(get_db)
):
    entry = instructor_hours_service.update_instructor_hours(
        db, hours_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Hours entry not found")
    return entry


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------
@router.delete("/{hours_id}")
def delete_instructor_hours(
    hours_id: int,
    db: Session = Depends(get_db)
):
    success = instructor_hours_service.delete_instructor_hours(db, hours_id)
    if not success:
        raise HTTPException(status_code=404, detail="Hours entry not found")
    return {"message": "Hours log deleted successfully"}


# ------------------------------------------------------------
# FILTER: BY INSTRUCTOR
# ------------------------------------------------------------
@router.get("/instructor/{instructor_id}", response_model=List[InstructorHoursRead])
def get_hours_by_instructor(
    instructor_id: int,
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db)
):
    return instructor_hours_service.list_hours_by_instructor(
        db, instructor_id, start, end
    )


# ------------------------------------------------------------
# FILTER: BY COHORT
# ------------------------------------------------------------
@router.get("/cohort/{cohort_id}", response_model=List[InstructorHoursRead])
def get_hours_by_cohort(
    cohort_id: int,
    db: Session = Depends(get_db)
):
    return instructor_hours_service.list_hours_by_cohort(db, cohort_id)


# ------------------------------------------------------------
# FILTER: BY LOCATION
# ------------------------------------------------------------
@router.get("/location/{location_id}", response_model=List[InstructorHoursRead])
def get_hours_by_location(
    location_id: int,
    db: Session = Depends(get_db)
):
    return instructor_hours_service.list_hours_by_location(db, location_id)
