"""Unit tests for UserId value object.

Tests the UserId value object to ensure proper UUID validation,
immutability, and factory methods.
"""
import pytest
from uuid import UUID, uuid4

from domain.value_objects.user_id import UserId


@pytest.mark.unit
class TestUserId:
    """Tests for UserId value object."""

    def test_user_id_from_valid_uuid_string(self):
        """UserId should be created from a valid UUID string."""
        # Arrange
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"

        # Act
        user_id = UserId.from_string(uuid_str)

        # Assert
        assert isinstance(user_id, UserId)
        assert str(user_id.value) == uuid_str

    def test_user_id_from_uuid_object(self):
        """UserId should be created from a UUID object."""
        # Arrange
        uuid_obj = uuid4()

        # Act
        user_id = UserId(uuid_obj)

        # Assert
        assert isinstance(user_id, UserId)
        assert user_id.value == uuid_obj

    def test_user_id_generate_creates_new_uuid(self):
        """UserId.generate() should create a new random UUID."""
        # Act
        user_id_1 = UserId.generate()
        user_id_2 = UserId.generate()

        # Assert
        assert isinstance(user_id_1, UserId)
        assert isinstance(user_id_2, UserId)
        assert user_id_1.value != user_id_2.value  # Should be different

    def test_user_id_string_representation(self):
        """str(UserId) should return the UUID string."""
        # Arrange
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        user_id = UserId.from_string(uuid_str)

        # Act
        result = str(user_id)

        # Assert
        assert result == uuid_str

    def test_user_id_equality(self):
        """Two UserIds with the same UUID should be equal."""
        # Arrange
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        user_id_1 = UserId.from_string(uuid_str)
        user_id_2 = UserId.from_string(uuid_str)

        # Act & Assert
        assert user_id_1 == user_id_2
        assert hash(user_id_1) == hash(user_id_2)
