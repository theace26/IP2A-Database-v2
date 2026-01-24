"""add city and state to locations

Revision ID: a3a3b68c72fc
Revises: c8997d54c438
Create Date: 2026-01-17 22:04:48.045760
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3a3b68c72fc"
down_revision: Union[str, Sequence[str], None] = "c8997d54c438"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add city and state columns to locations."""
    op.add_column(
        "locations",
        sa.Column("city", sa.String(), nullable=True),
    )
    op.add_column(
        "locations",
        sa.Column("state", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Remove city and state columns from locations."""
    op.drop_column("locations", "state")
    op.drop_column("locations", "city")
