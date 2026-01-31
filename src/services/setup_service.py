"""Initial system setup service for first-time configuration."""

import re
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.role import Role
from src.models.user_role import UserRole
from src.core.security import hash_password
from src.db.enums import RoleType


# Default admin account (seeded) - cannot be modified or deleted via setup
DEFAULT_ADMIN_EMAIL = "admin@ibew46.com"


class PasswordValidationError(Exception):
    """Raised when password doesn't meet requirements."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def has_any_users(db: Session) -> bool:
    """Check if any users exist in the database."""
    count = db.execute(select(func.count(User.id))).scalar()
    return count > 0


def validate_password(password: str) -> list[str]:
    """
    Validate password against requirements.

    Requirements:
    - Minimum 8 characters
    - At least 3 unique numbers
    - At least one special character
    - At least one capital letter
    - No repeating letters (lower or upper case)
    - No sequential numbers (123, 234, etc.)

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Minimum length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")

    # At least 3 unique numbers
    numbers = re.findall(r'\d', password)
    unique_numbers = set(numbers)
    if len(unique_numbers) < 3:
        errors.append("Password must contain at least 3 different numbers")

    # At least one special character
    special_chars = re.findall(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\`~]', password)
    if not special_chars:
        errors.append("Password must contain at least one special character")

    # At least one capital letter
    capitals = re.findall(r'[A-Z]', password)
    if not capitals:
        errors.append("Password must contain at least one capital letter")

    # No repeating letters (case-insensitive)
    letters = re.findall(r'[a-zA-Z]', password)
    letters_lower = [l.lower() for l in letters]
    if len(letters_lower) != len(set(letters_lower)):
        errors.append("Password cannot contain repeating letters")

    # No sequential numbers (123, 234, 345, etc.)
    for i in range(len(password) - 2):
        try:
            n1 = int(password[i])
            n2 = int(password[i + 1])
            n3 = int(password[i + 2])
            if n2 == n1 + 1 and n3 == n2 + 1:
                errors.append("Password cannot contain sequential numbers (like 123, 456)")
                break
        except ValueError:
            continue

    return errors


def create_setup_user(
    db: Session,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "admin",
    disable_default_admin_account: bool = False,
) -> User:
    """
    Create the initial user during system setup.

    This creates a new user account for the person setting up the system.
    The default admin account (admin@ibew46.com) remains but can be disabled.

    Args:
        db: Database session
        email: User email (cannot be admin@ibew46.com)
        password: User password (must pass validation)
        first_name: User first name
        last_name: User last name
        role: Role to assign (default: admin)
        disable_default_admin_account: If True, disable the default admin

    Returns:
        Created User object

    Raises:
        PasswordValidationError: If password doesn't meet requirements
        ValueError: If setup is already complete or email is reserved
    """
    # Check if setup is already complete (non-default users exist)
    if has_non_default_users(db):
        raise ValueError("System is already set up with existing users")

    # Prevent using the default admin email
    if email.lower().strip() == DEFAULT_ADMIN_EMAIL:
        raise ValueError(
            f"Cannot use {DEFAULT_ADMIN_EMAIL} - please choose a different email address"
        )

    # Validate password
    password_errors = validate_password(password)
    if password_errors:
        raise PasswordValidationError(password_errors)

    # Create user
    user = User(
        email=email.lower().strip(),
        password_hash=hash_password(password),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        is_active=True,
        is_verified=True,  # Initial user is pre-verified
        must_change_password=False,
    )
    db.add(user)
    db.flush()

    # Get the role - this should always exist from seeding
    db_role = db.execute(
        select(Role).where(Role.name == role.lower())
    ).scalar_one_or_none()

    if not db_role:
        # Role not found - this is a critical error, roles should be seeded
        db.rollback()
        raise ValueError(
            f"Role '{role}' not found in database. Please ensure roles are seeded. "
            "Run: python -m src.seed.run_seed"
        )

    user_role = UserRole(
        user_id=user.id,
        role_id=db_role.id,
        assigned_by="system_setup",
    )
    db.add(user_role)

    # Optionally disable the default admin account
    if disable_default_admin_account:
        default_admin = get_default_admin(db)
        if default_admin:
            default_admin.is_active = False

    db.commit()
    db.refresh(user)

    return user


# Keep for backward compatibility
def create_initial_admin(
    db: Session,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "admin",
) -> User:
    """
    Create the initial admin user during system setup.

    DEPRECATED: Use create_setup_user instead.

    Args:
        db: Database session
        email: Admin email
        password: Admin password (must pass validation)
        first_name: Admin first name
        last_name: Admin last name
        role: Role to assign (default: admin)

    Returns:
        Created User object

    Raises:
        PasswordValidationError: If password doesn't meet requirements
        ValueError: If users already exist
    """
    return create_setup_user(
        db=db,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
        disable_default_admin_account=False,
    )


def get_available_roles() -> list[dict]:
    """Get list of available roles for setup form."""
    return [
        {"value": RoleType.ADMIN.value, "label": "Administrator", "description": "Full system access"},
        {"value": RoleType.OFFICER.value, "label": "Officer", "description": "Union officer with elevated access"},
        {"value": RoleType.STAFF.value, "label": "Staff", "description": "General staff member"},
        {"value": RoleType.ORGANIZER.value, "label": "Organizer", "description": "Union organizer"},
        {"value": RoleType.INSTRUCTOR.value, "label": "Instructor", "description": "Training instructor"},
    ]


def get_default_admin(db: Session) -> Optional[User]:
    """Get the default seeded admin user if it exists."""
    return db.execute(
        select(User).where(User.email == DEFAULT_ADMIN_EMAIL)
    ).scalar_one_or_none()


def is_setup_required(db: Session) -> bool:
    """
    Check if initial setup is required.

    Setup is required when:
    - Only the default admin account exists (seeded but not configured)
    - No users exist at all
    """
    user_count = db.execute(select(func.count(User.id))).scalar()

    if user_count == 0:
        return True

    if user_count == 1:
        # Check if the only user is the default admin
        default_admin = get_default_admin(db)
        return default_admin is not None

    return False


def has_non_default_users(db: Session) -> bool:
    """Check if any users exist besides the default admin."""
    count = db.execute(
        select(func.count(User.id)).where(User.email != DEFAULT_ADMIN_EMAIL)
    ).scalar()
    return count > 0


def disable_default_admin(db: Session) -> bool:
    """
    Disable the default admin account.

    The default admin (admin@ibew46.com) can be disabled but not deleted.
    Its email and password cannot be changed via the setup page.

    Returns:
        True if admin was disabled, False if not found
    """
    admin = get_default_admin(db)
    if admin:
        admin.is_active = False
        db.commit()
        return True
    return False


def enable_default_admin(db: Session) -> bool:
    """
    Re-enable the default admin account.

    Returns:
        True if admin was enabled, False if not found
    """
    admin = get_default_admin(db)
    if admin:
        admin.is_active = True
        db.commit()
        return True
    return False


def get_default_admin_status(db: Session) -> dict:
    """
    Get the status of the default admin account.

    Returns:
        Dict with 'exists' and 'is_active' keys
    """
    admin = get_default_admin(db)
    if admin:
        return {
            "exists": True,
            "is_active": admin.is_active,
            "email": DEFAULT_ADMIN_EMAIL,
        }
    return {
        "exists": False,
        "is_active": False,
        "email": DEFAULT_ADMIN_EMAIL,
    }
