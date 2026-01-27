"""Organizations router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.session import get_db
from src.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationRead,
)
from src.services.organization_service import (
    create_organization,
    get_organization,
    list_organizations,
    update_organization,
    delete_organization,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("/", response_model=OrganizationRead, status_code=201)
def create(data: OrganizationCreate, db: Session = Depends(get_db)):
    """Create a new organization."""
    return create_organization(db, data)


@router.get("/{organization_id}", response_model=OrganizationRead)
def read(organization_id: int, db: Session = Depends(get_db)):
    """Get an organization by ID."""
    obj = get_organization(db, organization_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Organization not found")
    return obj


@router.get("/", response_model=List[OrganizationRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all organizations."""
    return list_organizations(db, skip, limit)


@router.put("/{organization_id}", response_model=OrganizationRead)
def update(
    organization_id: int, data: OrganizationUpdate, db: Session = Depends(get_db)
):
    """Update an organization."""
    obj = update_organization(db, organization_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Organization not found")
    return obj


@router.delete("/{organization_id}")
def delete(organization_id: int, db: Session = Depends(get_db)):
    """Delete an organization."""
    if not delete_organization(db, organization_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"message": "Organization deleted"}
