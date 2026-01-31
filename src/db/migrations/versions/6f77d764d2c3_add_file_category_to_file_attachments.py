"""Add file_category to file_attachments

Revision ID: 6f77d764d2c3
Revises: bc1f99c730dc
Create Date: 2026-01-28 00:56:18.375974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f77d764d2c3'
down_revision: Union[str, Sequence[str], None] = 'bc1f99c730dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('file_attachments', sa.Column('file_category', sa.String(length=50), server_default='general', nullable=False))
    op.create_index(op.f('ix_file_attachments_file_category'), 'file_attachments', ['file_category'], unique=False)
    # NOTE: Existing production indexes (idx_member_employments_*, idx_members_*, idx_contacts_*, idx_organization_contacts_*)
    # are intentionally preserved - they were created in migration 0b9b93948cdb and should NOT be dropped.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_file_attachments_file_category'), table_name='file_attachments')
    op.drop_column('file_attachments', 'file_category')
