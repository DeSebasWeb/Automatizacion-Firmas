"""Unit tests for domain exceptions.

Tests the custom exception hierarchy to ensure proper error handling
and exception attributes across the domain layer.
"""
import pytest

from domain.exceptions import (
    DomainException,
    UserNotFoundError,
    DuplicateEmailError,
    InvalidCredentialsError,
    RepositoryError
)


@pytest.mark.unit
class TestDomainException:
    """Tests for base DomainException class."""

    def test_domain_exception_is_base_exception(self):
        """DomainException should inherit from Exception."""
        # Arrange & Act
        exc = DomainException("test message")

        # Assert
        assert isinstance(exc, Exception)
        assert str(exc) == "test message"


@pytest.mark.unit
class TestUserNotFoundError:
    """Tests for UserNotFoundError."""

    def test_user_not_found_stores_user_id(self):
        """UserNotFoundError should store the user_id as an attribute."""
        # Arrange
        user_id = "test-user-123"

        # Act
        exc = UserNotFoundError(user_id)

        # Assert
        assert exc.user_id == user_id
        assert user_id in str(exc)

    def test_user_not_found_inherits_from_domain_exception(self):
        """UserNotFoundError should inherit from DomainException."""
        # Arrange & Act
        exc = UserNotFoundError("user-456")

        # Assert
        assert isinstance(exc, DomainException)


@pytest.mark.unit
class TestDuplicateEmailError:
    """Tests for DuplicateEmailError."""

    def test_duplicate_email_stores_email(self):
        """DuplicateEmailError should store the email as an attribute."""
        # Arrange
        email = "test@example.com"

        # Act
        exc = DuplicateEmailError(email)

        # Assert
        assert exc.email == email
        assert email in str(exc)

    def test_duplicate_email_inherits_from_domain_exception(self):
        """DuplicateEmailError should inherit from DomainException."""
        # Arrange & Act
        exc = DuplicateEmailError("duplicate@test.com")

        # Assert
        assert isinstance(exc, DomainException)


@pytest.mark.unit
class TestInvalidCredentialsError:
    """Tests for InvalidCredentialsError."""

    def test_invalid_credentials_message(self):
        """InvalidCredentialsError should have a clear message."""
        # Arrange & Act
        exc = InvalidCredentialsError()

        # Assert
        assert "Invalid email or password" in str(exc)
        assert isinstance(exc, DomainException)
