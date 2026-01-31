"""Service layer for member notes."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from src.models.member_note import MemberNote, NoteVisibility
from src.models.user import User
from src.schemas.member_note import MemberNoteCreate, MemberNoteUpdate
from src.services.audit_service import log_create, log_update, log_delete


class MemberNoteService:
    """Service for managing member notes."""

    @staticmethod
    def create(
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
        log_create(
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

    @staticmethod
    def get_by_id(db: Session, note_id: int) -> Optional[MemberNote]:
        """Get a note by ID."""
        return db.query(MemberNote).filter(
            MemberNote.id == note_id,
            MemberNote.is_deleted == False
        ).first()

    @staticmethod
    def get_by_member(
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
        visible_levels = MemberNoteService._get_visible_levels(current_user)

        # Special case: staff can see their own staff_only notes
        from sqlalchemy import or_
        if current_user.role not in ["admin", "officer"]:
            query = query.filter(
                or_(
                    MemberNote.visibility.in_(visible_levels),
                    MemberNote.created_by_id == current_user.id
                )
            )
        else:
            query = query.filter(MemberNote.visibility.in_(visible_levels))

        return query.options(
            joinedload(MemberNote.created_by)
        ).order_by(MemberNote.created_at.desc()).all()

    @staticmethod
    def _get_visible_levels(user: User) -> List[str]:
        """Determine which visibility levels a user can see."""
        # Admin sees everything
        if user.role == "admin":
            return [NoteVisibility.STAFF_ONLY, NoteVisibility.OFFICERS, NoteVisibility.ALL_AUTHORIZED]

        # Officers see officers and all_authorized
        if user.role in ["officer", "organizer"]:
            return [NoteVisibility.OFFICERS, NoteVisibility.ALL_AUTHORIZED]

        # Staff sees only all_authorized (and their own staff_only notes, handled separately)
        return [NoteVisibility.ALL_AUTHORIZED]

    @staticmethod
    def update(
        db: Session,
        note_id: int,
        data: MemberNoteUpdate,
        current_user: User
    ) -> Optional[MemberNote]:
        """Update an existing note."""
        note = MemberNoteService.get_by_id(db, note_id)
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
        log_update(
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

    @staticmethod
    def soft_delete(
        db: Session,
        note_id: int,
        current_user: User
    ) -> bool:
        """Soft delete a note (preserves for audit trail)."""
        note = MemberNoteService.get_by_id(db, note_id)
        if not note:
            return False

        note.is_deleted = True
        note.deleted_at = datetime.utcnow()

        # Audit the deletion
        log_delete(
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
