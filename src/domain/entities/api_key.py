"""API Key domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

from ..value_objects.user_id import UserId
from ..value_objects.api_key_value import APIKeyValue
from ..value_objects.api_key_hash import APIKeyHash
from ..value_objects.scope_code import ScopeCode


@dataclass
class APIKey:
    """
    API Key entity - Programmatic access token.

    API keys provide an alternative to JWT authentication for machine-to-machine
    communication and programmatic access to the VerifyID API.

    Security model:
        - key_value: Only returned ONCE on creation (never persisted)
        - key_hash: Stored in database (SHA-256)
        - key_prefix: First 12 chars for display (e.g., 'vfy_abc123...')
        - scopes: List of granular permissions

    Lifecycle:
        1. Created with scopes and optional expiration
        2. Validated on each API request
        3. Can be revoked at any time
        4. Automatically expires if expires_at is set

    Business Rules:
        - Must have at least one scope
        - Once revoked, cannot be un-revoked
        - Expired keys are invalid
        - Inactive keys are invalid
    """

    id: str  # UUID as string
    user_id: UserId
    key_hash: APIKeyHash
    key_prefix: str  # For display (e.g., 'vfy_abc123...')
    scopes: List[ScopeCode]
    is_active: bool = True
    name: Optional[str] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity invariants."""
        if not self.scopes:
            raise ValueError("API key must have at least one scope")

        # Ensure all scopes are ScopeCode instances
        if not all(isinstance(s, ScopeCode) for s in self.scopes):
            raise TypeError("All scopes must be ScopeCode instances")

    @classmethod
    def create(
        cls,
        user_id: UserId,
        name: str,
        scopes: List[str],
        expires_in_days: Optional[int] = None,
    ) -> tuple["APIKey", APIKeyValue]:
        """
        Create new API key.

        This is the ONLY way to obtain the plaintext API key value.
        After this method returns, the plaintext key will never be accessible again.

        Args:
            user_id: Owner user ID
            name: Key name/description (e.g., "Production Server", "CI/CD Pipeline")
            scopes: List of scope codes (strings like "documents:read")
            expires_in_days: Optional expiration in days (None = never expires)

        Returns:
            Tuple of:
                - APIKey entity (with hash, ready to persist)
                - APIKeyValue (plaintext key - SHOW TO USER IMMEDIATELY)

        Raises:
            ValueError: If scopes list is empty or invalid

        Security:
            The returned APIKeyValue must be shown to the user immediately
            and then discarded. It will never be shown again.

        Example:
            >>> api_key, plaintext_key = APIKey.create(
            ...     user_id=UserId.from_string("123e4567-e89b-12d3-a456-426614174000"),
            ...     name="Production API Key",
            ...     scopes=["documents:read", "documents:write"],
            ...     expires_in_days=365
            ... )
            >>> print(f"Save this key: {plaintext_key}")  # Show to user
            >>> # Persist api_key entity to database
            >>> # plaintext_key is now discarded
        """
        if not scopes:
            raise ValueError("At least one scope is required")

        # Generate random API key
        key_value = APIKeyValue.generate()

        # Hash the key for storage
        key_hash = APIKeyHash.from_key(str(key_value))

        # Parse scopes to ScopeCode objects
        scope_objects = ScopeCode.from_strings(scopes)

        # Calculate expiration if specified
        expires_at = None
        if expires_in_days is not None:
            if expires_in_days <= 0:
                raise ValueError("expires_in_days must be positive")
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        # Create entity
        api_key = cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_value.prefix,
            name=name,
            scopes=scope_objects,
            is_active=True,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )

        return api_key, key_value

    def is_valid(self) -> bool:
        """
        Check if API key is valid for use.

        An API key is valid if ALL of the following are true:
            1. is_active = True
            2. revoked_at is None (not revoked)
            3. expires_at is None OR > now (not expired)

        Returns:
            True if key is valid, False otherwise

        Example:
            >>> api_key, _ = APIKey.create(...)
            >>> api_key.is_valid()
            True
            >>> api_key.revoke()
            >>> api_key.is_valid()
            False
        """
        # Check active flag
        if not self.is_active:
            return False

        # Check not revoked
        if self.revoked_at is not None:
            return False

        # Check not expired
        if self.expires_at is not None:
            now = datetime.now(timezone.utc)
            # Handle timezone-naive datetimes from database
            expires_at_aware = (
                self.expires_at.replace(tzinfo=timezone.utc)
                if self.expires_at.tzinfo is None
                else self.expires_at
            )
            if expires_at_aware <= now:
                return False

        return True

    def has_scope(self, required_scope: str) -> bool:
        """
        Check if key has required scope.

        Supports wildcard matching:
            - "admin:all" matches any scope
            - "documents:all" matches "documents:read", "documents:write", etc.

        Args:
            required_scope: Scope code string (e.g., "documents:read")

        Returns:
            True if key has the required scope

        Example:
            >>> api_key, _ = APIKey.create(
            ...     user_id=user_id,
            ...     name="Test Key",
            ...     scopes=["documents:read", "documents:write"]
            ... )
            >>> api_key.has_scope("documents:read")
            True
            >>> api_key.has_scope("admin:all")
            False
        """
        required = ScopeCode.from_string(required_scope)
        return any(scope.matches(required) for scope in self.scopes)

    def has_scopes(self, required_scopes: List[str]) -> bool:
        """
        Check if key has ALL required scopes.

        Args:
            required_scopes: List of scope codes (e.g., ["documents:read", "users:read"])

        Returns:
            True if key has ALL required scopes

        Example:
            >>> api_key, _ = APIKey.create(
            ...     user_id=user_id,
            ...     name="Test Key",
            ...     scopes=["documents:read", "documents:write"]
            ... )
            >>> api_key.has_scopes(["documents:read", "documents:write"])
            True
            >>> api_key.has_scopes(["documents:read", "admin:all"])
            False
        """
        return all(self.has_scope(scope) for scope in required_scopes)

    def revoke(self) -> None:
        """
        Revoke API key (soft delete).

        A revoked key:
            - is_active = False
            - revoked_at = current timestamp
            - Cannot be un-revoked (immutable operation)
            - Will fail all future validations

        Example:
            >>> api_key, _ = APIKey.create(...)
            >>> api_key.revoke()
            >>> api_key.is_valid()
            False
            >>> api_key.revoked_at is not None
            True
        """
        self.is_active = False
        self.revoked_at = datetime.now(timezone.utc)

    def record_usage(self) -> None:
        """
        Record that the API key was used.

        Updates last_used_at timestamp for analytics and monitoring.

        Example:
            >>> api_key, _ = APIKey.create(...)
            >>> api_key.record_usage()
            >>> api_key.last_used_at is not None
            True
        """
        self.last_used_at = datetime.now(timezone.utc)

    def get_scope_codes(self) -> List[str]:
        """
        Get list of scope code strings.

        Returns:
            List of scope strings (e.g., ["documents:read", "documents:write"])

        Example:
            >>> api_key, _ = APIKey.create(
            ...     user_id=user_id,
            ...     name="Test Key",
            ...     scopes=["documents:read"]
            ... )
            >>> api_key.get_scope_codes()
            ['documents:read']
        """
        return [str(scope) for scope in self.scopes]

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        status = "valid" if self.is_valid() else "invalid"
        return (
            f"APIKey(id={self.id[:8]}..., "
            f"prefix={self.key_prefix}, "
            f"user_id={self.user_id}, "
            f"scopes={len(self.scopes)}, "
            f"status={status})"
        )
