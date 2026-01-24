"""add profile_photo_path to students

Revision ID: ea296d2988d7
Revises: a3a3b68c72fc
Create Date: 2026-01-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ea296d2988d7"
down_revision: Union[str, Sequence[str], None] = "a3a3b68c72fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column("profile_photo_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("students", "profile_photo_path")
