"""SALTing activities router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.salting_activity import (
    SALTingActivityCreate,
    SALTingActivityUpdate,
    SALTingActivityRead,
)
from src.services.salting_activity_service import (
    create_salting_activity,
    get_salting_activity,
    list_salting_activities,
    update_salting_activity,
    delete_salting_activity,
)

router = APIRouter(prefix="/salting-activities", tags=["SALTing Activities"])


@router.post("/", response_model=SALTingActivityRead, status_code=201)
def create(data: SALTingActivityCreate, db: Session = Depends(get_db)):
    """Create a new SALTing activity."""
    return create_salting_activity(db, data)


@router.get("/{activity_id}", response_model=SALTingActivityRead)
def read(activity_id: int, db: Session = Depends(get_db)):
    """Get a SALTing activity by ID."""
    obj = get_salting_activity(db, activity_id)
    if not obj:
        raise HTTPException(status_code=404, detail="SALTing activity not found")
    return obj


@router.get("/", response_model=List[SALTingActivityRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all SALTing activities."""
    return list_salting_activities(db, skip, limit)


@router.put("/{activity_id}", response_model=SALTingActivityRead)
def update(activity_id: int, data: SALTingActivityUpdate, db: Session = Depends(get_db)):
    """Update a SALTing activity."""
    obj = update_salting_activity(db, activity_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="SALTing activity not found")
    return obj


@router.delete("/{activity_id}")
def delete(activity_id: int, db: Session = Depends(get_db)):
    """Delete a SALTing activity."""
    if not delete_salting_activity(db, activity_id):
        raise HTTPException(status_code=404, detail="SALTing activity not found")
    return {"message": "SALTing activity deleted"}
