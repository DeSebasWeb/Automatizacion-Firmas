"""API Key repository port."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.api_key import APIKey
from ..value_objects.user_id import UserId
from ..value_objects.api_key_hash import APIKeyHash


class IAPIKeyRepository(ABC):
    """
    API Key repository interface (Port).

    Following the Repository pattern and Dependency Inversion Principle,
    this interface defines the contract for API key persistence without
    coupling the domain to any specific database implementation.

    Responsibilities:
        - CRUD operations for API keys
        - Querying by hash (for authentication)
        - Querying by user (for listing)
        - Managing scope relationships (many-to-many)
        - Retrieving available scopes catalog

    Implementation notes:
        - All datetime values should be timezone-aware (UTC)
        - Scopes must be eagerly loaded to avoid N+1 queries
        - find_by_hash should be optimized (indexed)
    """

    @abstractmethod
    def create(self, api_key: APIKey, scope_codes: List[str]) -> APIKey:
        """
        Create API key with scopes.

        This operation must be atomic (use database transaction):
            1. Insert into api_keys table
            2. Lookup scope IDs from api_permission_scopes
            3. Insert relationships into api_key_scopes table

        Args:
            api_key: API key entity to persist
            scope_codes: List of scope code strings (e.g., ["documents:read"])

        Returns:
            Created API key entity (with any DB-generated fields populated)

        Raises:
            ValueError: If any scope_code doesn't exist in catalog
            DatabaseError: If persistence fails

        Security:
            - Only key_hash is stored (never plaintext key)
            - All scopes must exist in api_permission_scopes table

        Example:
            >>> api_key, plaintext = APIKey.create(...)
            >>> persisted = repo.create(api_key, ["documents:read", "documents:write"])
            >>> # plaintext key is shown to user, then discarded
        """
        pass

    @abstractmethod
    def find_by_hash(self, key_hash: APIKeyHash) -> Optional[APIKey]:
        """
        Find API key by hash.

        This is the primary authentication lookup - must be fast.

        Performance requirements:
            - key_hash column must be indexed
            - Scopes must be eagerly loaded (use joinedload)
            - Should complete in <10ms

        Args:
            key_hash: Hashed API key to lookup

        Returns:
            APIKey entity if found, None otherwise
            (includes scopes in result)

        Example:
            >>> from src.domain.value_objects.api_key_hash import APIKeyHash
            >>> key_hash = APIKeyHash.from_key("vfy_abc123...")
            >>> api_key = repo.find_by_hash(key_hash)
            >>> if api_key and api_key.is_valid():
            ...     # Authenticated
        """
        pass

    @abstractmethod
    def find_by_id(self, api_key_id: str) -> Optional[APIKey]:
        """
        Find API key by ID.

        Args:
            api_key_id: API key UUID as string

        Returns:
            APIKey entity if found, None otherwise

        Example:
            >>> api_key = repo.find_by_id("123e4567-e89b-12d3-a456-426614174000")
        """
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: UserId) -> List[APIKey]:
        """
        List all API keys for user (active and revoked).

        Args:
            user_id: User ID to filter by

        Returns:
            List of API keys (may be empty)
            Ordered by created_at DESC (newest first)

        Example:
            >>> user_id = UserId.from_string("123e4567-e89b-12d3-a456-426614174000")
            >>> keys = repo.find_by_user_id(user_id)
            >>> print(f"User has {len(keys)} API keys")
        """
        pass

    @abstractmethod
    def find_active_by_user_id(self, user_id: UserId) -> List[APIKey]:
        """
        List only active (non-revoked, non-expired) API keys for user.

        Args:
            user_id: User ID to filter by

        Returns:
            List of active API keys (may be empty)
            Filtered by: is_active=True, revoked_at IS NULL
            Ordered by created_at DESC

        Example:
            >>> user_id = UserId.from_string("123e4567-e89b-12d3-a456-426614174000")
            >>> active_keys = repo.find_active_by_user_id(user_id)
        """
        pass

    @abstractmethod
    def update(self, api_key: APIKey) -> APIKey:
        """
        Update API key.

        Use cases:
            - Revoke key (set is_active=False, revoked_at=now)
            - Record usage (update last_used_at)

        Note:
            Scopes are NOT updated through this method.
            Scope changes require delete + recreate.

        Args:
            api_key: API key entity with updated fields

        Returns:
            Updated API key entity

        Example:
            >>> api_key.revoke()
            >>> repo.update(api_key)
        """
        pass

    @abstractmethod
    def delete(self, api_key_id: str) -> bool:
        """
        Permanently delete API key.

        Warning:
            This is a HARD delete. For normal operations, use revoke() instead.
            Hard delete should only be used for:
                - User account deletion (cascade)
                - Compliance requirements (GDPR, etc.)

        Args:
            api_key_id: API key UUID to delete

        Returns:
            True if deleted, False if not found

        Side effects:
            - Cascades to api_key_scopes (FK constraint)
            - Cascades to api_key_custom_limits (FK constraint)

        Example:
            >>> deleted = repo.delete("123e4567-e89b-12d3-a456-426614174000")
        """
        pass

    @abstractmethod
    def get_available_scopes(self) -> List[dict]:
        """
        Get all available scopes from api_permission_scopes catalog.

        This is used to:
            - Populate UI dropdowns
            - Validate scope codes
            - Display scope descriptions

        Returns:
            List of dicts with keys:
                - id: Scope ID (int)
                - code: Scope code (str, e.g., "documents:read")
                - name: Display name (str, e.g., "Read Documents")
                - description: Detailed description (str, optional)
                - category: Scope category (str, optional, e.g., "documents")

        Filter:
            Only include is_active=True scopes

        Example:
            >>> scopes = repo.get_available_scopes()
            >>> for scope in scopes:
            ...     print(f"{scope['code']}: {scope['name']}")
            documents:read: Read Documents
            documents:write: Write Documents
        """
        pass

    @abstractmethod
    def scope_exists(self, scope_code: str) -> bool:
        """
        Check if scope code exists in catalog.

        Args:
            scope_code: Scope code string (e.g., "documents:read")

        Returns:
            True if scope exists and is active, False otherwise

        Example:
            >>> repo.scope_exists("documents:read")
            True
            >>> repo.scope_exists("invalid:scope")
            False
        """
        pass
