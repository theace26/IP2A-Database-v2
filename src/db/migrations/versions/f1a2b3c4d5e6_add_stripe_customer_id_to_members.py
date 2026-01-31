"""add stripe_customer_id to members

Revision ID: f1a2b3c4d5e6
Revises: 0b9b93948cdb
Create Date: 2026-01-30 20:00:00.000000

Adds stripe_customer_id column to members table for payment processing integration.
This field stores the Stripe Customer ID created when a member makes their first payment.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "0b9b93948cdb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add stripe_customer_id column to members table."""
    # Add stripe_customer_id column
    op.add_column(
        'members',
        sa.Column('stripe_customer_id', sa.String(100), nullable=True)
    )

    # Create unique index for faster lookups and constraint enforcement
    op.create_index(
        'ix_members_stripe_customer_id',
        'members',
        ['stripe_customer_id'],
        unique=True
    )


def downgrade() -> None:
    """Remove stripe_customer_id column from members table."""
    op.drop_index('ix_members_stripe_customer_id', table_name='members')
    op.drop_column('members', 'stripe_customer_id')
