"""Unit tests for domain exceptions."""
import pytest
# Direct imports without src. prefix to avoid circular import through __init__.py
from domain.exceptions import (
    DomainException,
    RepositoryError,
    UserNotFoundError,
    DuplicateEmailError,
    InvalidCredentialsError
)


class TestDomainException:
    """Test DomainException base class."""

    def test_domain_exception_is_exception(self):
        """DomainException should inherit from Exception."""
        exc = DomainException("test error")
        assert isinstance(exc, Exception)

    def test_domain_exception_message(self):
        """DomainException should store error message."""
        exc = DomainException("test error")
        assert str(exc) == "test error"


class TestRepositoryError:
    """Test RepositoryError."""

    def test_repository_error_is_domain_exception(self):
        """RepositoryError should inherit from DomainException."""
        exc = RepositoryError("test error")
        assert isinstance(exc, DomainException)
        assert isinstance(exc, Exception)

    def test_repository_error_message(self):
        """RepositoryError should store error message."""
        exc = RepositoryError("Database connection failed")
        assert str(exc) == "Database connection failed"


class TestUserNotFoundError:
    """Test UserNotFoundError."""

    def test_user_not_found_error_is_repository_error(self):
        """UserNotFoundError should inherit from RepositoryError."""
        exc = UserNotFoundError("user-123")
        assert isinstance(exc, RepositoryError)
        assert isinstance(exc, DomainException)

    def test_user_not_found_error_message(self):
        """UserNotFoundError should format message with user_id."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        exc = UserNotFoundError(user_id)
        assert str(exc) == f"User not found: {user_id}"

    def test_user_not_found_error_stores_user_id(self):
        """UserNotFoundError should store user_id as attribute."""
        user_id = "user-123"
        exc = UserNotFoundError(user_id)
        assert exc.user_id == user_id

    def test_user_not_found_error_can_be_caught(self):
        """UserNotFoundError should be catchable."""
        with pytest.raises(UserNotFoundError) as exc_info:
            raise UserNotFoundError("test-user")

        assert exc_info.value.user_id == "test-user"


class TestDuplicateEmailError:
    """Test DuplicateEmailError."""

    def test_duplicate_email_error_is_repository_error(self):
        """DuplicateEmailError should inherit from RepositoryError."""
        exc = DuplicateEmailError("test@example.com")
        assert isinstance(exc, RepositoryError)
        assert isinstance(exc, DomainException)

    def test_duplicate_email_error_message(self):
        """DuplicateEmailError should format message with email."""
        email = "duplicate@example.com"
        exc = DuplicateEmailError(email)
        assert str(exc) == f"User with email already exists: {email}"

    def test_duplicate_email_error_stores_email(self):
        """DuplicateEmailError should store email as attribute."""
        email = "test@example.com"
        exc = DuplicateEmailError(email)
        assert exc.email == email

    def test_duplicate_email_error_can_be_caught(self):
        """DuplicateEmailError should be catchable."""
        with pytest.raises(DuplicateEmailError) as exc_info:
            raise DuplicateEmailError("test@example.com")

        assert exc_info.value.email == "test@example.com"


class TestInvalidCredentialsError:
    """Test InvalidCredentialsError."""

    def test_invalid_credentials_error_is_domain_exception(self):
        """InvalidCredentialsError should inherit from DomainException."""
        exc = InvalidCredentialsError()
        assert isinstance(exc, DomainException)
        assert not isinstance(exc, RepositoryError)  # Direct DomainException

    def test_invalid_credentials_error_message(self):
        """InvalidCredentialsError should have default message."""
        exc = InvalidCredentialsError()
        assert str(exc) == "Invalid email or password"

    def test_invalid_credentials_error_no_arguments(self):
        """InvalidCredentialsError should not require arguments."""
        exc = InvalidCredentialsError()
        assert exc is not None

    def test_invalid_credentials_error_can_be_caught(self):
        """InvalidCredentialsError should be catchable."""
        with pytest.raises(InvalidCredentialsError) as exc_info:
            raise InvalidCredentialsError()

        assert str(exc_info.value) == "Invalid email or password"


class TestExceptionHierarchy:
    """Test exception hierarchy relationships."""

    def test_all_exceptions_are_exceptions(self):
        """All domain exceptions should be Python exceptions."""
        exceptions = [
            DomainException("test"),
            RepositoryError("test"),
            UserNotFoundError("user-1"),
            DuplicateEmailError("test@example.com"),
            InvalidCredentialsError()
        ]

        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_repository_errors_hierarchy(self):
        """Repository errors should all inherit from RepositoryError."""
        repository_errors = [
            UserNotFoundError("user-1"),
            DuplicateEmailError("test@example.com")
        ]

        for exc in repository_errors:
            assert isinstance(exc, RepositoryError)
            assert isinstance(exc, DomainException)

    def test_catch_all_domain_exceptions(self):
        """Should be able to catch all domain exceptions with DomainException."""
        exceptions_to_test = [
            UserNotFoundError("user-1"),
            DuplicateEmailError("test@example.com"),
            InvalidCredentialsError(),
            RepositoryError("test")
        ]

        for exc_class in exceptions_to_test:
            with pytest.raises(DomainException):
                raise exc_class

    def test_catch_all_repository_errors(self):
        """Should be able to catch all repository errors with RepositoryError."""
        repository_errors = [
            UserNotFoundError("user-1"),
            DuplicateEmailError("test@example.com")
        ]

        for exc_class in repository_errors:
            with pytest.raises(RepositoryError):
                raise exc_class
