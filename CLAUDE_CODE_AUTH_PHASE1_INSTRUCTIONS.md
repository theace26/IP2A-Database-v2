# Claude Code Instructions: Phase 1.1 - Authentication Database Schema

> **Project:** IP2A-Database-v2
> **Phase:** 1.1 - Auth Database Schema
> **Estimated Time:** 4-6 hours
> **Prerequisites:** v0.3.0 tagged, all Phase 2 tests passing

---

## Objective

Implement the authentication database schema including User, Role, UserRole, and RefreshToken models following established project patterns.

---

## Before You Start

### 1. Verify Environment

```bash
cd ~/Projects/IP2A-Database-v2
git status                    # Should be clean, on main
git pull origin main          # Get latest
pytest -v                     # Verify tests pass (79/82)
```

### 2. Read Key Files for Context

```bash
# Understand existing patterns
cat CLAUDE.md                 # Full project context
cat src/models/member.py      # Model pattern example
cat src/db/enums/base_enums.py # Enum patterns
cat src/schemas/member.py     # Schema patterns
cat src/services/member_service.py # Service patterns
```

---

## Implementation Steps

### Step 1: Create Auth Enums

**File:** `src/db/enums/auth_enums.py`

```python
"""Authentication and authorization enums."""

from enum import Enum


class RoleType(str, Enum):
    """Default system roles."""
    ADMIN = "admin"
    OFFICER = "officer"
    STAFF = "staff"
    ORGANIZER = "organizer"
    INSTRUCTOR = "instructor"
    MEMBER = "member"


class TokenType(str, Enum):
    """Types of authentication tokens."""
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
```

**Update:** `src/db/enums/__init__.py` - Add exports for new enums

```python
# Add to existing imports
from src.db.enums.auth_enums import RoleType, TokenType

# Add to __all__ list
__all__ = [
    # ... existing exports ...
    "RoleType",
    "TokenType",
]
```

---

### Step 2: Create User Model

**File:** `src/models/user.py`

```python
"""User model for authentication."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.member import Member
    from src.models.role import Role
    from src.models.user_role import UserRole
    from src.models.refresh_token import RefreshToken


class User(Base, TimestampMixin, SoftDeleteMixin):
    """
    User account for authentication.

    A User may optionally be linked to a Member record.
    Users have roles assigned through the UserRole junction table.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Authentication fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile fields
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Security tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Optional link to Member
    member_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        unique=True  # One user per member
    )

    # Relationships
    member: Mapped[Optional["Member"]] = relationship(
        "Member",
        back_populates="user",
        lazy="joined"
    )

    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def roles(self) -> list["Role"]:
        """Return list of roles assigned to this user."""
        return [ur.role for ur in self.user_roles if ur.role]

    @property
    def role_names(self) -> list[str]:
        """Return list of role names for this user."""
        return [ur.role.name for ur in self.user_roles if ur.role]

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return role_name.lower() in [r.lower() for r in self.role_names]

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
```

---

### Step 3: Create Role Model

**File:** `src/models/role.py`

```python
"""Role model for authorization."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.user_role import UserRole


class Role(Base, TimestampMixin):
    """
    Role definition for role-based access control (RBAC).

    Default roles:
    - admin: Full system access
    - officer: Union officer privileges
    - staff: Staff-level access
    - organizer: SALTing and organizing access
    - instructor: Training program access
    - member: Basic member access
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # System roles cannot be deleted
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"
```

---

### Step 4: Create UserRole Junction Model

**File:** `src/models/user_role.py`

```python
"""UserRole junction model for many-to-many user-role relationship."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Integer, ForeignKey, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.role import Role


class UserRole(Base, TimestampMixin):
    """
    Junction table linking Users to Roles.

    Uses Association Object pattern to allow additional metadata
    on the user-role relationship (e.g., who assigned it, when it expires).
    """

    __tablename__ = "user_roles"

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Metadata about the role assignment
    assigned_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
```

---

### Step 5: Create RefreshToken Model

**File:** `src/models/refresh_token.py`

```python
"""RefreshToken model for JWT refresh token management."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User


class RefreshToken(Base, TimestampMixin):
    """
    Refresh token storage for JWT authentication.

    Tokens are stored hashed for security.
    Supports token rotation and revocation.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Token data (stored as hash, not plaintext)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Token metadata
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Device/session tracking
    device_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 max length

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)."""
        return not self.is_revoked and not self.is_expired

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, is_valid={self.is_valid})>"
```

---

### Step 6: Update Member Model (Add User Backref)

**File:** `src/models/member.py` - Add relationship

Add this import at the top with other TYPE_CHECKING imports:

