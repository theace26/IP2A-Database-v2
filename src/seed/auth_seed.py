"""Seed data for authentication system."""

from sqlalchemy.orm import Session

from src.models.role import Role
from src.models.user import User
from src.models.user_role import UserRole
from src.db.enums import RoleType
from src.core.security import hash_password


# Default admin user - created on every deploy if not exists
DEFAULT_ADMIN = {
    "email": "xerxes@ibew46.com",
    "password": "W33k3nd!",
    "first_name": "Xerxes",
    "last_name": "Admin",
}


DEFAULT_ROLES = [
    {
        "name": RoleType.ADMIN.value,
        "display_name": "Administrator",
        "description": "Full system access. Can manage all users, roles, and system settings.",
        "is_system_role": True,
    },
    {
        "name": RoleType.OFFICER.value,
        "display_name": "Union Officer",
        "description": "Union officer privileges. Can approve benevolence, manage grievances, view reports.",
        "is_system_role": True,
    },
    {
        "name": RoleType.STAFF.value,
        "display_name": "Staff",
        "description": "Staff-level access. Can manage members, employment records, and basic operations.",
        "is_system_role": True,
    },
    {
        "name": RoleType.ORGANIZER.value,
        "display_name": "Organizer",
        "description": "Organizing access. Can manage SALTing activities and organizing campaigns.",
        "is_system_role": True,
    },
    {
        "name": RoleType.INSTRUCTOR.value,
        "display_name": "Instructor",
        "description": "Training program access. Can manage students, classes, and training records.",
        "is_system_role": True,
    },
    {
        "name": RoleType.MEMBER.value,
        "display_name": "Member",
        "description": "Basic member access. Can view own records and submit requests.",
        "is_system_role": True,
    },
]


def seed_roles(db: Session) -> list[Role]:
    """Seed default system roles."""
    created_roles = []

    for role_data in DEFAULT_ROLES:
        # Check if role already exists
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if existing:
            print(f"  Role '{role_data['name']}' already exists, skipping...")
            continue

        role = Role(**role_data)
        db.add(role)
        created_roles.append(role)
        print(f"  Created role: {role_data['display_name']}")

    if created_roles:
        db.commit()

    return created_roles


def seed_admin_user(db: Session) -> User | None:
    """Seed default admin user if not exists."""
    # Check if admin user already exists
    existing = db.query(User).filter(User.email == DEFAULT_ADMIN["email"]).first()
    if existing:
        print(f"  Admin user '{DEFAULT_ADMIN['email']}' already exists, skipping...")
        return None

    # Get admin role
    admin_role = db.query(Role).filter(Role.name == RoleType.ADMIN.value).first()
    if not admin_role:
        print("  Warning: Admin role not found, creating user without role...")

    # Create admin user
    user = User(
        email=DEFAULT_ADMIN["email"],
        password_hash=hash_password(DEFAULT_ADMIN["password"]),
        first_name=DEFAULT_ADMIN["first_name"],
        last_name=DEFAULT_ADMIN["last_name"],
        is_active=True,
        is_verified=True,  # Pre-verified for admin
        must_change_password=True,  # Force password change on first login
    )
    db.add(user)
    db.flush()  # Get the user ID

    # Assign admin role
    if admin_role:
        user_role = UserRole(user_id=user.id, role_id=admin_role.id)
        db.add(user_role)

    db.commit()
    print(f"  Created admin user: {DEFAULT_ADMIN['email']}")
    return user


def run_auth_seed(db: Session) -> dict:
    """Run all auth seed operations."""
    print("\n=== Seeding Auth Data ===")

    roles = seed_roles(db)
    admin = seed_admin_user(db)

    return {
        "roles_created": len(roles),
        "admin_created": admin is not None,
    }
