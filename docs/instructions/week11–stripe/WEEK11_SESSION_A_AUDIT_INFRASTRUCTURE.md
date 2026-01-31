# Week 11 Session A: Audit Infrastructure Setup

**Project:** UnionCore (IP2A Database v2)
**Phase:** 6 - Frontend Implementation
**Week:** 11 - Audit Trail & Member History UI
**Session:** A (of 3)
**Estimated Duration:** 3-4 hours
**Branch:** `develop` (ALWAYS work on develop, main is frozen for Railway demo)
**Prerequisite:** Stripe Phase 3 complete (or can run in parallel)

---

## Session Overview

This session establishes critical audit infrastructure for NLRA compliance. We'll add database-level immutability to audit logs and create the member_notes table for staff documentation.

**⚠️ CRITICAL COMPLIANCE WORK:** All member information changes MUST be audited with 7-year retention (NLRA requirement).

---

## Pre-Session Checklist

```bash
# 1. Switch to develop branch
git checkout develop
git pull origin develop

# 2. Start environment
docker-compose up -d

# 3. Verify tests pass
pytest -v --tb=short

# 4. Review existing audit service
cat src/services/audit_service.py | head -100

# 5. Verify audit_logs table exists
# In psql: \d audit_logs
```

---

## Tasks

### Task 1: Add Immutability Trigger to audit_logs (45 min)

**Goal:** Prevent any UPDATE or DELETE operations on audit_logs at the database level.

This is **belt-and-suspenders security** - even if application code has a bug, the database won't allow audit log modification.

#### 1.1 Create Migration

```bash
alembic revision -m "add_audit_logs_immutability_trigger"
```

**File:** `alembic/versions/xxx_add_audit_logs_immutability_trigger.py`

```python
"""add_audit_logs_immutability_trigger

Revision ID: [auto-generated]
Revises: [previous]
Create Date: 2026-01-XX

CRITICAL: This migration enforces NLRA compliance by making audit logs immutable.
DO NOT modify or remove this trigger without legal review.
"""
from alembic import op
import sqlalchemy as sa

revision = '[auto-generated]'
down_revision = '[previous]'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are immutable. UPDATE and DELETE operations are prohibited for NLRA compliance.';
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers for UPDATE and DELETE
    op.execute("""
        CREATE TRIGGER audit_logs_prevent_update
            BEFORE UPDATE ON audit_logs
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_modification();
    """)
    
    op.execute("""
        CREATE TRIGGER audit_logs_prevent_delete
            BEFORE DELETE ON audit_logs
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_modification();
    """)
    
    # Add comment explaining the trigger
    op.execute("""
        COMMENT ON TRIGGER audit_logs_prevent_update ON audit_logs IS 
        'NLRA compliance: Prevents modification of audit records. 7-year retention required.';
    """)
    
    op.execute("""
        COMMENT ON TRIGGER audit_logs_prevent_delete ON audit_logs IS 
        'NLRA compliance: Prevents deletion of audit records. 7-year retention required.';
    """)


def downgrade() -> None:
    # WARNING: Removing this trigger may violate NLRA compliance requirements
    # Only downgrade if you have legal approval
    op.execute("DROP TRIGGER IF EXISTS audit_logs_prevent_update ON audit_logs;")
    op.execute("DROP TRIGGER IF EXISTS audit_logs_prevent_delete ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_modification();")
```

#### 1.2 Apply Migration

```bash
alembic upgrade head
```

#### 1.3 Verify Trigger Works

```sql
-- Test 1: Attempt UPDATE (should fail)
UPDATE audit_logs SET notes = 'test' WHERE id = 1;
-- Expected error: "Audit logs are immutable..."

-- Test 2: Attempt DELETE (should fail)
DELETE FROM audit_logs WHERE id = 1;
-- Expected error: "Audit logs are immutable..."

-- Test 3: INSERT should still work
INSERT INTO audit_logs (action, table_name, record_id, user_id, created_at)
VALUES ('TEST', 'test_table', 999, 1, NOW());
-- Should succeed

-- Verify triggers exist
SELECT tgname, tgtype, tgenabled 
FROM pg_trigger 
WHERE tgrelid = 'audit_logs'::regclass;
```

#### 1.4 Write Immutability Test

**File:** `src/tests/test_audit_immutability.py`

