"""Token response schema."""
from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """
    Token response DTO.

    Returned after successful login or token refresh.
    Contains JWT tokens for authentication.
    """

    access_token: str = Field(
        ...,
        description="JWT access token for API requests"
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }
    }
