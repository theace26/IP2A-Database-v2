"""OrganizationContacts router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.organization_contact import (
    OrganizationContactCreate,
    OrganizationContactUpdate,
    OrganizationContactRead,
)
from src.services.organization_contact_service import (
    create_organization_contact,
    get_organization_contact,
    list_organization_contacts,
    update_organization_contact,
    delete_organization_contact,
)

router = APIRouter(prefix="/organization-contacts", tags=["Organization Contacts"])


@router.post("/", response_model=OrganizationContactRead, status_code=201)
def create(data: OrganizationContactCreate, db: Session = Depends(get_db)):
    """Create a new organization contact."""
    return create_organization_contact(db, data)


@router.get("/{contact_id}", response_model=OrganizationContactRead)
def read(contact_id: int, db: Session = Depends(get_db)):
    """Get an organization contact by ID."""
    obj = get_organization_contact(db, contact_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Organization contact not found")
    return obj


@router.get("/", response_model=List[OrganizationContactRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all organization contacts."""
    return list_organization_contacts(db, skip, limit)


@router.put("/{contact_id}", response_model=OrganizationContactRead)
def update(
    contact_id: int, data: OrganizationContactUpdate, db: Session = Depends(get_db)
):
    """Update an organization contact."""
    obj = update_organization_contact(db, contact_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Organization contact not found")
    return obj


@router.delete("/{contact_id}")
def delete(contact_id: int, db: Session = Depends(get_db)):
    """Delete an organization contact."""
    if not delete_organization_contact(db, contact_id):
        raise HTTPException(status_code=404, detail="Organization contact not found")
    return {"message": "Organization contact deleted"}