```python
"""Tests for audit log immutability."""
import pytest
from sqlalchemy.exc import InternalError
from sqlalchemy import text


class TestAuditImmutability:
    """Tests that audit logs cannot be modified or deleted."""

    def test_audit_log_update_blocked(self, db_session):
        """Test that UPDATE on audit_logs is blocked by trigger."""
        # First, create an audit log entry
        db_session.execute(text("""
            INSERT INTO audit_logs (action, table_name, record_id, user_id, created_at)
            VALUES ('TEST', 'test_table', 1, 1, NOW())
        """))
        db_session.commit()
        
        # Attempt to UPDATE - should fail
        with pytest.raises(InternalError) as exc_info:
            db_session.execute(text("""
                UPDATE audit_logs SET notes = 'modified' 
                WHERE action = 'TEST' AND table_name = 'test_table'
            """))
            db_session.commit()
        
        assert "immutable" in str(exc_info.value).lower()
        db_session.rollback()

    def test_audit_log_delete_blocked(self, db_session):
        """Test that DELETE on audit_logs is blocked by trigger."""
        # Create an audit log entry
        db_session.execute(text("""
            INSERT INTO audit_logs (action, table_name, record_id, user_id, created_at)
            VALUES ('TEST_DELETE', 'test_table', 2, 1, NOW())
        """))
        db_session.commit()
        
        # Attempt to DELETE - should fail
        with pytest.raises(InternalError) as exc_info:
            db_session.execute(text("""
                DELETE FROM audit_logs 
                WHERE action = 'TEST_DELETE' AND table_name = 'test_table'
            """))
            db_session.commit()
        
        assert "immutable" in str(exc_info.value).lower()
        db_session.rollback()

    def test_audit_log_insert_still_works(self, db_session):
        """Test that INSERT on audit_logs still works."""
        result = db_session.execute(text("""
            INSERT INTO audit_logs (action, table_name, record_id, user_id, created_at)
            VALUES ('TEST_INSERT', 'test_table', 3, 1, NOW())
            RETURNING id
        """))
        db_session.commit()
        
        inserted_id = result.scalar()
        assert inserted_id is not None
        assert inserted_id > 0
```

---

### Task 2: Create member_notes Table (60 min)

**Goal:** Add a dedicated table for staff notes on members, with full audit integration.

#### 2.1 Create MemberNote Model

**File:** `src/models/member_note.py`

```python
"""Member notes model for staff documentation."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.mixins import TimestampMixin


class NoteVisibility:
    """Visibility levels for member notes."""
    STAFF_ONLY = "staff_only"          # Only staff who created or admins
    OFFICERS = "officers"               # Officers and above
    ALL_AUTHORIZED = "all_authorized"   # Anyone with member view permission


class MemberNote(Base, TimestampMixin):
    """
    Staff notes about members.
    
    All changes to this table are automatically audited for NLRA compliance.
    Notes have visibility levels to control who can see sensitive information.
    """
    __tablename__ = "member_notes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    member_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Note content
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Visibility control
    visibility: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=NoteVisibility.STAFF_ONLY,
        comment="Who can view this note: staff_only, officers, all_authorized"
    )
    
    # Categorization (optional)
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Optional category: contact, dues, grievance, general, etc."
    )
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    member = relationship("Member", back_populates="notes")
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    def __repr__(self) -> str:
        return f"<MemberNote(id={self.id}, member_id={self.member_id}, visibility={self.visibility})>"
```

#### 2.2 Update Member Model with Relationship

**File:** `src/models/member.py`

Add to Member class:
```python
# Relationships
notes = relationship(
    "MemberNote", 
    back_populates="member",
    cascade="all, delete-orphan",
    order_by="desc(MemberNote.created_at)"
)
```

#### 2.3 Create Schemas

**File:** `src/schemas/member_note.py`

```python
"""Pydantic schemas for member notes."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MemberNoteBase(BaseModel):
    """Base schema for member note."""
    note_text: str = Field(..., min_length=1, max_length=10000)
    visibility: str = Field(default="staff_only")
    category: Optional[str] = Field(default=None, max_length=50)


class MemberNoteCreate(MemberNoteBase):
    """Schema for creating a member note."""
    member_id: int


class MemberNoteUpdate(BaseModel):
    """Schema for updating a member note."""
    note_text: Optional[str] = Field(None, min_length=1, max_length=10000)
    visibility: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)


class MemberNoteRead(MemberNoteBase):
    """Schema for reading a member note."""
    id: int
    member_id: int
    created_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    
    # Include creator info
    created_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class MemberNoteList(BaseModel):
    """Schema for listing member notes."""
    items: list[MemberNoteRead]
    total: int
```

#### 2.4 Create Migration

```bash
alembic revision --autogenerate -m "create_member_notes_table"
```

