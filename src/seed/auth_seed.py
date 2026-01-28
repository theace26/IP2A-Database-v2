"""Seed data for authentication system."""

from sqlalchemy.orm import Session

from src.models.role import Role
from src.db.enums import RoleType


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


def run_auth_seed(db: Session) -> dict:
    """Run all auth seed operations."""
    print("\n=== Seeding Auth Data ===")

    roles = seed_roles(db)

    return {
        "roles_created": len(roles),
    }
