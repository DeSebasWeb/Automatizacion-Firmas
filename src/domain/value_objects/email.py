"""Email value object."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Email:
    """
    Email value object - Immutable and self-validating.

    Represents a valid email address with automatic normalization.
    """

    value: str

    # Email validation regex (RFC 5322 simplified)
    _EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    def __post_init__(self):
        """Validate email format on creation."""
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email format: {self.value}")

        # Validate length
        if len(self.value) < 5:
            raise ValueError(f"Email too short (min 5 chars): {self.value}")

        if len(self.value) > 255:
            raise ValueError(f"Email too long (max 255 chars): {self.value}")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """
        Validate email using regex.

        Args:
            email: Email string to validate

        Returns:
            True if email format is valid, False otherwise
        """
        if not email or ' ' in email:
            return False

        return bool(Email._EMAIL_REGEX.match(email))

    @classmethod
    def from_string(cls, email_str: str) -> "Email":
        """
        Create Email from string with normalization.

        Normalization:
        - Strips whitespace
        - Converts to lowercase

        Args:
            email_str: Raw email string

        Returns:
            Email instance

        Raises:
            ValueError: If email format is invalid

        Example:
            >>> email = Email.from_string("  USER@EXAMPLE.COM  ")
            >>> str(email)
            'user@example.com'
        """
        normalized = email_str.strip().lower()
        return cls(value=normalized)

    @classmethod
    def try_create(cls, email_str: str) -> "Email | None":
        """
        Try to create Email, returns None if invalid.

        Use this when you want to handle invalid emails gracefully
        without exceptions.

        Args:
            email_str: Raw email string

        Returns:
            Email instance or None if invalid

        Example:
            >>> email = Email.try_create("invalid-email")
            >>> email is None
            True
        """
        try:
            return cls.from_string(email_str)
        except ValueError:
            return None

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Email('{self.value}')"