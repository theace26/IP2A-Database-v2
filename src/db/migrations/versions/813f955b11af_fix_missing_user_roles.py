"""fix_missing_user_roles

Revision ID: 813f955b11af
Revises: 9adc3bee4ecd
Create Date: 2026-01-30 09:41:20.392746

This migration fixes a bug where users created during setup
were not assigned roles if the Role table lookup failed silently.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '813f955b11af'
down_revision: Union[str, Sequence[str], None] = '9adc3bee4ecd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix users who were created during setup but have no roles assigned.

    This can happen if:
    1. The roles table wasn't seeded properly
    2. The role lookup in setup_service returned None silently

    Solution: Assign admin role to any user (except default admin) who has no roles.
    """
    # Get connection for raw SQL
    conn = op.get_bind()

    # First, ensure the admin role exists
    result = conn.execute(
        sa.text("SELECT id FROM roles WHERE name = 'admin'")
    )
    admin_role = result.fetchone()

    if not admin_role:
        # Create the admin role if it doesn't exist
        # Include display_name and is_system_role as they are NOT NULL in production
        conn.execute(
            sa.text("""
                INSERT INTO roles (name, display_name, description, is_system_role, created_at, updated_at)
                VALUES ('admin', 'Administrator', 'Full system access', true, NOW(), NOW())
            """)
        )
        result = conn.execute(
            sa.text("SELECT id FROM roles WHERE name = 'admin'")
        )
        admin_role = result.fetchone()

    admin_role_id = admin_role[0]

    # Find users who have no roles (excluding default admin which should already have roles)
    result = conn.execute(
        sa.text("""
            SELECT u.id, u.email
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            WHERE ur.id IS NULL
            AND u.email != 'admin@ibew46.com'
            AND u.deleted_at IS NULL
        """)
    )
    users_without_roles = result.fetchall()

    # Assign admin role to each user without roles
    for user in users_without_roles:
        user_id = user[0]
        user_email = user[1]
        print(f"Assigning admin role to user: {user_email} (id={user_id})")

        conn.execute(
            sa.text("""
                INSERT INTO user_roles (user_id, role_id, assigned_by, created_at)
                VALUES (:user_id, :role_id, 'migration_fix', NOW())
            """),
            {"user_id": user_id, "role_id": admin_role_id}
        )

    if users_without_roles:
        print(f"Fixed {len(users_without_roles)} user(s) with missing roles")
    else:
        print("No users found with missing roles")


def downgrade() -> None:
    """
    Remove roles that were added by this migration.
    Note: This is generally safe since we're only removing roles we added.
    """
    conn = op.get_bind()

    # Remove user_roles that were assigned by this migration
    conn.execute(
        sa.text("""
            DELETE FROM user_roles
            WHERE assigned_by = 'migration_fix'
        """)
    )
