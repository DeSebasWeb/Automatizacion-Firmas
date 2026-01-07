"""Authenticate user use case."""
import structlog
from src.domain.repositories.user_repository import IUserRepository
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.exceptions.exceptions import InvalidCredentialsError

logger = structlog.get_logger(__name__)


class AuthenticateUserUseCase:
    """
    Use case: Authenticate user with credentials.

    Business rules:
    - User must exist
    - Password must match
    - User must be active
    - Email must be verified (enforced by can_authenticate())
    """

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize use case.

        Args:
            user_repository: User repository implementation
        """
        self._user_repo = user_repository

    def execute(self, email_str: str, password: str) -> User:
        """
        Authenticate user.

        Args:
            email_str: User email
            password: Plain password to verify

        Returns:
            Authenticated user entity

        Raises:
            InvalidCredentialsError: Invalid email or password
        """
        logger.info("Authenticating user", email=email_str)

        # 1. Validate Email VO
        try:
            email = Email.from_string(email_str)
        except ValueError:
            # Invalid email format
            logger.warning("Authentication failed: invalid email format", email=email_str)
            raise InvalidCredentialsError()

        # 2. Find user by email
        user = self._user_repo.find_by_email(email)
        if user is None:
            # User not found - use generic error message for security
            logger.warning("Authentication failed: user not found", email=str(email))
            raise InvalidCredentialsError()

        # 3. Verify password
        if not user.verify_password(password):
            # Wrong password - use generic error message for security
            logger.warning(
                "Authentication failed: invalid password",
                user_id=str(user.id),
                email=str(email)
            )
            raise InvalidCredentialsError()

        # 4. Verify user can authenticate (active + email verified)
        if not user.can_authenticate():
            logger.warning(
                "Authentication failed: user cannot authenticate",
                user_id=str(user.id),
                email=str(email),
                is_active=user.is_active,
                email_verified=user.email_verified
            )
            raise InvalidCredentialsError()

        # 5. Update last_login_at
        user.record_login()
        updated_user = self._user_repo.save(user)

        # 6. Log success and return
        logger.info(
            "User authenticated successfully",
            user_id=str(updated_user.id),
            email=str(updated_user.email)
        )

        return updated_user