Verify the migration creates:
- `member_notes` table with all columns
- Foreign keys to `members` and `users`
- Indexes on `member_id` and `created_by_id`

```bash
alembic upgrade head
```

#### 2.5 Add to AUDITED_TABLES

**File:** `src/services/audit_service.py`

Add `member_notes` to the `AUDITED_TABLES` constant:

```python
AUDITED_TABLES = [
    "members",
    "member_employments",
    "member_notes",        # Added for staff notes auditing
    "students",
    "users",
    "dues_payments",
    "grievances",
    "benevolence_applications",
    "salting_activities",
]
```

---

### Task 3: Create MemberNoteService (45 min)

**Goal:** Service layer for CRUD operations on member notes with audit integration.

**File:** `src/services/member_note_service.py`

```python
"""Service layer for member notes."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from src.models.member_note import MemberNote, NoteVisibility
from src.models.user import User
from src.schemas.member_note import MemberNoteCreate, MemberNoteUpdate
from src.services.audit_service import audit_service


class MemberNoteService:
    """Service for managing member notes."""

    def create(
        self, 
        db: Session, 
        data: MemberNoteCreate, 
        current_user: User
    ) -> MemberNote:
        """Create a new member note."""
        note = MemberNote(
            member_id=data.member_id,
            note_text=data.note_text,
            visibility=data.visibility,
            category=data.category,
            created_by_id=current_user.id,
        )
        db.add(note)
        db.flush()
        
        # Audit the creation
        audit_service.log_create(
            db=db,
            table_name="member_notes",
            record_id=note.id,
            user_id=current_user.id,
            new_values={
                "member_id": note.member_id,
                "note_text": note.note_text[:100] + "..." if len(note.note_text) > 100 else note.note_text,
                "visibility": note.visibility,
                "category": note.category,
            }
        )
        
        db.commit()
        db.refresh(note)
        return note

    def get_by_id(self, db: Session, note_id: int) -> Optional[MemberNote]:
        """Get a note by ID."""
        return db.query(MemberNote).filter(
            MemberNote.id == note_id,
            MemberNote.is_deleted == False
        ).first()

    def get_by_member(
        self, 
        db: Session, 
        member_id: int,
        current_user: User,
        include_deleted: bool = False
    ) -> List[MemberNote]:
        """
        Get all notes for a member, filtered by user's permission level.
        """
        query = db.query(MemberNote).filter(MemberNote.member_id == member_id)
        
        if not include_deleted:
            query = query.filter(MemberNote.is_deleted == False)
        
        # Filter by visibility based on user role
        visible_levels = self._get_visible_levels(current_user)
        query = query.filter(MemberNote.visibility.in_(visible_levels))
        
        return query.options(
            joinedload(MemberNote.created_by)
        ).order_by(MemberNote.created_at.desc()).all()

    def _get_visible_levels(self, user: User) -> List[str]:
        """Determine which visibility levels a user can see."""
        # Admin sees everything
        if user.role == "admin":
            return [NoteVisibility.STAFF_ONLY, NoteVisibility.OFFICERS, NoteVisibility.ALL_AUTHORIZED]
        
        # Officers see officers and all_authorized
        if user.role in ["officer", "organizer"]:
            return [NoteVisibility.OFFICERS, NoteVisibility.ALL_AUTHORIZED]
        
        # Staff sees only all_authorized (and their own staff_only notes)
        # This is handled separately in the query if needed
        return [NoteVisibility.ALL_AUTHORIZED]

    def update(
        self, 
        db: Session, 
        note_id: int, 
        data: MemberNoteUpdate, 
        current_user: User
    ) -> Optional[MemberNote]:
        """Update an existing note."""
        note = self.get_by_id(db, note_id)
        if not note:
            return None
        
        # Capture old values for audit
        old_values = {
            "note_text": note.note_text[:100] + "..." if len(note.note_text) > 100 else note.note_text,
            "visibility": note.visibility,
            "category": note.category,
        }
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)
        
        # Capture new values
        new_values = {
            "note_text": note.note_text[:100] + "..." if len(note.note_text) > 100 else note.note_text,
            "visibility": note.visibility,
            "category": note.category,
        }
        
        # Audit the update
        audit_service.log_update(
            db=db,
            table_name="member_notes",
            record_id=note.id,
            user_id=current_user.id,
            old_values=old_values,
            new_values=new_values
        )
        
        db.commit()
        db.refresh(note)
        return note

    def soft_delete(
        self, 
        db: Session, 
        note_id: int, 
        current_user: User
    ) -> bool:
        """Soft delete a note (preserves for audit trail)."""
        note = self.get_by_id(db, note_id)
        if not note:
            return False
        
        note.is_deleted = True
        note.deleted_at = datetime.utcnow()
        
        # Audit the deletion
        audit_service.log_delete(
            db=db,
            table_name="member_notes",
            record_id=note.id,
            user_id=current_user.id,
            old_values={
                "member_id": note.member_id,
                "note_text": note.note_text[:100] + "..." if len(note.note_text) > 100 else note.note_text,
                "visibility": note.visibility,
            }
        )
        
        db.commit()
        return True


# Singleton instance
member_note_service = MemberNoteService()
```

