"""User repository port (interface)."""
from abc import ABC, abstractmethod
from typing import Optional, List

from ..entities.user import User
from ..value_objects.user_id import UserId
from ..value_objects.email import Email


class IUserRepository(ABC):
    """
    User repository interface (Port).

    Defines the contract for user persistence operations.
    Implementations must be provided by infrastructure layer.

    This interface allows the domain layer to remain independent
    of persistence details (database, ORM, etc.).
    """

    @abstractmethod
    def create(self, user: User) -> User:
        """
        Persist a new user.

        Args:
            user: User entity to persist

        Returns:
            Persisted user with database-generated fields

        Raises:
            DuplicateEmailError: If email already exists
            RepositoryError: If persistence fails
        """
        pass

    @abstractmethod
    def find_by_id(self, user_id: UserId) -> Optional[User]:
        """
        Find user by ID.

        Args:
            user_id: User identifier

        Returns:
            User entity if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        pass

    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        """
        Find user by email.

        Args:
            email: User email

        Returns:
            User entity if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """
        Update existing user.

        Args:
            user: User entity with updated data

        Returns:
            Updated user entity

        Raises:
            UserNotFoundError: If user doesn't exist
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    def delete(self, user_id: UserId) -> bool:
        """
        Delete user by ID.

        Args:
            user_id: User identifier

        Returns:
            True if user was deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool:
        """
        Check if user exists with given email.

        Args:
            email: User email

        Returns:
            True if user exists, False otherwise

        Raises:
            RepositoryError: If query fails
        """
        pass

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        List all users with pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of user entities

        Raises:
            RepositoryError: If query fails
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Count total number of users.

        Returns:
            Total user count

        Raises:
            RepositoryError: If query fails
        """
        pass
