"""Certification service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.certification import Certification
from src.schemas.certification import CertificationCreate, CertificationUpdate


def create_certification(db: Session, data: CertificationCreate) -> Certification:
    """Create a new certification."""
    obj = Certification(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_certification(db: Session, certification_id: int) -> Optional[Certification]:
    """Get certification by ID."""
    return db.query(Certification).filter(Certification.id == certification_id).first()


def get_student_certifications(
    db: Session, student_id: int, skip: int = 0, limit: int = 100
) -> List[Certification]:
    """Get all certifications for a student."""
    return db.query(Certification).filter(
        Certification.student_id == student_id
    ).offset(skip).limit(limit).all()


def list_certifications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    cert_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[Certification]:
    """List certifications with pagination and optional filters."""
    query = db.query(Certification)

    if student_id:
        query = query.filter(Certification.student_id == student_id)

    if cert_type:
        query = query.filter(Certification.cert_type == cert_type)

    if status:
        query = query.filter(Certification.status == status)

    return query.offset(skip).limit(limit).all()


def update_certification(
    db: Session, certification_id: int, data: CertificationUpdate
) -> Optional[Certification]:
    """Update a certification."""
    obj = get_certification(db, certification_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_certification(db: Session, certification_id: int) -> bool:
    """Delete a certification."""
    obj = get_certification(db, certification_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
