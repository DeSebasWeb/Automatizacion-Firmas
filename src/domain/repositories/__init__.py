"""Domain repositories (ports)."""
from .user_repository import IUserRepository
from .document_type_repository import IDocumentTypeRepository
from .permission_type_repository import IPermissionTypeRepository

__all__ = [
    "IUserRepository",
    "IDocumentTypeRepository",
    "IPermissionTypeRepository",
]
