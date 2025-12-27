"""Usage counter model."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class UsageCounter(Base):
    """
    Aggregated usage counters per user/resource/period.

    Provides fast lookups for rate limiting and quota checking
    without scanning all usage events.
    """

    __tablename__ = "usage_counters"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_type_id = Column(SmallInteger, ForeignKey("period_types.id"), nullable=False)
    resource_type_id = Column(SmallInteger, ForeignKey("resource_types.id"), nullable=False)

    # Period Window
    period_start = Column(DateTime(timezone=False), nullable=False, index=True)
    period_end = Column(DateTime(timezone=False), nullable=False, index=True)

    # Counter Data
    count_current = Column(Integer, default=0, server_default="0")
    limit_max = Column(Integer, nullable=True)
    last_incremented_at = Column(DateTime(timezone=False), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    user = relationship("User", back_populates="usage_counters")
    period_type = relationship("PeriodType")
    resource_type = relationship("ResourceType")

    @property
    def is_limit_exceeded(self) -> bool:
        """Check if usage has exceeded the limit."""
        if self.limit_max is None:
            return False
        return self.count_current >= self.limit_max

    @property
    def remaining_quota(self) -> int:
        """Get remaining quota (returns -1 if unlimited)."""
        if self.limit_max is None:
            return -1
        return max(0, self.limit_max - self.count_current)

    def __repr__(self) -> str:
        return f"<UsageCounter(id={self.id}, user_id={self.user_id}, count={self.count_current}/{self.limit_max})>"
