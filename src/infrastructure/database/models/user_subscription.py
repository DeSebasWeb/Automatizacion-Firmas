"""User subscription model."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.infrastructure.database.base import Base


class UserSubscription(Base):
    """
    User subscriptions linking users to plans.

    Tracks subscription lifecycle, billing periods, and status.
    """

    __tablename__ = "user_subscriptions"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False, index=True)
    billing_cycle_id = Column(SmallInteger, ForeignKey("subscription_billing_cycles.id"), nullable=False)
    status_id = Column(SmallInteger, ForeignKey("subscription_statuses.id"), nullable=False, index=True)

    # Subscription Period
    trial_ends_at = Column(DateTime(timezone=False), nullable=True)
    current_period_start = Column(DateTime(timezone=False), nullable=False)
    current_period_end = Column(DateTime(timezone=False), nullable=False, index=True)
    cancelled_at = Column(DateTime(timezone=False), nullable=True)

    # External Integration
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    auto_renew = Column(Boolean, default=True, server_default="true")

    # Timestamps
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    billing_cycle = relationship("SubscriptionBillingCycle")
    status = relationship("SubscriptionStatus")
    invoices = relationship("Invoice", back_populates="subscription")

    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.current_period_end >= datetime.utcnow() and self.cancelled_at is None

    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period."""
        return self.trial_ends_at is not None and self.trial_ends_at >= datetime.utcnow()

    def __repr__(self) -> str:
        return f"<UserSubscription(id={self.id}, user_id={self.user_id}, plan_id={self.plan_id}, active={self.is_active})>"
