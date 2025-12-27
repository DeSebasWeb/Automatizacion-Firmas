"""Usage event type lookup table model."""

from sqlalchemy import Column, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import relationship
from src.infrastructure.database.base import Base


class UsageEventType(Base):
    """
    Usage event types linking to resource types.

    Examples: 'api_call_success', 'document_processed', 'verification_completed'
    """

    __tablename__ = "usage_event_types"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    resource_type_id = Column(
        SmallInteger, ForeignKey("resource_types.id"), nullable=False
    )
    default_quantity = Column(Integer, default=1, server_default="1")

    # Relationships
    resource_type = relationship("ResourceType", backref="event_types")

    def __repr__(self) -> str:
        return f"<UsageEventType(id={self.id}, code='{self.code}')>"
