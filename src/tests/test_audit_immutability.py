"""Tests for audit log immutability."""
import pytest
from sqlalchemy.exc import InternalError, ProgrammingError
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
        with pytest.raises((InternalError, ProgrammingError)) as exc_info:
            db_session.execute(text("""
                UPDATE audit_logs SET notes = 'modified'
                WHERE action = 'TEST' AND table_name = 'test_table'
            """))
            db_session.commit()

        # Check that error message mentions immutability
        error_msg = str(exc_info.value).lower()
        assert "immutable" in error_msg or "prohibited" in error_msg
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
        with pytest.raises((InternalError, ProgrammingError)) as exc_info:
            db_session.execute(text("""
                DELETE FROM audit_logs
                WHERE action = 'TEST_DELETE' AND table_name = 'test_table'
            """))
            db_session.commit()

        # Check that error message mentions immutability
        error_msg = str(exc_info.value).lower()
        assert "immutable" in error_msg or "prohibited" in error_msg
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

    def test_audit_log_select_still_works(self, db_session):
        """Test that SELECT on audit_logs still works."""
        # Insert a test record
        db_session.execute(text("""
            INSERT INTO audit_logs (action, table_name, record_id, user_id, created_at)
            VALUES ('TEST_SELECT', 'test_table', 4, 1, NOW())
        """))
        db_session.commit()

        # Query the record
        result = db_session.execute(text("""
            SELECT action, table_name FROM audit_logs
            WHERE action = 'TEST_SELECT'
        """))

        row = result.fetchone()
        assert row is not None
        assert row[0] == 'TEST_SELECT'
        assert row[1] == 'test_table'
