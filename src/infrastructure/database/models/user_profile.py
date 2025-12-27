"""User profile model - Extended user information."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class UserProfile(Base):
    """
    Extended user profile information.

    Separated from User to maintain clean separation between
    authentication (User) and profile data (UserProfile).
    """

    __tablename__ = "user_profiles"

    # Primary Key (also Foreign Key to users)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Personal Information (Colombian naming convention)
    primer_nombre = Column(String(100), nullable=True)
    segundo_nombre = Column(String(100), nullable=True)
    primer_apellido = Column(String(100), nullable=True)
    segundo_apellido = Column(String(100), nullable=True)

    # Organization Information
    nombre_organizacion = Column(String(200), nullable=True)
    tipo_organizacion = Column(String(100), nullable=True)

    # Localization
    country_code = Column(CHAR(2), default="CO", server_default="'CO'")
    timezone = Column(
        String(50), default="America/Bogota", server_default="'America/Bogota'"
    )
    telefono = Column(String(20), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    user = relationship("User", back_populates="profile")

    @property
    def full_name(self) -> str:
        """Get formatted full name (Colombian style)."""
        parts = [
            self.primer_nombre,
            self.segundo_nombre,
            self.primer_apellido,
            self.segundo_apellido,
        ]
        return " ".join(filter(None, parts))

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, name='{self.full_name}')>"
