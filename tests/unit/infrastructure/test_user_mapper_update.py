"""Unit tests for UserMapper.update_db_from_domain() method.

Tests the in-place update of database models from domain entities.
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
class TestUserMapperUpdate:
    """Tests for UserMapper.update_db_from_domain() method."""

    def test_update_db_from_domain_modifies_mutable_fields(self):
        """update_db_from_domain() should update mutable fields in-place."""
        # Arrange
        original_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        original_created_at = datetime(2024, 1, 1, 12, 0, 0)

        db_user = create_mock_db_user(
            id=original_id,
            email="old@example.com",
            password_hash="$2b$12$OldHashValue",
            email_verified=False,
            is_active=True,
            created_at=original_created_at,
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
            last_login_at=None
        )

        domain_user = DomainUser(
            id=UserId.from_string(str(original_id)),
            email=Email.from_string("new@example.com"),
            password=HashedPassword.from_hash("$2b$12$NewHashValue"),
            email_verified=True,
            is_active=True,
            created_at=original_created_at,  # Should NOT be updated
            updated_at=datetime(2024, 2, 1, 14, 30, 0),  # Should be updated
            last_login_at=datetime(2024, 1, 15, 10, 0, 0)
        )

        # Act
        result = UserMapper.update_db_from_domain(db_user, domain_user)

        # Assert
        assert result is db_user  # Same instance returned
        assert db_user.email == "new@example.com"
        assert db_user.password_hash == "$2b$12$NewHashValue"
        assert db_user.email_verified is True
        assert db_user.updated_at == datetime(2024, 2, 1, 14, 30, 0)
        assert db_user.last_login_at == datetime(2024, 1, 15, 10, 0, 0)

    def test_update_db_from_domain_preserves_immutable_fields(self):
        """update_db_from_domain() should NOT update id and created_at."""
        # Arrange
        original_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        original_created_at = datetime(2024, 1, 1, 12, 0, 0)

        db_user = create_mock_db_user(
            id=original_id,
            email="test@example.com",
            password_hash="$2b$12$OriginalHash",
            email_verified=False,
            is_active=True,
            created_at=original_created_at,
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
            last_login_at=None
        )

        # Domain user with different ID and created_at (should be ignored)
        different_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        different_created_at = datetime(2025, 1, 1, 12, 0, 0)

        domain_user = DomainUser(
            id=UserId.from_string(str(different_id)),
            email=Email.from_string("updated@example.com"),
            password=HashedPassword.from_hash("$2b$12$UpdatedHash"),
            email_verified=True,
            is_active=True,
            created_at=different_created_at,  # Different, should be ignored
            updated_at=datetime(2024, 2, 1, 14, 30, 0),
            last_login_at=None
        )

        # Act
        UserMapper.update_db_from_domain(db_user, domain_user)

        # Assert - Immutable fields should NOT change
        assert db_user.id == original_id  # ID unchanged
        assert db_user.created_at == original_created_at  # created_at unchanged

    def test_update_db_from_domain_updates_password_hash(self):
        """update_db_from_domain() should update password hash on password change."""
        # Arrange
        db_user = create_mock_db_user(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            password_hash="$2b$12$OldPasswordHash",
            email_verified=True,
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
            last_login_at=None
        )

        # Domain user with changed password
        domain_user = DomainUser.create(
            email=Email.from_string("test@example.com"),
            plain_password="OldPassword123"
        )
        # Simulate password change
        domain_user.change_password("NewPassword456")

        # Act
        UserMapper.update_db_from_domain(db_user, domain_user)

        # Assert
        assert db_user.password_hash != "$2b$12$OldPasswordHash"
        assert db_user.password_hash == domain_user.password.hash_value

    def test_update_db_from_domain_updates_account_status(self):
        """update_db_from_domain() should update email_verified and is_active."""
        # Arrange
        db_user = create_mock_db_user(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            password_hash="$2b$12$HashValue",
            email_verified=False,  # Not verified
            is_active=True,  # Active
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
            last_login_at=None
        )

        domain_user = DomainUser.create(
            email=Email.from_string("test@example.com"),
            plain_password="SecurePass123"
        )
        # Verify email and deactivate account
        domain_user.verify_email()
        domain_user.deactivate()

        # Act
        UserMapper.update_db_from_domain(db_user, domain_user)

        # Assert
        assert db_user.email_verified is True  # Now verified
        assert db_user.is_active is False  # Now deactivated

    def test_update_db_from_domain_updates_last_login(self):
        """update_db_from_domain() should update last_login_at after login."""
        # Arrange
        db_user = create_mock_db_user(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            email="test@example.com",
            password_hash="$2b$12$HashValue",
            email_verified=True,
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
            last_login_at=None  # Never logged in
        )

        domain_user = DomainUser.create(
            email=Email.from_string("test@example.com"),
            plain_password="SecurePass123"
        )
        domain_user.verify_email()
        # Simulate login
        domain_user.record_login()

        # Act
        UserMapper.update_db_from_domain(db_user, domain_user)

        # Assert
        assert db_user.last_login_at is not None
        assert db_user.last_login_at == domain_user.last_login_at
        assert isinstance(db_user.last_login_at, datetime)
