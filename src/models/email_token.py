"""Email verification and password reset token model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixins import TimestampMixin
from src.db.enums import TokenType

if TYPE_CHECKING:
    from src.models.user import User


class EmailToken(Base, TimestampMixin):
    """
    Token for email verification and password reset.

    Tokens are stored hashed for security.
    Single-use: marked as used after successful verification.
    """

    __tablename__ = "email_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    token_type: Mapped[TokenType] = mapped_column(
        SQLEnum(TokenType, name="token_type_enum"), nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_tokens")

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired

    def mark_used(self) -> None:
        """Mark token as used."""
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<EmailToken(id={self.id}, type={self.token_type}, is_valid={self.is_valid})>"
