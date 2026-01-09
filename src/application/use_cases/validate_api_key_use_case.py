"""Validate API key use case."""

import structlog
from typing import List, Optional

from src.domain.repositories.api_key_repository import IAPIKeyRepository
from src.domain.entities.api_key import APIKey
from src.domain.value_objects.api_key_value import APIKeyValue
from src.domain.value_objects.api_key_hash import APIKeyHash

logger = structlog.get_logger(__name__)


class InvalidCredentialsError(Exception):
    """Raised when API key is invalid or expired."""

    pass


class InsufficientPermissionsError(Exception):
    """Raised when API key lacks required scopes."""

    pass


class ValidateAPIKeyUseCase:
    """
    Validate API key and check permissions.

    This is the authentication use case for API keys.
    Called on every API request that uses X-API-Key header.

    Validation steps:
        1. Hash the plaintext key
        2. Lookup by hash
        3. Check is_valid() (active, not revoked, not expired)
        4. Optionally check required scopes
        5. Record usage (last_used_at)

    Example:
        >>> use_case = ValidateAPIKeyUseCase(api_key_repo)
        >>> api_key = use_case.execute(
        ...     key_str="vfy_abc123...",
        ...     required_scopes=["documents:read"]
        ... )
        >>> # API key is valid and has required scopes
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
        key_str: str,
        required_scopes: List[str] | None = None,
    ) -> APIKey:
        """
        Validate API key and check permissions.

        Args:
            key_str: Plaintext API key from X-API-Key header
            required_scopes: Optional list of required scopes

        Returns:
            Valid APIKey entity (for use in request context)

        Raises:
            InvalidCredentialsError: If key is invalid/expired/revoked
            InsufficientPermissionsError: If key lacks required scopes

        Example:
            >>> # In middleware/dependency
            >>> api_key = use_case.execute(
            ...     key_str=request.headers["X-API-Key"],
            ...     required_scopes=["documents:read"]
            ... )
            >>> request.state.api_key = api_key
        """
        logger.debug("Validating API key", required_scopes=required_scopes)

        # Step 1: Validate key format
        try:
            api_key_value = APIKeyValue.from_string(key_str)
        except ValueError as e:
            logger.warning("Invalid API key format", error=str(e))
            raise InvalidCredentialsError("Invalid API key format") from e

        # Step 2: Hash the key
        key_hash = APIKeyHash.from_key(str(api_key_value))

        # Step 3: Lookup by hash
        api_key = self._api_key_repo.find_by_hash(key_hash)

        if api_key is None:
            logger.warning(
                "API key not found",
                key_prefix=api_key_value.prefix,
            )
            raise InvalidCredentialsError("Invalid API key")

        logger.debug(
            "API key found",
            api_key_id=api_key.id,
            user_id=str(api_key.user_id),
            is_valid=api_key.is_valid(),
        )

        # Step 4: Check is_valid (active, not revoked, not expired)
        if not api_key.is_valid():
            logger.warning(
                "API key is invalid",
                api_key_id=api_key.id,
                is_active=api_key.is_active,
                revoked_at=api_key.revoked_at,
                expires_at=api_key.expires_at,
            )
            raise InvalidCredentialsError(
                "API key is revoked or expired"
            )

        # Step 5: Check required scopes (if specified)
        if required_scopes:
            if not api_key.has_scopes(required_scopes):
                logger.warning(
                    "API key lacks required scopes",
                    api_key_id=api_key.id,
                    required_scopes=required_scopes,
                    actual_scopes=api_key.get_scope_codes(),
                )
                raise InsufficientPermissionsError(
                    f"Missing required scopes: {required_scopes}"
                )

        # Step 6: Record usage
        api_key.record_usage()
        self._api_key_repo.update(api_key)

        logger.info(
            "API key validated successfully",
            api_key_id=api_key.id,
            user_id=str(api_key.user_id),
            scopes=api_key.get_scope_codes(),
        )

        return api_key

    def validate_without_scopes(self, key_str: str) -> APIKey:
        """
        Validate API key without checking scopes.

        Use when scopes will be checked later by endpoint.

        Args:
            key_str: Plaintext API key

        Returns:
            Valid APIKey entity

        Raises:
            InvalidCredentialsError: If key is invalid

        Example:
            >>> api_key = use_case.validate_without_scopes("vfy_abc123...")
        """
        return self.execute(key_str, required_scopes=None)
