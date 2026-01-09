"""Get available API key scopes use case."""

import structlog
from typing import List

from src.domain.repositories.api_key_repository import IAPIKeyRepository

logger = structlog.get_logger(__name__)


class GetAPIKeyScopesUseCase:
    """
    Get list of available permission scopes.

    This use case retrieves the catalog of all available scopes
    that can be assigned to API keys.

    Used for:
        - Populating UI dropdowns
        - Showing available permissions
        - Validating scope requests

    Example:
        >>> use_case = GetAPIKeyScopesUseCase(api_key_repo)
        >>> scopes = use_case.execute()
        >>> for scope in scopes:
        ...     print(f"{scope['code']}: {scope['name']}")
        documents:read: Read Documents
        documents:write: Write Documents
    """

    def __init__(self, api_key_repo: IAPIKeyRepository):
        """
        Initialize use case.

        Args:
            api_key_repo: API key repository
        """
        self._api_key_repo = api_key_repo

    def execute(self) -> List[dict]:
        """
        Get all available scopes.

        Returns:
            List of scope dicts with:
                - id: Scope ID (int)
                - code: Scope code (str, e.g., "documents:read")
                - name: Display name (str, e.g., "Read Documents")
                - description: Detailed description (str, optional)
                - category: Scope category (str, optional)

        Example:
            >>> scopes = use_case.execute()
            >>> [
            ...     {
            ...         "id": 1,
            ...         "code": "documents:read",
            ...         "name": "Read Documents",
            ...         "description": "Read document metadata and content",
            ...         "category": "documents"
            ...     },
            ...     ...
            ... ]
        """
        logger.debug("Retrieving available API key scopes")

        scopes = self._api_key_repo.get_available_scopes()

        logger.info("Available scopes retrieved", count=len(scopes))

        return scopes
