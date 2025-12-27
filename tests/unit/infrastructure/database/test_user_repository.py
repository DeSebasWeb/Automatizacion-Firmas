"""Unit tests for UserRepository implementation."""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

# Import domain without going through infrastructure __init__.py to avoid circular imports
from domain.entities.user import User as DomainUser
from domain.value_objects.user_id import UserId
from domain.value_objects.email import Email
from domain.value_objects.hashed_password import HashedPassword
from domain.exceptions import (
    UserNotFoundError,
    DuplicateEmailError,
    RepositoryError
)

# Import models and repository directly from their modules, not through package __init__.py
# This avoids triggering infrastructure.database.__init__.py which causes circular import
import importlib.util

# Load User model directly
user_model_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "infrastructure" / "database" / "models" / "user.py"
spec = importlib.util.spec_from_file_location("user_model", user_model_path)
user_model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_model)
DBUser = user_model.User

# Load UserRepository directly
repo_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "infrastructure" / "database" / "repositories" / "user_repository_impl.py"
spec = importlib.util.spec_from_file_location("user_repository", repo_path)
repo_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repo_module)
UserRepository = repo_module.UserRepository


@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.flush = Mock()
    session.rollback = Mock()
    session.execute = Mock()
    return session


@pytest.fixture
def sample_domain_user():
    """Create a sample domain user."""
    return DomainUser(
        id=UserId.generate(),
        email=Email.from_string("test@example.com"),
        password=HashedPassword.from_plain_text("SecurePass123"),
        email_verified=False,
        is_active=True,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        last_login_at=None
    )


@pytest.fixture
def sample_db_user():
    """Create a sample database user."""
    return DBUser(
        id=uuid4(),
        email="dbtest@example.com",
        password_hash="$2b$12$abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOP",
        email_verified=True,
        is_active=True,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 15, 10, 30, 0),
        last_login_at=datetime(2024, 1, 15, 11, 0, 0)
    )


@pytest.fixture
def user_repository(mock_session):
    """Create UserRepository instance with mock session."""
    return UserRepository(mock_session)


class TestUserRepositoryCreate:
    """Test UserRepository.create() method."""

    def test_create_user_success(self, user_repository, mock_session, sample_domain_user):
        """Should successfully create a new user."""
        # Setup
        mock_session.flush.return_value = None

        # Execute
        result = user_repository.create(sample_domain_user)

        # Verify
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert isinstance(result, DomainUser)
        assert str(result.email) == str(sample_domain_user.email)

    def test_create_user_duplicate_email_raises_error(self, user_repository, mock_session, sample_domain_user):
        """Should raise DuplicateEmailError when email already exists."""
        # Setup - simulate IntegrityError for duplicate email
        integrity_error = IntegrityError(
            statement="INSERT INTO users...",
            params={},
            orig=Exception("duplicate key value violates unique constraint \"users_email_key\"")
        )
        mock_session.flush.side_effect = integrity_error

        # Execute & Verify
        with pytest.raises(DuplicateEmailError) as exc_info:
            user_repository.create(sample_domain_user)

        assert str(sample_domain_user.email) in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    def test_create_user_other_integrity_error_raises_repository_error(
        self, user_repository, mock_session, sample_domain_user
    ):
        """Should raise RepositoryError for non-duplicate integrity errors."""
        # Setup - simulate other IntegrityError
        integrity_error = IntegrityError(
            statement="INSERT INTO users...",
            params={},
            orig=Exception("some other constraint violation")
        )
        mock_session.flush.side_effect = integrity_error

        # Execute & Verify
        with pytest.raises(RepositoryError):
            user_repository.create(sample_domain_user)

        mock_session.rollback.assert_called_once()

    def test_create_user_sqlalchemy_error_raises_repository_error(
        self, user_repository, mock_session, sample_domain_user
    ):
        """Should raise RepositoryError for generic SQLAlchemy errors."""
        # Setup
        mock_session.flush.side_effect = SQLAlchemyError("Database connection failed")

        # Execute & Verify
        with pytest.raises(RepositoryError) as exc_info:
            user_repository.create(sample_domain_user)

        assert "Failed to create user" in str(exc_info.value)
        mock_session.rollback.assert_called_once()


