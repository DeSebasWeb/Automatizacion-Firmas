"""Usage event metadata model."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class UsageEventMetadata(Base):
    """
    Key-value metadata for usage events.

    Stores additional context about usage events (e.g., IP address,
    user agent, document type, confidence score, etc.)
    """

    __tablename__ = "usage_event_metadata"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Key
    usage_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usage_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Key-Value Data
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())

    # Relationships
    usage_event = relationship("UsageEvent", back_populates="event_metadata")

    def __repr__(self) -> str:
        return f"<UsageEventMetadata(id={self.id}, event_id={self.usage_event_id}, key='{self.key}')>"
