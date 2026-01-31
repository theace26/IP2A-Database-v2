"""Organization service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.organization import Organization
from src.schemas.organization import OrganizationCreate, OrganizationUpdate


def create_organization(db: Session, data: OrganizationCreate) -> Organization:
    """Create a new organization."""
    obj = Organization(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_organization(db: Session, organization_id: int) -> Optional[Organization]:
    """Get organization by ID."""
    return db.query(Organization).filter(Organization.id == organization_id).first()


def list_organizations(
    db: Session, skip: int = 0, limit: int = 100
) -> List[Organization]:
    """List organizations with pagination."""
    return db.query(Organization).offset(skip).limit(limit).all()


def update_organization(
    db: Session, organization_id: int, data: OrganizationUpdate
) -> Optional[Organization]:
    """Update an organization."""
    obj = get_organization(db, organization_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_organization(db: Session, organization_id: int) -> bool:
    """Delete an organization."""
    obj = get_organization(db, organization_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
