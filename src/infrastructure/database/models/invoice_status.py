"""Invoice status lookup table model."""

from sqlalchemy import Boolean, Column, Integer, SmallInteger, String, Text
from ..base import Base


class InvoiceStatus(Base):
    """
    Invoice statuses.

    Examples: 'draft', 'pending', 'paid', 'overdue', 'cancelled'
    """

    __tablename__ = "invoice_statuses"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_paid_status = Column(Boolean, default=False, server_default="false")
    display_order = Column(Integer, default=0, server_default="0")

    def __repr__(self) -> str:
        return f"<InvoiceStatus(id={self.id}, code='{self.code}', paid={self.is_paid_status})>"
