"""Period type lookup table model."""

from sqlalchemy import Column, Integer, SmallInteger, String
from src.infrastructure.database.base import Base


class PeriodType(Base):
    """
    Period types for usage tracking (hourly, daily, monthly, yearly).

    This is a lookup/catalog table with predefined values.
    """

    __tablename__ = "period_types"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    duration_minutes = Column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<PeriodType(id={self.id}, code='{self.code}', name='{self.name}')>"
