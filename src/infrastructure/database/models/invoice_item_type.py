"""Invoice item type lookup table model."""

from sqlalchemy import Column, SmallInteger, String, Text
from src.infrastructure.database.base import Base


class InvoiceItemType(Base):
    """
    Invoice line item types.

    Examples: 'subscription_fee', 'usage_charge', 'overage', 'credit', 'refund'
    """

    __tablename__ = "invoice_item_types"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<InvoiceItemType(id={self.id}, code='{self.code}')>"
