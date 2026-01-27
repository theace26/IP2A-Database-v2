"""add mixins columns and new fields to all models

Revision ID: 3317e9b9b593
Revises: ad4f65911cd7
Create Date: 2026-01-25 16:55:49.443010

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3317e9b9b593"
down_revision: Union[str, Sequence[str], None] = "ad4f65911cd7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ============================================================
    # STEP 1: Create all enum types FIRST
    # ============================================================

    # Create enum types (these must exist before columns reference them)
    attendance_status = postgresql.ENUM(
        "PRESENT",
        "ABSENT",
        "LATE",
        "EXCUSED",
        "EARLY_DEPARTURE",
        name="attendance_status",
        create_type=True,
    )
    attendance_status.create(op.get_bind(), checkfirst=True)

    cohort_status = postgresql.ENUM(
        "PLANNED",
        "ENROLLING",
        "ACTIVE",
        "COMPLETED",
        "CANCELLED",
        name="cohort_status",
        create_type=True,
    )
    cohort_status.create(op.get_bind(), checkfirst=True)

    credential_status = postgresql.ENUM(
        "PENDING",
        "ACTIVE",
        "EXPIRED",
        "REVOKED",
        "RENEWED",
        name="credential_status",
        create_type=True,
    )
    credential_status.create(op.get_bind(), checkfirst=True)

    payment_method = postgresql.ENUM(
        "CASH",
        "CHECK",
        "CARD",
        "ACH",
        "WIRE",
        "GRANT",
        "OTHER",
        name="payment_method",
        create_type=True,
    )
    payment_method.create(op.get_bind(), checkfirst=True)

    rate_type = postgresql.ENUM(
        "HOURLY", "DAILY", "FLAT", "SALARY", name="rate_type", create_type=True
    )
    rate_type.create(op.get_bind(), checkfirst=True)

    location_type = postgresql.ENUM(
        "TRAINING_SITE",
        "SCHOOL",
        "OFFICE",
        "JOBSITE",
        "VENDOR",
        "OTHER",
        name="location_type",
        create_type=True,
    )
    location_type.create(op.get_bind(), checkfirst=True)

    # ============================================================
    # STEP 2: Create new tables
    # ============================================================

    op.create_table(
        "file_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("record_type", sa.String(length=50), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_file_attachment_record",
        "file_attachments",
        ["record_type", "record_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_file_attachments_id"), "file_attachments", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_file_attachments_is_deleted"),
        "file_attachments",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        op.f("ix_file_attachments_record_id"),
        "file_attachments",
        ["record_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_file_attachments_record_type"),
        "file_attachments",
        ["record_type"],
        unique=False,
    )

    # ============================================================
    # STEP 3: Alter existing tables - ATTENDANCE
    # ============================================================

    # Convert status column from VARCHAR to ENUM (requires USING clause)
    op.execute("""
        ALTER TABLE attendance
        ALTER COLUMN status TYPE attendance_status
        USING status::attendance_status
    """)

    op.create_index(
        op.f("ix_attendance_class_session_id"),
        "attendance",
        ["class_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_is_deleted"), "attendance", ["is_deleted"], unique=False
    )
    op.create_index("ix_attendance_status", "attendance", ["status"], unique=False)
    op.create_index(
        op.f("ix_attendance_student_id"), "attendance", ["student_id"], unique=False
    )

    # Update foreign keys with CASCADE
    op.drop_constraint(
        "attendance_class_session_id_fkey", "attendance", type_="foreignkey"
    )
    op.drop_constraint("attendance_student_id_fkey", "attendance", type_="foreignkey")
    op.create_foreign_key(
        None, "attendance", "students", ["student_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        None,
        "attendance",
        "class_sessions",
        ["class_session_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ============================================================
    # STEP 4: CLASS_SESSIONS
    # ============================================================

    op.alter_column(
        "class_sessions", "instructor_id", existing_type=sa.INTEGER(), nullable=True
    )
    op.create_index(
        "ix_class_session_date_cohort",
        "class_sessions",
        ["date", "cohort_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_class_sessions_cohort_id"),
        "class_sessions",
        ["cohort_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_class_sessions_date"), "class_sessions", ["date"], unique=False
    )
    op.create_index(
        op.f("ix_class_sessions_instructor_id"),
        "class_sessions",
        ["instructor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_class_sessions_is_deleted"),
        "class_sessions",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        op.f("ix_class_sessions_location_id"),
        "class_sessions",
        ["location_id"],
        unique=False,
    )

    op.drop_constraint(
        "class_sessions_cohort_id_fkey", "class_sessions", type_="foreignkey"
    )
    op.drop_constraint(
        "class_sessions_instructor_id_fkey", "class_sessions", type_="foreignkey"
    )
    op.drop_constraint(
        "class_sessions_location_id_fkey", "class_sessions", type_="foreignkey"
    )
    op.create_foreign_key(
        None,
        "class_sessions",
        "instructors",
        ["instructor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        None,
        "class_sessions",
        "locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        None, "class_sessions", "cohorts", ["cohort_id"], ["id"], ondelete="CASCADE"
    )

    # ============================================================
    # STEP 5: COHORTS
    # ============================================================

    op.add_column("cohorts", sa.Column("code", sa.String(length=50), nullable=True))
    op.add_column(
        "cohorts",
        sa.Column(
            "status",
            sa.Enum(
                "PLANNED",
                "ENROLLING",
                "ACTIVE",
                "COMPLETED",
                "CANCELLED",
                name="cohort_status",
            ),
            nullable=True,
        ),
    )
    op.add_column("cohorts", sa.Column("max_students", sa.Integer(), nullable=True))

    # Set default status for existing rows
    op.execute("UPDATE cohorts SET status = 'ACTIVE' WHERE status IS NULL")
    op.alter_column("cohorts", "status", nullable=False)

    op.alter_column(
        "cohorts",
        "description",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.create_index(
        "ix_cohort_dates", "cohorts", ["start_date", "end_date"], unique=False
    )
    op.create_index(op.f("ix_cohorts_code"), "cohorts", ["code"], unique=True)
    op.create_index(
        op.f("ix_cohorts_is_deleted"), "cohorts", ["is_deleted"], unique=False
    )
    op.create_index(
        op.f("ix_cohorts_location_id"), "cohorts", ["location_id"], unique=False
    )
    op.create_index(
        op.f("ix_cohorts_start_date"), "cohorts", ["start_date"], unique=False
    )
    op.create_index(op.f("ix_cohorts_status"), "cohorts", ["status"], unique=False)

    op.drop_constraint("cohorts_location_id_fkey", "cohorts", type_="foreignkey")
    op.drop_constraint(
        "cohorts_primary_instructor_id_fkey", "cohorts", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "cohorts", "locations", ["location_id"], ["id"], ondelete="SET NULL"
    )
    op.drop_column("cohorts", "primary_instructor_id")

    # ============================================================
    # STEP 6: CREDENTIALS
    # ============================================================

    op.add_column(
        "credentials",
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "ACTIVE",
                "EXPIRED",
                "REVOKED",
                "RENEWED",
                name="credential_status",
            ),
            nullable=True,
        ),
    )
    op.execute("UPDATE credentials SET status = 'ACTIVE' WHERE status IS NULL")
    op.alter_column("credentials", "status", nullable=False)

    op.create_index(
        "ix_credential_expiration", "credentials", ["expiration_date"], unique=False
    )
    op.create_index(
        "ix_credential_student_name",
        "credentials",
        ["student_id", "credential_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_credentials_credential_name"),
        "credentials",
        ["credential_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_credentials_expiration_date"),
        "credentials",
        ["expiration_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_credentials_is_deleted"), "credentials", ["is_deleted"], unique=False
    )
    op.create_index(
        op.f("ix_credentials_status"), "credentials", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_credentials_student_id"), "credentials", ["student_id"], unique=False
    )

    op.drop_constraint("credentials_student_id_fkey", "credentials", type_="foreignkey")
    op.create_foreign_key(
        None, "credentials", "students", ["student_id"], ["id"], ondelete="CASCADE"
    )

    # ============================================================
    # STEP 7: EXPENSES
    # ============================================================

    op.add_column("expenses", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "expenses",
        sa.Column(
            "payment_method",
            sa.Enum(
                "CASH",
                "CHECK",
                "CARD",
                "ACH",
                "WIRE",
                "GRANT",
                "OTHER",
                name="payment_method",
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "expenses", sa.Column("receipt_number", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "expenses", sa.Column("receipt_path", sa.String(length=500), nullable=True)
    )

    op.create_index(
        "ix_expense_date_category",
        "expenses",
        ["purchased_at", "category"],
        unique=False,
    )
    op.create_index(
        "ix_expense_grant", "expenses", ["grant_id", "purchased_at"], unique=False
    )
    op.create_index(
        op.f("ix_expenses_category"), "expenses", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_expenses_grant_id"), "expenses", ["grant_id"], unique=False
    )
    op.create_index(
        op.f("ix_expenses_is_deleted"), "expenses", ["is_deleted"], unique=False
    )
    op.create_index(
        op.f("ix_expenses_location_id"), "expenses", ["location_id"], unique=False
    )
    op.create_index(
        op.f("ix_expenses_purchased_at"), "expenses", ["purchased_at"], unique=False
    )
    op.create_index(
        op.f("ix_expenses_student_id"), "expenses", ["student_id"], unique=False
    )

    op.drop_constraint("expenses_location_id_fkey", "expenses", type_="foreignkey")
    op.drop_constraint("expenses_grant_id_fkey", "expenses", type_="foreignkey")
    op.drop_constraint("expenses_student_id_fkey", "expenses", type_="foreignkey")
    op.create_foreign_key(
        None, "expenses", "grants", ["grant_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        None, "expenses", "students", ["student_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        None, "expenses", "locations", ["location_id"], ["id"], ondelete="SET NULL"
    )

    # ============================================================
    # STEP 8: GRANTS
    # ============================================================

    op.add_column(
        "grants", sa.Column("grant_number", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "grants", sa.Column("reporting_frequency", sa.String(length=50), nullable=True)
    )
    op.add_column("grants", sa.Column("next_report_due", sa.Date(), nullable=True))
    op.alter_column(
        "grants",
        "allowable_categories",
        existing_type=sa.TEXT(),
        type_=sa.JSON(),
        existing_nullable=True,
        postgresql_using="allowable_categories::json",
    )
    op.alter_column(
        "grants",
        "is_active",
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default="true",
    )

    op.create_index("ix_grant_active", "grants", ["is_active"], unique=False)
    op.create_index(
        "ix_grant_dates", "grants", ["start_date", "end_date"], unique=False
    )
    op.create_index(op.f("ix_grants_end_date"), "grants", ["end_date"], unique=False)
    op.create_index(op.f("ix_grants_is_active"), "grants", ["is_active"], unique=False)
    op.create_index(
        op.f("ix_grants_is_deleted"), "grants", ["is_deleted"], unique=False
    )
    op.create_index(op.f("ix_grants_name"), "grants", ["name"], unique=False)
    op.create_index(
        op.f("ix_grants_start_date"), "grants", ["start_date"], unique=False
    )
    op.create_unique_constraint("uq_grants_grant_number", "grants", ["grant_number"])

    # ============================================================
    # STEP 9: INSTRUCTOR_COHORT (Association Object)
    # ============================================================

    op.add_column(
        "instructor_cohort", sa.Column("is_primary", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "instructor_cohort", sa.Column("created_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "instructor_cohort", sa.Column("updated_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "instructor_cohort", sa.Column("is_deleted", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "instructor_cohort", sa.Column("deleted_at", sa.DateTime(), nullable=True)
    )

    # Backfill existing rows
    op.execute(
        "UPDATE instructor_cohort SET is_primary = false, created_at = NOW(), updated_at = NOW(), is_deleted = false WHERE is_primary IS NULL"
    )

    # Now make columns non-nullable
    op.alter_column("instructor_cohort", "is_primary", nullable=False)
    op.alter_column("instructor_cohort", "created_at", nullable=False)
    op.alter_column("instructor_cohort", "updated_at", nullable=False)
    op.alter_column("instructor_cohort", "is_deleted", nullable=False)

    op.create_index(
        "ix_instructor_cohort_cohort", "instructor_cohort", ["cohort_id"], unique=False
    )
    op.create_index(
        "ix_instructor_cohort_instructor",
        "instructor_cohort",
        ["instructor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instructor_cohort_is_deleted"),
        "instructor_cohort",
        ["is_deleted"],
        unique=False,
    )

    # ============================================================
    # STEP 10: INSTRUCTOR_HOURS
    # ============================================================

    op.add_column(
        "instructor_hours",
        sa.Column("rate_override", sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.add_column("instructor_hours", sa.Column("is_paid", sa.Boolean(), nullable=True))
    op.add_column("instructor_hours", sa.Column("paid_date", sa.Date(), nullable=True))

    op.execute("UPDATE instructor_hours SET is_paid = false WHERE is_paid IS NULL")
    op.alter_column("instructor_hours", "is_paid", nullable=False)

    op.create_index(
        op.f("ix_instructor_hours_cohort_id"),
        "instructor_hours",
        ["cohort_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instructor_hours_date"), "instructor_hours", ["date"], unique=False
    )
    op.create_index(
        "ix_instructor_hours_date_range",
        "instructor_hours",
        ["instructor_id", "date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instructor_hours_instructor_id"),
        "instructor_hours",
        ["instructor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instructor_hours_is_deleted"),
        "instructor_hours",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instructor_hours_is_paid"),
        "instructor_hours",
        ["is_paid"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instructor_hours_location_id"),
        "instructor_hours",
        ["location_id"],
        unique=False,
    )
    op.create_index(
        "ix_instructor_hours_unpaid",
        "instructor_hours",
        ["is_paid", "instructor_id"],
        unique=False,
    )

    op.drop_constraint(
        "instructor_hours_location_id_fkey", "instructor_hours", type_="foreignkey"
    )
    op.drop_constraint(
        "instructor_hours_cohort_id_fkey", "instructor_hours", type_="foreignkey"
    )
    op.drop_constraint(
        "instructor_hours_instructor_id_fkey", "instructor_hours", type_="foreignkey"
    )
    op.create_foreign_key(
        None,
        "instructor_hours",
        "instructors",
        ["instructor_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        None, "instructor_hours", "cohorts", ["cohort_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        None,
        "instructor_hours",
        "locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ============================================================
    # STEP 11: INSTRUCTORS
    # ============================================================

    op.add_column("instructors", sa.Column("specialties", sa.Text(), nullable=True))
    op.add_column(
        "instructors",
        sa.Column(
            "rate_type",
            sa.Enum("HOURLY", "DAILY", "FLAT", "SALARY", name="rate_type"),
            nullable=True,
        ),
    )
    op.add_column(
        "instructors",
        sa.Column("rate_amount", sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.add_column(
        "instructors", sa.Column("is_contractor_1099", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "instructors", sa.Column("tax_id", sa.String(length=20), nullable=True)
    )
    op.add_column("instructors", sa.Column("is_active", sa.Boolean(), nullable=True))

    # Backfill existing rows
    op.execute(
        "UPDATE instructors SET rate_type = 'HOURLY', is_contractor_1099 = false, is_active = true WHERE rate_type IS NULL"
    )

    op.alter_column("instructors", "rate_type", nullable=False)
    op.alter_column("instructors", "is_contractor_1099", nullable=False)
    op.alter_column("instructors", "is_active", nullable=False)

    op.create_index("ix_instructor_active", "instructors", ["is_active"], unique=False)
    op.create_index(
        "ix_instructor_name", "instructors", ["last_name", "first_name"], unique=False
    )
    op.create_index(op.f("ix_instructors_email"), "instructors", ["email"], unique=True)
    op.create_index(
        op.f("ix_instructors_is_active"), "instructors", ["is_active"], unique=False
    )
    op.create_index(
        op.f("ix_instructors_is_deleted"), "instructors", ["is_deleted"], unique=False
    )

    # ============================================================
    # STEP 12: JATC_APPLICATIONS
    # ============================================================

    op.add_column(
        "jatc_applications", sa.Column("decision_date", sa.Date(), nullable=True)
    )
    op.add_column(
        "jatc_applications",
        sa.Column("interview_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "jatc_applications",
        sa.Column("aptitude_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "jatc_applications",
        sa.Column("math_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "jatc_applications",
        sa.Column("reading_score", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "jatc_applications",
        sa.Column("trade_preference", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "jatc_applications",
        sa.Column("local_applied", sa.String(length=50), nullable=True),
    )

    op.create_index(
        op.f("ix_jatc_applications_application_date"),
        "jatc_applications",
        ["application_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jatc_applications_interview_date"),
        "jatc_applications",
        ["interview_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jatc_applications_is_deleted"),
        "jatc_applications",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jatc_applications_status"),
        "jatc_applications",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jatc_applications_student_id"),
        "jatc_applications",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_jatc_dates",
        "jatc_applications",
        ["application_date", "interview_date"],
        unique=False,
    )
    op.create_index(
        "ix_jatc_student_status",
        "jatc_applications",
        ["student_id", "status"],
        unique=False,
    )

    op.drop_constraint(
        "jatc_applications_student_id_fkey", "jatc_applications", type_="foreignkey"
    )
    op.create_foreign_key(
        None,
        "jatc_applications",
        "students",
        ["student_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ============================================================
    # STEP 13: LOCATIONS
    # ============================================================

    op.add_column("locations", sa.Column("code", sa.String(length=50), nullable=True))
    op.add_column(
        "locations",
        sa.Column(
            "type",
            sa.Enum(
                "TRAINING_SITE",
                "SCHOOL",
                "OFFICE",
                "JOBSITE",
                "VENDOR",
                "OTHER",
                name="location_type",
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "locations", sa.Column("address_line1", sa.String(length=200), nullable=True)
    )
    op.add_column(
        "locations", sa.Column("address_line2", sa.String(length=200), nullable=True)
    )
    op.add_column(
        "locations", sa.Column("postal_code", sa.String(length=20), nullable=True)
    )
    op.add_column("locations", sa.Column("square_footage", sa.Integer(), nullable=True))
    op.add_column(
        "locations", sa.Column("contact_name", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "locations", sa.Column("contact_phone", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "locations", sa.Column("contact_email", sa.String(length=255), nullable=True)
    )
    op.add_column("locations", sa.Column("notes", sa.Text(), nullable=True))

    op.execute("UPDATE locations SET type = 'TRAINING_SITE' WHERE type IS NULL")
    op.alter_column("locations", "type", nullable=False)

    op.alter_column(
        "locations",
        "name",
        existing_type=sa.VARCHAR(length=100),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
    op.alter_column(
        "locations", "address", existing_type=sa.VARCHAR(length=255), nullable=True
    )

    op.create_index(
        "ix_location_city_state", "locations", ["city", "state"], unique=False
    )
    op.create_index(op.f("ix_locations_city"), "locations", ["city"], unique=False)
    op.create_index(
        op.f("ix_locations_is_deleted"), "locations", ["is_deleted"], unique=False
    )
    op.create_index(op.f("ix_locations_name"), "locations", ["name"], unique=False)
    op.create_index(op.f("ix_locations_state"), "locations", ["state"], unique=False)
    op.create_index(op.f("ix_locations_type"), "locations", ["type"], unique=False)
    op.create_unique_constraint("uq_locations_code", "locations", ["code"])

    # ============================================================
    # STEP 14: STUDENTS
    # ============================================================

    op.add_column(
        "students", sa.Column("middle_name", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "students", sa.Column("address_line1", sa.String(length=200), nullable=True)
    )
    op.add_column(
        "students", sa.Column("address_line2", sa.String(length=200), nullable=True)
    )
    op.add_column("students", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("students", sa.Column("state", sa.String(length=50), nullable=True))
    op.add_column(
        "students", sa.Column("postal_code", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "students", sa.Column("shoe_size", sa.String(length=16), nullable=True)
    )
    op.add_column(
        "students", sa.Column("shirt_size", sa.String(length=16), nullable=True)
    )
    op.add_column(
        "students",
        sa.Column("emergency_contact_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("emergency_contact_phone", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("emergency_contact_relation", sa.String(length=50), nullable=True),
    )
    op.add_column("students", sa.Column("extra", sa.JSON(), nullable=True))

    op.create_index(
        "ix_student_city_state", "students", ["city", "state"], unique=False
    )
    op.create_index(
        "ix_student_name", "students", ["last_name", "first_name"], unique=False
    )
    op.create_index(
        op.f("ix_students_cohort_id"), "students", ["cohort_id"], unique=False
    )
    op.create_index(op.f("ix_students_email"), "students", ["email"], unique=True)
    op.create_index(
        op.f("ix_students_is_deleted"), "students", ["is_deleted"], unique=False
    )

    op.drop_constraint("students_cohort_id_fkey", "students", type_="foreignkey")
    op.create_foreign_key(
        None, "students", "cohorts", ["cohort_id"], ["id"], ondelete="SET NULL"
    )

    # ============================================================
    # STEP 15: TOOLS_ISSUED
    # ============================================================

    op.add_column(
        "tools_issued", sa.Column("tool_category", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "tools_issued", sa.Column("serial_number", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "tools_issued", sa.Column("issued_by", sa.String(length=100), nullable=True)
    )
    op.add_column("tools_issued", sa.Column("date_returned", sa.Date(), nullable=True))
    op.add_column("tools_issued", sa.Column("is_returned", sa.Boolean(), nullable=True))
    op.add_column(
        "tools_issued",
        sa.Column("return_condition", sa.String(length=50), nullable=True),
    )
    op.add_column("tools_issued", sa.Column("unit_value", sa.Integer(), nullable=True))

    op.execute("UPDATE tools_issued SET is_returned = false WHERE is_returned IS NULL")
    op.alter_column("tools_issued", "is_returned", nullable=False)

    op.create_index(
        op.f("ix_tools_issued_date_issued"),
        "tools_issued",
        ["date_issued"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tools_issued_is_deleted"), "tools_issued", ["is_deleted"], unique=False
    )
    op.create_index(
        op.f("ix_tools_issued_is_returned"),
        "tools_issued",
        ["is_returned"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tools_issued_student_id"), "tools_issued", ["student_id"], unique=False
    )
    op.create_index(
        op.f("ix_tools_issued_tool_name"), "tools_issued", ["tool_name"], unique=False
    )
    op.create_index(
        "ix_tools_outstanding",
        "tools_issued",
        ["is_returned", "student_id"],
        unique=False,
    )
    op.create_index(
        "ix_tools_student_date",
        "tools_issued",
        ["student_id", "date_issued"],
        unique=False,
    )

    op.drop_constraint(
        "tools_issued_student_id_fkey", "tools_issued", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "tools_issued", "students", ["student_id"], ["id"], ondelete="CASCADE"
    )

    # ============================================================
    # STEP 16: USERS
    # ============================================================

    op.add_column(
        "users", sa.Column("password_hash", sa.String(length=255), nullable=True)
    )
    op.add_column("users", sa.Column("role", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.add_column(
        "users", sa.Column("failed_login_attempts", sa.Integer(), nullable=True)
    )
    op.add_column("users", sa.Column("locked_until", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("student_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("instructor_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("is_deleted", sa.Boolean(), nullable=True))
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(), nullable=True))

    # Backfill existing rows
    op.execute("""
        UPDATE users SET
            role = 'admin',
            is_active = true,
            is_verified = false,
            failed_login_attempts = 0,
            created_at = NOW(),
            updated_at = NOW(),
            is_deleted = false
        WHERE role IS NULL
    """)

    op.alter_column("users", "role", nullable=False)
    op.alter_column("users", "is_active", nullable=False)
    op.alter_column("users", "is_verified", nullable=False)
    op.alter_column("users", "failed_login_attempts", nullable=False)
    op.alter_column("users", "created_at", nullable=False)
    op.alter_column("users", "updated_at", nullable=False)
    op.alter_column("users", "is_deleted", nullable=False)

    op.create_index("ix_user_role_active", "users", ["role", "is_active"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(
        op.f("ix_users_instructor_id"), "users", ["instructor_id"], unique=False
    )
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)
    op.create_index(op.f("ix_users_is_deleted"), "users", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
    op.create_index(op.f("ix_users_student_id"), "users", ["student_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema - simplified, drops new stuff."""
    # Drop new indexes and columns in reverse order
    # This is a simplified downgrade - in production you'd want full reversal

    # Drop enum types at the end
    op.execute("DROP TYPE IF EXISTS attendance_status CASCADE")
    op.execute("DROP TYPE IF EXISTS cohort_status CASCADE")
    op.execute("DROP TYPE IF EXISTS credential_status CASCADE")
    op.execute("DROP TYPE IF EXISTS payment_method CASCADE")
    op.execute("DROP TYPE IF EXISTS rate_type CASCADE")
    op.execute("DROP TYPE IF EXISTS location_type CASCADE")

    op.drop_table("file_attachments")
