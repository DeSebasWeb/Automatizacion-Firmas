"""Unit tests for UserMapper."""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Import domain without going through infrastructure __init__.py to avoid circular imports
from domain.entities.user import User as DomainUser
from domain.value_objects.user_id import UserId
from domain.value_objects.email import Email
from domain.value_objects.hashed_password import HashedPassword

# Import models and mappers directly from their modules, not through package __init__.py
# This avoids triggering infrastructure.database.__init__.py which causes circular import
import importlib.util
import types

# Load Base first (needed by User model)
base_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "infrastructure" / "database" / "base.py"
spec = importlib.util.spec_from_file_location("base_module", base_path)
base_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_module)

# Create fake parent package structure for relative imports
sys.modules['infrastructure'] = types.ModuleType('infrastructure')
sys.modules['infrastructure.database'] = types.ModuleType('infrastructure.database')
sys.modules['infrastructure.database.base'] = base_module
sys.modules['infrastructure.database.models'] = types.ModuleType('infrastructure.database.models')

# Load User model (relative imports will now work)
user_model_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "infrastructure" / "database" / "models" / "user.py"
spec = importlib.util.spec_from_file_location("infrastructure.database.models.user", user_model_path)
user_model = importlib.util.module_from_spec(spec)
sys.modules['infrastructure.database.models.user'] = user_model
spec.loader.exec_module(user_model)
DBUser = user_model.User

# Create fake mappers package
sys.modules['infrastructure.database.mappers'] = types.ModuleType('infrastructure.database.mappers')

# Load UserMapper directly
mapper_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "infrastructure" / "database" / "mappers" / "user_mapper.py"
spec = importlib.util.spec_from_file_location("infrastructure.database.mappers.user_mapper", mapper_path)
mapper_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mapper_module)
UserMapper = mapper_module.UserMapper


@pytest.fixture
def sample_domain_user():
    """Create a sample domain user for testing."""
    user_id = UserId.generate()
    email = Email.from_string("test@example.com")
    password = HashedPassword.from_plain_text("SecurePass123")

    return DomainUser(
        id=user_id,
        email=email,
        password=password,
        email_verified=False,
        is_active=True,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        last_login_at=None
    )


@pytest.fixture
def sample_db_user():
    """Create a sample database user for testing."""
    user_id = uuid4()

    db_user = DBUser(
        id=user_id,
        email="dbtest@example.com",
        password_hash="$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP",
        email_verified=True,
        is_active=True,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 15, 10, 30, 0),
        last_login_at=datetime(2024, 1, 15, 11, 0, 0)
    )

    return db_user


class TestUserMapperToDomain:
    """Test UserMapper.to_domain() method."""

    def test_to_domain_converts_all_fields(self, sample_db_user):
        """Should convert all database fields to domain fields."""
        domain_user = UserMapper.to_domain(sample_db_user)

        assert isinstance(domain_user, DomainUser)
        assert str(domain_user.id) == str(sample_db_user.id)
        assert str(domain_user.email) == sample_db_user.email
        assert domain_user.email_verified == sample_db_user.email_verified
        assert domain_user.is_active == sample_db_user.is_active
        assert domain_user.created_at == sample_db_user.created_at
        assert domain_user.updated_at == sample_db_user.updated_at
        assert domain_user.last_login_at == sample_db_user.last_login_at

    def test_to_domain_creates_value_objects(self, sample_db_user):
        """Should create proper value objects from primitives."""
        domain_user = UserMapper.to_domain(sample_db_user)

        assert isinstance(domain_user.id, UserId)
        assert isinstance(domain_user.email, Email)
        assert isinstance(domain_user.password, HashedPassword)

    def test_to_domain_preserves_uuid(self, sample_db_user):
        """Should preserve UUID value correctly."""
        domain_user = UserMapper.to_domain(sample_db_user)

        assert domain_user.id.value == sample_db_user.id

    def test_to_domain_preserves_email(self, sample_db_user):
        """Should preserve email value correctly."""
        domain_user = UserMapper.to_domain(sample_db_user)

        assert domain_user.email.value == sample_db_user.email

    def test_to_domain_preserves_password_hash(self, sample_db_user):
        """Should preserve password hash correctly."""
        domain_user = UserMapper.to_domain(sample_db_user)

        assert domain_user.password.hash_value == sample_db_user.password_hash

    def test_to_domain_handles_null_last_login(self):
        """Should handle NULL last_login_at correctly."""
        db_user = DBUser(
            id=uuid4(),
            email="test@example.com",
            password_hash="$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP",
            email_verified=False,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login_at=None
        )

        domain_user = UserMapper.to_domain(db_user)

        assert domain_user.last_login_at is None

    def test_to_domain_with_email_verified_false(self):
        """Should correctly map email_verified=False."""
        db_user = DBUser(
            id=uuid4(),
            email="unverified@example.com",
            password_hash="$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP",
            email_verified=False,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login_at=None
        )

        domain_user = UserMapper.to_domain(db_user)

        assert domain_user.email_verified is False

    def test_to_domain_with_inactive_user(self):
        """Should correctly map is_active=False."""
        db_user = DBUser(
            id=uuid4(),
            email="inactive@example.com",
            password_hash="$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP",
            email_verified=True,
            is_active=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login_at=None
        )

        domain_user = UserMapper.to_domain(db_user)

        assert domain_user.is_active is False


