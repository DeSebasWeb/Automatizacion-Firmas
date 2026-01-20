"""API permission scope lookup table model."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import relationship
from ..base import Base


class APIPermissionScope(Base):
    """
    API permission scopes for granular access control.

    Now connected to document_types and permission_types for scalability.

    Examples:
    - cedula_form:read (document_type_id=1, permission_type_id=1)
    - e14:validate (document_type_id=2, permission_type_id=4)
    - documents:admin (document_type_id=NULL, permission_type_id=6)
    """

    __tablename__ = "api_permission_scopes"

    # Primary Key
    id = Column(SmallInteger, primary_key=True, autoincrement=True)

    # Foreign Keys
    document_type_id = Column(
        Integer,
        ForeignKey("document_types.id", ondelete="CASCADE"),
        nullable=True,  # NULL for generic scopes (admin, webhooks, etc.)
        index=True
    )
    permission_type_id = Column(
        SmallInteger,
        ForeignKey("permission_types.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Attributes
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, server_default="true")

    # Relationships
    document_type = relationship("DocumentType", back_populates="permission_scopes")
    permission_type = relationship("PermissionType", back_populates="permission_scopes")

    # Existing relationship (DO NOT REMOVE)
    api_key_scopes = relationship(
        "APIKeyScope",
        back_populates="scope",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<APIPermissionScope(id={self.id}, code='{self.code}')>"
