"""User repository implementation (Adapter)."""
from typing import Optional, List
import structlog
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.domain.repositories.user_repository import IUserRepository
from src.domain.entities.user import User as DomainUser
from src.domain.value_objects.user_id import UserId
from src.domain.value_objects.email import Email
from src.domain.exceptions import (
    UserNotFoundError,
    DuplicateEmailError,
    RepositoryError
)
from src.infrastructure.database.models.user import User as DBUser
from src.infrastructure.database.mappers.user_mapper import UserMapper

logger = structlog.get_logger(__name__)


class UserRepository(IUserRepository):
    """
    SQLAlchemy implementation of IUserRepository.

    This adapter translates domain operations into SQLAlchemy queries
    and handles the conversion between domain entities and database models.
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session (injected via dependency)
        """
        self._session = session
        self._mapper = UserMapper()

    def create(self, user: DomainUser) -> DomainUser:
        """
        Persist new user.

        Args:
            user: Domain user entity

        Returns:
            Persisted user with generated fields

        Raises:
            DuplicateEmailError: If email already exists
            RepositoryError: If creation fails
        """
        try:
            # Convert domain → persistence
            db_user = self._mapper.to_persistence(user)

            # Persist
            self._session.add(db_user)
            self._session.flush()  # Get generated ID without committing

            logger.info("user_created", user_id=str(db_user.id), email=db_user.email)

            # Convert back to domain
            return self._mapper.to_domain(db_user)

        except IntegrityError as e:
            self._session.rollback()
            if "users_email_key" in str(e.orig):
                logger.warning("duplicate_email_error", email=str(user.email))
                raise DuplicateEmailError(str(user.email))
            raise RepositoryError(f"Failed to create user: {e}") from e

        except SQLAlchemyError as e:
            self._session.rollback()
            logger.error("user_creation_failed", error=str(e))
            raise RepositoryError(f"Failed to create user: {e}") from e

    def find_by_id(self, user_id: UserId) -> Optional[DomainUser]:
        """
        Find user by ID.

        Args:
            user_id: User identifier

        Returns:
            Domain user entity or None
        """
        try:
            db_user = self._session.query(DBUser).filter(
                DBUser.id == user_id.value
            ).first()

            if db_user is None:
                logger.debug("user_not_found_by_id", user_id=str(user_id))
                return None

            logger.debug("user_found_by_id", user_id=str(user_id))
            return self._mapper.to_domain(db_user)

        except SQLAlchemyError as e:
            logger.error("find_by_id_failed", user_id=str(user_id), error=str(e))
            raise RepositoryError(f"Failed to find user: {e}") from e

    def find_by_email(self, email: Email) -> Optional[DomainUser]:
        """
        Find user by email.

        Args:
            email: User email

        Returns:
            Domain user entity or None
        """
        try:
            db_user = self._session.query(DBUser).filter(
                DBUser.email == str(email)
            ).first()

            if db_user is None:
                logger.debug("user_not_found_by_email", email=str(email))
                return None

            logger.debug("user_found_by_email", email=str(email))
            return self._mapper.to_domain(db_user)

        except SQLAlchemyError as e:
            logger.error("find_by_email_failed", email=str(email), error=str(e))
            raise RepositoryError(f"Failed to find user: {e}") from e

    def update(self, user: DomainUser) -> DomainUser:
        """
        Update existing user.

        Args:
            user: Domain user with updated data

        Returns:
            Updated domain user

        Raises:
            UserNotFoundError: If user doesn't exist
            RepositoryError: If update fails
        """
        try:
            # Find existing record
            db_user = self._session.query(DBUser).filter(
                DBUser.id == user.id.value
            ).first()

            if db_user is None:
                logger.warning("user_not_found_for_update", user_id=str(user.id))
                raise UserNotFoundError(str(user.id))

            # Update fields
            db_user = self._mapper.update_db_from_domain(db_user, user)

            self._session.flush()

            logger.info("user_updated", user_id=str(user.id))

            return self._mapper.to_domain(db_user)

        except SQLAlchemyError as e:
            self._session.rollback()
            logger.error("user_update_failed", user_id=str(user.id), error=str(e))
            raise RepositoryError(f"Failed to update user: {e}") from e

    def delete(self, user_id: UserId) -> bool:
        """
        Delete user by ID.

        Args:
            user_id: User identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            deleted_count = self._session.query(DBUser).filter(
                DBUser.id == user_id.value
            ).delete()

            self._session.flush()

            if deleted_count > 0:
                logger.info("user_deleted", user_id=str(user_id))
                return True
            else:
                logger.debug("user_not_found_for_deletion", user_id=str(user_id))
                return False

        except SQLAlchemyError as e:
            self._session.rollback()
            logger.error("user_deletion_failed", user_id=str(user_id), error=str(e))
            raise RepositoryError(f"Failed to delete user: {e}") from e

    def exists_by_email(self, email: Email) -> bool:
        """Check if user with email exists."""
        try:
            exists = self._session.query(DBUser).filter(
                DBUser.email == str(email)
            ).first() is not None

            logger.debug("email_existence_check", email=str(email), exists=exists)
            return exists

        except SQLAlchemyError as e:
            logger.error("exists_check_failed", email=str(email), error=str(e))
            raise RepositoryError(f"Failed to check email existence: {e}") from e

    def list_all(self, limit: int = 100, offset: int = 0) -> List[DomainUser]:
        """List users with pagination."""
        try:
            db_users = self._session.query(DBUser).limit(limit).offset(offset).all()

            logger.debug("users_listed", count=len(db_users), limit=limit, offset=offset)

            return [self._mapper.to_domain(db_user) for db_user in db_users]

        except SQLAlchemyError as e:
            logger.error("list_users_failed", error=str(e))
            raise RepositoryError(f"Failed to list users: {e}") from e

    def count(self) -> int:
        """Count total users."""
        try:
            count = self._session.query(DBUser).count()

            logger.debug("users_counted", total=count)
            return count

        except SQLAlchemyError as e:
            logger.error("count_users_failed", error=str(e))
            raise RepositoryError(f"Failed to count users: {e}") from e
