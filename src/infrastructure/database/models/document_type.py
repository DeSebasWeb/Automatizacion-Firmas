"""Document type model."""
from sqlalchemy import Boolean, Column, Integer, Numeric, SmallInteger, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class DocumentType(Base):
    """
    Document types that can be processed by the system.

    Examples: cedula_form, e14, generic_text
    """
    __tablename__ = "document_types"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Attributes
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)

    # Configuration
    expected_rows = Column(SmallInteger, nullable=True)
    validate_totals = Column(Boolean, default=False, server_default="false")
    base_cost = Column(Numeric(10, 6), default=0, server_default="0")

    # Status
    is_active = Column(Boolean, default=True, server_default="true", index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=False), server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    permission_scopes = relationship(
        "APIPermissionScope",
        back_populates="document_type",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DocumentType(id={self.id}, code='{self.code}', name='{self.name}')>"
