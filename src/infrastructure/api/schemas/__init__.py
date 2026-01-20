"""API schemas (DTOs)."""
from .register_request import RegisterRequest
from .login_request import LoginRequest
from .token_response import TokenResponse
from .user_schemas import UserResponse
from .catalog_schemas import DocumentTypeResponse, PermissionTypeResponse, ScopeResponse

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "DocumentTypeResponse",
    "PermissionTypeResponse",
    "ScopeResponse",
]
