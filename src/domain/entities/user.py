"""User domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..value_objects.user_id import UserId
from ..value_objects.email import Email
from ..value_objects.hashed_password import HashedPassword


@dataclass
class User:
    """
    User domain entity.

    Represents a user in the system with authentication capabilities.
    This is the DOMAIN representation, separate from the database model.

    The User entity encapsulates business logic related to user authentication,
    authorization, and account management. It uses value objects for type safety
    and validation.

    Key responsibilities:
    - Password verification
    - Email verification status
    - Account activation/deactivation
    - Login tracking
    - Business rules enforcement (e.g., only verified users can authenticate)
    """

    id: UserId
    email: Email
    password: HashedPassword
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        email: Email,
        plain_password: str,
        user_id: Optional[UserId] = None,
        bcrypt_rounds: int = 12
    ) -> "User":
        """
        Create new user (factory method).

        This is the recommended way to create a new User entity.
        It handles:
        - UUID generation if not provided
        - Password hashing
        - Default values for new users

        Args:
            email: User email (Email value object)
            plain_password: Password in plain text (will be hashed)
            user_id: Optional user ID (generates UUID if not provided)
            bcrypt_rounds: Bcrypt cost factor (default: 12)

        Returns:
            User instance with default values for new users

        Example:
            >>> email = Email.from_string("user@example.com")
            >>> user = User.create(email=email, plain_password="SecurePass123")
            >>> user.email_verified
            False
            >>> user.is_active
            True
        """
        now = datetime.utcnow()

        return cls(
            id=user_id or UserId.generate(),
            email=email,
            password=HashedPassword.from_plain_text(
                plain_password,
                rounds=bcrypt_rounds
            ),
            email_verified=False,
            is_active=True,
            created_at=now,
            updated_at=now
        )

    def verify_password(self, plain_password: str) -> bool:
        """
        Verify password against stored hash.

        Uses constant-time comparison via bcrypt to prevent timing attacks.

        Args:
            plain_password: Password to verify

        Returns:
            True if password matches, False otherwise

        Example:
            >>> user = User.create(
            ...     email=Email.from_string("user@example.com"),
            ...     plain_password="SecurePass123"
            ... )
            >>> user.verify_password("SecurePass123")
            True
            >>> user.verify_password("WrongPassword")
            False
        """
        return self.password.verify(plain_password)

    def change_password(
        self,
        new_plain_password: str,
        bcrypt_rounds: int = 12
    ) -> None:
        """
        Change user password.

        Creates a new HashedPassword value object (immutable pattern).

        Args:
            new_plain_password: New password in plain text
            bcrypt_rounds: Bcrypt cost factor (default: 12)

        Raises:
            ValueError: If new password doesn't meet requirements

        Example:
            >>> user.change_password("NewSecurePass456")
        """
        # Value objects are immutable, so we create a new one
        new_password = HashedPassword.from_plain_text(
            new_plain_password,
            rounds=bcrypt_rounds
        )

        object.__setattr__(self, 'password', new_password)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def verify_email(self) -> None:
        """
        Mark email as verified.

        Business rule: Email verification is required for authentication.

        Example:
            >>> user = User.create(
            ...     email=Email.from_string("user@example.com"),
            ...     plain_password="SecurePass123"
            ... )
            >>> user.can_authenticate()
            False
            >>> user.verify_email()
            >>> user.can_authenticate()
            True
        """
        object.__setattr__(self, 'email_verified', True)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def deactivate(self) -> None:
        """
        Deactivate user account.

        Deactivated users cannot authenticate. Use this instead of deletion
        to preserve data integrity and audit trails.

        Example:
            >>> user.deactivate()
            >>> user.can_authenticate()
            False
        """
        object.__setattr__(self, 'is_active', False)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def activate(self) -> None:
        """
        Activate user account.

        Reactivates a previously deactivated account.

        Example:
            >>> user.deactivate()
            >>> user.activate()
            >>> user.is_active
            True
        """
        object.__setattr__(self, 'is_active', True)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def record_login(self) -> None:
        """
        Record successful login timestamp.

        Call this after successful authentication to track user activity.

        Example:
            >>> user.record_login()
            >>> user.last_login_at is not None
            True
        """
        object.__setattr__(self, 'last_login_at', datetime.utcnow())

    def can_authenticate(self) -> bool:
        """
        Check if user can authenticate.

        Business rules:
        - User must be active
        - Email must be verified

        Returns:
            True if user meets authentication requirements

        Example:
            >>> user = User.create(
            ...     email=Email.from_string("user@example.com"),
            ...     plain_password="SecurePass123"
            ... )
            >>> user.can_authenticate()
            False  # Email not verified
            >>> user.verify_email()
            >>> user.can_authenticate()
            True
        """
        return self.is_active and self.email_verified

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"User(id={self.id}, email={self.email}, "
            f"verified={self.email_verified}, active={self.is_active})"
        )
