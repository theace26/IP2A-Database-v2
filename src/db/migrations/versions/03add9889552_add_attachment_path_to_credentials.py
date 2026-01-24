"""add attachment_path to credentials

Revision ID: 03add9889552
Revises: dd55a5a4513a
Create Date: 2026-01-18 00:10:47.693166

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "03add9889552"
down_revision: Union[str, Sequence[str], None] = "dd55a5a4513a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "credentials",
        sa.Column("attachment_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("credentials", "attachment_path")
