"""List API keys use case."""

import structlog
from typing import List

from src.domain.repositories.api_key_repository import IAPIKeyRepository
from src.domain.entities.api_key import APIKey
from src.domain.value_objects.user_id import UserId

logger = structlog.get_logger(__name__)


class ListAPIKeysUseCase:
    """
    List all API keys for a user.

    Returns both active and revoked keys for visibility.
    User can see their API key history.

    Example:
        >>> use_case = ListAPIKeysUseCase(api_key_repo)
        >>> keys = use_case.execute(user_id_str="123e4567-...")
        >>> for key in keys:
        ...     print(f"{key.key_prefix} - {key.name}")
    """

    def __init__(self, api_key_repo: IAPIKeyRepository):
        """
        Initialize use case.

        Args:
            api_key_repo: API key repository
        """
        self._api_key_repo = api_key_repo

    def execute(
        self,
        user_id_str: str,
        active_only: bool = False,
    ) -> List[APIKey]:
        """
        List API keys for user.

        Args:
            user_id_str: User ID as UUID string
            active_only: If True, return only active keys (default: False)

        Returns:
            List of APIKey entities (ordered by created_at DESC)

        Example:
            >>> # Get all keys
            >>> all_keys = use_case.execute(user_id_str="123e4567-...")
            >>> # Get only active keys
            >>> active_keys = use_case.execute(
            ...     user_id_str="123e4567-...",
            ...     active_only=True
            ... )
        """
        logger.info(
            "Listing API keys",
            user_id=user_id_str,
            active_only=active_only,
        )

        # Parse user ID
        user_id = UserId.from_string(user_id_str)

        # Get keys
        if active_only:
            api_keys = self._api_key_repo.find_active_by_user_id(user_id)
        else:
            api_keys = self._api_key_repo.find_by_user_id(user_id)

        logger.info(
            "API keys retrieved",
            user_id=user_id_str,
            count=len(api_keys),
            active_only=active_only,
        )

        return api_keys
