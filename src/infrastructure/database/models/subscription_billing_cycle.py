"""Subscription billing cycle lookup table model."""

from sqlalchemy import Boolean, Column, Integer, SmallInteger, String
from ..base import Base


class SubscriptionBillingCycle(Base):
    """
    Billing cycles for subscriptions.

    Examples: 'monthly', 'quarterly', 'annual'
    """

    __tablename__ = "subscription_billing_cycles"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    months_duration = Column(Integer, nullable=False)
    display_order = Column(Integer, default=0, server_default="0")
    is_active = Column(Boolean, default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<SubscriptionBillingCycle(id={self.id}, code='{self.code}', months={self.months_duration})>"