---

### Task 4: Create Member Notes Router (30 min)

**Goal:** REST API endpoints for member notes.

**File:** `src/routers/member_notes.py`

```python
"""API endpoints for member notes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.user import User
from src.routers.dependencies.auth import get_current_active_user
from src.schemas.member_note import (
    MemberNoteCreate,
    MemberNoteUpdate,
    MemberNoteRead,
    MemberNoteList,
)
from src.services.member_note_service import member_note_service

router = APIRouter(prefix="/member-notes", tags=["member-notes"])


@router.post("/", response_model=MemberNoteRead, status_code=status.HTTP_201_CREATED)
def create_note(
    data: MemberNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new member note."""
    note = member_note_service.create(db, data, current_user)
    return _note_to_read(note)


@router.get("/member/{member_id}", response_model=MemberNoteList)
def get_notes_for_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all notes for a member (filtered by permission)."""
    notes = member_note_service.get_by_member(db, member_id, current_user)
    return MemberNoteList(
        items=[_note_to_read(n) for n in notes],
        total=len(notes)
    )


@router.get("/{note_id}", response_model=MemberNoteRead)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific note by ID."""
    note = member_note_service.get_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check visibility permission
    visible_levels = member_note_service._get_visible_levels(current_user)
    if note.visibility not in visible_levels:
        raise HTTPException(status_code=403, detail="Not authorized to view this note")
    
    return _note_to_read(note)


@router.patch("/{note_id}", response_model=MemberNoteRead)
def update_note(
    note_id: int,
    data: MemberNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a member note."""
    note = member_note_service.update(db, note_id, data, current_user)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _note_to_read(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Soft delete a member note."""
    success = member_note_service.soft_delete(db, note_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")


def _note_to_read(note) -> MemberNoteRead:
    """Convert MemberNote model to read schema."""
    return MemberNoteRead(
        id=note.id,
        member_id=note.member_id,
        note_text=note.note_text,
        visibility=note.visibility,
        category=note.category,
        created_by_id=note.created_by_id,
        created_by_name=note.created_by.email if note.created_by else None,
        created_at=note.created_at,
        updated_at=note.updated_at,
        is_deleted=note.is_deleted,
    )
```

#### 4.1 Register Router in main.py

**File:** `src/main.py`

```python
from src.routers.member_notes import router as member_notes_router

# ... in router registration section ...
app.include_router(member_notes_router, prefix="/api/v1")
```

---

### Task 5: Write Tests (30 min)

**Goal:** Comprehensive tests for member notes functionality.

**File:** `src/tests/test_member_notes.py`

