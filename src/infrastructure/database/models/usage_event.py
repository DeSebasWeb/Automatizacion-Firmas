"""Usage event model."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class UsageEvent(Base):
    """
    Individual usage events for billing and analytics.

    Tracks every API call, document verification, or resource consumption
    with cost calculation and metadata.
    """

    __tablename__ = "usage_events"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type_id = Column(SmallInteger, ForeignKey("usage_event_types.id"), nullable=False, index=True)

    # Usage Quantity
    quantity = Column(Integer, default=1, server_default="1")

    # Cost Calculation
    provider_cost_usd = Column(Numeric(12, 6), nullable=True)
    markup_percentage = Column(Numeric(5, 2), default=Decimal("30.00"), server_default="30.00")
    billable_amount_usd = Column(Numeric(12, 6), nullable=True)

    # Polymorphic Resource Reference (for linking to specific resources)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    resource_table = Column(String(100), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp(), index=True)

    # Relationships
    user = relationship("User", back_populates="usage_events")
    event_type = relationship("UsageEventType")
    event_metadata = relationship("UsageEventMetadata", back_populates="usage_event", cascade="all, delete-orphan")

    @property
    def calculated_billable_amount(self) -> Decimal:
        """Calculate billable amount from provider cost and markup."""
        if self.provider_cost_usd is None:
            return Decimal("0.00")
        markup_multiplier = 1 + (self.markup_percentage / 100)
        return self.provider_cost_usd * markup_multiplier

    def __repr__(self) -> str:
        return f"<UsageEvent(id={self.id}, user_id={self.user_id}, type_id={self.event_type_id}, qty={self.quantity})>"
