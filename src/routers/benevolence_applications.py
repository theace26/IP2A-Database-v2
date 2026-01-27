"""Benevolence applications router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.benevolence_application import (
    BenevolenceApplicationCreate,
    BenevolenceApplicationUpdate,
    BenevolenceApplicationRead,
)
from src.services.benevolence_application_service import (
    create_benevolence_application,
    get_benevolence_application,
    list_benevolence_applications,
    update_benevolence_application,
    delete_benevolence_application,
)

router = APIRouter(prefix="/benevolence-applications", tags=["Benevolence Applications"])


@router.post("/", response_model=BenevolenceApplicationRead, status_code=201)
def create(data: BenevolenceApplicationCreate, db: Session = Depends(get_db)):
    """Create a new benevolence application."""
    return create_benevolence_application(db, data)


@router.get("/{application_id}", response_model=BenevolenceApplicationRead)
def read(application_id: int, db: Session = Depends(get_db)):
    """Get a benevolence application by ID."""
    obj = get_benevolence_application(db, application_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Benevolence application not found")
    return obj


@router.get("/", response_model=List[BenevolenceApplicationRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all benevolence applications."""
    return list_benevolence_applications(db, skip, limit)


@router.put("/{application_id}", response_model=BenevolenceApplicationRead)
def update(
    application_id: int,
    data: BenevolenceApplicationUpdate,
    db: Session = Depends(get_db),
):
    """Update a benevolence application."""
    obj = update_benevolence_application(db, application_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Benevolence application not found")
    return obj


@router.delete("/{application_id}")
def delete(application_id: int, db: Session = Depends(get_db)):
    """Delete a benevolence application."""
    if not delete_benevolence_application(db, application_id):
        raise HTTPException(status_code=404, detail="Benevolence application not found")
    return {"message": "Benevolence application deleted"}
