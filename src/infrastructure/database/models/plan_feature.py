"""Plan feature model."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class PlanFeature(Base):
    """
    Features included in subscription plans.

    Examples:
    - feature_name: 'api_access', feature_value: 'true'
    - feature_name: 'support_level', feature_value: 'priority'
    - feature_name: 'custom_branding', feature_value: 'enabled'
    """

    __tablename__ = "plan_features"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Key
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Feature Data
    feature_name = Column(String(100), nullable=False)
    feature_value = Column(String(255), nullable=True)
    display_order = Column(Integer, default=0, server_default="0")

    # Timestamp
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())

    # Relationships
    plan = relationship("SubscriptionPlan", back_populates="features")

    def __repr__(self) -> str:
        return f"<PlanFeature(id={self.id}, plan_id={self.plan_id}, name='{self.feature_name}', value='{self.feature_value}')>"
