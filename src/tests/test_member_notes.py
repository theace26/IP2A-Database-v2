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

    async def test_create_note_endpoint(self, async_client_with_db):
        """Test POST /api/v1/member-notes/"""
        client, db_session = async_client_with_db

        # Create test user in the same session
        from src.models.user import User
        from src.models.role import Role
        from src.models.user_role import UserRole
        from src.core.security import hash_password
        admin_role = db_session.query(Role).filter(Role.name == "admin").first()
        test_user = User(
            email="test_api@example.com",
            password_hash=hash_password("testpass"),
            first_name="API",
            last_name="Test",
            is_active=True,
            is_verified=True,
        )
        db_session.add(test_user)
        db_session.flush()
        user_role = UserRole(user_id=test_user.id, role_id=admin_role.id)
        db_session.add(user_role)
        db_session.flush()

        # Create test member in the same session
        from src.models.member import Member
        from src.db.enums import MemberStatus, MemberClassification
        test_member = Member(
            first_name="Test",
            last_name="Member",
            member_number="API_TEST_001",
            email="api_member@test.com",
            status=MemberStatus.ACTIVE,
            classification=MemberClassification.JOURNEYMAN,
        )
        db_session.add(test_member)
        db_session.flush()

        # Create auth headers with test_user
        from src.core.jwt import create_access_token
        token = create_access_token(
            subject=test_user.id,
            additional_claims={"email": test_user.email, "roles": ["admin"]},
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/api/v1/member-notes/",
            json={
                "member_id": test_member.id,
                "note_text": "API test note",
                "visibility": "staff_only",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["note_text"] == "API test note"

    async def test_get_notes_for_member(self, async_client_with_db):
        """Test GET /api/v1/member-notes/member/{member_id}"""
        client, db_session = async_client_with_db

        # Create test user and member in the same session
        from src.models.user import User
        from src.models.role import Role
        from src.models.user_role import UserRole
        from src.core.security import hash_password
        from src.models.member import Member
        from src.db.enums import MemberStatus, MemberClassification

        admin_role = db_session.query(Role).filter(Role.name == "admin").first()
        test_user = User(
            email="test_api2@example.com",
            password_hash=hash_password("testpass"),
            first_name="API",
            last_name="Test",
            is_active=True,
            is_verified=True,
        )
        db_session.add(test_user)
        db_session.flush()
        user_role = UserRole(user_id=test_user.id, role_id=admin_role.id)
        db_session.add(user_role)
        db_session.flush()

        test_member = Member(
            first_name="Test",
            last_name="Member",
            member_number="API_TEST_002",
            email="api_member2@test.com",
            status=MemberStatus.ACTIVE,
            classification=MemberClassification.JOURNEYMAN,
        )
        db_session.add(test_member)
        db_session.flush()

        # Create auth headers with test_user
        from src.core.jwt import create_access_token
        token = create_access_token(
            subject=test_user.id,
            additional_claims={"email": test_user.email, "roles": ["admin"]},
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Create a note first
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="Test note for retrieval",
            visibility=NoteVisibility.ALL_AUTHORIZED
        )
        db_session.add(note)
        db_session.commit()

        response = await client.get(
            f"/api/v1/member-notes/member/{test_member.id}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_get_note_by_id(self, async_client_with_db):
        """Test GET /api/v1/member-notes/{note_id}"""
        client, db_session = async_client_with_db

        # Create test user and member in the same session
        from src.models.user import User
        from src.models.role import Role
        from src.models.user_role import UserRole
        from src.core.security import hash_password
        from src.models.member import Member
        from src.db.enums import MemberStatus, MemberClassification

        admin_role = db_session.query(Role).filter(Role.name == "admin").first()
        test_user = User(
            email="test_api3@example.com",
            password_hash=hash_password("testpass"),
            first_name="API",
            last_name="Test",
            is_active=True,
            is_verified=True,
        )
        db_session.add(test_user)
        db_session.flush()
        user_role = UserRole(user_id=test_user.id, role_id=admin_role.id)
        db_session.add(user_role)
        db_session.flush()

        test_member = Member(
            first_name="Test",
            last_name="Member",
            member_number="API_TEST_003",
            email="api_member3@test.com",
            status=MemberStatus.ACTIVE,
            classification=MemberClassification.JOURNEYMAN,
        )
        db_session.add(test_member)
        db_session.flush()

        # Create auth headers with test_user
        from src.core.jwt import create_access_token
        token = create_access_token(
            subject=test_user.id,
            additional_claims={"email": test_user.email, "roles": ["admin"]},
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Create a note
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="Test note",
            visibility=NoteVisibility.ALL_AUTHORIZED
        )
        db_session.add(note)
        db_session.commit()

        response = await client.get(
            f"/api/v1/member-notes/{note.id}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == note.id
        assert data["note_text"] == "Test note"

    async def test_update_note_endpoint(self, async_client_with_db):
        """Test PATCH /api/v1/member-notes/{note_id}"""
        client, db_session = async_client_with_db

        # Create test user and member in the same session
        from src.models.user import User
        from src.models.role import Role
        from src.models.user_role import UserRole
        from src.core.security import hash_password
        from src.models.member import Member
        from src.db.enums import MemberStatus, MemberClassification

        admin_role = db_session.query(Role).filter(Role.name == "admin").first()
        test_user = User(
            email="test_api4@example.com",
            password_hash=hash_password("testpass"),
            first_name="API",
            last_name="Test",
            is_active=True,
            is_verified=True,
        )
        db_session.add(test_user)
        db_session.flush()
        user_role = UserRole(user_id=test_user.id, role_id=admin_role.id)
        db_session.add(user_role)
        db_session.flush()

        test_member = Member(
            first_name="Test",
            last_name="Member",
            member_number="API_TEST_004",
            email="api_member4@test.com",
            status=MemberStatus.ACTIVE,
            classification=MemberClassification.JOURNEYMAN,
        )
        db_session.add(test_member)
        db_session.flush()

        # Create auth headers with test_user
        from src.core.jwt import create_access_token
        token = create_access_token(
            subject=test_user.id,
            additional_claims={"email": test_user.email, "roles": ["admin"]},
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Create a note
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="Original",
            visibility=NoteVisibility.STAFF_ONLY
        )
        db_session.add(note)
        db_session.commit()

        response = await client.patch(
            f"/api/v1/member-notes/{note.id}",
            json={"note_text": "Updated via API"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["note_text"] == "Updated via API"

    async def test_delete_note_endpoint(self, async_client_with_db):
        """Test DELETE /api/v1/member-notes/{note_id}"""
        client, db_session = async_client_with_db

        # Create test user and member in the same session
        from src.models.user import User
        from src.models.role import Role
        from src.models.user_role import UserRole
        from src.core.security import hash_password
        from src.models.member import Member
        from src.db.enums import MemberStatus, MemberClassification

        admin_role = db_session.query(Role).filter(Role.name == "admin").first()
        test_user = User(
            email="test_api5@example.com",
            password_hash=hash_password("testpass"),
            first_name="API",
            last_name="Test",
            is_active=True,
            is_verified=True,
        )
        db_session.add(test_user)
        db_session.flush()
        user_role = UserRole(user_id=test_user.id, role_id=admin_role.id)
        db_session.add(user_role)
        db_session.flush()

        test_member = Member(
            first_name="Test",
            last_name="Member",
            member_number="API_TEST_005",
            email="api_member5@test.com",
            status=MemberStatus.ACTIVE,
            classification=MemberClassification.JOURNEYMAN,
        )
        db_session.add(test_member)
        db_session.flush()

        # Create auth headers with test_user
        from src.core.jwt import create_access_token
        token = create_access_token(
            subject=test_user.id,
            additional_claims={"email": test_user.email, "roles": ["admin"]},
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Create a note
        note = MemberNote(
            member_id=test_member.id,
            created_by_id=test_user.id,
            note_text="To be deleted",
        )
        db_session.add(note)
        db_session.commit()

        response = await client.delete(
            f"/api/v1/member-notes/{note.id}",
            headers=headers,
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
