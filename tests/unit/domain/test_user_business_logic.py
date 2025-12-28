"""Unit tests for User entity business logic methods.

Tests the business logic methods of the User entity to ensure
proper behavior for authentication, password management, and account status.
"""
import pytest
from datetime import datetime

from domain.entities.user import User
from domain.value_objects.email import Email


@pytest.mark.unit
class TestUserAuthentication:
    """Tests for User authentication-related methods."""

    def test_verify_password_with_correct_password(self):
        """verify_password() should return True for correct password."""
        # Arrange
        email = Email.from_string("test@example.com")
        plain_password = "SecurePass123!"
        user = User.create(email=email, plain_password=plain_password)

        # Act
        result = user.verify_password(plain_password)

        # Assert
        assert result is True

    def test_verify_password_with_incorrect_password(self):
        """verify_password() should return False for incorrect password."""
        # Arrange
        email = Email.from_string("test@example.com")
        plain_password = "CorrectPassword123"
        wrong_password = "WrongPassword456"
        user = User.create(email=email, plain_password=plain_password)

        # Act
        result = user.verify_password(wrong_password)

        # Assert
        assert result is False

    def test_can_authenticate_requires_email_verification(self):
        """can_authenticate() should return False if email not verified."""
        # Arrange
        email = Email.from_string("test@example.com")
        user = User.create(email=email, plain_password="SecurePass123")

        # Act
        result = user.can_authenticate()

        # Assert
        assert result is False  # Email not verified yet
        assert user.email_verified is False

    def test_can_authenticate_requires_active_account(self):
        """can_authenticate() should return False if account is deactivated."""
        # Arrange
        email = Email.from_string("test@example.com")
        user = User.create(email=email, plain_password="SecurePass123")
        user.verify_email()  # Email verified
        user.deactivate()     # But account deactivated

        # Act
        result = user.can_authenticate()

        # Assert
        assert result is False
        assert user.email_verified is True
        assert user.is_active is False

    def test_can_authenticate_returns_true_when_all_requirements_met(self):
        """can_authenticate() should return True when verified and active."""
        # Arrange
        email = Email.from_string("test@example.com")
        user = User.create(email=email, plain_password="SecurePass123")
        user.verify_email()  # Verify email

        # Act
        result = user.can_authenticate()

        # Assert
        assert result is True
        assert user.email_verified is True
        assert user.is_active is True
