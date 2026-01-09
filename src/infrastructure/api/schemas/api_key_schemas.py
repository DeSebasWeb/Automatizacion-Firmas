"""API Key schemas (DTOs)."""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional


class CreateAPIKeyRequest(BaseModel):
    """
    Create API key request.

    Example:
        {
            "name": "Production Server",
            "scopes": ["documents:read", "documents:write"],
            "expires_in_days": 365
        }
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="API key name/description",
        examples=["Production Server", "CI/CD Pipeline", "Development Key"],
    )
    scopes: List[str] = Field(
        ...,
        min_length=1,
        description="List of permission scopes",
        examples=[["documents:read", "documents:write"]],
    )
    expires_in_days: Optional[int] = Field(
        None,
        gt=0,
        le=3650,  # Max 10 years
        description="Expiration in days (null = never expires)",
        examples=[365, 90, None],
    )

    @field_validator("scopes")
    @classmethod
    def validate_scopes_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure scopes list is not empty."""
        if not v:
            raise ValueError("At least one scope is required")
        return v

    @field_validator("scopes")
    @classmethod
    def validate_scope_format(cls, v: List[str]) -> List[str]:
        """Validate scope format (basic check)."""
        for scope in v:
            if ":" not in scope:
                raise ValueError(
                    f"Invalid scope format: '{scope}'. "
                    f"Expected format: 'category:action' (e.g., 'documents:read')"
                )
        return v


class APIKeyResponse(BaseModel):
    """
    API key response with plaintext key.

    ⚠️ SECURITY WARNING:
        This schema includes the plaintext 'key' field.
        Only use for creation response - key is shown ONCE.

    Example:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "key": "vfy_abc123...",
            "key_prefix": "vfy_abc123...",
            "name": "Production Server",
            "scopes": ["documents:read", "documents:write"],
            "expires_at": "2025-12-31T23:59:59Z",
            "created_at": "2024-01-01T00:00:00Z"
        }
    """

    id: str = Field(..., description="API key UUID")
    key: str = Field(
        ...,
        description="Plaintext API key (SHOWN ONLY ONCE - SAVE IT!)",
    )
    key_prefix: str = Field(..., description="Key prefix for identification")
    name: Optional[str] = Field(None, description="API key name")
    scopes: List[str] = Field(..., description="Permission scopes")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "key": "vfy_xQW9k3mNpR7Lj2Hs8Kt5Yz4Vw1Ex6Gf9Aq3Bc0Td8Ue2Nf7Jg1Hk5Ml4Zn6Vx",
                "key_prefix": "vfy_xQW9k3mN",
                "name": "Production Server",
                "scopes": ["documents:read", "documents:write"],
                "expires_at": "2025-12-31T23:59:59Z",
                "created_at": "2024-01-01T00:00:00Z",
            }
        },
    }


class APIKeyListItem(BaseModel):
    """
    API key list item (without plaintext key).

    Used for listing user's API keys.
    Does NOT include plaintext key (only shown on creation).

    Example:
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "key_prefix": "vfy_abc123...",
            "name": "Production Server",
            "scopes": ["documents:read", "documents:write"],
            "is_active": true,
            "last_used_at": "2024-01-15T10:30:00Z",
            "expires_at": "2025-12-31T23:59:59Z",
            "created_at": "2024-01-01T00:00:00Z",
            "revoked_at": null
        }
    """

    id: str = Field(..., description="API key UUID")
    key_prefix: str = Field(
        ...,
        description="Key prefix for identification (e.g., 'vfy_abc123...')",
    )
    name: Optional[str] = Field(None, description="API key name")
    scopes: List[str] = Field(..., description="Permission scopes")
    is_active: bool = Field(..., description="Active status")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    revoked_at: Optional[datetime] = Field(None, description="Revocation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "key_prefix": "vfy_xQW9k3mN",
                "name": "Production Server",
                "scopes": ["documents:read", "documents:write"],
                "is_active": True,
                "last_used_at": "2024-01-15T10:30:00Z",
                "expires_at": "2025-12-31T23:59:59Z",
                "created_at": "2024-01-01T00:00:00Z",
                "revoked_at": None,
            }
        },
    }


class AvailableScopeResponse(BaseModel):
    """
    Available permission scope.

    Used to show available scopes for API key creation.

    Example:
        {
            "code": "documents:read",
            "name": "Read Documents",
            "description": "Read document metadata and content",
            "category": "documents"
        }
    """

    code: str = Field(..., description="Scope code (e.g., 'documents:read')")
    name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Detailed description")
    category: Optional[str] = Field(None, description="Scope category")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "code": "documents:read",
                "name": "Read Documents",
                "description": "Read document metadata and content",
                "category": "documents",
            }
        },
    }


class APIKeyListResponse(BaseModel):
    """
    List of API keys response.

    Example:
        {
            "api_keys": [...],
            "total": 5,
            "active_count": 3
        }
    """

    api_keys: List[APIKeyListItem] = Field(..., description="List of API keys")
    total: int = Field(..., description="Total number of API keys")
    active_count: int = Field(..., description="Number of active API keys")

    model_config = {
        "json_schema_extra": {
            "example": {
                "api_keys": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "key_prefix": "vfy_xQW9k3mN",
                        "name": "Production Server",
                        "scopes": ["documents:read"],
                        "is_active": True,
                        "last_used_at": "2024-01-15T10:30:00Z",
                        "expires_at": None,
                        "created_at": "2024-01-01T00:00:00Z",
                        "revoked_at": None,
                    }
                ],
                "total": 1,
                "active_count": 1,
            }
        },
    }


class ErrorResponse(BaseModel):
    """
    Standard error response.

    Example:
        {
            "detail": "Invalid API key",
            "error_code": "INVALID_CREDENTIALS"
        }
    """

    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Invalid API key",
                "error_code": "INVALID_CREDENTIALS",
            }
        },
    }
