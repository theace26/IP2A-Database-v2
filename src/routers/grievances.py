"""Grievances router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.grievance import (
    GrievanceCreate,
    GrievanceUpdate,
    GrievanceRead,
    GrievanceStepRecordCreate,
    GrievanceStepRecordUpdate,
    GrievanceStepRecordRead,
)
from src.services.grievance_service import (
    create_grievance,
    get_grievance,
    get_grievance_by_number,
    list_grievances,
    update_grievance,
    delete_grievance,
    create_step_record,
    get_step_record,
    list_step_records,
    update_step_record,
    delete_step_record,
)

router = APIRouter(prefix="/grievances", tags=["Grievances"])


# --- Grievance Endpoints ---


@router.post("/", response_model=GrievanceRead, status_code=201)
def create(data: GrievanceCreate, db: Session = Depends(get_db)):
    """Create a new grievance."""
    return create_grievance(db, data)


@router.get("/{grievance_id}", response_model=GrievanceRead)
def read(grievance_id: int, db: Session = Depends(get_db)):
    """Get a grievance by ID."""
    obj = get_grievance(db, grievance_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Grievance not found")
    return obj


@router.get("/by-number/{grievance_number}", response_model=GrievanceRead)
def read_by_number(grievance_number: str, db: Session = Depends(get_db)):
    """Get a grievance by grievance number."""
    obj = get_grievance_by_number(db, grievance_number)
    if not obj:
        raise HTTPException(status_code=404, detail="Grievance not found")
    return obj


@router.get("/", response_model=List[GrievanceRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all grievances."""
    return list_grievances(db, skip, limit)


@router.put("/{grievance_id}", response_model=GrievanceRead)
def update(grievance_id: int, data: GrievanceUpdate, db: Session = Depends(get_db)):
    """Update a grievance."""
    obj = update_grievance(db, grievance_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Grievance not found")
    return obj


@router.delete("/{grievance_id}")
def delete(grievance_id: int, db: Session = Depends(get_db)):
    """Delete a grievance."""
    if not delete_grievance(db, grievance_id):
        raise HTTPException(status_code=404, detail="Grievance not found")
    return {"message": "Grievance deleted"}


# --- Grievance Step Record Endpoints ---


@router.post(
    "/{grievance_id}/steps",
    response_model=GrievanceStepRecordRead,
    status_code=201,
)
def create_step(
    grievance_id: int,
    data: GrievanceStepRecordCreate,
    db: Session = Depends(get_db),
):
    """Create a new step record for a grievance."""
    # Verify grievance exists
    if not get_grievance(db, grievance_id):
        raise HTTPException(status_code=404, detail="Grievance not found")
    return create_step_record(db, data)


@router.get(
    "/{grievance_id}/steps",
    response_model=List[GrievanceStepRecordRead],
)
def list_steps(grievance_id: int, db: Session = Depends(get_db)):
    """List all step records for a grievance."""
    if not get_grievance(db, grievance_id):
        raise HTTPException(status_code=404, detail="Grievance not found")
    return list_step_records(db, grievance_id)


@router.get("/steps/{record_id}", response_model=GrievanceStepRecordRead)
def read_step(record_id: int, db: Session = Depends(get_db)):
    """Get a grievance step record by ID."""
    obj = get_step_record(db, record_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Grievance step record not found")
    return obj


@router.put("/steps/{record_id}", response_model=GrievanceStepRecordRead)
def update_step(
    record_id: int,
    data: GrievanceStepRecordUpdate,
    db: Session = Depends(get_db),
):
    """Update a grievance step record."""
    obj = update_step_record(db, record_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Grievance step record not found")
    return obj


@router.delete("/steps/{record_id}")
def delete_step(record_id: int, db: Session = Depends(get_db)):
    """Delete a grievance step record."""
    if not delete_step_record(db, record_id):
        raise HTTPException(status_code=404, detail="Grievance step record not found")
    return {"message": "Grievance step record deleted"}
