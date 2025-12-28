"""Unit tests for UserMapper.to_persistence() method.

Tests the conversion from domain entities to database models.
"""
import pytest
from datetime import datetime
from uuid import UUID
from unittest.mock import Mock, patch

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
class TestUserMapperToPersistence:
    """Tests for UserMapper.to_persistence() method."""

    @patch('infrastructure.database.mappers.user_mapper.DBUser')
    def test_to_persistence_converts_domain_to_db_model(self, mock_db_user_class):
        """to_persistence() should convert domain entity to database model."""
        # Arrange
        domain_user = DomainUser.create(
            email=Email.from_string("test@example.com"),
            plain_password="SecurePass123"
        )

        mock_db_instance = Mock()
        mock_db_user_class.return_value = mock_db_instance

        # Act
        db_user = UserMapper.to_persistence(domain_user)

        # Assert
        mock_db_user_class.assert_called_once()
        call_kwargs = mock_db_user_class.call_args.kwargs

        assert call_kwargs['id'] == domain_user.id.value
        assert call_kwargs['email'] == str(domain_user.email)
        assert call_kwargs['password_hash'] == domain_user.password.hash_value
        assert call_kwargs['email_verified'] == domain_user.email_verified
        assert call_kwargs['is_active'] == domain_user.is_active

    @patch('infrastructure.database.mappers.user_mapper.DBUser')
    def test_to_persistence_extracts_primitives_from_value_objects(self, mock_db_user_class):
        """to_persistence() should extract primitive values from value objects."""
        # Arrange
        user_id = UserId.generate()
        email = Email.from_string("user@test.com")
        password = HashedPassword.from_plain_text("MyPassword123")

        domain_user = DomainUser(
            id=user_id,
            email=email,
            password=password,
            email_verified=True,
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 2, 12, 0, 0),
            last_login_at=None
        )

        mock_db_instance = Mock()
        mock_db_user_class.return_value = mock_db_instance

        # Act
        db_user = UserMapper.to_persistence(domain_user)

        # Assert
        call_kwargs = mock_db_user_class.call_args.kwargs

        assert isinstance(call_kwargs['id'], UUID)  # UUID primitive, not UserId
        assert isinstance(call_kwargs['email'], str)  # String primitive, not Email
        assert isinstance(call_kwargs['password_hash'], str)  # String hash, not HashedPassword
        assert call_kwargs['password_hash'].startswith("$2b$")

    @patch('infrastructure.database.mappers.user_mapper.DBUser')
    def test_to_persistence_preserves_all_timestamps(self, mock_db_user_class):
        """to_persistence() should preserve all timestamp values."""
        # Arrange
        created = datetime(2024, 1, 1, 10, 30, 0)
        updated = datetime(2024, 1, 5, 15, 45, 0)
        last_login = datetime(2024, 1, 10, 8, 20, 0)

        domain_user = DomainUser(
            id=UserId.generate(),
            email=Email.from_string("test@example.com"),
            password=HashedPassword.from_plain_text("SecurePass123"),
            email_verified=True,
            is_active=True,
            created_at=created,
            updated_at=updated,
            last_login_at=last_login
        )

        mock_db_instance = Mock()
        mock_db_user_class.return_value = mock_db_instance

        # Act
        db_user = UserMapper.to_persistence(domain_user)

        # Assert
        call_kwargs = mock_db_user_class.call_args.kwargs

        assert call_kwargs['created_at'] == created
        assert call_kwargs['updated_at'] == updated
        assert call_kwargs['last_login_at'] == last_login

    @patch('infrastructure.database.mappers.user_mapper.DBUser')
    def test_to_persistence_handles_none_last_login(self, mock_db_user_class):
        """to_persistence() should handle None for last_login_at."""
        # Arrange
        domain_user = DomainUser.create(
            email=Email.from_string("new@example.com"),
            plain_password="Password123"
        )
        # User.create() sets last_login_at to None by default

        mock_db_instance = Mock()
        mock_db_user_class.return_value = mock_db_instance

        # Act
        db_user = UserMapper.to_persistence(domain_user)

        # Assert
        call_kwargs = mock_db_user_class.call_args.kwargs
        assert call_kwargs['last_login_at'] is None

    @patch('infrastructure.database.mappers.user_mapper.DBUser')
    def test_to_persistence_round_trip_consistency(self, mock_db_user_class):
        """to_persistence() followed by to_domain() should preserve data."""
        # Arrange
        original_domain_user = DomainUser(
            id=UserId.from_string("550e8400-e29b-41d4-a716-446655440000"),
            email=Email.from_string("roundtrip@test.com"),
            password=HashedPassword.from_hash("$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8fW.lQ4F9y"),
            email_verified=True,
            is_active=False,  # Deactivated user
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 10, 14, 30, 0),
            last_login_at=datetime(2024, 1, 8, 9, 15, 0)
        )

        # Create a mock DB user with the same data that to_persistence would create
        mock_db_user = create_mock_db_user(
            id=original_domain_user.id.value,
            email=str(original_domain_user.email),
            password_hash=original_domain_user.password.hash_value,
            email_verified=original_domain_user.email_verified,
            is_active=original_domain_user.is_active,
            created_at=original_domain_user.created_at,
            updated_at=original_domain_user.updated_at,
            last_login_at=original_domain_user.last_login_at
        )
        mock_db_user_class.return_value = mock_db_user

        # Act - Round trip: domain → persistence → domain
        db_user = UserMapper.to_persistence(original_domain_user)
        reconstructed_domain_user = UserMapper.to_domain(db_user)

        # Assert - All fields should match
        assert reconstructed_domain_user.id == original_domain_user.id
        assert reconstructed_domain_user.email == original_domain_user.email
        assert reconstructed_domain_user.password.hash_value == original_domain_user.password.hash_value
        assert reconstructed_domain_user.email_verified == original_domain_user.email_verified
        assert reconstructed_domain_user.is_active == original_domain_user.is_active
        assert reconstructed_domain_user.created_at == original_domain_user.created_at
        assert reconstructed_domain_user.updated_at == original_domain_user.updated_at
        assert reconstructed_domain_user.last_login_at == original_domain_user.last_login_at
