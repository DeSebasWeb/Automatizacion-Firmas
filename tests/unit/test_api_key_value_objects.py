"""Unit tests for API Key value objects."""

import pytest
from src.domain.value_objects.api_key_value import APIKeyValue
from src.domain.value_objects.api_key_hash import APIKeyHash
from src.domain.value_objects.scope_code import ScopeCode


class TestAPIKeyValue:
    """Tests for APIKeyValue value object."""

    def test_generate_creates_valid_key(self):
        """Test that generate() creates valid API key."""
        key = APIKeyValue.generate()

        assert isinstance(key, APIKeyValue)
        assert str(key).startswith("vfy_")
        assert len(str(key)) == 68  # vfy_ (4) + 64 chars

    def test_generate_creates_unique_keys(self):
        """Test that generate() creates unique keys."""
        key1 = APIKeyValue.generate()
        key2 = APIKeyValue.generate()

        assert str(key1) != str(key2)

    def test_from_string_valid_key(self):
        """Test creating APIKeyValue from valid string."""
        key = APIKeyValue.generate()
        key_str = str(key)

        reconstructed = APIKeyValue.from_string(key_str)
        assert str(reconstructed) == key_str

    def test_from_string_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid API key format"):
            APIKeyValue.from_string("invalid_key_format")

    def test_from_string_wrong_prefix_raises_error(self):
        """Test that wrong prefix raises ValueError."""
        with pytest.raises(ValueError, match="Invalid API key format"):
            APIKeyValue.from_string("abc_" + "x" * 64)

    def test_from_string_wrong_length_raises_error(self):
        """Test that wrong length raises ValueError."""
        with pytest.raises(ValueError, match="Invalid API key format"):
            APIKeyValue.from_string("vfy_tooshort")

    def test_prefix_property(self):
        """Test prefix property returns first 12 chars."""
        key = APIKeyValue.generate()
        prefix = key.prefix

        assert len(prefix) == 12
        assert prefix.startswith("vfy_")
        assert prefix == str(key)[:12]

    def test_str_returns_full_value(self):
        """Test __str__ returns full key value."""
        key = APIKeyValue.generate()
        assert str(key) == key.value

    def test_repr_masks_key(self):
        """Test __repr__ doesn't expose full key."""
        key = APIKeyValue.generate()
        repr_str = repr(key)

        assert "APIKeyValue" in repr_str
        assert key.prefix in repr_str
        assert "..." in repr_str
        # Full key should NOT be in repr
        assert str(key) not in repr_str or "..." in repr_str

    def test_immutability(self):
        """Test that APIKeyValue is immutable."""
        key = APIKeyValue.generate()

        with pytest.raises((AttributeError, TypeError)):
            key.value = "new_value"  # type: ignore


