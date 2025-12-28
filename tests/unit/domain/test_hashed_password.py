"""Unit tests for HashedPassword value object.

Tests the HashedPassword value object to ensure proper password hashing,
verification, and security.
"""
import pytest

from domain.value_objects.hashed_password import HashedPassword


@pytest.mark.unit
class TestHashedPasswordCreation:
    """Tests for HashedPassword creation."""

    def test_hashed_password_from_plain_text(self):
        """HashedPassword should hash plain text passwords."""
        # Arrange
        plain_password = "SecurePassword123!"

        # Act
        hashed = HashedPassword.from_plain_text(plain_password)

        # Assert
        assert isinstance(hashed, HashedPassword)
        assert hashed.hash_value != plain_password  # Should be hashed
        assert hashed.hash_value.startswith("$2b$")  # Bcrypt format

    def test_hashed_password_from_hash(self):
        """HashedPassword should accept pre-hashed passwords."""
        # Arrange
        existing_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8fW.lQ4F9y"

        # Act
        hashed = HashedPassword.from_hash(existing_hash)

        # Assert
        assert isinstance(hashed, HashedPassword)
        assert hashed.hash_value == existing_hash

    def test_hashed_password_verify_correct_password(self):
        """verify() should return True for correct password."""
        # Arrange
        plain_password = "MySecretPass123"
        hashed = HashedPassword.from_plain_text(plain_password)

        # Act
        result = hashed.verify(plain_password)

        # Assert
        assert result is True

    def test_hashed_password_verify_incorrect_password(self):
        """verify() should return False for incorrect password."""
        # Arrange
        plain_password = "CorrectPassword123"
        wrong_password = "WrongPassword456"
        hashed = HashedPassword.from_plain_text(plain_password)

        # Act
        result = hashed.verify(wrong_password)

        # Assert
        assert result is False

    def test_hashed_password_same_input_different_hashes(self):
        """Same password should produce different hashes (salt)."""
        # Arrange
        plain_password = "SamePassword123"

        # Act
        hashed_1 = HashedPassword.from_plain_text(plain_password)
        hashed_2 = HashedPassword.from_plain_text(plain_password)

        # Assert
        assert hashed_1.hash_value != hashed_2.hash_value  # Different due to salt
        assert hashed_1.verify(plain_password)  # Both verify correctly
        assert hashed_2.verify(plain_password)
