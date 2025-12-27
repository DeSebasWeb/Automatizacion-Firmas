"""Limit type lookup table model."""

from sqlalchemy import Boolean, Column, SmallInteger, String, Text
from src.infrastructure.database.base import Base


class LimitType(Base):
    """
    Limit types for plan restrictions.

    Examples: 'max_api_calls_per_month', 'max_storage_gb'
    """

    __tablename__ = "limit_types"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<LimitType(id={self.id}, code='{self.code}', unit='{self.unit}')>"