class TestAPIKeyHash:
    """Tests for APIKeyHash value object."""

    def test_from_key_creates_hash(self):
        """Test creating hash from plaintext key."""
        key = "vfy_" + "x" * 64
        key_hash = APIKeyHash.from_key(key)

        assert isinstance(key_hash, APIKeyHash)
        assert len(str(key_hash)) == 64  # SHA-256 hex = 64 chars

    def test_from_key_deterministic(self):
        """Test that same key produces same hash."""
        key = "vfy_" + "x" * 64
        hash1 = APIKeyHash.from_key(key)
        hash2 = APIKeyHash.from_key(key)

        assert str(hash1) == str(hash2)

    def test_from_key_different_keys_different_hashes(self):
        """Test that different keys produce different hashes."""
        key1 = "vfy_" + "x" * 64
        key2 = "vfy_" + "y" * 64

        hash1 = APIKeyHash.from_key(key1)
        hash2 = APIKeyHash.from_key(key2)

        assert str(hash1) != str(hash2)

    def test_verify_valid_key(self):
        """Test verify() returns True for correct key."""
        key = "vfy_" + "x" * 64
        key_hash = APIKeyHash.from_key(key)

        assert key_hash.verify(key) is True

    def test_verify_invalid_key(self):
        """Test verify() returns False for incorrect key."""
        key = "vfy_" + "x" * 64
        wrong_key = "vfy_" + "y" * 64
        key_hash = APIKeyHash.from_key(key)

        assert key_hash.verify(wrong_key) is False

    def test_from_string_valid_hash(self):
        """Test creating APIKeyHash from hash string."""
        original_hash = "a" * 64
        key_hash = APIKeyHash.from_string(original_hash)

        assert str(key_hash) == original_hash

    def test_from_string_invalid_hash_length(self):
        """Test invalid hash length raises ValueError."""
        with pytest.raises(ValueError, match="Invalid hash format"):
            APIKeyHash.from_string("tooshort")

    def test_from_string_invalid_hash_chars(self):
        """Test invalid hash characters raises ValueError."""
        with pytest.raises(ValueError, match="Invalid hash format"):
            APIKeyHash.from_string("z" * 64)  # 'z' not hex

    def test_repr_masks_hash(self):
        """Test __repr__ truncates hash."""
        key_hash = APIKeyHash.from_key("vfy_" + "x" * 64)
        repr_str = repr(key_hash)

        assert "APIKeyHash" in repr_str
        assert "..." in repr_str
        # Full hash should be truncated
        assert len(repr_str) < len(str(key_hash))

    def test_immutability(self):
        """Test that APIKeyHash is immutable."""
        key_hash = APIKeyHash.from_key("vfy_" + "x" * 64)

        with pytest.raises((AttributeError, TypeError)):
            key_hash.hash_value = "new_hash"  # type: ignore


