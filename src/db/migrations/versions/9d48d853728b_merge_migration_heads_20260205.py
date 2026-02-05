"""merge_migration_heads_20260205

Revision ID: 9d48d853728b
Revises: 813f955b11af, j5e6f7g8h9i0
Create Date: 2026-02-05 02:30:00.725288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d48d853728b'
down_revision: Union[str, Sequence[str], None] = ('813f955b11af', 'j5e6f7g8h9i0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
