"""API permission scope lookup table model."""

from sqlalchemy import Boolean, Column, SmallInteger, String, Text
from src.infrastructure.database.base import Base


class APIPermissionScope(Base):
    """
    API permission scopes for granular access control.

    Examples: 'read:user', 'write:verification', 'admin:all'
    """

    __tablename__ = "api_permission_scopes"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<APIPermissionScope(id={self.id}, code='{self.code}')>"
