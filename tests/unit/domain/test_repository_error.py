"""Unit tests for RepositoryError exception.

Tests the RepositoryError to ensure proper error handling
when repository operations fail.
"""
import pytest

from domain.exceptions import RepositoryError, DomainException


@pytest.mark.unit
class TestRepositoryError:
    """Tests for RepositoryError exception."""

    def test_repository_error_with_message(self):
        """RepositoryError should accept and store a message."""
        # Arrange
        message = "Database connection failed"

        # Act
        exc = RepositoryError(message)

        # Assert
        assert str(exc) == message
        assert isinstance(exc, DomainException)

    def test_repository_error_inherits_from_domain_exception(self):
        """RepositoryError should inherit from DomainException."""
        # Arrange & Act
        exc = RepositoryError("test error")

        # Assert
        assert isinstance(exc, DomainException)
        assert isinstance(exc, Exception)

    def test_repository_error_can_be_raised(self):
        """RepositoryError should be raiseable and catchable."""
        # Arrange
        message = "Transaction failed"

        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            raise RepositoryError(message)

        assert str(exc_info.value) == message

    def test_repository_error_with_nested_exception(self):
        """RepositoryError should support exception chaining."""
        # Arrange
        original_error = ValueError("Original error")
        message = "Failed to save user"

        # Act
        try:
            try:
                raise original_error
            except ValueError as e:
                raise RepositoryError(message) from e
        except RepositoryError as exc:
            # Assert
            assert str(exc) == message
            assert exc.__cause__ == original_error

    def test_repository_error_empty_message(self):
        """RepositoryError should handle empty message."""
        # Arrange & Act
        exc = RepositoryError("")

        # Assert
        assert str(exc) == ""
        assert isinstance(exc, RepositoryError)
