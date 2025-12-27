"""User model - Core authentication entity."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class User(Base):
    """
    Core user authentication entity.

    Handles authentication, email verification, and account status.
    Profile information is stored separately in UserProfile.
    """

    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False, server_default="false")
    is_active = Column(Boolean, default=True, server_default="true", index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    last_login_at = Column(DateTime(timezone=False), nullable=True)

    # Relationships (lazy loading, will be populated when related models are loaded)
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="user", cascade="all, delete-orphan")
    usage_counters = relationship("UsageCounter", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"
