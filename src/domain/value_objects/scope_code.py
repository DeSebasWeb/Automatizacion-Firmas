"""Scope code value object."""

from dataclasses import dataclass
import re
from typing import List


@dataclass(frozen=True)
class ScopeCode:
    """
    Permission scope code (e.g., 'documents:read').

    Format: category:action
    Examples:
        - documents:read
        - documents:write
        - verifications:create
        - admin:all

    Scopes define granular permissions for API keys, following OAuth 2.0 conventions.

    Business Rules:
        - Format must be category:action
        - Only lowercase letters and underscores allowed
        - Cannot start or end with underscore
        - Minimum length: 3 chars (e.g., "a:b")
    """

    value: str

    def __post_init__(self):
        """Validate scope format."""
        if not self._is_valid_format(self.value):
            raise ValueError(
                f"Invalid scope format: '{self.value}'. "
                f"Expected format: category:action (e.g., 'documents:read')"
            )

    @staticmethod
    def _is_valid_format(scope: str) -> bool:
        """
        Validate format: category:action

        Rules:
            - Must contain exactly one colon
            - Parts can only contain lowercase letters and underscores
            - Cannot start/end with underscores
            - Minimum 1 char per part

        Valid:
            ✓ documents:read
            ✓ documents:write
            ✓ user_profile:update
            ✓ admin:all

        Invalid:
            ✗ documents (no colon)
            ✗ documents: (empty action)
            ✗ :read (empty category)
            ✗ Documents:Read (uppercase)
            ✗ documents:read:all (multiple colons)
            ✗ _documents:read (starts with underscore)
        """
        pattern = r'^[a-z][a-z_]*[a-z]:[a-z][a-z_]*[a-z]$|^[a-z]:[a-z]$'
        return bool(re.match(pattern, scope))

    @classmethod
    def from_string(cls, scope_str: str) -> "ScopeCode":
        """
        Create from string (normalized to lowercase).

        Args:
            scope_str: Scope string (will be lowercased)

        Returns:
            ScopeCode instance

        Raises:
            ValueError: If format is invalid

        Example:
            >>> scope = ScopeCode.from_string("Documents:Read")
            >>> str(scope)
            'documents:read'
        """
        normalized = scope_str.strip().lower()
        return cls(value=normalized)

    @classmethod
    def from_strings(cls, scope_strs: List[str]) -> List["ScopeCode"]:
        """
        Create list of ScopeCodes from string list.

        Args:
            scope_strs: List of scope strings

        Returns:
            List of ScopeCode instances

        Raises:
            ValueError: If any scope format is invalid

        Example:
            >>> scopes = ScopeCode.from_strings(["documents:read", "documents:write"])
            >>> [str(s) for s in scopes]
            ['documents:read', 'documents:write']
        """
        return [cls.from_string(s) for s in scope_strs]

    @property
    def category(self) -> str:
        """
        Get scope category (part before colon).

        Example:
            >>> scope = ScopeCode.from_string("documents:read")
            >>> scope.category
            'documents'
        """
        return self.value.split(":")[0]

    @property
    def action(self) -> str:
        """
        Get scope action (part after colon).

        Example:
            >>> scope = ScopeCode.from_string("documents:read")
            >>> scope.action
            'read'
        """
        return self.value.split(":")[1]

    def matches(self, required_scope: "ScopeCode") -> bool:
        """
        Check if this scope satisfies required scope.

        Admin scopes (*:all or admin:all) match everything in that category.

        Args:
            required_scope: Required scope to check against

        Returns:
            True if this scope satisfies the requirement

        Example:
            >>> admin = ScopeCode.from_string("admin:all")
            >>> user_read = ScopeCode.from_string("users:read")
            >>> admin.matches(user_read)
            True
            >>> user_read.matches(admin)
            False
        """
        # Exact match
        if self.value == required_scope.value:
            return True

        # Admin:all matches everything
        if self.value == "admin:all":
            return True

        # Category:all matches all actions in that category
        if (
            self.action == "all"
            and self.category == required_scope.category
        ):
            return True

        return False

    def __str__(self) -> str:
        """Return scope code value."""
        return self.value

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"ScopeCode('{self.value}')"

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, ScopeCode):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.value)
