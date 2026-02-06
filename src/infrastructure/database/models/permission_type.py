"""Permission type model."""
from sqlalchemy import Boolean, Column, SmallInteger, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base


class PermissionType(Base):
    """
    Permission types that can be applied to resources.

    Examples: read, write, delete, validate, export, admin
    """
    __tablename__ = "permission_types"

    # Primary Key
    id = Column(SmallInteger, primary_key=True, autoincrement=True)

    # Attributes
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, server_default="true")

    # Timestamps
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())

    # Relationships
    permission_scopes = relationship(
        "APIPermissionScope",
        back_populates="permission_type",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PermissionType(id={self.id}, code='{self.code}', name='{self.name}')>"
