"""Service functions for Role model."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.role import Role
from src.schemas.role import RoleCreate, RoleUpdate


def get_role(db: Session, role_id: int) -> Optional[Role]:
    """Get a role by ID."""
    return db.get(Role, role_id)


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    """Get a role by name."""
    stmt = select(Role).where(Role.name == name.lower())
    return db.execute(stmt).scalar_one_or_none()


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> list[Role]:
    """Get a list of roles."""
    stmt = select(Role).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def create_role(db: Session, role_data: RoleCreate) -> Role:
    """Create a new role."""
    role = Role(
        name=role_data.name.lower(),
        display_name=role_data.display_name,
        description=role_data.description,
        is_system_role=role_data.is_system_role,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, role: Role, role_data: RoleUpdate) -> Role:
    """Update an existing role."""
    if role.is_system_role:
        # Only allow updating description for system roles
        if role_data.description is not None:
            role.description = role_data.description
    else:
        update_data = role_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role: Role) -> bool:
    """Delete a role (only non-system roles)."""
    if role.is_system_role:
        return False
    db.delete(role)
    db.commit()
    return True