class TestUserRepositoryFindById:
    """Test UserRepository.find_by_id() method."""

    def test_find_by_id_user_exists(self, user_repository, mock_session, sample_db_user):
        """Should return domain user when user exists."""
        # Setup
        user_id = UserId.from_string(str(sample_db_user.id))
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_db_user
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.find_by_id(user_id)

        # Verify
        assert result is not None
        assert isinstance(result, DomainUser)
        assert str(result.id) == str(sample_db_user.id)
        assert str(result.email) == sample_db_user.email

    def test_find_by_id_user_not_found(self, user_repository, mock_session):
        """Should return None when user doesn't exist."""
        # Setup
        user_id = UserId.generate()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.find_by_id(user_id)

        # Verify
        assert result is None

    def test_find_by_id_sqlalchemy_error_raises_repository_error(
        self, user_repository, mock_session
    ):
        """Should raise RepositoryError when query fails."""
        # Setup
        user_id = UserId.generate()
        mock_session.query.side_effect = SQLAlchemyError("Connection lost")

        # Execute & Verify
        with pytest.raises(RepositoryError) as exc_info:
            user_repository.find_by_id(user_id)

        assert "Failed to find user" in str(exc_info.value)


class TestUserRepositoryFindByEmail:
    """Test UserRepository.find_by_email() method."""

    def test_find_by_email_user_exists(self, user_repository, mock_session, sample_db_user):
        """Should return domain user when user with email exists."""
        # Setup
        email = Email.from_string(sample_db_user.email)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_db_user
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.find_by_email(email)

        # Verify
        assert result is not None
        assert isinstance(result, DomainUser)
        assert str(result.email) == str(email)

    def test_find_by_email_user_not_found(self, user_repository, mock_session):
        """Should return None when no user with email exists."""
        # Setup
        email = Email.from_string("notfound@example.com")
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.find_by_email(email)

        # Verify
        assert result is None

    def test_find_by_email_sqlalchemy_error_raises_repository_error(
        self, user_repository, mock_session
    ):
        """Should raise RepositoryError when query fails."""
        # Setup
        email = Email.from_string("test@example.com")
        mock_session.query.side_effect = SQLAlchemyError("Connection lost")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            user_repository.find_by_email(email)


class TestUserRepositoryUpdate:
    """Test UserRepository.update() method."""

    def test_update_user_success(self, user_repository, mock_session, sample_db_user, sample_domain_user):
        """Should successfully update an existing user."""
        # Setup
        sample_domain_user = DomainUser(
            id=UserId.from_string(str(sample_db_user.id)),
            email=Email.from_string("updated@example.com"),
            password=HashedPassword.from_hash(sample_db_user.password_hash),
            email_verified=True,
            is_active=True,
            created_at=sample_db_user.created_at,
            updated_at=datetime.utcnow(),
            last_login_at=None
        )

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_db_user
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.update(sample_domain_user)

        # Verify
        assert isinstance(result, DomainUser)
        mock_session.flush.assert_called_once()
        # Email should be updated in db_user
        assert sample_db_user.email == "updated@example.com"

    def test_update_user_not_found_raises_error(self, user_repository, mock_session, sample_domain_user):
        """Should raise UserNotFoundError when user doesn't exist."""
        # Setup
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        # Execute & Verify
        with pytest.raises(UserNotFoundError) as exc_info:
            user_repository.update(sample_domain_user)

        assert str(sample_domain_user.id) in str(exc_info.value)
        # Should NOT call rollback for UserNotFoundError (it's a domain exception, not DB error)
        mock_session.flush.assert_not_called()

    def test_update_user_sqlalchemy_error_raises_repository_error(
        self, user_repository, mock_session, sample_db_user, sample_domain_user
    ):
        """Should raise RepositoryError for SQLAlchemy errors."""
        # Setup
        sample_domain_user = DomainUser(
            id=UserId.from_string(str(sample_db_user.id)),
            email=Email.from_string("updated@example.com"),
            password=HashedPassword.from_hash(sample_db_user.password_hash),
            email_verified=True,
            is_active=True,
            created_at=sample_db_user.created_at,
            updated_at=datetime.utcnow(),
            last_login_at=None
        )

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_db_user
        mock_session.query.return_value = mock_query
        mock_session.flush.side_effect = SQLAlchemyError("Update failed")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            user_repository.update(sample_domain_user)

        mock_session.rollback.assert_called_once()


