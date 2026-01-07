"""Login request schema."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Login request DTO.

    Used for POST /auth/login endpoint.

    Note: Login does NOT require strict validation since we're only checking
    credentials. Invalid formats will simply fail authentication.
    """

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="User password",
        examples=["SecurePass123!"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    }
