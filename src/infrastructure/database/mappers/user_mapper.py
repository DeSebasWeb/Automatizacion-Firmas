"""User entity mapper - Domain ↔ Persistence."""
from domain.entities.user import User as DomainUser
from domain.value_objects.user_id import UserId
from domain.value_objects.email import Email
from domain.value_objects.hashed_password import HashedPassword
from ..models.user import User as DBUser


class UserMapper:
    """
    Maps between domain User entity and database User model.

    Responsibilities:
    - Convert domain entities to database models
    - Convert database models to domain entities
    - Handle Value Object ↔ primitive type conversions

    No business logic - only translation.
    """

    @staticmethod
    def to_domain(db_user: DBUser) -> DomainUser:
        """
        Convert database model to domain entity.

        Args:
            db_user: SQLAlchemy User model

        Returns:
            Domain User entity

        Raises:
            ValueError: If data is invalid
        """
        return DomainUser(
            id=UserId.from_string(str(db_user.id)),
            email=Email.from_string(db_user.email),
            password=HashedPassword.from_hash(db_user.password_hash),
            email_verified=db_user.email_verified,
            is_active=db_user.is_active,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            last_login_at=db_user.last_login_at
        )

    @staticmethod
    def to_persistence(domain_user: DomainUser) -> DBUser:
        """
        Convert domain entity to database model.

        IMPORTANT: For new users created with User.create(), the id will be
        a generated UUID from the domain layer. For database-generated timestamps,
        created_at and updated_at should be set by the DB on INSERT if None.

        Args:
            domain_user: Domain User entity

        Returns:
            SQLAlchemy User model
        """
        return DBUser(
            id=domain_user.id.value,
            email=str(domain_user.email),
            password_hash=domain_user.password.hash_value,
            email_verified=domain_user.email_verified,
            is_active=domain_user.is_active,
            # NOTE: We pass timestamps to preserve domain entity state
            # SQLAlchemy will use these values if provided, or DB defaults if None
            created_at=domain_user.created_at,
            updated_at=domain_user.updated_at,
            last_login_at=domain_user.last_login_at
        )

    @staticmethod
    def update_db_from_domain(db_user: DBUser, domain_user: DomainUser) -> DBUser:
        """
        Update database model with data from domain entity.

        Useful for update operations - modifies existing db_user.

        IMPORTANT:
        - ID is NOT updated (immutable primary key)
        - created_at is NOT updated (immutable creation timestamp)
        - All other fields are synchronized from domain entity

        Args:
            db_user: Existing SQLAlchemy model (will be modified in-place)
            domain_user: Domain entity with new data

        Returns:
            Updated database model (same instance as db_user parameter)
        """
        # Update mutable fields only (ID and created_at are immutable)
        db_user.email = str(domain_user.email)
        db_user.password_hash = domain_user.password.hash_value
        db_user.email_verified = domain_user.email_verified
        db_user.is_active = domain_user.is_active
        db_user.updated_at = domain_user.updated_at
        db_user.last_login_at = domain_user.last_login_at

        return db_user