class TestUserRepositoryDelete:
    """Test UserRepository.delete() method."""

    def test_delete_user_success(self, user_repository, mock_session):
        """Should successfully delete an existing user."""
        # Setup
        user_id = UserId.generate()
        mock_query = Mock()
        mock_query.filter.return_value.delete.return_value = 1  # 1 row deleted
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.delete(user_id)

        # Verify
        assert result is True
        mock_session.flush.assert_called_once()

    def test_delete_user_not_found(self, user_repository, mock_session):
        """Should return False when user doesn't exist."""
        # Setup
        user_id = UserId.generate()
        mock_query = Mock()
        mock_query.filter.return_value.delete.return_value = 0  # 0 rows deleted
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.delete(user_id)

        # Verify
        assert result is False

    def test_delete_user_sqlalchemy_error_raises_repository_error(
        self, user_repository, mock_session
    ):
        """Should raise RepositoryError for SQLAlchemy errors."""
        # Setup
        user_id = UserId.generate()
        mock_session.query.side_effect = SQLAlchemyError("Delete failed")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            user_repository.delete(user_id)

        mock_session.rollback.assert_called_once()


class TestUserRepositoryExistsByEmail:
    """Test UserRepository.exists_by_email() method."""

    def test_exists_by_email_user_exists(self, user_repository, mock_session):
        """Should return True when user with email exists."""
        # Setup
        email = Email.from_string("exists@example.com")
        mock_result = Mock()
        mock_result.scalar.return_value = True
        mock_session.execute.return_value = mock_result

        # Execute
        result = user_repository.exists_by_email(email)

        # Verify
        assert result is True
        mock_session.execute.assert_called_once()

    def test_exists_by_email_user_not_found(self, user_repository, mock_session):
        """Should return False when no user with email exists."""
        # Setup
        email = Email.from_string("notfound@example.com")
        mock_result = Mock()
        mock_result.scalar.return_value = False
        mock_session.execute.return_value = mock_result

        # Execute
        result = user_repository.exists_by_email(email)

        # Verify
        assert result is False

    def test_exists_by_email_sqlalchemy_error_raises_repository_error(
        self, user_repository, mock_session
    ):
        """Should raise RepositoryError for SQLAlchemy errors."""
        # Setup
        email = Email.from_string("test@example.com")
        mock_session.execute.side_effect = SQLAlchemyError("Query failed")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            user_repository.exists_by_email(email)


class TestUserRepositoryListAll:
    """Test UserRepository.list_all() method."""

    def test_list_all_returns_users(self, user_repository, mock_session, sample_db_user):
        """Should return list of domain users."""
        # Setup
        db_users = [sample_db_user]
        mock_query = Mock()
        mock_query.limit.return_value.offset.return_value.all.return_value = db_users
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.list_all(limit=10, offset=0)

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], DomainUser)

    def test_list_all_empty_database(self, user_repository, mock_session):
        """Should return empty list when no users exist."""
        # Setup
        mock_query = Mock()
        mock_query.limit.return_value.offset.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.list_all()

        # Verify
        assert result == []

    def test_list_all_pagination_parameters(self, user_repository, mock_session):
        """Should apply limit and offset parameters correctly."""
        # Setup
        mock_query = Mock()
        mock_limit = Mock()
        mock_offset = Mock()
        mock_query.limit.return_value = mock_limit
        mock_limit.offset.return_value = mock_offset
        mock_offset.all.return_value = []
        mock_session.query.return_value = mock_query

        # Execute
        user_repository.list_all(limit=50, offset=100)

        # Verify
        mock_query.limit.assert_called_once_with(50)
        mock_limit.offset.assert_called_once_with(100)

    def test_list_all_sqlalchemy_error_raises_repository_error(
        self, user_repository, mock_session
    ):
        """Should raise RepositoryError for SQLAlchemy errors."""
        # Setup
        mock_session.query.side_effect = SQLAlchemyError("Query failed")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            user_repository.list_all()


class TestUserRepositoryCount:
    """Test UserRepository.count() method."""

    def test_count_returns_total(self, user_repository, mock_session):
        """Should return total number of users."""
        # Setup
        mock_query = Mock()
        mock_query.count.return_value = 42
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.count()

        # Verify
        assert result == 42

    def test_count_zero_users(self, user_repository, mock_session):
        """Should return 0 when no users exist."""
        # Setup
        mock_query = Mock()
        mock_query.count.return_value = 0
        mock_session.query.return_value = mock_query

        # Execute
        result = user_repository.count()

        # Verify
        assert result == 0

    def test_count_sqlalchemy_error_raises_repository_error(
        self, user_repository, mock_session
    ):
        """Should raise RepositoryError for SQLAlchemy errors."""
        # Setup
        mock_session.query.side_effect = SQLAlchemyError("Query failed")

        # Execute & Verify
        with pytest.raises(RepositoryError):
            user_repository.count()
