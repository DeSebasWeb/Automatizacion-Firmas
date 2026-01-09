"""API Key hash value object."""

from dataclasses import dataclass
import hashlib
import hmac


@dataclass(frozen=True)
class APIKeyHash:
    """
    Hashed API key (SHA-256).

    Security:
        - Store ONLY hashes in database, never plaintext keys
        - Uses SHA-256 for deterministic hashing (faster than bcrypt for lookups)
        - Comparison uses constant-time comparison to prevent timing attacks

    Note:
        Unlike passwords, API keys are random tokens, so SHA-256 is sufficient.
        Password hashing requires bcrypt/argon2 due to low entropy.
    """

    hash_value: str

    def __post_init__(self):
        """Validate hash format (64 hex chars for SHA-256)."""
        if not self._is_valid_hash(self.hash_value):
            raise ValueError(
                f"Invalid hash format: {self.hash_value[:20]}... "
                f"(expected 64 hex characters)"
            )

    @staticmethod
    def _is_valid_hash(hash_str: str) -> bool:
        """
        Validate SHA-256 hash format.

        SHA-256 produces 32 bytes = 64 hex characters
        """
        return (
            isinstance(hash_str, str)
            and len(hash_str) == 64
            and all(c in "0123456789abcdef" for c in hash_str)
        )

    @classmethod
    def from_key(cls, key_value: str) -> "APIKeyHash":
        """
        Create hash from plaintext key.

        Args:
            key_value: Plaintext API key string (e.g., "vfy_abc123...")

        Returns:
            APIKeyHash instance with SHA-256 hash

        Security Note:
            Uses direct SHA-256 without salt because:
            1. API keys are cryptographically random (48 bytes = 288 bits entropy)
            2. Rainbow tables ineffective against high-entropy tokens
            3. Each key is unique by design (secrets.token_urlsafe)

            For additional security in production, consider:
            - HMAC-SHA256 with application secret key
            - Bcrypt/Argon2 for defense-in-depth

        Example:
            >>> from src.domain.value_objects.api_key_value import APIKeyValue
            >>> key = APIKeyValue.generate()
            >>> key_hash = APIKeyHash.from_key(str(key))
            >>> key_hash.hash_value
            'a1b2c3d4...'  # 64 hex chars
        """
        # SHA-256 hash of the key
        # Note: Salt not required for high-entropy random tokens,
        # but HMAC-SHA256 with secret key would be more secure
        hash_bytes = hashlib.sha256(key_value.encode("utf-8")).digest()
        hash_hex = hash_bytes.hex()
        return cls(hash_value=hash_hex)

    def verify(self, key_value: str) -> bool:
        """
        Verify plaintext key against this hash.

        Args:
            key_value: Plaintext API key to verify

        Returns:
            True if key matches hash, False otherwise

        Security:
            Uses constant-time comparison to prevent timing attacks

        Example:
            >>> key = APIKeyValue.generate()
            >>> key_hash = APIKeyHash.from_key(str(key))
            >>> key_hash.verify(str(key))
            True
            >>> key_hash.verify("wrong_key")
            False
        """
        # Hash the provided key
        provided_hash = hashlib.sha256(key_value.encode("utf-8")).hexdigest()

        # Constant-time comparison (prevents timing attacks)
        return hmac.compare_digest(self.hash_value, provided_hash)

    @classmethod
    def from_string(cls, hash_str: str) -> "APIKeyHash":
        """
        Create APIKeyHash from existing hash string.

        Args:
            hash_str: 64-character hex hash string

        Returns:
            APIKeyHash instance

        Raises:
            ValueError: If hash format is invalid
        """
        return cls(hash_value=hash_str.lower())

    def __str__(self) -> str:
        """Return hash value (safe to expose in logs)."""
        return self.hash_value

    def __repr__(self) -> str:
        """Secure representation (truncated for brevity)."""
        return f"APIKeyHash({self.hash_value[:16]}...)"
