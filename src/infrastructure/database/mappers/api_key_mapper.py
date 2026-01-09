"""API Key mapper - Domain ↔ Persistence."""

from datetime import timezone
from typing import List
from uuid import UUID

from src.domain.entities.api_key import APIKey as DomainAPIKey
from src.domain.value_objects.user_id import UserId
from src.domain.value_objects.api_key_hash import APIKeyHash
from src.domain.value_objects.scope_code import ScopeCode
from src.infrastructure.database.models.api_key import APIKey as DBAPIKey


class APIKeyMapper:
    """
    Maps between domain APIKey entity and database APIKey model.

    Responsibilities:
        - Convert DB models to domain entities (with scopes)
        - Convert domain entities to DB models
        - Handle timezone conversions
        - Extract scopes from relationships

    Design notes:
        - Scopes are loaded via SQLAlchemy relationships
        - All datetime values are made timezone-aware (UTC)
        - Mapper is stateless (pure functions)
    """

    @staticmethod
    def to_domain(db_api_key: DBAPIKey) -> DomainAPIKey:
        """
        Convert database model to domain entity.

        Must include scopes from api_key_scopes relationship.

        Args:
            db_api_key: SQLAlchemy APIKey model instance
                (must have scopes relationship loaded)

        Returns:
            Domain APIKey entity

        Raises:
            ValueError: If required relationships are not loaded

        Example:
            >>> db_key = session.query(DBAPIKey).options(
            ...     joinedload(DBAPIKey.scopes)
            ... ).first()
            >>> domain_key = APIKeyMapper.to_domain(db_key)
        """
        # Extract scope codes from relationship
        # db_api_key.scopes -> List[APIKeyScope]
        # Each APIKeyScope has .scope -> APIPermissionScope
        # APIPermissionScope has .code -> str
        scope_codes: List[ScopeCode] = []
        if hasattr(db_api_key, "scopes") and db_api_key.scopes is not None:
            for api_key_scope in db_api_key.scopes:
                if api_key_scope.scope is not None:
                    scope_code = ScopeCode.from_string(api_key_scope.scope.code)
                    scope_codes.append(scope_code)

        if not scope_codes:
            raise ValueError(
                f"API key {db_api_key.id} has no scopes. "
                "Ensure scopes relationship is loaded with joinedload."
            )

        # Convert datetime fields to timezone-aware
        created_at_aware = (
            db_api_key.created_at.replace(tzinfo=timezone.utc)
            if db_api_key.created_at and db_api_key.created_at.tzinfo is None
            else db_api_key.created_at
        )

        last_used_at_aware = None
        if db_api_key.last_used_at:
            last_used_at_aware = (
                db_api_key.last_used_at.replace(tzinfo=timezone.utc)
                if db_api_key.last_used_at.tzinfo is None
                else db_api_key.last_used_at
            )

        expires_at_aware = None
        if db_api_key.expires_at:
            expires_at_aware = (
                db_api_key.expires_at.replace(tzinfo=timezone.utc)
                if db_api_key.expires_at.tzinfo is None
                else db_api_key.expires_at
            )

        revoked_at_aware = None
        if db_api_key.revoked_at:
            revoked_at_aware = (
                db_api_key.revoked_at.replace(tzinfo=timezone.utc)
                if db_api_key.revoked_at.tzinfo is None
                else db_api_key.revoked_at
            )

        # Create domain entity
        return DomainAPIKey(
            id=str(db_api_key.id),
            user_id=UserId.from_string(str(db_api_key.user_id)),
            key_hash=APIKeyHash.from_string(db_api_key.key_hash),
            key_prefix=db_api_key.key_prefix,
            name=db_api_key.name,
            scopes=scope_codes,
            is_active=db_api_key.is_active,
            last_used_at=last_used_at_aware,
            expires_at=expires_at_aware,
            created_at=created_at_aware,
            revoked_at=revoked_at_aware,
        )

    @staticmethod
    def to_persistence(domain_api_key: DomainAPIKey) -> DBAPIKey:
        """
        Convert domain entity to database model.

        Note:
            Scopes are handled separately via api_key_scopes table.
            This method only maps the main api_keys table fields.

        Args:
            domain_api_key: Domain APIKey entity

        Returns:
            SQLAlchemy APIKey model instance (without scopes relationship)

        Example:
            >>> api_key, _ = APIKey.create(...)
            >>> db_key = APIKeyMapper.to_persistence(api_key)
            >>> session.add(db_key)
            >>> # Scopes handled separately in repository
        """
        # Convert datetime to timezone-naive for database
        # PostgreSQL stores as timezone-naive, application handles timezone
        created_at_naive = (
            domain_api_key.created_at.replace(tzinfo=None)
            if domain_api_key.created_at and domain_api_key.created_at.tzinfo
            else domain_api_key.created_at
        )

        last_used_at_naive = None
        if domain_api_key.last_used_at:
            last_used_at_naive = (
                domain_api_key.last_used_at.replace(tzinfo=None)
                if domain_api_key.last_used_at.tzinfo
                else domain_api_key.last_used_at
            )

        expires_at_naive = None
        if domain_api_key.expires_at:
            expires_at_naive = (
                domain_api_key.expires_at.replace(tzinfo=None)
                if domain_api_key.expires_at.tzinfo
                else domain_api_key.expires_at
            )

        revoked_at_naive = None
        if domain_api_key.revoked_at:
            revoked_at_naive = (
                domain_api_key.revoked_at.replace(tzinfo=None)
                if domain_api_key.revoked_at.tzinfo
                else domain_api_key.revoked_at
            )

        return DBAPIKey(
            id=UUID(domain_api_key.id),  # Convert string to UUID object
            user_id=domain_api_key.user_id.value,  # Already UUID
            key_hash=str(domain_api_key.key_hash),
            key_prefix=domain_api_key.key_prefix,
            name=domain_api_key.name,
            is_active=domain_api_key.is_active,
            last_used_at=last_used_at_naive,
            expires_at=expires_at_naive,
            created_at=created_at_naive,
            revoked_at=revoked_at_naive,
        )

    @staticmethod
    def to_domain_list(db_api_keys: List[DBAPIKey]) -> List[DomainAPIKey]:
        """
        Convert list of DB models to domain entities.

        Args:
            db_api_keys: List of SQLAlchemy APIKey models

        Returns:
            List of domain APIKey entities

        Example:
            >>> db_keys = session.query(DBAPIKey).options(
            ...     joinedload(DBAPIKey.scopes)
            ... ).all()
            >>> domain_keys = APIKeyMapper.to_domain_list(db_keys)
        """
        return [APIKeyMapper.to_domain(db_key) for db_key in db_api_keys]
