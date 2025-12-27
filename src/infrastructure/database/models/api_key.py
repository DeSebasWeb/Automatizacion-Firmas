"""API key model."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.infrastructure.database.base import Base


class APIKey(Base):
    """
    API keys for programmatic access.

    Security:
    - key_hash: bcrypt/sha256 hash of the actual key (never store plaintext)
    - key_prefix: First 8 characters for identification (e.g., 'vfy_12345678...')
    """

    __tablename__ = "api_keys"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Key Security
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(20), nullable=False, index=True)

    # Metadata
    name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, server_default="true", index=True)

    # Usage Tracking
    last_used_at = Column(DateTime(timezone=False), nullable=True)

    # Expiration
    expires_at = Column(DateTime(timezone=False), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    revoked_at = Column(DateTime(timezone=False), nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")
    scopes = relationship("APIKeyScope", back_populates="api_key", cascade="all, delete-orphan")
    custom_limits = relationship("APIKeyCustomLimit", back_populates="api_key", cascade="all, delete-orphan")

    @property
    def is_valid(self) -> bool:
        """Check if API key is valid (active, not revoked, not expired)."""
        if not self.is_active or self.revoked_at is not None:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, prefix='{self.key_prefix}', valid={self.is_valid})>"
