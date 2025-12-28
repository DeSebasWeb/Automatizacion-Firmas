"""Unit tests for Email value object.

Tests the Email value object to ensure proper email validation,
immutability, and normalization.
"""
import pytest

from domain.value_objects.email import Email


@pytest.mark.unit
class TestEmailValidation:
    """Tests for Email validation."""

    def test_email_with_valid_format(self):
        """Email should accept valid email addresses."""
        # Arrange
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "john+tag@company.org",
            "alice_123@test-domain.com"
        ]

        # Act & Assert
        for email_str in valid_emails:
            email = Email.from_string(email_str)
            assert isinstance(email, Email)

    def test_email_normalization_to_lowercase(self):
        """Email should be normalized to lowercase."""
        # Arrange
        email_str = "User@EXAMPLE.COM"

        # Act
        email = Email.from_string(email_str)

        # Assert
        assert str(email) == "user@example.com"

    def test_email_with_invalid_format_raises_error(self):
        """Email should raise ValueError for invalid formats."""
        # Arrange
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com",
            ""
        ]

        # Act & Assert
        for invalid in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email"):
                Email.from_string(invalid)

    def test_email_string_representation(self):
        """str(Email) should return the normalized email string."""
        # Arrange
        email_str = "test@example.com"
        email = Email.from_string(email_str)

        # Act
        result = str(email)

        # Assert
        assert result == email_str

    def test_email_equality(self):
        """Two Emails with the same address should be equal."""
        # Arrange
        email_1 = Email.from_string("user@example.com")
        email_2 = Email.from_string("USER@EXAMPLE.COM")  # Different case

        # Act & Assert
        assert email_1 == email_2  # Should be equal after normalization
        assert hash(email_1) == hash(email_2)
