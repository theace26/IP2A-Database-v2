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
    # Create grant_status enum
    grant_status_enum = sa.Enum(
        'pending', 'active', 'completed', 'closed', 'suspended',
        name='grant_status'
    )
    grant_status_enum.create(op.get_bind(), checkfirst=True)

    # Create grant_enrollment_status enum
    grant_enrollment_status_enum = sa.Enum(
        'enrolled', 'active', 'completed', 'withdrawn', 'dropped',
        name='grant_enrollment_status'
    )
    grant_enrollment_status_enum.create(op.get_bind(), checkfirst=True)

    # Create grant_outcome enum
    grant_outcome_enum = sa.Enum(
        'completed_program', 'obtained_credential', 'entered_apprenticeship',
        'obtained_employment', 'continued_education', 'withdrawn', 'other',
        name='grant_outcome'
    )
    grant_outcome_enum.create(op.get_bind(), checkfirst=True)

    # Add new columns to grants table
    op.add_column('grants', sa.Column(
        'status',
        sa.Enum('pending', 'active', 'completed', 'closed', 'suspended', name='grant_status'),
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

    # Create grant_enrollments table
    op.create_table(
        'grant_enrollments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('grant_id', sa.Integer(), sa.ForeignKey('grants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enrollment_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('enrolled', 'active', 'completed', 'withdrawn', 'dropped', name='grant_enrollment_status'), nullable=False, server_default='enrolled'),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('outcome', sa.Enum('completed_program', 'obtained_credential', 'entered_apprenticeship', 'obtained_employment', 'continued_education', 'withdrawn', 'other', name='grant_outcome'), nullable=True),
        sa.Column('outcome_date', sa.Date(), nullable=True),
        sa.Column('placement_employer', sa.String(200), nullable=True),
        sa.Column('placement_date', sa.Date(), nullable=True),
        sa.Column('placement_wage', sa.String(50), nullable=True),
        sa.Column('placement_job_title', sa.String(200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('grant_id', 'student_id', name='uq_grant_student'),
    )

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
