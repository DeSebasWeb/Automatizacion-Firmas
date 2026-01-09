"""API Key repository implementation."""

import structlog
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.domain.repositories.api_key_repository import IAPIKeyRepository
from src.domain.entities.api_key import APIKey as DomainAPIKey
from src.domain.value_objects.user_id import UserId
from src.domain.value_objects.api_key_hash import APIKeyHash
from src.infrastructure.database.models.api_key import APIKey as DBAPIKey
from src.infrastructure.database.models.api_key_scope import APIKeyScope
from src.infrastructure.database.models.api_permission_scope import APIPermissionScope
from src.infrastructure.database.mappers.api_key_mapper import APIKeyMapper

logger = structlog.get_logger(__name__)


class APIKeyRepository(IAPIKeyRepository):
    """
    SQLAlchemy implementation of IAPIKeyRepository.

    Handles persistence of API keys with their scopes (many-to-many relationship).

    Performance optimizations:
        - Uses joinedload for eager loading scopes (prevents N+1)
        - Indexes on key_hash, user_id, expires_at
        - Atomic transactions for create operations

    Security:
        - Only stores key hashes, never plaintext
        - Validates scope codes exist before creating relationships
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self._session = session
        self._mapper = APIKeyMapper()

    def create(self, api_key: DomainAPIKey, scope_codes: List[str]) -> DomainAPIKey:
        """
        Create API key with scopes.

        This is an atomic operation:
            1. Validate all scope codes exist
            2. Insert api_keys record
            3. Create api_key_scopes relationships
            4. Commit transaction

        Args:
            api_key: Domain APIKey entity
            scope_codes: List of scope code strings

        Returns:
            Created APIKey entity

        Raises:
            ValueError: If any scope code doesn't exist
            SQLAlchemyError: If database operation fails

        Example:
            >>> api_key, plaintext = APIKey.create(...)
            >>> created = repo.create(api_key, ["documents:read"])
        """
        logger.info(
            "Creating API key",
            api_key_id=api_key.id,
            user_id=str(api_key.user_id),
            scope_count=len(scope_codes),
        )

        # Step 1: Validate all scope codes exist
        scope_map = self._get_scope_id_map(scope_codes)
        missing_scopes = [code for code in scope_codes if code not in scope_map]
        if missing_scopes:
            logger.error(
                "Invalid scope codes",
                missing_scopes=missing_scopes,
                available_scopes=list(scope_map.keys()),
            )
            raise ValueError(
                f"Invalid scope codes: {missing_scopes}. "
                f"Available scopes: {list(scope_map.keys())}"
            )

        # Step 2: Convert domain entity to DB model
        db_api_key = self._mapper.to_persistence(api_key)

        # Step 3: Add to session
        self._session.add(db_api_key)
        self._session.flush()  # Generate ID if needed

        # Step 4: Create api_key_scopes relationships
        for scope_code in scope_codes:
            scope_id = scope_map[scope_code]
            api_key_scope = APIKeyScope(
                api_key_id=db_api_key.id,
                scope_id=scope_id,
            )
            self._session.add(api_key_scope)

        self._session.flush()

        logger.info(
            "API key created successfully",
            api_key_id=api_key.id,
            key_prefix=api_key.key_prefix,
            scopes=scope_codes,
        )

        # Step 5: Reload with scopes to return complete entity
        db_api_key_with_scopes = (
            self._session.query(DBAPIKey)
            .options(joinedload(DBAPIKey.scopes).joinedload(APIKeyScope.scope))
            .filter(DBAPIKey.id == db_api_key.id)
            .one()
        )

        return self._mapper.to_domain(db_api_key_with_scopes)

    def find_by_hash(self, key_hash: APIKeyHash) -> Optional[DomainAPIKey]:
        """
        Find API key by hash (authentication lookup).

        Performance: This is the hot path for API authentication.
            - key_hash column is indexed
            - Scopes are eagerly loaded
            - Should complete in <10ms

        Args:
            key_hash: Hashed API key

        Returns:
            APIKey entity if found, None otherwise

        Example:
            >>> key_hash = APIKeyHash.from_key("vfy_abc123...")
            >>> api_key = repo.find_by_hash(key_hash)
        """
        logger.debug("Looking up API key by hash", hash_prefix=str(key_hash)[:16])

        stmt = (
            select(DBAPIKey)
            .options(joinedload(DBAPIKey.scopes).joinedload(APIKeyScope.scope))
            .where(DBAPIKey.key_hash == str(key_hash))
        )

        result = self._session.execute(stmt).unique()
        db_api_key = result.scalar_one_or_none()

        if db_api_key is None:
            logger.debug("API key not found by hash")
            return None

        logger.debug(
            "API key found",
            api_key_id=str(db_api_key.id),
            user_id=str(db_api_key.user_id),
            is_valid=db_api_key.is_valid,
        )

        return self._mapper.to_domain(db_api_key)

    def find_by_id(self, api_key_id: str) -> Optional[DomainAPIKey]:
        """
        Find API key by ID.

        Args:
            api_key_id: API key UUID as string

        Returns:
            APIKey entity if found, None otherwise

        Example:
            >>> api_key = repo.find_by_id("123e4567-...")
        """
        logger.debug("Looking up API key by ID", api_key_id=api_key_id)

        stmt = (
            select(DBAPIKey)
            .options(joinedload(DBAPIKey.scopes).joinedload(APIKeyScope.scope))
            .where(DBAPIKey.id == api_key_id)
        )

        result = self._session.execute(stmt).unique()
        db_api_key = result.scalar_one_or_none()

        if db_api_key is None:
            logger.debug("API key not found by ID", api_key_id=api_key_id)
            return None

        return self._mapper.to_domain(db_api_key)

    def find_by_user_id(self, user_id: UserId) -> List[DomainAPIKey]:
        """
        List all API keys for user (active and revoked).

        Args:
            user_id: User ID

        Returns:
            List of API keys (ordered by created_at DESC)

        Example:
            >>> keys = repo.find_by_user_id(user_id)
        """
        logger.debug("Listing API keys for user", user_id=str(user_id))

        stmt = (
            select(DBAPIKey)
            .options(joinedload(DBAPIKey.scopes).joinedload(APIKeyScope.scope))
            .where(DBAPIKey.user_id == user_id.value)
            .order_by(DBAPIKey.created_at.desc())
        )

        result = self._session.execute(stmt).unique()
        db_api_keys = result.scalars().all()

        logger.debug(
            "Found API keys for user",
            user_id=str(user_id),
            count=len(db_api_keys),
        )

        return self._mapper.to_domain_list(db_api_keys)

    def find_active_by_user_id(self, user_id: UserId) -> List[DomainAPIKey]:
        """
        List only active API keys for user.

        Filters:
            - is_active = True
            - revoked_at IS NULL

        Args:
            user_id: User ID

        Returns:
            List of active API keys (ordered by created_at DESC)

        Example:
            >>> active_keys = repo.find_active_by_user_id(user_id)
        """
        logger.debug("Listing active API keys for user", user_id=str(user_id))

        stmt = (
            select(DBAPIKey)
            .options(joinedload(DBAPIKey.scopes).joinedload(APIKeyScope.scope))
            .where(
                DBAPIKey.user_id == user_id.value,
                DBAPIKey.is_active == True,  # noqa: E712
                DBAPIKey.revoked_at.is_(None),
            )
            .order_by(DBAPIKey.created_at.desc())
        )

        result = self._session.execute(stmt).unique()
        db_api_keys = result.scalars().all()

        logger.debug(
            "Found active API keys for user",
            user_id=str(user_id),
            count=len(db_api_keys),
        )

        return self._mapper.to_domain_list(db_api_keys)

    def update(self, api_key: DomainAPIKey) -> DomainAPIKey:
        """
        Update API key (revoke, record usage, etc.).

        Note:
            Scopes are NOT updated (immutable after creation).

        Args:
            api_key: Domain entity with updated fields

        Returns:
            Updated APIKey entity

        Example:
            >>> api_key.revoke()
            >>> repo.update(api_key)
        """
        logger.info(
            "Updating API key",
            api_key_id=api_key.id,
            is_active=api_key.is_active,
            revoked=api_key.revoked_at is not None,
        )

        # Get existing DB record
        db_api_key = self._session.query(DBAPIKey).filter(DBAPIKey.id == api_key.id).one()

        # Update fields (except scopes)
        db_api_key.is_active = api_key.is_active
        db_api_key.last_used_at = (
            api_key.last_used_at.replace(tzinfo=None)
            if api_key.last_used_at and api_key.last_used_at.tzinfo
            else api_key.last_used_at
        )
        db_api_key.revoked_at = (
            api_key.revoked_at.replace(tzinfo=None)
            if api_key.revoked_at and api_key.revoked_at.tzinfo
            else api_key.revoked_at
        )

        self._session.flush()

        logger.info("API key updated successfully", api_key_id=api_key.id)

        # Reload with scopes
        db_api_key_with_scopes = (
            self._session.query(DBAPIKey)
            .options(joinedload(DBAPIKey.scopes).joinedload(APIKeyScope.scope))
            .filter(DBAPIKey.id == db_api_key.id)
            .one()
        )

        return self._mapper.to_domain(db_api_key_with_scopes)

    def delete(self, api_key_id: str) -> bool:
        """
        Permanently delete API key (HARD DELETE).

        Warning: Use revoke() instead for normal operations.

        Args:
            api_key_id: API key UUID

        Returns:
            True if deleted, False if not found

        Example:
            >>> deleted = repo.delete("123e4567-...")
        """
        logger.warning("Hard deleting API key", api_key_id=api_key_id)

        db_api_key = self._session.query(DBAPIKey).filter(DBAPIKey.id == api_key_id).first()

        if db_api_key is None:
            logger.debug("API key not found for deletion", api_key_id=api_key_id)
            return False

        self._session.delete(db_api_key)
        self._session.flush()

        logger.info("API key deleted permanently", api_key_id=api_key_id)
        return True

    def get_available_scopes(self) -> List[dict]:
        """
        Get all available scopes from catalog.

        Returns:
            List of scope dicts with id, code, name, description, category

        Example:
            >>> scopes = repo.get_available_scopes()
        """
        logger.debug("Fetching available scopes")

        stmt = (
            select(APIPermissionScope)
            .where(APIPermissionScope.is_active == True)  # noqa: E712
            .order_by(APIPermissionScope.category, APIPermissionScope.code)
        )

        result = self._session.execute(stmt)
        scopes = result.scalars().all()

        scope_dicts = [
            {
                "id": scope.id,
                "code": scope.code,
                "name": scope.name,
                "description": scope.description,
                "category": scope.category,
            }
            for scope in scopes
        ]

        logger.debug("Available scopes fetched", count=len(scope_dicts))
        return scope_dicts

    def scope_exists(self, scope_code: str) -> bool:
        """
        Check if scope code exists in catalog.

        Args:
            scope_code: Scope code string

        Returns:
            True if exists and is active

        Example:
            >>> repo.scope_exists("documents:read")
            True
        """
        stmt = select(APIPermissionScope).where(
            APIPermissionScope.code == scope_code,
            APIPermissionScope.is_active == True,  # noqa: E712
        )

        result = self._session.execute(stmt)
        scope = result.scalar_one_or_none()

        return scope is not None

    # Private helper methods

    def _get_scope_id_map(self, scope_codes: List[str]) -> dict[str, int]:
        """
        Get mapping of scope codes to IDs.

        Args:
            scope_codes: List of scope code strings

        Returns:
            Dict mapping scope code -> scope ID

        Example:
            >>> repo._get_scope_id_map(["documents:read", "documents:write"])
            {'documents:read': 1, 'documents:write': 2}
        """
        stmt = select(APIPermissionScope).where(
            APIPermissionScope.code.in_(scope_codes),
            APIPermissionScope.is_active == True,  # noqa: E712
        )

        result = self._session.execute(stmt)
        scopes = result.scalars().all()

        return {scope.code: scope.id for scope in scopes}
