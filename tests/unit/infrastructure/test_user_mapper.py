"""Unit tests for UserMapper.

Tests the bidirectional mapping between domain entities and database models.
"""
import pytest
from datetime import datetime
from uuid import UUID
from unittest.mock import Mock

from domain.entities.user import User as DomainUser
from domain.value_objects.user_id import UserId
from domain.value_objects.email import Email
from domain.value_objects.hashed_password import HashedPassword
from infrastructure.database.mappers.user_mapper import UserMapper


def create_mock_db_user(
    id: UUID,
    email: str,
    password_hash: str,
    email_verified: bool,
    is_active: bool,
    created_at: datetime,
    updated_at: datetime,
    last_login_at: datetime | None = None
) -> Mock:
    """Create a mock database user for testing."""
    mock_user = Mock()
    mock_user.id = id
    mock_user.email = email
    mock_user.password_hash = password_hash
    mock_user.email_verified = email_verified
    mock_user.is_active = is_active
    mock_user.created_at = created_at
    mock_user.updated_at = updated_at
    mock_user.last_login_at = last_login_at
    return mock_user


@pytest.mark.unit
class TestUserMapperToDomain:
    """Tests for UserMapper.to_domain() method."""

    def test_to_domain_converts_db_user_to_domain_user(self):
        """to_domain() should convert database model to domain entity."""
        # Arrange
        db_user = create_mock_db_user(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8fW.lQ4F9y",
            email_verified=True,
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 2, 12, 0, 0),
            last_login_at=datetime(2024, 1, 3, 12, 0, 0)
        )

        # Act
        domain_user = UserMapper.to_domain(db_user)

        # Assert
        assert isinstance(domain_user, DomainUser)
        assert str(domain_user.id.value) == "550e8400-e29b-41d4-a716-446655440000"
        assert str(domain_user.email) == "test@example.com"
        assert domain_user.email_verified is True
        assert domain_user.is_active is True

    def test_to_domain_converts_value_objects_correctly(self):
        """to_domain() should create proper value objects."""
        # Arrange
        db_user = create_mock_db_user(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="user@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8fW.lQ4F9y",
            email_verified=False,
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
            last_login_at=None
        )

        # Act
        domain_user = UserMapper.to_domain(db_user)

        # Assert
        assert isinstance(domain_user.id, UserId)
        assert isinstance(domain_user.email, Email)
        assert isinstance(domain_user.password, HashedPassword)
        assert domain_user.password.hash_value.startswith("$2b$")

    def test_to_domain_handles_null_last_login(self):
        """to_domain() should handle None for last_login_at."""
        # Arrange
        db_user = create_mock_db_user(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="new@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8fW.lQ4F9y",
            email_verified=False,
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
            last_login_at=None
        )

        # Act
        domain_user = UserMapper.to_domain(db_user)

        # Assert
        assert domain_user.last_login_at is None

    def test_to_domain_preserves_timestamps(self):
        """to_domain() should preserve all timestamp values."""
        # Arrange
        created = datetime(2024, 1, 1, 10, 30, 0)
        updated = datetime(2024, 1, 5, 15, 45, 0)
        last_login = datetime(2024, 1, 10, 8, 20, 0)

        db_user = create_mock_db_user(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8fW.lQ4F9y",
            email_verified=True,
            is_active=True,
            created_at=created,
            updated_at=updated,
            last_login_at=last_login
        )

        # Act
        domain_user = UserMapper.to_domain(db_user)

        # Assert
        assert domain_user.created_at == created
        assert domain_user.updated_at == updated
        assert domain_user.last_login_at == last_login

    def test_to_domain_normalizes_email_to_lowercase(self):
        """to_domain() should normalize email through Email value object."""
        # Arrange
        db_user = create_mock_db_user(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="USER@EXAMPLE.COM",  # Uppercase in database
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8fW.lQ4F9y",
            email_verified=False,
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
            last_login_at=None
        )

        # Act
        domain_user = UserMapper.to_domain(db_user)

        # Assert
        assert str(domain_user.email) == "user@example.com"  # Normalized to lowercase
