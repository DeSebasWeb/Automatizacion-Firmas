"""Create API key use case."""

import structlog
from typing import Tuple

from src.domain.repositories.api_key_repository import IAPIKeyRepository
from src.domain.entities.api_key import APIKey
from src.domain.value_objects.user_id import UserId
from src.domain.value_objects.api_key_value import APIKeyValue

logger = structlog.get_logger(__name__)


class CreateAPIKeyUseCase:
    """
    Create new API key for user.

    Business Rules:
        - User must exist
        - At least one scope required
        - All scopes must exist in catalog
        - Plaintext key shown ONLY ONCE

    Security:
        - Only key hash is persisted
        - Plaintext key returned once, then discarded
        - Scopes validated against catalog

    Example:
        >>> use_case = CreateAPIKeyUseCase(api_key_repo)
        >>> api_key, plaintext = use_case.execute(
        ...     user_id_str="123e4567-...",
        ...     name="Production Key",
        ...     scope_codes=["documents:read", "documents:write"],
        ...     expires_in_days=365
        ... )
        >>> print(f"Save this key: {plaintext}")  # Show to user
        >>> # plaintext is now discarded
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
        name: str,
        scope_codes: list[str],
        expires_in_days: int | None = None,
    ) -> Tuple[APIKey, str]:
        """
        Create API key.

        Args:
            user_id_str: User ID as UUID string
            name: API key name/description
            scope_codes: List of scope codes (e.g., ["documents:read"])
            expires_in_days: Optional expiration in days (None = never)

        Returns:
            Tuple of:
                - APIKey entity (persisted)
                - Plaintext key string (SHOW ONCE TO USER)

        Raises:
            ValueError: If user_id invalid, scopes empty, or scope doesn't exist
            DatabaseError: If persistence fails

        Security:
            The plaintext key is returned ONLY ONCE. After this method,
            it will never be accessible again. Must be shown to user immediately.

        Example:
            >>> api_key, plaintext = use_case.execute(
            ...     user_id_str="123e4567-e89b-12d3-a456-426614174000",
            ...     name="CI/CD Pipeline",
            ...     scope_codes=["documents:read"],
            ...     expires_in_days=365
            ... )
            >>> # Show plaintext to user in response
        """
        logger.info(
            "Creating API key",
            user_id=user_id_str,
            name=name,
            scope_count=len(scope_codes),
            expires_in_days=expires_in_days,
        )

        # Validate inputs
        if not scope_codes:
            raise ValueError("At least one scope is required")

        # Parse user ID
        user_id = UserId.from_string(user_id_str)

        # Validate all scopes exist
        for scope_code in scope_codes:
            if not self._api_key_repo.scope_exists(scope_code):
                available_scopes = self._api_key_repo.get_available_scopes()
                available_codes = [s["code"] for s in available_scopes]
                logger.error(
                    "Invalid scope code",
                    scope_code=scope_code,
                    available_scopes=available_codes,
                )
                raise ValueError(
                    f"Invalid scope code: '{scope_code}'. "
                    f"Available scopes: {available_codes}"
                )

        # Create domain entity (generates random key)
        api_key, plaintext_key = APIKey.create(
            user_id=user_id,
            name=name,
            scopes=scope_codes,
            expires_in_days=expires_in_days,
        )

        logger.info(
            "API key entity created",
            api_key_id=api_key.id,
            key_prefix=api_key.key_prefix,
        )

        # Persist to database
        created_api_key = self._api_key_repo.create(api_key, scope_codes)

        logger.info(
            "API key persisted successfully",
            api_key_id=created_api_key.id,
            user_id=str(created_api_key.user_id),
            scopes=scope_codes,
        )

        # Return entity and plaintext key
        # WARNING: plaintext_key will never be accessible again
        return created_api_key, str(plaintext_key)
