"""Invoice line item model."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class InvoiceLineItem(Base):
    """
    Individual line items within an invoice.

    Can represent subscription fees, usage charges, credits, or adjustments.
    """

    __tablename__ = "invoice_line_items"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Keys
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type_id = Column(SmallInteger, ForeignKey("invoice_item_types.id"), nullable=False)

    # Line Item Data
    description = Column(String(500), nullable=False)
    quantity = Column(Integer, default=1, server_default="1")
    unit_price_usd = Column(Numeric(12, 6), nullable=False)
    total_price_usd = Column(Numeric(12, 2), nullable=False)

    # Optional References
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True)
    resource_type_id = Column(SmallInteger, ForeignKey("resource_types.id"), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    item_type = relationship("InvoiceItemType")
    plan = relationship("SubscriptionPlan", back_populates="invoice_line_items")
    resource_type = relationship("ResourceType")

    def __repr__(self) -> str:
        return f"<InvoiceLineItem(id={self.id}, invoice_id={self.invoice_id}, desc='{self.description}', total=${self.total_price_usd})>"