```python
if TYPE_CHECKING:
    # ... existing imports ...
    from src.models.user import User
```

Add this relationship to the Member class:

```python
    # Add after other relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="member",
        uselist=False
    )
```

---

### Step 7: Update Models __init__.py

**File:** `src/models/__init__.py`

```python
"""SQLAlchemy models."""

from src.models.base import Base
from src.models.mixins import TimestampMixin, SoftDeleteMixin

# Phase 1 models
from src.models.organization import Organization
from src.models.organization_contact import OrganizationContact
from src.models.member import Member
from src.models.member_employment import MemberEmployment
from src.models.audit_log import AuditLog
from src.models.file_attachment import FileAttachment

# Phase 2 models
from src.models.salting_activity import SaltingActivity
from src.models.benevolence_application import BenevolenceApplication
from src.models.benevolence_review import BenevolenceReview
from src.models.grievance import Grievance
from src.models.grievance_step_record import GrievanceStepRecord

# Auth models
from src.models.user import User
from src.models.role import Role
from src.models.user_role import UserRole
from src.models.refresh_token import RefreshToken

__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    # Phase 1
    "Organization",
    "OrganizationContact",
    "Member",
    "MemberEmployment",
    "AuditLog",
    "FileAttachment",
    # Phase 2
    "SaltingActivity",
    "BenevolenceApplication",
    "BenevolenceReview",
    "Grievance",
    "GrievanceStepRecord",
    # Auth
    "User",
    "Role",
    "UserRole",
    "RefreshToken",
]
```

---

### Step 8: Create Database Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Add auth models: User, Role, UserRole, RefreshToken"

# Review the generated migration file in alembic/versions/
# Verify it creates:
# - users table
# - roles table
# - user_roles table
# - refresh_tokens table
# - Adds member_id FK to users
# - Adds user relationship to members

# Apply migration
alembic upgrade head
```

---

### Step 9: Create Auth Schemas

**File:** `src/schemas/user.py`

```python
"""Pydantic schemas for User model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for User."""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a User."""

    password: str = Field(..., min_length=8, max_length=128)
    member_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Schema for updating a User."""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    member_id: Optional[int] = None


class UserRead(UserBase):
    """Schema for reading a User."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    member_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    role_names: list[str] = []


class UserReadWithRoles(UserRead):
    """Schema for reading a User with full role details."""

    roles: list["RoleRead"] = []


# Avoid circular import
from src.schemas.role import RoleRead
UserReadWithRoles.model_rebuild()
```

**File:** `src/schemas/role.py`

```python
"""Pydantic schemas for Role model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    """Base schema for Role."""

    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a Role."""

    is_system_role: bool = False


class RoleUpdate(BaseModel):
    """Schema for updating a Role."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class RoleRead(RoleBase):
    """Schema for reading a Role."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_system_role: bool
    created_at: datetime
    updated_at: datetime
```

**File:** `src/schemas/user_role.py`

```python
"""Pydantic schemas for UserRole model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserRoleBase(BaseModel):
    """Base schema for UserRole."""

    user_id: int
    role_id: int


class UserRoleCreate(UserRoleBase):
    """Schema for creating a UserRole."""

    assigned_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserRoleRead(UserRoleBase):
    """Schema for reading a UserRole."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    assigned_by: Optional[str] = None
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
```

**File:** `src/schemas/refresh_token.py`

```python
"""Pydantic schemas for RefreshToken model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RefreshTokenCreate(BaseModel):
    """Schema for creating a RefreshToken (internal use)."""

    user_id: int
    token_hash: str
    expires_at: datetime
    device_info: Optional[str] = None
    ip_address: Optional[str] = None


class RefreshTokenRead(BaseModel):
    """Schema for reading a RefreshToken."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    expires_at: datetime
    is_revoked: bool
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
```

---

### Step 10: Update Schemas __init__.py

**File:** `src/schemas/__init__.py`

Add to the file:

```python
# Auth schemas
from src.schemas.user import UserBase, UserCreate, UserUpdate, UserRead, UserReadWithRoles
from src.schemas.role import RoleBase, RoleCreate, RoleUpdate, RoleRead
from src.schemas.user_role import UserRoleBase, UserRoleCreate, UserRoleRead
from src.schemas.refresh_token import RefreshTokenCreate, RefreshTokenRead

# Add to __all__
__all__ = [
    # ... existing exports ...
    # Auth
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserReadWithRoles",
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleRead",
    "UserRoleBase",
    "UserRoleCreate",
    "UserRoleRead",
    "RefreshTokenCreate",
    "RefreshTokenRead",
]
```

---

### Step 11: Create Auth Services

**File:** `src/services/user_service.py`

```python
"""Service functions for User model."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email address."""
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False
) -> list[User]:
    """Get a list of users."""
    stmt = select(User)
    if not include_inactive:
        stmt = stmt.where(User.is_active == True)
    stmt = stmt.offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def create_user(db: Session, user_data: UserCreate, password_hash: str) -> User:
    """
    Create a new user.

    Note: password_hash should be generated by the auth layer,
    not stored as plaintext from user_data.password.
    """
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        password_hash=password_hash,
        member_id=user_data.member_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, user_data: UserUpdate) -> User:
    """Update an existing user."""
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """Soft delete a user."""
    user.soft_delete()
    db.commit()


