"""Subscription status lookup table model."""

from sqlalchemy import Boolean, Column, Integer, SmallInteger, String, Text
from ..base import Base


class SubscriptionStatus(Base):
    """
    Subscription statuses.

    Examples: 'active', 'trial', 'cancelled', 'expired', 'past_due'
    """

    __tablename__ = "subscription_statuses"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active_status = Column(Boolean, default=False, server_default="false")
    display_order = Column(Integer, default=0, server_default="0")

    def __repr__(self) -> str:
        return f"<SubscriptionStatus(id={self.id}, code='{self.code}', active={self.is_active_status})>"
