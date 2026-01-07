"""Register user use case."""
import structlog
from src.domain.repositories.user_repository import IUserRepository
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.exceptions.exceptions import DuplicateEmailError

logger = structlog.get_logger(__name__)


class RegisterUserUseCase:
    """
    Use case: Register new user.

    Business rules:
    - Email must be unique
    - Password must meet security requirements (enforced by HashedPassword VO)
    - User starts inactive until email verified
    """

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize use case.

        Args:
            user_repository: User repository implementation
        """
        self._user_repo = user_repository

    def execute(self, email_str: str, password: str) -> User:
        """
        Register new user.

        Args:
            email_str: User email (will be validated)
            password: Plain password (will be hashed)

        Returns:
            Created user entity

        Raises:
            DuplicateEmailError: Email already registered
            ValueError: Invalid email format or weak password
        """
        logger.info("Registering new user", email=email_str)

        # 1. Validate and create Email VO
        email = Email.from_string(email_str)

        # 2. Verify email doesn't exist
        existing_user = self._user_repo.find_by_email(email)
        if existing_user is not None:
            logger.warning("Registration failed: duplicate email", email=str(email))
            raise DuplicateEmailError(str(email))

        # 3. Create User entity (handles password hashing internally)
        user = User.create(email=email, plain_password=password)

        # 4. Persist user
        created_user = self._user_repo.save(user)

        # 5. Log success and return
        logger.info(
            "User registered successfully",
            user_id=str(created_user.id),
            email=str(created_user.email)
        )

        return created_user
