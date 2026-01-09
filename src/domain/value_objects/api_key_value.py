"""API Key value object - Generated key."""

from dataclasses import dataclass
import secrets
import re


@dataclass(frozen=True)
class APIKeyValue:
    """
    API Key value (e.g., 'vfy_abc123...').

    Format: prefix_random
    - Prefix: 'vfy_' (verifyid)
    - Random: 48 bytes urlsafe base64 (~64 chars)

    Security:
        This plaintext key is ONLY shown once during creation.
        After that, only the hash is stored and the prefix is shown.
    """

    value: str

    def __post_init__(self):
        """Validate API key format."""
        if not self._is_valid_format(self.value):
            raise ValueError(
                f"Invalid API key format: {self.value[:20]}... "
                f"(expected format: vfy_[a-zA-Z0-9_-]{{64}})"
            )

    @staticmethod
    def _is_valid_format(key: str) -> bool:
        """
        Validate key format: vfy_[a-zA-Z0-9_-]{64}

        The urlsafe base64 encoding produces characters: A-Z, a-z, 0-9, _, -
        """
        pattern = r'^vfy_[a-zA-Z0-9_-]{64}$'
        return bool(re.match(pattern, key))

    @classmethod
    def generate(cls, prefix: str = "vfy") -> "APIKeyValue":
        """
        Generate new random API key.

        Args:
            prefix: Key prefix (default: "vfy" for VerifyID)

        Returns:
            New APIKeyValue with cryptographically secure random string

        Example:
            >>> key = APIKeyValue.generate()
            >>> str(key)
            'vfy_xQW9k3mN...'  # 68 chars total
        """
        # Generate 48 random bytes -> base64 -> ~64 chars
        random_part = secrets.token_urlsafe(48)
        key = f"{prefix}_{random_part}"
        return cls(value=key)

    @classmethod
    def from_string(cls, key_str: str) -> "APIKeyValue":
        """
        Create APIKeyValue from string (with validation).

        Args:
            key_str: Plaintext API key string

        Returns:
            APIKeyValue instance

        Raises:
            ValueError: If key format is invalid
        """
        # Strip whitespace
        cleaned = key_str.strip()
        return cls(value=cleaned)

    @property
    def prefix(self) -> str:
        """
        Get key prefix for display (first 12 chars).

        Example:
            >>> key = APIKeyValue.generate()
            >>> key.prefix
            'vfy_xQW9k3mN'
        """
        return self.value[:12]

    def __str__(self) -> str:
        """Return full key value."""
        return self.value

    def __repr__(self) -> str:
        """Secure representation (don't leak full key in logs)."""
        return f"APIKeyValue({self.prefix}...)"
