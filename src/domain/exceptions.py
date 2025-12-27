"""Domain exceptions."""


class DomainException(Exception):
    """Base exception for domain layer."""
    pass


class RepositoryError(DomainException):
    """Base exception for repository operations."""
    pass


class UserNotFoundError(RepositoryError):
    """User not found in repository."""

    def __init__(self, user_id: str):
        super().__init__(f"User not found: {user_id}")
        self.user_id = user_id


class DuplicateEmailError(RepositoryError):
    """User with email already exists."""

    def __init__(self, email: str):
        super().__init__(f"User with email already exists: {email}")
        self.email = email


class InvalidCredentialsError(DomainException):
    """Invalid authentication credentials."""

    def __init__(self):
        super().__init__("Invalid email or password")
