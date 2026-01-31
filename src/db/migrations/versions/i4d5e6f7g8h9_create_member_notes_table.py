"""create_member_notes_table

Revision ID: i4d5e6f7g8h9
Revises: h3c4d5e6f7g8
Create Date: 2026-01-30 21:15:00.000000

Creates member_notes table for staff documentation about members.
All changes to this table are automatically audited.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "i4d5e6f7g8h9"
down_revision: Union[str, Sequence[str], None] = "h3c4d5e6f7g8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create member_notes table."""
    op.create_table(
        'member_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.Column('visibility', sa.String(length=50), nullable=False, server_default='staff_only'),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
    )

    # Create indexes
    op.create_index('ix_member_notes_id', 'member_notes', ['id'])
    op.create_index('ix_member_notes_member_id', 'member_notes', ['member_id'])
    op.create_index('ix_member_notes_created_by_id', 'member_notes', ['created_by_id'])

    # Add column comments
    op.execute("""
        COMMENT ON COLUMN member_notes.visibility IS
        'Who can view this note: staff_only, officers, all_authorized'
    """)

    op.execute("""
        COMMENT ON COLUMN member_notes.category IS
        'Optional category: contact, dues, grievance, general, etc.'
    """)


def downgrade() -> None:
    """Drop member_notes table."""
    op.drop_index('ix_member_notes_created_by_id', table_name='member_notes')
    op.drop_index('ix_member_notes_member_id', table_name='member_notes')
    op.drop_index('ix_member_notes_id', table_name='member_notes')
    op.drop_table('member_notes')
