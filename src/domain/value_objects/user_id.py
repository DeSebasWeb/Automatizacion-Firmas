"""User ID value object."""

from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class UserId:
    """
    User ID value object - Wrapper for UUID.

    Provides type safety and domain semantics for user identifiers.
    Uses UUID v4 (random) for unique user identification.

    Benefits:
    - Type safety: Can't accidentally pass wrong ID type
    - Domain semantics: Clear that this is a user identifier
    - Immutability: IDs never change after creation
    - Standard format: UUID ensures uniqueness across systems
    """

    value: uuid.UUID

    @classmethod
    def generate(cls) -> "UserId":
        """
        Generate new random UserId.

        Uses UUID v4 (random) for guaranteed uniqueness.

        Returns:
            New UserId instance

        Example:
            >>> user_id = UserId.generate()
            >>> str(user_id)
            '550e8400-e29b-41d4-a716-446655440000'
        """
        return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> "UserId":
        """
        Create UserId from string.

        Accepts standard UUID string formats:
        - Hyphenated: '550e8400-e29b-41d4-a716-446655440000'
        - Hex: '550e8400e29b41d4a716446655440000'
        - URN: 'urn:uuid:550e8400-e29b-41d4-a716-446655440000'

        Args:
            id_str: UUID string in any standard format

        Returns:
            UserId instance

        Raises:
            ValueError: If string is not a valid UUID

        Example:
            >>> user_id = UserId.from_string("550e8400-e29b-41d4-a716-446655440000")
            >>> str(user_id)
            '550e8400-e29b-41d4-a716-446655440000'
        """
        try:
            return cls(value=uuid.UUID(id_str))
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(
                f"Invalid UUID format: '{id_str}'. "
                f"Expected format: '550e8400-e29b-41d4-a716-446655440000'"
            ) from e

    @classmethod
    def try_create(cls, id_str: str) -> "UserId | None":
        """
        Try to create UserId from string, returns None if invalid.

        Use this when you want to handle invalid UUIDs gracefully
        without exceptions.

        Args:
            id_str: UUID string

        Returns:
            UserId instance or None if invalid

        Example:
            >>> user_id = UserId.try_create("invalid-uuid")
            >>> user_id is None
            True
        """
        try:
            return cls.from_string(id_str)
        except ValueError:
            return None

    def __str__(self) -> str:
        """
        String representation (hyphenated UUID).

        Returns:
            UUID string in standard hyphenated format

        Example:
            >>> user_id = UserId.generate()
            >>> str(user_id)
            '550e8400-e29b-41d4-a716-446655440000'
        """
        return str(self.value)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"UserId('{self.value}')"
