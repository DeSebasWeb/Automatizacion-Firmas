"""Register request schema."""
import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """
    Register user request DTO.

    Used for POST /auth/register endpoint.

    Email requirements:
    - Valid email format (RFC 5322)
    - Between 5 and 255 characters
    - No spaces allowed
    - Common disposable email domains blocked

    Password requirements:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character (!@#$%^&*(),.?":{}|<>)
    """

    email: EmailStr = Field(
        ...,
        description="User email address (will be normalized to lowercase)",
        examples=["user@example.com"],
        min_length=5,
        max_length=255
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description=(
            "User password. Must contain: "
            "min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char"
        ),
        examples=["SecurePass123!"]
    )

    @field_validator("email")
    @classmethod
    def validate_email_security(cls, v: str) -> str:
        """
        Additional email validation for security.

        Validates:
        - No spaces in email
        - No consecutive dots
        - Valid TLD (top-level domain) with at least 2 chars
        - Blocks common disposable email providers
        - Proper format before and after @

        Args:
            v: Email string to validate

        Returns:
            Validated and normalized email (lowercase)

        Raises:
            ValueError: If email doesn't meet security requirements
        """
        email = v.lower().strip()

        # Check for spaces
        if ' ' in email:
            raise ValueError("Email cannot contain spaces")

        # Check for consecutive dots
        if '..' in email:
            raise ValueError("Email cannot contain consecutive dots")

        # Split into local and domain parts
        if '@' not in email:
            raise ValueError("Email must contain @")

        parts = email.split('@')
        if len(parts) != 2:
            raise ValueError("Email must have exactly one @ symbol")

        local_part, domain_part = parts

        # Validate local part (before @)
        if not local_part or len(local_part) < 1:
            raise ValueError("Email local part cannot be empty")

        if len(local_part) > 64:
            raise ValueError("Email local part cannot exceed 64 characters")

        # Validate local part characters
        if not re.match(r'^[a-z0-9._+-]+$', local_part):
            raise ValueError(
                "Email local part can only contain letters, numbers, and ._+- symbols"
            )

        # Cannot start or end with dot
        if local_part.startswith('.') or local_part.endswith('.'):
            raise ValueError("Email local part cannot start or end with a dot")

        # Validate domain part (after @)
        if not domain_part or len(domain_part) < 3:
            raise ValueError("Email domain must be at least 3 characters")

        if not re.match(r'^[a-z0-9.-]+$', domain_part):
            raise ValueError(
                "Email domain can only contain letters, numbers, dots, and hyphens"
            )

        # Validate domain has a TLD
        if '.' not in domain_part:
            raise ValueError("Email domain must have a top-level domain (TLD)")

        domain_labels = domain_part.split('.')
        tld = domain_labels[-1]

        # TLD must be at least 2 characters
        if len(tld) < 2:
            raise ValueError("Email top-level domain must be at least 2 characters")

        # TLD must be only letters
        if not re.match(r'^[a-z]+$', tld):
            raise ValueError("Email top-level domain must contain only letters")

        # Block common disposable email domains (security)
        disposable_domains = [
            'tempmail.com', 'throwaway.email', 'guerrillamail.com',
            '10minutemail.com', 'mailinator.com', 'trashmail.com',
            'fakeinbox.com', 'yopmail.com', 'temp-mail.org'
        ]

        if domain_part in disposable_domains:
            raise ValueError(
                f"Disposable email addresses are not allowed: {domain_part}"
            )

        # Validate domain doesn't start or end with hyphen or dot
        if domain_part.startswith('-') or domain_part.endswith('-'):
            raise ValueError("Email domain cannot start or end with a hyphen")

        if domain_part.startswith('.') or domain_part.endswith('.'):
            raise ValueError("Email domain cannot start or end with a dot")

        return email

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets security requirements.

        Requirements:
        - At least 8 characters (enforced by Field min_length)
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character

        Args:
            v: Password string to validate

        Returns:
            Validated password

        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError(
                "Password must contain at least one uppercase letter (A-Z)"
            )

        if not re.search(r"[a-z]", v):
            raise ValueError(
                "Password must contain at least one lowercase letter (a-z)"
            )

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number (0-9)")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError(
                "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
            )

        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    }
