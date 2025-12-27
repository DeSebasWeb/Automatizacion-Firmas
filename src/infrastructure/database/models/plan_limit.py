"""Plan limit model."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class PlanLimit(Base):
    """
    Resource limits for subscription plans.

    Examples:
    - limit_type: 'max_api_calls_per_month', limit_value: 10000
    - limit_type: 'max_documents_per_day', limit_value: 500
    """

    __tablename__ = "plan_limits"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Keys
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    limit_type_id = Column(SmallInteger, ForeignKey("limit_types.id"), nullable=False)

    # Limit Configuration
    limit_value = Column(Integer, nullable=False)
    is_hard_limit = Column(Boolean, default=True, server_default="true")

    # Timestamp
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())

    # Relationships
    plan = relationship("SubscriptionPlan", back_populates="limits")
    limit_type = relationship("LimitType")

    def __repr__(self) -> str:
        return f"<PlanLimit(id={self.id}, plan_id={self.plan_id}, type_id={self.limit_type_id}, value={self.limit_value}, hard={self.is_hard_limit})>"
