"""
User model for system authentication and authorization.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index

from src.db.base import Base
from src.db.mixins import TimestampMixin, SoftDeleteMixin


class User(TimestampMixin, SoftDeleteMixin, Base):
    """
    System user for authentication and authorization.

    Separate from Student/Instructor - represents people who log into the system.
    A User may be linked to a Student or Instructor record, or be an admin.

    Note: Password handling should use proper hashing (bcrypt/argon2).
    This model stores the hash, never the plaintext password.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Authentication (to be implemented)
    password_hash = Column(String(255), nullable=True)  # bcrypt/argon2 hash

    # Role-based access (simple approach)
    # Roles: admin, staff, instructor, student
    role = Column(String(50), nullable=False, default="student", index=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Login tracking
    last_login_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # Optional links to domain entities
    # These allow a user to be associated with their Student or Instructor record
    student_id = Column(Integer, nullable=True, index=True)
    instructor_id = Column(Integer, nullable=True, index=True)

    __table_args__ = (Index("ix_user_role_active", "role", "is_active"),)

    @property
    def full_name(self) -> str:
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_locked(self) -> bool:
        """Check if account is locked due to failed login attempts."""
        from datetime import datetime

        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
