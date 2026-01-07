"""User response schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserResponse(BaseModel):
    """
    User public information DTO.

    Returns user data without sensitive information (no password).
    Used in responses for authenticated endpoints.
    """
    id: str = Field(
        ...,
        description="User unique identifier (UUID)"
    )
    email: str = Field(
        ...,
        description="User email address"
    )
    email_verified: bool = Field(
        ...,
        description="Whether user's email has been verified"
    )
    is_active: bool = Field(
        ...,
        description="Whether user account is active"
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp (UTC)"
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        description="Last successful login timestamp (UTC)"
    )

    model_config = {
        "from_attributes": True,  # Allows creating from ORM models and domain entities
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "email_verified": True,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "last_login_at": "2024-01-20T14:22:00Z"
            }
        }
    }

    @classmethod
    def from_domain(cls, user) -> "UserResponse":
        """
        Create UserResponse from domain User entity.

        Args:
            user: Domain User entity

        Returns:
            UserResponse DTO
        """
        return cls(
            id=str(user.id),
            email=str(user.email),
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