class TestUserMapperToPersistence:
    """Test UserMapper.to_persistence() method."""

    def test_to_persistence_converts_all_fields(self, sample_domain_user):
        """Should convert all domain fields to database fields."""
        db_user = UserMapper.to_persistence(sample_domain_user)

        assert isinstance(db_user, DBUser)
        assert db_user.id == sample_domain_user.id.value
        assert db_user.email == str(sample_domain_user.email)
        assert db_user.password_hash == sample_domain_user.password.hash_value
        assert db_user.email_verified == sample_domain_user.email_verified
        assert db_user.is_active == sample_domain_user.is_active
        assert db_user.created_at == sample_domain_user.created_at
        assert db_user.updated_at == sample_domain_user.updated_at
        assert db_user.last_login_at == sample_domain_user.last_login_at

    def test_to_persistence_extracts_uuid_from_value_object(self, sample_domain_user):
        """Should extract UUID from UserId value object."""
        db_user = UserMapper.to_persistence(sample_domain_user)

        assert db_user.id == sample_domain_user.id.value
        assert isinstance(db_user.id, type(sample_domain_user.id.value))

    def test_to_persistence_extracts_email_string(self, sample_domain_user):
        """Should extract string from Email value object."""
        db_user = UserMapper.to_persistence(sample_domain_user)

        assert db_user.email == str(sample_domain_user.email)
        assert isinstance(db_user.email, str)

    def test_to_persistence_extracts_password_hash(self, sample_domain_user):
        """Should extract hash from HashedPassword value object."""
        db_user = UserMapper.to_persistence(sample_domain_user)

        assert db_user.password_hash == sample_domain_user.password.hash_value
        assert isinstance(db_user.password_hash, str)

    def test_to_persistence_preserves_timestamps(self, sample_domain_user):
        """Should preserve timestamp values."""
        db_user = UserMapper.to_persistence(sample_domain_user)

        assert db_user.created_at == sample_domain_user.created_at
        assert db_user.updated_at == sample_domain_user.updated_at

    def test_to_persistence_handles_none_last_login(self, sample_domain_user):
        """Should handle None last_login_at correctly."""
        sample_domain_user = DomainUser(
            id=sample_domain_user.id,
            email=sample_domain_user.email,
            password=sample_domain_user.password,
            email_verified=sample_domain_user.email_verified,
            is_active=sample_domain_user.is_active,
            created_at=sample_domain_user.created_at,
            updated_at=sample_domain_user.updated_at,
            last_login_at=None
        )

        db_user = UserMapper.to_persistence(sample_domain_user)

        assert db_user.last_login_at is None