class TestScopeCode:
    """Tests for ScopeCode value object."""

    def test_from_string_valid_scope(self):
        """Test creating ScopeCode from valid string."""
        scope = ScopeCode.from_string("documents:read")

        assert isinstance(scope, ScopeCode)
        assert str(scope) == "documents:read"

    def test_from_string_normalizes_to_lowercase(self):
        """Test that scope is normalized to lowercase."""
        scope = ScopeCode.from_string("Documents:Read")

        assert str(scope) == "documents:read"

    def test_from_string_invalid_no_colon(self):
        """Test invalid format without colon raises ValueError."""
        with pytest.raises(ValueError, match="Invalid scope format"):
            ScopeCode.from_string("documents")

    def test_from_string_invalid_empty_category(self):
        """Test invalid format with empty category raises ValueError."""
        with pytest.raises(ValueError, match="Invalid scope format"):
            ScopeCode.from_string(":read")

    def test_from_string_invalid_empty_action(self):
        """Test invalid format with empty action raises ValueError."""
        with pytest.raises(ValueError, match="Invalid scope format"):
            ScopeCode.from_string("documents:")

    def test_from_string_invalid_uppercase(self):
        """Test that only lowercase after normalization."""
        scope = ScopeCode.from_string("DOCUMENTS:READ")
        assert str(scope) == "documents:read"

    def test_from_strings_list(self):
        """Test creating list of ScopeCodes."""
        scope_strs = ["documents:read", "documents:write", "users:read"]
        scopes = ScopeCode.from_strings(scope_strs)

        assert len(scopes) == 3
        assert all(isinstance(s, ScopeCode) for s in scopes)
        assert [str(s) for s in scopes] == scope_strs

    def test_from_strings_invalid_raises_error(self):
        """Test invalid scope in list raises ValueError."""
        with pytest.raises(ValueError):
            ScopeCode.from_strings(["documents:read", "invalid"])

    def test_category_property(self):
        """Test category property returns part before colon."""
        scope = ScopeCode.from_string("documents:read")
        assert scope.category == "documents"

    def test_action_property(self):
        """Test action property returns part after colon."""
        scope = ScopeCode.from_string("documents:read")
        assert scope.action == "read"

    def test_matches_exact_match(self):
        """Test matches() returns True for exact match."""
        scope1 = ScopeCode.from_string("documents:read")
        scope2 = ScopeCode.from_string("documents:read")

        assert scope1.matches(scope2)

    def test_matches_admin_all(self):
        """Test admin:all matches everything."""
        admin_scope = ScopeCode.from_string("admin:all")
        user_scope = ScopeCode.from_string("users:read")

        assert admin_scope.matches(user_scope)
        assert not user_scope.matches(admin_scope)

    def test_matches_category_all(self):
        """Test category:all matches all actions in category."""
        all_docs = ScopeCode.from_string("documents:all")
        read_docs = ScopeCode.from_string("documents:read")
        write_docs = ScopeCode.from_string("documents:write")
        read_users = ScopeCode.from_string("users:read")

        assert all_docs.matches(read_docs)
        assert all_docs.matches(write_docs)
        assert not all_docs.matches(read_users)

    def test_matches_no_match(self):
        """Test matches() returns False for different scopes."""
        scope1 = ScopeCode.from_string("documents:read")
        scope2 = ScopeCode.from_string("users:read")

        assert not scope1.matches(scope2)

    def test_equality(self):
        """Test equality comparison."""
        scope1 = ScopeCode.from_string("documents:read")
        scope2 = ScopeCode.from_string("documents:read")
        scope3 = ScopeCode.from_string("documents:write")

        assert scope1 == scope2
        assert scope1 != scope3

    def test_hash_consistency(self):
        """Test that equal scopes have same hash."""
        scope1 = ScopeCode.from_string("documents:read")
        scope2 = ScopeCode.from_string("documents:read")

        assert hash(scope1) == hash(scope2)

    def test_can_be_used_in_set(self):
        """Test that ScopeCode can be used in sets."""
        scope1 = ScopeCode.from_string("documents:read")
        scope2 = ScopeCode.from_string("documents:read")
        scope3 = ScopeCode.from_string("documents:write")

        scope_set = {scope1, scope2, scope3}
        assert len(scope_set) == 2  # scope1 and scope2 are duplicates

    def test_immutability(self):
        """Test that ScopeCode is immutable."""
        scope = ScopeCode.from_string("documents:read")

        with pytest.raises((AttributeError, TypeError)):
            scope.value = "new_value"  # type: ignore


class TestAPIKeyValueIntegration:
    """Integration tests for API Key value objects."""

    def test_generate_hash_verify_flow(self):
        """Test complete flow: generate key, hash it, verify it."""
        # Generate key
        key = APIKeyValue.generate()
        key_str = str(key)

        # Hash the key
        key_hash = APIKeyHash.from_key(key_str)

        # Verify the key
        assert key_hash.verify(key_str)

        # Verify wrong key fails
        wrong_key = APIKeyValue.generate()
        assert not key_hash.verify(str(wrong_key))

    def test_prefix_for_display(self):
        """Test using prefix for user display."""
        key = APIKeyValue.generate()
        prefix = key.prefix

        # Prefix should be safe to show in UI
        assert len(prefix) == 12
        assert prefix.startswith("vfy_")

    def test_scope_matching_hierarchy(self):
        """Test scope matching hierarchy."""
        # Create scopes
        admin_all = ScopeCode.from_string("admin:all")
        docs_all = ScopeCode.from_string("documents:all")
        docs_read = ScopeCode.from_string("documents:read")
        users_read = ScopeCode.from_string("users:read")

        # Admin:all matches everything
        assert admin_all.matches(docs_read)
        assert admin_all.matches(users_read)

        # Documents:all matches documents:* but not users:*
        assert docs_all.matches(docs_read)
        assert not docs_all.matches(users_read)

        # Specific scopes only match themselves
        assert docs_read.matches(docs_read)
        assert not docs_read.matches(users_read)