```python
"""Tests for member notes functionality."""
import pytest
from src.models.member_note import MemberNote, NoteVisibility
from src.schemas.member_note import MemberNoteCreate, MemberNoteUpdate
from src.services.member_note_service import member_note_service


class TestMemberNoteModel:
    """Tests for MemberNote model."""

    def test_create_note(self, db_session, test_member, test_user):
        """Test creating a member note."""
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="Test note content",
            visibility=NoteVisibility.STAFF_ONLY,
        )
        db_session.add(note)
        db_session.commit()
        
        assert note.id is not None
        assert note.note_text == "Test note content"
        assert note.visibility == "staff_only"
        assert note.is_deleted == False


class TestMemberNoteService:
    """Tests for MemberNoteService."""

    def test_create_note(self, db_session, test_member, test_user):
        """Test service creates note with audit trail."""
        data = MemberNoteCreate(
            member_id=test_member.id,
            note_text="Service test note",
            visibility="officers",
        )
        
        note = member_note_service.create(db_session, data, test_user)
        
        assert note.id is not None
        assert note.created_by_id == test_user.id
        assert note.visibility == "officers"

    def test_soft_delete_preserves_note(self, db_session, test_member, test_user):
        """Test soft delete marks note but preserves data."""
        data = MemberNoteCreate(
            member_id=test_member.id,
            note_text="Note to delete",
        )
        note = member_note_service.create(db_session, data, test_user)
        note_id = note.id
        
        # Soft delete
        result = member_note_service.soft_delete(db_session, note_id, test_user)
        assert result == True
        
        # Note still exists in DB but is marked deleted
        deleted_note = db_session.query(MemberNote).filter(
            MemberNote.id == note_id
        ).first()
        assert deleted_note is not None
        assert deleted_note.is_deleted == True
        assert deleted_note.deleted_at is not None

    def test_visibility_filtering(self, db_session, test_member, staff_user, admin_user):
        """Test notes are filtered by visibility and user role."""
        # Create notes with different visibility
        for vis in [NoteVisibility.STAFF_ONLY, NoteVisibility.OFFICERS, NoteVisibility.ALL_AUTHORIZED]:
            data = MemberNoteCreate(
                member_id=test_member.id,
                note_text=f"Note with {vis} visibility",
                visibility=vis,
            )
            member_note_service.create(db_session, data, admin_user)
        
        # Admin sees all 3
        admin_notes = member_note_service.get_by_member(
            db_session, test_member.id, admin_user
        )
        assert len(admin_notes) == 3
        
        # Staff sees only all_authorized
        staff_notes = member_note_service.get_by_member(
            db_session, test_member.id, staff_user
        )
        assert len(staff_notes) == 1
        assert staff_notes[0].visibility == NoteVisibility.ALL_AUTHORIZED


class TestMemberNotesAPI:
    """Tests for member notes API endpoints."""

    def test_create_note_endpoint(self, client, auth_headers, test_member):
        """Test POST /api/v1/member-notes/"""
        response = client.post(
            "/api/v1/member-notes/",
            json={
                "member_id": test_member.id,
                "note_text": "API test note",
                "visibility": "staff_only",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["note_text"] == "API test note"

    def test_get_notes_for_member(self, client, auth_headers, test_member):
        """Test GET /api/v1/member-notes/member/{member_id}"""
        response = client.get(
            f"/api/v1/member-notes/member/{test_member.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_delete_note_requires_auth(self, client):
        """Test DELETE endpoint requires authentication."""
        response = client.delete("/api/v1/member-notes/1")
        assert response.status_code in [401, 403]
```

Run tests:
```bash
pytest src/tests/test_member_notes.py -v
pytest src/tests/test_audit_immutability.py -v
```

---

## Acceptance Criteria

- [ ] Immutability trigger prevents UPDATE on audit_logs
- [ ] Immutability trigger prevents DELETE on audit_logs
- [ ] INSERT on audit_logs still works
- [ ] `member_notes` table created with all columns
- [ ] MemberNote model with visibility levels
- [ ] MemberNoteService with CRUD + audit integration
- [ ] Member notes router registered and working
- [ ] Notes automatically appear in audit trail
- [ ] Visibility filtering works based on user role
- [ ] All tests pass (~10-15 new tests)

---

## Files Created

```
src/models/member_note.py
src/schemas/member_note.py
src/services/member_note_service.py
src/routers/member_notes.py
src/tests/test_member_notes.py
src/tests/test_audit_immutability.py
alembic/versions/xxx_add_audit_logs_immutability_trigger.py
alembic/versions/xxx_create_member_notes_table.py
```

## Files Modified

```
src/models/member.py                 # Added notes relationship
src/services/audit_service.py        # Added member_notes to AUDITED_TABLES
src/main.py                          # Registered member_notes router
```

---

## Next Session Preview

**Week 11 Session B: Audit UI & Role Permissions** will add:
- AuditFrontendService with role-based filtering
- Field-level redaction for sensitive data
- Audit log list page at /admin/audit-logs
- HTMX search/filter functionality

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** 

### Before Ending This Session:

Scan all documentation in `/app/*`. Update *ANY* & *ALL* relevant documentation as necessary with current progress for the historical record. Do not forget to update ADRs, Roadmap, Checklist, again only if necessary.

**Documentation Checklist:**

| Document | Updated? | Notes |
|----------|----------|-------|
| CLAUDE.md | [ ] | Add Week 11 Session A status |
| CHANGELOG.md | [ ] | Add audit immutability + member_notes entries |
| CONTINUITY.md | [ ] | Update current status |
| IP2A_MILESTONE_CHECKLIST.md | [ ] | Update Week 11 progress |
| IP2A_BACKEND_ROADMAP.md | [ ] | Mark 11.1 Database Completeness items |
| ADR-008 (Audit Logging) | [ ] | Update implementation status |
| docs/decisions/README.md | [ ] | Verify ADR index current |
| Session log created | [ ] | `docs/reports/session-logs/` |

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*End of instruction document*
