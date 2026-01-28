"""Certifications router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.schemas.certification import CertificationCreate, CertificationUpdate, CertificationRead
from src.services.certification_service import (
    create_certification,
    get_certification,
    get_student_certifications,
    list_certifications,
    update_certification,
    delete_certification,
)

router = APIRouter(prefix="/training/certifications", tags=["Training - Certifications"])


@router.post("/", response_model=CertificationRead, status_code=201)
def create(data: CertificationCreate, db: Session = Depends(get_db)):
    """Create a new certification."""
    return create_certification(db, data)


@router.get("/{certification_id}", response_model=CertificationRead)
def read(certification_id: int, db: Session = Depends(get_db)):
    """Get a certification by ID."""
    obj = get_certification(db, certification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Certification not found")
    return obj


@router.get("/student/{student_id}", response_model=List[CertificationRead])
def list_by_student(
    student_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List all certifications for a student."""
    return get_student_certifications(db, student_id, skip, limit)


@router.get("/", response_model=List[CertificationRead])
def list_all(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = Query(None),
    cert_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all certifications with optional filters."""
    return list_certifications(db, skip, limit, student_id, cert_type, status)


@router.patch("/{certification_id}", response_model=CertificationRead)
def update(
    certification_id: int, data: CertificationUpdate, db: Session = Depends(get_db)
):
    """Update a certification."""
    obj = update_certification(db, certification_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Certification not found")
    return obj


@router.delete("/{certification_id}")
def delete(certification_id: int, db: Session = Depends(get_db)):
    """Delete a certification."""
    if not delete_certification(db, certification_id):
        raise HTTPException(status_code=404, detail="Certification not found")
    return {"message": "Certification deleted"}
