"""Resource type lookup table model."""

from sqlalchemy import Boolean, Column, SmallInteger, String, Text
from src.infrastructure.database.base import Base


class ResourceType(Base):
    """
    Resource types for usage tracking and billing.

    Examples: 'document_verification', 'api_call', 'storage_gb'
    """

    __tablename__ = "resource_types"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_billable = Column(Boolean, default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<ResourceType(id={self.id}, code='{self.code}', billable={self.is_billable})>"
