"""Hashed password value object."""

from dataclasses import dataclass
import bcrypt


@dataclass(frozen=True)
class HashedPassword:
    """
    Hashed password value object - Never stores plain text.

    This value object encapsulates password hashing and verification logic.
    It NEVER stores passwords in plain text, only bcrypt hashes.

    Security features:
    - Bcrypt hashing with configurable cost factor
    - Constant-time password verification
    - Masked string representation (prevents accidental logging)
    """

    hash_value: str  # bcrypt hash string

    def __post_init__(self):
        """Validate bcrypt hash format on creation."""
        if not self.hash_value.startswith("$2b$"):
            raise ValueError(
                f"Invalid bcrypt hash format. Must start with '$2b$', "
                f"got: {self.hash_value[:10]}..."
            )

        # Validate minimum hash length (bcrypt hashes are 60 chars)
        if len(self.hash_value) != 60:
            raise ValueError(
                f"Invalid bcrypt hash length. Expected 60 chars, "
                f"got: {len(self.hash_value)}"
            )

    @classmethod
    def from_plain_text(
        cls,
        plain_password: str,
        rounds: int = 12
    ) -> "HashedPassword":
        """
        Create hashed password from plain text.

        This is the PRIMARY way to create a HashedPassword when registering
        a new user or changing passwords.

        Args:
            plain_password: Password in plain text
            rounds: Bcrypt cost factor (4-31, default: 12)
                   Higher = more secure but slower
                   12 = ~250ms per hash (recommended for production)

        Returns:
            HashedPassword instance with bcrypt hash

        Raises:
            ValueError: If password is too short or rounds invalid

        Example:
            >>> pwd = HashedPassword.from_plain_text("SecurePass123")
            >>> pwd.verify("SecurePass123")
            True
        """
        # Validate password strength
        if len(plain_password) < 8:
            raise ValueError(
                f"Password must be at least 8 characters, "
                f"got: {len(plain_password)}"
            )

        # Validate bcrypt rounds
        if not (4 <= rounds <= 31):
            raise ValueError(
                f"Bcrypt rounds must be between 4 and 31, got: {rounds}"
            )

        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)

        return cls(hash_value=hashed.decode('utf-8'))

    @classmethod
    def from_hash(cls, hash_str: str) -> "HashedPassword":
        """
        Create from existing bcrypt hash.

        Use this when loading a user from the database - the password
        is already hashed.

        Args:
            hash_str: Existing bcrypt hash string

        Returns:
            HashedPassword instance

        Raises:
            ValueError: If hash format is invalid

        Example:
            >>> hash_str = "$2b$12$..."
            >>> pwd = HashedPassword.from_hash(hash_str)
        """
        return cls(hash_value=hash_str)

    def verify(self, plain_password: str) -> bool:
        """
        Verify plain password against stored hash.

        Uses bcrypt's constant-time comparison to prevent timing attacks.

        Args:
            plain_password: Password to verify

        Returns:
            True if password matches hash, False otherwise

        Example:
            >>> pwd = HashedPassword.from_plain_text("SecurePass123")
            >>> pwd.verify("SecurePass123")
            True
            >>> pwd.verify("WrongPassword")
            False
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                self.hash_value.encode('utf-8')
            )
        except (ValueError, TypeError):
            # Invalid hash or password format
            return False

    def __str__(self) -> str:
        """
        Return masked representation for security.

        Prevents accidental logging of password hashes.
        """
        return "HashedPassword(***)"

    def __repr__(self) -> str:
        """
        Return masked representation for security.

        Prevents accidental logging of password hashes in debug output.
        """
        return "HashedPassword(***)"
