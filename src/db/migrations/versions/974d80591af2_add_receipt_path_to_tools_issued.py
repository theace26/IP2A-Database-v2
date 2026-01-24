"""add receipt_path to tools_issued

Revision ID: 974d80591af2
Revises: 03add9889552
Create Date: 2026-01-18 00:11:59.362230

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "974d80591af2"
down_revision: Union[str, Sequence[str], None] = "03add9889552"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tools_issued",
        sa.Column("receipt_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tools_issued", "receipt_path")