class TestUserMapperUpdateDbFromDomain:
    """Test UserMapper.update_db_from_domain() method."""

    def test_update_db_from_domain_updates_mutable_fields(self, sample_db_user, sample_domain_user):
        """Should update all mutable fields."""
        original_id = sample_db_user.id
        original_created_at = sample_db_user.created_at

        updated_db_user = UserMapper.update_db_from_domain(sample_db_user, sample_domain_user)

        # Mutable fields updated
        assert updated_db_user.email == str(sample_domain_user.email)
        assert updated_db_user.password_hash == sample_domain_user.password.hash_value
        assert updated_db_user.email_verified == sample_domain_user.email_verified
        assert updated_db_user.is_active == sample_domain_user.is_active
        assert updated_db_user.updated_at == sample_domain_user.updated_at
        assert updated_db_user.last_login_at == sample_domain_user.last_login_at

        # Immutable fields NOT updated (preserved from original db_user)
        assert updated_db_user.id == original_id
        assert updated_db_user.created_at == original_created_at

    def test_update_db_from_domain_returns_same_instance(self, sample_db_user, sample_domain_user):
        """Should return the same DB user instance (in-place modification)."""
        updated_db_user = UserMapper.update_db_from_domain(sample_db_user, sample_domain_user)

        assert updated_db_user is sample_db_user

    def test_update_db_from_domain_does_not_change_id(self, sample_db_user, sample_domain_user):
        """Should NOT change the primary key ID."""
        original_id = sample_db_user.id

        UserMapper.update_db_from_domain(sample_db_user, sample_domain_user)

        assert sample_db_user.id == original_id

    def test_update_db_from_domain_does_not_change_created_at(self, sample_db_user, sample_domain_user):
        """Should NOT change the created_at timestamp."""
        original_created_at = sample_db_user.created_at

        UserMapper.update_db_from_domain(sample_db_user, sample_domain_user)

        assert sample_db_user.created_at == original_created_at

    def test_update_db_from_domain_changes_email(self, sample_db_user):
        """Should update email when domain user email changes."""
        new_email = Email.from_string("newemail@example.com")
        domain_user = DomainUser(
            id=UserId.from_string(str(sample_db_user.id)),
            email=new_email,
            password=HashedPassword.from_hash(sample_db_user.password_hash),
            email_verified=sample_db_user.email_verified,
            is_active=sample_db_user.is_active,
            created_at=sample_db_user.created_at,
            updated_at=datetime.utcnow(),
            last_login_at=sample_db_user.last_login_at
        )

        UserMapper.update_db_from_domain(sample_db_user, domain_user)

        assert sample_db_user.email == "newemail@example.com"

    def test_update_db_from_domain_changes_password(self, sample_db_user):
        """Should update password_hash when domain user password changes."""
        new_password = HashedPassword.from_plain_text("NewSecurePass456")
        domain_user = DomainUser(
            id=UserId.from_string(str(sample_db_user.id)),
            email=Email.from_string(sample_db_user.email),
            password=new_password,
            email_verified=sample_db_user.email_verified,
            is_active=sample_db_user.is_active,
            created_at=sample_db_user.created_at,
            updated_at=datetime.utcnow(),
            last_login_at=sample_db_user.last_login_at
        )

        UserMapper.update_db_from_domain(sample_db_user, domain_user)

        assert sample_db_user.password_hash == new_password.hash_value

    def test_update_db_from_domain_verifies_email(self, sample_db_user):
        """Should update email_verified flag."""
        domain_user = DomainUser(
            id=UserId.from_string(str(sample_db_user.id)),
            email=Email.from_string(sample_db_user.email),
            password=HashedPassword.from_hash(sample_db_user.password_hash),
            email_verified=True,  # Changed to True
            is_active=sample_db_user.is_active,
            created_at=sample_db_user.created_at,
            updated_at=datetime.utcnow(),
            last_login_at=sample_db_user.last_login_at
        )

        UserMapper.update_db_from_domain(sample_db_user, domain_user)

        assert sample_db_user.email_verified is True

    def test_update_db_from_domain_deactivates_user(self, sample_db_user):
        """Should update is_active flag."""
        domain_user = DomainUser(
            id=UserId.from_string(str(sample_db_user.id)),
            email=Email.from_string(sample_db_user.email),
            password=HashedPassword.from_hash(sample_db_user.password_hash),
            email_verified=sample_db_user.email_verified,
            is_active=False,  # Changed to False
            created_at=sample_db_user.created_at,
            updated_at=datetime.utcnow(),
            last_login_at=sample_db_user.last_login_at
        )

        UserMapper.update_db_from_domain(sample_db_user, domain_user)

        assert sample_db_user.is_active is False


class TestUserMapperRoundTrip:
    """Test round-trip conversions (domain → persistence → domain)."""

    def test_round_trip_preserves_data(self, sample_domain_user):
        """Should preserve all data through round-trip conversion."""
        # Domain → Persistence
        db_user = UserMapper.to_persistence(sample_domain_user)

        # Persistence → Domain
        restored_domain_user = UserMapper.to_domain(db_user)

        # Verify all fields match
        assert str(restored_domain_user.id) == str(sample_domain_user.id)
        assert str(restored_domain_user.email) == str(sample_domain_user.email)
        assert restored_domain_user.password.hash_value == sample_domain_user.password.hash_value
        assert restored_domain_user.email_verified == sample_domain_user.email_verified
        assert restored_domain_user.is_active == sample_domain_user.is_active
        assert restored_domain_user.created_at == sample_domain_user.created_at
        assert restored_domain_user.updated_at == sample_domain_user.updated_at
        assert restored_domain_user.last_login_at == sample_domain_user.last_login_at

    def test_reverse_round_trip_preserves_data(self, sample_db_user):
        """Should preserve all data through reverse round-trip conversion."""
        # Persistence → Domain
        domain_user = UserMapper.to_domain(sample_db_user)

        # Domain → Persistence
        restored_db_user = UserMapper.to_persistence(domain_user)

        # Verify all fields match
        assert restored_db_user.id == sample_db_user.id
        assert restored_db_user.email == sample_db_user.email
        assert restored_db_user.password_hash == sample_db_user.password_hash
        assert restored_db_user.email_verified == sample_db_user.email_verified
        assert restored_db_user.is_active == sample_db_user.is_active
        assert restored_db_user.created_at == sample_db_user.created_at
        assert restored_db_user.updated_at == sample_db_user.updated_at
        assert restored_db_user.last_login_at == sample_db_user.last_login_at
