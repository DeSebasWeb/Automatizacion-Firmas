"""Payment method lookup table model."""

from sqlalchemy import Boolean, Column, Integer, SmallInteger, String, Text
from ..base import Base


class PaymentMethod(Base):
    """
    Payment methods.

    Examples: 'credit_card', 'paypal', 'bank_transfer', 'stripe'
    """

    __tablename__ = "payment_methods"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    requires_gateway = Column(Boolean, default=True, server_default="true")
    is_active = Column(Boolean, default=True, server_default="true")
    display_order = Column(Integer, default=0, server_default="0")

    def __repr__(self) -> str:
        return f"<PaymentMethod(id={self.id}, code='{self.code}')>"
