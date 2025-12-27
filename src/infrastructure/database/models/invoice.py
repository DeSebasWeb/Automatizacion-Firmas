"""Invoice model."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class Invoice(Base):
    """
    Invoices for subscription billing and usage charges.

    Tracks invoice lifecycle from draft to paid, including
    line items, taxes, and payment information.
    """

    __tablename__ = "invoices"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status_id = Column(SmallInteger, ForeignKey("invoice_statuses.id"), nullable=False, index=True)
    payment_method_id = Column(SmallInteger, ForeignKey("payment_methods.id"), nullable=True)

    # Invoice Identification
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)

    # Billing Period
    period_start = Column(DateTime(timezone=False), nullable=False)
    period_end = Column(DateTime(timezone=False), nullable=False)

    # Amounts (USD)
    subtotal_usd = Column(Numeric(12, 2), nullable=False)
    tax_percentage = Column(Numeric(5, 2), default=Decimal("0.00"), server_default="0.00")
    tax_amount_usd = Column(Numeric(12, 2), default=Decimal("0.00"), server_default="0.00")
    total_usd = Column(Numeric(12, 2), nullable=False)

    # Invoice Lifecycle
    issued_at = Column(DateTime(timezone=False), nullable=True)
    due_at = Column(DateTime(timezone=False), nullable=True, index=True)
    paid_at = Column(DateTime(timezone=False), nullable=True)

    # External Integration
    stripe_invoice_id = Column(String(255), unique=True, nullable=True, index=True)
    pdf_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    user = relationship("User", back_populates="invoices")
    subscription = relationship("UserSubscription", back_populates="invoices")
    status = relationship("InvoiceStatus")
    payment_method = relationship("PaymentMethod")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")

    @property
    def is_paid(self) -> bool:
        """Check if invoice has been paid."""
        return self.paid_at is not None

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.is_paid or self.due_at is None:
            return False
        return self.due_at < datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total=${self.total_usd}, paid={self.is_paid})>"
