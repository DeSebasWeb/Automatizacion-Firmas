"""API key custom limit model."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.infrastructure.database.base import Base


class APIKeyCustomLimit(Base):
    """
    Custom limits per API key (override plan limits).

    Allows setting specific limits for individual API keys,
    useful for special agreements or temporary increases.
    """

    __tablename__ = "api_key_custom_limits"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Keys
    api_key_id = Column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    limit_type_id = Column(SmallInteger, ForeignKey("limit_types.id"), nullable=False)

    # Limit Value
    limit_value = Column(Integer, nullable=False)

    # Timestamp
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())

    # Relationships
    api_key = relationship("APIKey", back_populates="custom_limits")
    limit_type = relationship("LimitType")

    def __repr__(self) -> str:
        return f"<APIKeyCustomLimit(id={self.id}, api_key_id={self.api_key_id}, type_id={self.limit_type_id}, value={self.limit_value})>"
