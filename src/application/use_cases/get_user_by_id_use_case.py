"""Get user by ID use case."""
import structlog
from src.domain.repositories.user_repository import IUserRepository
from src.domain.entities.user import User
from src.domain.value_objects.user_id import UserId
from src.domain.exceptions.exceptions import UserNotFoundError

logger = structlog.get_logger(__name__)


class GetUserByIdUseCase:
    """
    Use case: Get user by ID.

    Used for retrieving user information in protected endpoints.
    """

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize use case.

        Args:
            user_repository: User repository implementation
        """
        self._user_repo = user_repository

    def execute(self, user_id_str: str) -> User:
        """
        Get user by ID.

        Args:
            user_id_str: User ID as string (UUID format)

        Returns:
            User entity

        Raises:
            UserNotFoundError: User not found
            ValueError: Invalid UUID format
        """
        logger.info("Getting user by ID", user_id=user_id_str)

        # 1. Validate and create UserId VO
        user_id = UserId.from_string(user_id_str)

        # 2. Find user by ID
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            logger.warning("User not found", user_id=str(user_id))
            raise UserNotFoundError(str(user_id))

        # 3. Log and return
        logger.info(
            "User retrieved successfully",
            user_id=str(user.id),
            email=str(user.email)
        )

        return user
