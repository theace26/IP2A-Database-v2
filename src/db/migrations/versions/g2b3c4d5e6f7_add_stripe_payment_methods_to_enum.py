"""add stripe payment methods to enum

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-01-30 20:05:00.000000

Adds Stripe-specific payment method values to the DuesPaymentMethod enum.
This allows tracking which payments came through Stripe vs other methods.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "g2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new Stripe payment method enum values."""
    # Check if the enum exists first (it might not exist if upgrading from a branch
    # that didn't include the dues tracking migration)
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""SELECT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'duespaymentmethod'
        )""")
    )
    enum_exists = result.scalar()

    if not enum_exists:
        # Create the enum if it doesn't exist (cross-branch migration scenario)
        op.execute("""
            CREATE TYPE duespaymentmethod AS ENUM (
                'PAYROLL_DEDUCTION', 'CHECK', 'CASH', 'MONEY_ORDER',
                'CREDIT_CARD', 'ACH_TRANSFER', 'ONLINE', 'OTHER',
                'stripe_card', 'stripe_ach', 'stripe_other'
            )
        """)
    else:
        # Add new enum values to existing enum
        # Note: PostgreSQL requires ADD VALUE commands to be run outside transactions
        # Alembic handles this automatically for ALTER TYPE commands
        op.execute("ALTER TYPE duespaymentmethod ADD VALUE IF NOT EXISTS 'stripe_card'")
        op.execute("ALTER TYPE duespaymentmethod ADD VALUE IF NOT EXISTS 'stripe_ach'")
        op.execute("ALTER TYPE duespaymentmethod ADD VALUE IF NOT EXISTS 'stripe_other'")


def downgrade() -> None:
    """Remove Stripe payment method enum values.

    Note: PostgreSQL doesn't support removing enum values directly.
    This would require recreating the enum type, which is complex and risky.
    Instead, we leave the values in place (they're additive only).

    If you absolutely need to remove these values in production, you must:
    1. Create a new enum type with desired values
    2. Alter columns to use the new type
    3. Drop the old enum type
    4. Rename the new type to the old name

    This is intentionally left empty as enum changes are typically additive.
    """
    pass
