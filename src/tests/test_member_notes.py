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

    def test_note_soft_delete(self, db_session, test_member, test_user):
        """Test soft delete sets is_deleted flag."""
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="Note to delete",
        )
        db_session.add(note)
        db_session.commit()

        note.is_deleted = True
        db_session.commit()

        assert note.is_deleted == True


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

    def test_get_by_id(self, db_session, test_member, test_user):
        """Test getting note by ID."""
        data = MemberNoteCreate(
            member_id=test_member.id,
            note_text="Test note",
        )
        note = member_note_service.create(db_session, data, test_user)

        retrieved = member_note_service.get_by_id(db_session, note.id)

        assert retrieved is not None
        assert retrieved.id == note.id
        assert retrieved.note_text == "Test note"

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

    def test_get_by_id_excludes_deleted(self, db_session, test_member, test_user):
        """Test that get_by_id doesn't return deleted notes."""
        data = MemberNoteCreate(
            member_id=test_member.id,
            note_text="Deleted note",
        )
        note = member_note_service.create(db_session, data, test_user)
        note_id = note.id

        # Delete the note
        member_note_service.soft_delete(db_session, note_id, test_user)

        # Try to retrieve - should return None
        retrieved = member_note_service.get_by_id(db_session, note_id)
        assert retrieved is None

    def test_update_note(self, db_session, test_member, test_user):
        """Test updating a note."""
        data = MemberNoteCreate(
            member_id=test_member.id,
            note_text="Original text",
            visibility="staff_only",
        )
        note = member_note_service.create(db_session, data, test_user)

        # Update
        update_data = MemberNoteUpdate(
            note_text="Updated text",
            visibility="officers"
        )
        updated = member_note_service.update(db_session, note.id, update_data, test_user)

        assert updated is not None
        assert updated.note_text == "Updated text"
        assert updated.visibility == "officers"


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

    def test_get_notes_for_member(self, client, auth_headers, test_member, db_session, test_user):
        """Test GET /api/v1/member-notes/member/{member_id}"""
        # Create a note first
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="Test note for retrieval",
            visibility=NoteVisibility.ALL_AUTHORIZED
        )
        db_session.add(note)
        db_session.commit()

        response = client.get(
            f"/api/v1/member-notes/member/{test_member.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_note_by_id(self, client, auth_headers, test_member, db_session, test_user):
        """Test GET /api/v1/member-notes/{note_id}"""
        # Create a note
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="Test note",
            visibility=NoteVisibility.ALL_AUTHORIZED
        )
        db_session.add(note)
        db_session.commit()

        response = client.get(
            f"/api/v1/member-notes/{note.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == note.id
        assert data["note_text"] == "Test note"

    def test_update_note_endpoint(self, client, auth_headers, test_member, db_session, test_user):
        """Test PATCH /api/v1/member-notes/{note_id}"""
        # Create a note
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="Original",
            visibility=NoteVisibility.STAFF_ONLY
        )
        db_session.add(note)
        db_session.commit()

        response = client.patch(
            f"/api/v1/member-notes/{note.id}",
            json={"note_text": "Updated via API"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["note_text"] == "Updated via API"

    def test_delete_note_endpoint(self, client, auth_headers, test_member, db_session, test_user):
        """Test DELETE /api/v1/member-notes/{note_id}"""
        # Create a note
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="To be deleted",
        )
        db_session.add(note)
        db_session.commit()

        response = client.delete(
            f"/api/v1/member-notes/{note.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's soft deleted
        db_session.expire(note)
        db_session.refresh(note)
        assert note.is_deleted == True

    def test_delete_note_requires_auth(self, client):
        """Test DELETE endpoint requires authentication."""
        response = client.delete("/api/v1/member-notes/1")
        assert response.status_code in [401, 403]

    def test_create_note_requires_auth(self, client):
        """Test POST endpoint requires authentication."""
        response = client.post(
            "/api/v1/member-notes/",
            json={"member_id": 1, "note_text": "Test"}
        )
        assert response.status_code in [401, 403]
