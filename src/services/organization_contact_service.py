"""OrganizationContact service for business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.organization_contact import OrganizationContact
from src.schemas.organization_contact import (
    OrganizationContactCreate,
    OrganizationContactUpdate,
)


def create_organization_contact(
    db: Session, data: OrganizationContactCreate
) -> OrganizationContact:
    """Create a new organization contact."""
    obj = OrganizationContact(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_organization_contact(
    db: Session, contact_id: int
) -> Optional[OrganizationContact]:
    """Get organization contact by ID."""
    return (
        db.query(OrganizationContact)
        .filter(OrganizationContact.id == contact_id)
        .first()
    )


def list_organization_contacts(
    db: Session, skip: int = 0, limit: int = 100
) -> List[OrganizationContact]:
    """List organization contacts with pagination."""
    return db.query(OrganizationContact).offset(skip).limit(limit).all()


def update_organization_contact(
    db: Session, contact_id: int, data: OrganizationContactUpdate
) -> Optional[OrganizationContact]:
    """Update an organization contact."""
    obj = get_organization_contact(db, contact_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_organization_contact(db: Session, contact_id: int) -> bool:
    """Delete an organization contact."""
    obj = get_organization_contact(db, contact_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
