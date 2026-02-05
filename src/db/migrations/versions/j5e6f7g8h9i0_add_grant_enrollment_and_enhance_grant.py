"""Add grant enrollment table and enhance grant model with targets

Revision ID: j5e6f7g8h9i0
Revises: i4d5e6f7g8h9
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j5e6f7g8h9i0'
down_revision = 'i4d5e6f7g8h9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Drop existing enum types if they exist (from failed migration attempts)
    # This ensures we start clean
    conn.execute(sa.text("DROP TYPE IF EXISTS grant_status CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS grant_enrollment_status CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS grant_outcome CASCADE"))

    # Create enums fresh
    grant_status_enum = sa.Enum(
        'pending', 'active', 'completed', 'closed', 'suspended',
        name='grant_status'
    )
    grant_status_enum.create(op.get_bind())

    grant_enrollment_status_enum = sa.Enum(
        'enrolled', 'active', 'completed', 'withdrawn', 'dropped',
        name='grant_enrollment_status'
    )
    grant_enrollment_status_enum.create(op.get_bind())

    grant_outcome_enum = sa.Enum(
        'completed_program', 'obtained_credential', 'entered_apprenticeship',
        'obtained_employment', 'continued_education', 'withdrawn', 'other',
        name='grant_outcome'
    )
    grant_outcome_enum.create(op.get_bind())

    # Add new columns to grants table
    op.add_column('grants', sa.Column(
        'status',
        sa.Enum('pending', 'active', 'completed', 'closed', 'suspended', name='grant_status', create_type=False),
        nullable=True,
        server_default='pending'
    ))
    op.add_column('grants', sa.Column('target_enrollment', sa.Integer(), nullable=True))
    op.add_column('grants', sa.Column('target_completion', sa.Integer(), nullable=True))
    op.add_column('grants', sa.Column('target_placement', sa.Integer(), nullable=True))

    # Create index on status
    op.create_index('ix_grants_status', 'grants', ['status'], unique=False)

    # Update existing rows to have default status
    op.execute("UPDATE grants SET status = 'active' WHERE is_active = true")
    op.execute("UPDATE grants SET status = 'closed' WHERE is_active = false")

    # Make status non-nullable after setting defaults
    op.alter_column('grants', 'status', nullable=False)

    # Create grant_enrollments table using raw SQL to avoid enum creation issues
    conn.execute(sa.text("""
        CREATE TABLE grant_enrollments (
            id SERIAL PRIMARY KEY,
            grant_id INTEGER NOT NULL REFERENCES grants(id) ON DELETE CASCADE,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            enrollment_date DATE NOT NULL,
            status grant_enrollment_status NOT NULL DEFAULT 'enrolled',
            completion_date DATE,
            outcome grant_outcome,
            outcome_date DATE,
            placement_employer VARCHAR(200),
            placement_date DATE,
            placement_wage VARCHAR(50),
            placement_job_title VARCHAR(200),
            notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN NOT NULL DEFAULT false,
            deleted_at TIMESTAMP,
            CONSTRAINT uq_grant_student UNIQUE (grant_id, student_id)
        )
    """))

    # Create indexes
    op.create_index('ix_grant_enrollments_grant_id', 'grant_enrollments', ['grant_id'], unique=False)
    op.create_index('ix_grant_enrollments_student_id', 'grant_enrollments', ['student_id'], unique=False)
    op.create_index('ix_grant_enrollments_enrollment_date', 'grant_enrollments', ['enrollment_date'], unique=False)
    op.create_index('ix_grant_enrollment_status', 'grant_enrollments', ['grant_id', 'status'], unique=False)
    op.create_index('ix_grant_enrollment_outcome', 'grant_enrollments', ['grant_id', 'outcome'], unique=False)


def downgrade() -> None:
    # Drop grant_enrollments table
    op.drop_index('ix_grant_enrollment_outcome', table_name='grant_enrollments')
    op.drop_index('ix_grant_enrollment_status', table_name='grant_enrollments')
    op.drop_index('ix_grant_enrollments_enrollment_date', table_name='grant_enrollments')
    op.drop_index('ix_grant_enrollments_student_id', table_name='grant_enrollments')
    op.drop_index('ix_grant_enrollments_grant_id', table_name='grant_enrollments')
    op.drop_table('grant_enrollments')

    # Remove columns from grants
    op.drop_index('ix_grants_status', table_name='grants')
    op.drop_column('grants', 'target_placement')
    op.drop_column('grants', 'target_completion')
    op.drop_column('grants', 'target_enrollment')
    op.drop_column('grants', 'status')

    # Drop enums
    sa.Enum(name='grant_outcome').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='grant_enrollment_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='grant_status').drop(op.get_bind(), checkfirst=True)
