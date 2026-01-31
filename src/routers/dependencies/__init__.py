"""FastAPI dependencies."""

from src.routers.dependencies.auth import (
    get_current_user,
    get_current_user_optional,
    require_roles,
    require_verified_email,
    CurrentUser,
    OptionalUser,
    AdminUser,
    OfficerUser,
    StaffUser,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "require_roles",
    "require_verified_email",
    "CurrentUser",
    "OptionalUser",
    "AdminUser",
    "OfficerUser",
    "StaffUser",
]
