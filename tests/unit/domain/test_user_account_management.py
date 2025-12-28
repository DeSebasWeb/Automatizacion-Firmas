"""Unit tests for User account management methods.

Tests password changes, email verification, account activation/deactivation,
and login tracking functionality.
"""
import pytest
from datetime import datetime

from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.hashed_password import HashedPassword


@pytest.mark.unit
class TestUserAccountManagement:
    """Tests for User account management methods."""

    def test_change_password_updates_password_hash(self):
        """change_password() should update the password hash."""
        # Arrange
        email = Email.from_string("test@example.com")
        old_password = "OldPassword123"
        new_password = "NewPassword456"
        user = User.create(email=email, plain_password=old_password)
        old_hash = user.password.hash_value

        # Act
        user.change_password(new_password)

        # Assert
        assert user.password.hash_value != old_hash  # Hash changed
        assert user.verify_password(new_password) is True  # New password works
        assert user.verify_password(old_password) is False  # Old password doesn't work

    def test_verify_email_sets_email_verified_to_true(self):
        """verify_email() should mark email as verified."""
        # Arrange
        email = Email.from_string("test@example.com")
        user = User.create(email=email, plain_password="SecurePass123")
        assert user.email_verified is False  # Initially not verified

        # Act
        user.verify_email()

        # Assert
        assert user.email_verified is True

    def test_deactivate_sets_is_active_to_false(self):
        """deactivate() should set is_active to False."""
        # Arrange
        email = Email.from_string("test@example.com")
        user = User.create(email=email, plain_password="SecurePass123")
        assert user.is_active is True  # Initially active

        # Act
        user.deactivate()

        # Assert
        assert user.is_active is False

    def test_activate_sets_is_active_to_true(self):
        """activate() should set is_active to True."""
        # Arrange
        email = Email.from_string("test@example.com")
        user = User.create(email=email, plain_password="SecurePass123")
        user.deactivate()  # First deactivate
        assert user.is_active is False

        # Act
        user.activate()

        # Assert
        assert user.is_active is True

    def test_record_login_sets_last_login_timestamp(self):
        """record_login() should set last_login_at timestamp."""
        # Arrange
        email = Email.from_string("test@example.com")
        user = User.create(email=email, plain_password="SecurePass123")
        assert user.last_login_at is None  # Initially no login

        # Act
        user.record_login()

        # Assert
        assert user.last_login_at is not None
        assert isinstance(user.last_login_at, datetime)
