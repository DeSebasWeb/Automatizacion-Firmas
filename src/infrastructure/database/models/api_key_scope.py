"""API key scope model - Many-to-many relationship."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class APIKeyScope(Base):
    """
    API key permission scopes (many-to-many relationship).

    Implements fine-grained access control for API keys.
    Example: An API key might have scopes ['read:user', 'write:verification']
    """

    __tablename__ = "api_key_scopes"

    # Composite Primary Key
    api_key_id = Column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        primary_key=True,
    )
    scope_id = Column(
        SmallInteger,
        ForeignKey("api_permission_scopes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Timestamp
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())

    # Relationships
    api_key = relationship("APIKey", back_populates="scopes")
    scope = relationship("APIPermissionScope")

    def __repr__(self) -> str:
        return f"<APIKeyScope(api_key_id={self.api_key_id}, scope_id={self.scope_id})>"
