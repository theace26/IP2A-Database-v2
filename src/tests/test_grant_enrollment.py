"""Tests for grant enrollment model and enums."""
import pytest
from datetime import date

from src.db.enums import GrantStatus, GrantEnrollmentStatus, GrantOutcome


class TestGrantEnums:
    """Test grant-related enums."""

    def test_grant_status_values(self):
        """Verify GrantStatus enum has expected values."""
        assert GrantStatus.PENDING.value == "pending"
        assert GrantStatus.ACTIVE.value == "active"
        assert GrantStatus.COMPLETED.value == "completed"
        assert GrantStatus.CLOSED.value == "closed"
        assert GrantStatus.SUSPENDED.value == "suspended"

    def test_grant_enrollment_status_values(self):
        """Verify GrantEnrollmentStatus enum has expected values."""
        assert GrantEnrollmentStatus.ENROLLED.value == "enrolled"
        assert GrantEnrollmentStatus.ACTIVE.value == "active"
        assert GrantEnrollmentStatus.COMPLETED.value == "completed"
        assert GrantEnrollmentStatus.WITHDRAWN.value == "withdrawn"
        assert GrantEnrollmentStatus.DROPPED.value == "dropped"

    def test_grant_outcome_values(self):
        """Verify GrantOutcome enum has expected values."""
        assert GrantOutcome.COMPLETED_PROGRAM.value == "completed_program"
        assert GrantOutcome.OBTAINED_CREDENTIAL.value == "obtained_credential"
        assert GrantOutcome.ENTERED_APPRENTICESHIP.value == "entered_apprenticeship"
        assert GrantOutcome.OBTAINED_EMPLOYMENT.value == "obtained_employment"
        assert GrantOutcome.CONTINUED_EDUCATION.value == "continued_education"
        assert GrantOutcome.WITHDRAWN.value == "withdrawn"
        assert GrantOutcome.OTHER.value == "other"


class TestGrantModel:
    """Test Grant model enhancements."""

    def test_grant_model_has_status(self):
        """Verify Grant model has status field."""
        from src.models import Grant
        assert hasattr(Grant, "status")

    def test_grant_model_has_target_fields(self):
        """Verify Grant model has target fields."""
        from src.models import Grant
        assert hasattr(Grant, "target_enrollment")
        assert hasattr(Grant, "target_completion")
        assert hasattr(Grant, "target_placement")

    def test_grant_model_has_enrollments_relationship(self):
        """Verify Grant model has enrollments relationship."""
        from src.models import Grant
        assert hasattr(Grant, "enrollments")


class TestGrantEnrollmentModel:
    """Test GrantEnrollment model."""

    def test_grant_enrollment_model_exists(self):
        """Verify GrantEnrollment model can be imported."""
        from src.models.grant_enrollment import GrantEnrollment
        assert GrantEnrollment is not None

    def test_grant_enrollment_has_required_fields(self):
        """Verify GrantEnrollment has required fields."""
        from src.models.grant_enrollment import GrantEnrollment
        assert hasattr(GrantEnrollment, "grant_id")
        assert hasattr(GrantEnrollment, "student_id")
        assert hasattr(GrantEnrollment, "enrollment_date")
        assert hasattr(GrantEnrollment, "status")

    def test_grant_enrollment_has_outcome_fields(self):
        """Verify GrantEnrollment has outcome tracking fields."""
        from src.models.grant_enrollment import GrantEnrollment
        assert hasattr(GrantEnrollment, "outcome")
        assert hasattr(GrantEnrollment, "outcome_date")
        assert hasattr(GrantEnrollment, "completion_date")

    def test_grant_enrollment_has_placement_fields(self):
        """Verify GrantEnrollment has placement tracking fields."""
        from src.models.grant_enrollment import GrantEnrollment
        assert hasattr(GrantEnrollment, "placement_employer")
        assert hasattr(GrantEnrollment, "placement_date")
        assert hasattr(GrantEnrollment, "placement_wage")
        assert hasattr(GrantEnrollment, "placement_job_title")

    def test_grant_enrollment_relationships(self):
        """Verify GrantEnrollment has required relationships."""
        from src.models.grant_enrollment import GrantEnrollment
        assert hasattr(GrantEnrollment, "grant")
        assert hasattr(GrantEnrollment, "student")


class TestStudentGrantEnrollmentRelationship:
    """Test Student model grant enrollment relationship."""

    def test_student_has_grant_enrollments(self):
        """Verify Student model has grant_enrollments relationship."""
        from src.models import Student
        assert hasattr(Student, "grant_enrollments")


class TestGrantSchemas:
    """Test grant-related Pydantic schemas."""

    def test_grant_schemas_exist(self):
        """Verify grant schemas can be imported."""
        from src.schemas.grant import (
            GrantBase,
            GrantCreate,
            GrantUpdate,
            GrantRead,
            GrantSummary,
            GrantMetrics,
        )
        assert GrantBase is not None
        assert GrantCreate is not None
        assert GrantUpdate is not None
        assert GrantRead is not None
        assert GrantSummary is not None
        assert GrantMetrics is not None

    def test_grant_enrollment_schemas_exist(self):
        """Verify grant enrollment schemas can be imported."""
        from src.schemas.grant_enrollment import (
            GrantEnrollmentBase,
            GrantEnrollmentCreate,
            GrantEnrollmentUpdate,
            GrantEnrollmentRead,
            GrantEnrollmentWithStudent,
            GrantEnrollmentWithGrant,
            RecordOutcome,
        )
        assert GrantEnrollmentBase is not None
        assert GrantEnrollmentCreate is not None
        assert GrantEnrollmentUpdate is not None
        assert GrantEnrollmentRead is not None
        assert GrantEnrollmentWithStudent is not None
        assert GrantEnrollmentWithGrant is not None
        assert RecordOutcome is not None
