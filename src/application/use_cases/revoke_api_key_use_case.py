"""Revoke API key use case."""

import structlog

from src.domain.repositories.api_key_repository import IAPIKeyRepository
from src.domain.value_objects.user_id import UserId

logger = structlog.get_logger(__name__)


class APIKeyNotFoundError(Exception):
    """Raised when API key doesn't exist."""

    pass


class UnauthorizedError(Exception):
    """Raised when user tries to revoke someone else's key."""

    pass


class RevokeAPIKeyUseCase:
    """
    Revoke API key (soft delete).

    Business Rules:
        - Only key owner can revoke
        - Revocation is permanent (cannot be undone)
        - Revoked keys fail all future validations

    Security:
        - Prevents users from revoking others' keys
        - Audit trail preserved (revoked_at timestamp)

    Example:
        >>> use_case = RevokeAPIKeyUseCase(api_key_repo)
        >>> use_case.execute(
        ...     api_key_id="123e4567-...",
        ...     user_id_str="user-uuid"
        ... )
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
        api_key_id: str,
        user_id_str: str,
    ) -> None:
        """
        Revoke API key.

        Args:
            api_key_id: API key UUID to revoke
            user_id_str: User ID making the request (for authorization)

        Raises:
            APIKeyNotFoundError: If API key doesn't exist
            UnauthorizedError: If user doesn't own the key

        Example:
            >>> use_case.execute(
            ...     api_key_id="123e4567-e89b-12d3-a456-426614174000",
            ...     user_id_str="user-uuid"
            ... )
        """
        logger.info(
            "Revoking API key",
            api_key_id=api_key_id,
            user_id=user_id_str,
        )

        # Parse user ID
        user_id = UserId.from_string(user_id_str)

        # Get API key
        api_key = self._api_key_repo.find_by_id(api_key_id)

        if api_key is None:
            logger.warning(
                "API key not found for revocation",
                api_key_id=api_key_id,
            )
            raise APIKeyNotFoundError(f"API key not found: {api_key_id}")

        # Authorization check: User must own the key
        if api_key.user_id != user_id:
            logger.warning(
                "Unauthorized revocation attempt",
                api_key_id=api_key_id,
                actual_owner=str(api_key.user_id),
                attempted_by=user_id_str,
            )
            raise UnauthorizedError(
                "You are not authorized to revoke this API key"
            )

        # Revoke the key
        api_key.revoke()

        # Persist
        self._api_key_repo.update(api_key)

        logger.info(
            "API key revoked successfully",
            api_key_id=api_key_id,
            user_id=user_id_str,
        )
