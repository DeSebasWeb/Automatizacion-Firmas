"""Subscription plan model."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class SubscriptionPlan(Base):
    """
    Subscription plans defining pricing tiers and features.

    Examples: 'free', 'basic', 'professional', 'enterprise'
    """

    __tablename__ = "subscription_plans"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Plan Identification
    plan_code = Column(String(50), unique=True, nullable=False, index=True)
    plan_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Pricing (USD)
    precio_mensual_usd = Column(Numeric(10, 2), nullable=False)
    precio_anual_usd = Column(Numeric(10, 2), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, server_default="true", index=True)
    is_public = Column(Boolean, default=True, server_default="true")
    display_order = Column(Integer, default=0, server_default="0")

    # Timestamps
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    features = relationship("PlanFeature", back_populates="plan", cascade="all, delete-orphan")
    limits = relationship("PlanLimit", back_populates="plan", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="plan")
    invoice_line_items = relationship("InvoiceLineItem", back_populates="plan")

    @property
    def monthly_discount_percentage(self) -> Decimal:
        """Calculate monthly discount when paying annually."""
        if not self.precio_anual_usd or not self.precio_mensual_usd:
            return Decimal("0.00")
        annual_as_monthly = self.precio_mensual_usd * 12
        savings = annual_as_monthly - self.precio_anual_usd
        return (savings / annual_as_monthly) * 100

    def __repr__(self) -> str:
        return f"<SubscriptionPlan(id={self.id}, code='{self.plan_code}', price=${self.precio_mensual_usd}/mo)>"