def verify_user(db: Session, user: User) -> User:
    """Mark user as verified."""
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user
```

**File:** `src/services/role_service.py`

```python
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
```

**File:** `src/services/user_role_service.py`

```python
"""Service functions for UserRole model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.models.user_role import UserRole
from src.schemas.user_role import UserRoleCreate


def get_user_role(db: Session, user_id: int, role_id: int) -> Optional[UserRole]:
    """Get a specific user-role assignment."""
    stmt = select(UserRole).where(
        and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_user_roles(db: Session, user_id: int) -> list[UserRole]:
    """Get all roles for a user."""
    stmt = select(UserRole).where(UserRole.user_id == user_id)
    return list(db.execute(stmt).scalars().all())


def assign_role(db: Session, data: UserRoleCreate) -> UserRole:
    """Assign a role to a user."""
    user_role = UserRole(
        user_id=data.user_id,
        role_id=data.role_id,
        assigned_by=data.assigned_by,
        expires_at=data.expires_at,
    )
    db.add(user_role)
    db.commit()
    db.refresh(user_role)
    return user_role


def remove_role(db: Session, user_role: UserRole) -> None:
    """Remove a role from a user."""
    db.delete(user_role)
    db.commit()


def get_expired_roles(db: Session) -> list[UserRole]:
    """Get all expired role assignments."""
    stmt = select(UserRole).where(
        and_(
            UserRole.expires_at.isnot(None),
            UserRole.expires_at < datetime.utcnow()
        )
    )
    return list(db.execute(stmt).scalars().all())
```

---

### Step 12: Create Role Seed Data

**File:** `src/seed/auth_seed.py`

```python
"""Seed data for authentication system."""

from sqlalchemy.orm import Session

from src.models.role import Role
from src.db.enums import RoleType


DEFAULT_ROLES = [
    {
        "name": RoleType.ADMIN.value,
        "display_name": "Administrator",
        "description": "Full system access. Can manage all users, roles, and system settings.",
        "is_system_role": True,
    },
    {
        "name": RoleType.OFFICER.value,
        "display_name": "Union Officer",
        "description": "Union officer privileges. Can approve benevolence, manage grievances, view reports.",
        "is_system_role": True,
    },
    {
        "name": RoleType.STAFF.value,
        "display_name": "Staff",
        "description": "Staff-level access. Can manage members, employment records, and basic operations.",
        "is_system_role": True,
    },
    {
        "name": RoleType.ORGANIZER.value,
        "display_name": "Organizer",
        "description": "Organizing access. Can manage SALTing activities and organizing campaigns.",
        "is_system_role": True,
    },
    {
        "name": RoleType.INSTRUCTOR.value,
        "display_name": "Instructor",
        "description": "Training program access. Can manage students, classes, and training records.",
        "is_system_role": True,
    },
    {
        "name": RoleType.MEMBER.value,
        "display_name": "Member",
        "description": "Basic member access. Can view own records and submit requests.",
        "is_system_role": True,
    },
]


def seed_roles(db: Session) -> list[Role]:
    """Seed default system roles."""
    created_roles = []

    for role_data in DEFAULT_ROLES:
        # Check if role already exists
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if existing:
            print(f"  Role '{role_data['name']}' already exists, skipping...")
            continue

        role = Role(**role_data)
        db.add(role)
        created_roles.append(role)
        print(f"  Created role: {role_data['display_name']}")

    if created_roles:
        db.commit()

    return created_roles


def run_auth_seed(db: Session) -> dict:
    """Run all auth seed operations."""
    print("\n=== Seeding Auth Data ===")

    roles = seed_roles(db)

    return {
        "roles_created": len(roles),
    }
```

---

### Step 13: Update Main Seed Runner

**File:** `src/seed/run_seed.py` - Add auth seed import and call

Add import at top:

```python
from src.seed.auth_seed import run_auth_seed
```

Add call in appropriate location (after phase 1, before phase 2):

```python
# Run auth seed (roles)
auth_results = run_auth_seed(db)
print(f"Auth: Created {auth_results['roles_created']} roles")
```

---

### Step 14: Create Tests

**File:** `src/tests/test_auth_models.py`

```python
"""Tests for authentication models."""

import pytest
from datetime import datetime, timedelta

from src.models.user import User
from src.models.role import Role
from src.models.user_role import UserRole
from src.models.refresh_token import RefreshToken


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.full_name == "Test User"

    def test_user_email_unique(self, db_session):
        """Test that email must be unique."""
        user1 = User(
            email="same@example.com",
            password_hash="hash1",
            first_name="User",
            last_name="One",
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            email="same@example.com",
            password_hash="hash2",
            first_name="User",
            last_name="Two",
        )
        db_session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_soft_delete(self, db_session):
        """Test soft delete functionality."""
        user = User(
            email="delete@example.com",
            password_hash="hash",
            first_name="Delete",
            last_name="Me",
        )
        db_session.add(user)
        db_session.commit()

        user.soft_delete()
        db_session.commit()

        assert user.deleted_at is not None


class TestRoleModel:
    """Tests for Role model."""

    def test_create_role(self, db_session):
        """Test creating a role."""
        role = Role(
            name="test_role",
            display_name="Test Role",
            description="A test role",
            is_system_role=False,
        )
        db_session.add(role)
        db_session.commit()

        assert role.id is not None
        assert role.name == "test_role"

    def test_role_name_unique(self, db_session):
        """Test that role name must be unique."""
        role1 = Role(name="unique_role", display_name="Role 1")
        db_session.add(role1)
        db_session.commit()

        role2 = Role(name="unique_role", display_name="Role 2")
        db_session.add(role2)

        with pytest.raises(Exception):
            db_session.commit()


class TestUserRoleModel:
    """Tests for UserRole model."""

    def test_assign_role_to_user(self, db_session):
        """Test assigning a role to a user."""
        user = User(
            email="roletest@example.com",
            password_hash="hash",
            first_name="Role",
            last_name="Test",
        )
        role = Role(name="member", display_name="Member")

        db_session.add(user)
        db_session.add(role)
        db_session.commit()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            assigned_by="admin@example.com",
        )
        db_session.add(user_role)
        db_session.commit()

        assert user_role.id is not None
        assert user.has_role("member")

    def test_user_role_unique_constraint(self, db_session):
        """Test that user can only have each role once."""
        user = User(
            email="unique@example.com",
            password_hash="hash",
            first_name="Unique",
            last_name="User",
        )
        role = Role(name="single_role", display_name="Single Role")

        db_session.add(user)
        db_session.add(role)
        db_session.commit()

        ur1 = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(ur1)
        db_session.commit()

        ur2 = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(ur2)

        with pytest.raises(Exception):
            db_session.commit()


class TestRefreshTokenModel:
    """Tests for RefreshToken model."""

    def test_create_refresh_token(self, db_session):
        """Test creating a refresh token."""
        user = User(
            email="token@example.com",
            password_hash="hash",
            first_name="Token",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash="abc123hash",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(token)
        db_session.commit()

        assert token.id is not None
        assert token.is_valid is True
        assert token.is_expired is False
        assert token.is_revoked is False

    def test_expired_token(self, db_session):
        """Test expired token detection."""
        user = User(
            email="expired@example.com",
            password_hash="hash",
            first_name="Expired",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash="expiredhash",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        db_session.add(token)
        db_session.commit()

        assert token.is_expired is True
        assert token.is_valid is False

    def test_revoked_token(self, db_session):
        """Test revoked token detection."""
        user = User(
            email="revoked@example.com",
            password_hash="hash",
            first_name="Revoked",
            last_name="User",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash="revokedhash",
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_revoked=True,
            revoked_at=datetime.utcnow(),
        )
        db_session.add(token)
        db_session.commit()

        assert token.is_revoked is True
        assert token.is_valid is False
```

**File:** `src/tests/test_auth_services.py`

```python
"""Tests for authentication services."""

import pytest

from src.models.user import User
from src.models.role import Role
from src.services.user_service import (
    create_user,
    get_user,
    get_user_by_email,
    get_users,
    update_user,
    delete_user,
)
from src.services.role_service import (
    create_role,
    get_role,
    get_role_by_name,
    get_roles,
)
from src.services.user_role_service import (
    assign_role,
    get_user_roles,
    remove_role,
)
from src.schemas.user import UserCreate, UserUpdate
from src.schemas.role import RoleCreate
from src.schemas.user_role import UserRoleCreate


class TestUserService:
    """Tests for user service."""

    def test_create_user(self, db_session):
        """Test creating a user through service."""
        user_data = UserCreate(
            email="service@example.com",
            first_name="Service",
            last_name="Test",
            password="securepassword123",
        )

        user = create_user(db_session, user_data, password_hash="hashed_pw")

        assert user.id is not None
        assert user.email == "service@example.com"
        assert user.password_hash == "hashed_pw"

    def test_get_user_by_email(self, db_session):
        """Test finding user by email."""
        user = User(
            email="find@example.com",
            password_hash="hash",
            first_name="Find",
            last_name="Me",
        )
        db_session.add(user)
        db_session.commit()

        found = get_user_by_email(db_session, "find@example.com")
        assert found is not None
        assert found.id == user.id

        not_found = get_user_by_email(db_session, "notexist@example.com")
        assert not_found is None

    def test_update_user(self, db_session):
        """Test updating a user."""
        user = User(
            email="update@example.com",
            password_hash="hash",
            first_name="Before",
            last_name="Update",
        )
        db_session.add(user)
        db_session.commit()

        update_data = UserUpdate(first_name="After")
        updated = update_user(db_session, user, update_data)

        assert updated.first_name == "After"
        assert updated.last_name == "Update"  # Unchanged


class TestRoleService:
    """Tests for role service."""

    def test_create_role(self, db_session):
        """Test creating a role through service."""
        role_data = RoleCreate(
            name="Custom Role",
            display_name="Custom Role",
            description="A custom role",
        )

        role = create_role(db_session, role_data)

        assert role.id is not None
        assert role.name == "custom role"  # Lowercased

    def test_get_role_by_name(self, db_session):
        """Test finding role by name."""
        role = Role(name="findme", display_name="Find Me")
        db_session.add(role)
        db_session.commit()

        found = get_role_by_name(db_session, "findme")
        assert found is not None

        # Case insensitive
        found_upper = get_role_by_name(db_session, "FINDME")
        assert found_upper is not None


class TestUserRoleService:
    """Tests for user role service."""

    def test_assign_and_remove_role(self, db_session):
        """Test assigning and removing roles."""
        user = User(
            email="roleop@example.com",
            password_hash="hash",
            first_name="Role",
            last_name="Op",
        )
        role = Role(name="testassign", display_name="Test Assign")
        db_session.add(user)
        db_session.add(role)
        db_session.commit()

        # Assign
        assignment = UserRoleCreate(
            user_id=user.id,
            role_id=role.id,
            assigned_by="admin",
        )
        user_role = assign_role(db_session, assignment)
        assert user_role.id is not None

        # Verify
        roles = get_user_roles(db_session, user.id)
        assert len(roles) == 1

        # Remove
        remove_role(db_session, user_role)
        roles_after = get_user_roles(db_session, user.id)
        assert len(roles_after) == 0
```

---

### Step 15: Run Tests and Verify

```bash
# Run all tests
pytest -v

# Run only auth tests
pytest -v src/tests/test_auth_models.py src/tests/test_auth_services.py

# Check code quality
ruff check . --fix
ruff format .
```

---

### Step 16: Update Documentation

**Update CLAUDE.md** - Add Auth section to models list and update phase status.

**Update CHANGELOG.md** - Add entry for auth schema implementation.

---

## Verification Checklist

Before committing, verify:

- [ ] All 4 new models created (User, Role, UserRole, RefreshToken)
- [ ] Auth enums created and exported
- [ ] Member model updated with user relationship
- [ ] Migration generated and applied
- [ ] Schemas created for all auth models
- [ ] Services created with CRUD operations
- [ ] Role seed data created
- [ ] All new tests pass
- [ ] All existing tests still pass (79/82)
- [ ] Code passes ruff check
- [ ] CLAUDE.md updated
- [ ] CHANGELOG.md updated

---

## Commit Message Template

```
feat(auth): Add authentication database schema

- Add User model with email/password auth fields
- Add Role model for RBAC
- Add UserRole junction with assignment metadata
- Add RefreshToken model for JWT token management
- Add auth enums (RoleType, TokenType)
- Add Member.user backref relationship
- Add schemas for all auth models
- Add services for user, role, user_role management
- Add seed data for 6 default system roles
- Add comprehensive tests (X new tests passing)

Phase 1.1 complete. Ready for Phase 1.2 (JWT implementation).
```

---

## Next Phase Preview

**Phase 1.2: JWT Authentication** (4-6 hours)
- Password hashing with bcrypt/passlib
- JWT token generation and validation
- Login/logout endpoints
- Token refresh flow
- Password reset flow

---

*End of Instructions*
