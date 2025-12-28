"""Unit tests for User entity.

Tests the User domain entity to ensure proper business logic,
immutability, and factory methods.
"""
import pytest
from datetime import datetime

from domain.entities.user import User
from domain.value_objects.user_id import UserId
from domain.value_objects.email import Email
from domain.value_objects.hashed_password import HashedPassword


@pytest.mark.unit
class TestUserCreation:
    """Tests for User entity creation."""

    def test_user_create_with_valid_data(self):
        """User.create() should create a new user with hashed password."""
        # Arrange
        email = Email.from_string("test@example.com")
        plain_password = "SecurePass123!"

        # Act
        user = User.create(email=email, plain_password=plain_password)

        # Assert
        assert isinstance(user, User)
        assert isinstance(user.id, UserId)
        assert isinstance(user.email, Email)
        assert str(user.email) == "test@example.com"
        assert user.email_verified is False
        assert user.is_active is True

    def test_user_create_hashes_password(self):
        """User.create() should hash the password, not store plain text."""
        # Arrange
        email = Email.from_string("user@test.com")
        plain_password = "MyPassword123"

        # Act
        user = User.create(email=email, plain_password=plain_password)

        # Assert
        assert isinstance(user.password, HashedPassword)
        assert user.password.verify(plain_password) is True
        assert user.password.hash_value != plain_password

    def test_user_has_timestamps_on_creation(self):
        """User.create() should set created_at timestamp."""
        # Arrange
        email = Email.from_string("new@example.com")

        # Act
        user = User.create(email=email, plain_password="Password123")

        # Assert
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)  # Set on creation
        assert user.last_login_at is None  # Not logged in yet

    def test_user_constructor_with_all_fields(self):
        """User() constructor should accept all fields."""
        # Arrange
        user_id = UserId.generate()
        email = Email.from_string("test@example.com")
        password = HashedPassword.from_plain_text("SecurePass123")
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()

        # Act
        user = User(
            id=user_id,
            email=email,
            password=password,
            email_verified=True,
            is_active=True,
            created_at=created_at,
            updated_at=updated_at,
            last_login_at=None
        )

        # Assert
        assert user.id == user_id
        assert user.email == email
        assert user.password == password
        assert user.email_verified is True
        assert user.is_active is True

    def test_user_equality_requires_all_fields(self):
        """Two users are equal only if all fields match (dataclass behavior)."""
        # Arrange
        user_id = UserId.generate()
        email = Email.from_string("test@example.com")
        password = HashedPassword.from_plain_text("SecurePass123")
        now = datetime.utcnow()

        user_1 = User(
            id=user_id,
            email=email,
            password=password,
            email_verified=False,
            is_active=True,
            created_at=now,
            updated_at=now
        )

        user_2 = User(
            id=user_id,  # Same ID but different email
            email=Email.from_string("different@example.com"),
            password=password,
            email_verified=False,
            is_active=True,
            created_at=now,
            updated_at=now
        )

        user_3 = User(
            id=user_id,  # Exact same everything
            email=email,
            password=password,
            email_verified=False,
            is_active=True,
            created_at=now,
            updated_at=now
        )

        # Act & Assert
        assert user_1 != user_2  # Different email means not equal
        assert user_1 == user_3  # All fields match means equal
