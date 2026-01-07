"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from src.infrastructure.api.schemas.register_request import RegisterRequest
from src.infrastructure.api.schemas.login_request import LoginRequest
from src.infrastructure.api.schemas.token_response import TokenResponse
from src.infrastructure.api.schemas.user_schemas import UserResponse
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.authenticate_user_use_case import AuthenticateUserUseCase
from src.application.use_cases.get_user_by_id_use_case import GetUserByIdUseCase
from src.domain.repositories.user_repository import IUserRepository
from src.infrastructure.api.dependencies import (
    get_register_use_case,
    get_authenticate_use_case,
    get_current_user,
    get_jwt_handler,
    get_user_by_id_use_case,
    get_user_repository,
    CurrentUser
)
from src.infrastructure.security.jwt_handler import JWTHandler
from src.domain.entities.user import User
from src.domain.exceptions.exceptions import (
    DuplicateEmailError,
    InvalidCredentialsError
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="""
    Register a new user account.

    - **email**: Must be unique and valid email format
    - **password**: Minimum 8 characters

    Returns the created user information (without password).

    **Important:** User starts with `is_active=true` but `email_verified=false`.
    Email verification is required before the user can login.
    """
)
async def register(
    request: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_use_case)
):
    """
    Register new user.

    Business rules:
    - Email must be unique
    - Password minimum 8 characters
    - User starts with email_verified=False
    - User starts with is_active=True
    """
    try:
        # Execute use case (use case already logs the details)
        user = use_case.execute(
            email_str=request.email,
            password=request.password
        )

        # Convert domain entity to DTO
        response = UserResponse.from_domain(user)

        return response

    except DuplicateEmailError as e:
        logger.warning("Registration failed: duplicate email", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email already registered: {e.email}"
        )
    except ValueError as e:
        # Email validation or password validation error
        logger.warning("Registration failed: validation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with credentials",
    description="""
    Authenticate with email and password.

    Returns JWT tokens:
    - **access_token**: Short-lived token for API requests (1 hour)
    - **refresh_token**: Long-lived token for obtaining new access tokens (7 days)

    Use the access_token in the Authorization header: `Bearer <access_token>`
    """
)
async def login(
    request: LoginRequest,
    use_case: AuthenticateUserUseCase = Depends(get_authenticate_use_case),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
):
    """
    Login with credentials.

    Returns JWT access token and refresh token.

    Business rules:
    - Email and password must match
    - User must be active
    - Email must be verified (enforced by can_authenticate())
    """
    try:
        # 1. Authenticate user (use case already logs authentication)
        user = use_case.execute(
            email_str=request.email,
            password=request.password
        )

        # 2. Generate JWT tokens
        access_token = jwt_handler.create_access_token(
            user_id=str(user.id),
            email=str(user.email)
        )
        refresh_token = jwt_handler.create_refresh_token(
            user_id=str(user.id)
        )

        # 3. Build response
        response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=jwt_handler.get_expiration_seconds()
        )

        return response

    except InvalidCredentialsError:
        logger.warning("Login failed: invalid credentials", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError as e:
        # Email validation error
        logger.warning("Login failed: validation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="""
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.

    **Authentication required**: Bearer token
    """
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires: Bearer token in Authorization header

    The current_user is automatically injected and validated by the
    get_current_user dependency. If the token is invalid or expired,
    a 401 error is returned before this endpoint is called.

    Note: Authentication is already logged by get_current_user dependency.
    """
    # Convert domain entity to DTO
    return UserResponse.from_domain(current_user)


@router.post(
    "/dev/verify-email/{user_id}",
    response_model=UserResponse,
    summary="[DEV ONLY] Verify user email",
    description="""
    **DEVELOPMENT ONLY** - Remove this endpoint in production!

    Manually verify a user's email for testing purposes.
    In production, this should be done via email verification link.
    """,
    tags=["Development"]
)
async def dev_verify_email(
    user_id: str,
    get_user_use_case: GetUserByIdUseCase = Depends(get_user_by_id_use_case),
    user_repo: IUserRepository = Depends(get_user_repository)
):
    """
    DEV ONLY: Manually verify user email.

    This endpoint should ONLY be used in development/testing.
    Remove or disable in production environments.
    """
    from src.infrastructure.api.config import settings
    from src.domain.value_objects.user_id import UserId
    from src.domain.exceptions.exceptions import UserNotFoundError

    # Safety check: only allow in development
    if not settings.is_development:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available"
        )

    try:
        logger.warning(
            "[DEV] Email verification requested",
            user_id=user_id
        )

        # Get user
        user_id_vo = UserId.from_string(user_id)
        user = user_repo.find_by_id(user_id_vo)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}"
            )

        # Verify email
        user.verify_email()

        # Save changes
        updated_user = user_repo.save(user)

        logger.warning(
            "[DEV] Email verified",
            user_id=str(updated_user.id),
            email=str(updated_user.email)
        )

        return UserResponse.from_domain(updated_user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
