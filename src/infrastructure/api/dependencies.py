"""FastAPI dependencies for dependency injection."""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import structlog

from src.infrastructure.database.dependencies import get_db
from src.infrastructure.database.repositories.user_repository_impl import UserRepository
from src.domain.repositories.user_repository import IUserRepository
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.authenticate_user_use_case import AuthenticateUserUseCase
from src.application.use_cases.get_user_by_id_use_case import GetUserByIdUseCase
from src.infrastructure.security.jwt_handler import JWTHandler
from src.domain.entities.user import User
from src.domain.exceptions.exceptions import UserNotFoundError

logger = structlog.get_logger(__name__)

# Configure HTTPBearer with auto_error=True to ensure proper Swagger UI integration
security = HTTPBearer(
    scheme_name="Bearer",
    description="Enter your JWT access token (without 'Bearer' prefix)"
)


# =========================================================================
# REPOSITORY DEPENDENCIES
# =========================================================================

def get_user_repository(db: Session = Depends(get_db)) -> IUserRepository:
    """
    Get user repository instance.

    Args:
        db: Database session from get_db dependency

    Returns:
        IUserRepository implementation
    """
    return UserRepository(db)


# =========================================================================
# SECURITY DEPENDENCIES
# =========================================================================

def get_jwt_handler() -> JWTHandler:
    """
    Get JWT handler instance.

    Returns:
        JWTHandler for token operations
    """
    return JWTHandler()


# =========================================================================
# USE CASE DEPENDENCIES
# =========================================================================

def get_register_use_case(
    user_repo: IUserRepository = Depends(get_user_repository)
) -> RegisterUserUseCase:
    """
    Get register user use case.

    Args:
        user_repo: User repository (injected)

    Returns:
        RegisterUserUseCase instance
    """
    return RegisterUserUseCase(user_repo)


def get_authenticate_use_case(
    user_repo: IUserRepository = Depends(get_user_repository)
) -> AuthenticateUserUseCase:
    """
    Get authenticate user use case.

    Args:
        user_repo: User repository (injected)

    Returns:
        AuthenticateUserUseCase instance
    """
    return AuthenticateUserUseCase(user_repo)


def get_user_by_id_use_case(
    user_repo: IUserRepository = Depends(get_user_repository)
) -> GetUserByIdUseCase:
    """
    Get user by ID use case.

    Args:
        user_repo: User repository (injected)

    Returns:
        GetUserByIdUseCase instance
    """
    return GetUserByIdUseCase(user_repo)


# =========================================================================
# AUTHENTICATION DEPENDENCIES
# =========================================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    get_user_use_case: GetUserByIdUseCase = Depends(get_user_by_id_use_case)
) -> User:
    """
    Get current authenticated user from JWT token.

    Validates Bearer token from Authorization header and returns
    the authenticated user entity.

    Args:
        credentials: HTTP Bearer token credentials
        jwt_handler: JWT handler for token decoding
        get_user_use_case: Use case to fetch user by ID

    Returns:
        Authenticated User domain entity

    Raises:
        HTTPException 401: Invalid, expired, or missing token
        HTTPException 401: User not found

    Usage:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": str(current_user.id)}
    """
    token = credentials.credentials

    try:
        # 1. Decode JWT token
        payload = jwt_handler.decode_token(token)

        # 2. Extract user_id from payload
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # 3. Verify token type is "access"
        token_type = payload.get("type", "access")
        if token_type != "access":
            logger.warning("Invalid token type", token_type=token_type)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # 4. Fetch user from repository
        user = get_user_use_case.execute(user_id)

        # 5. Verify user can still authenticate (not deactivated)
        if not user.can_authenticate():
            logger.warning(
                "User cannot authenticate",
                user_id=user_id,
                is_active=user.is_active,
                email_verified=user.email_verified
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or unverified",
                headers={"WWW-Authenticate": "Bearer"}
            )

        logger.info("User authenticated successfully", user_id=str(user.id))
        return user

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except UserNotFoundError:
        logger.warning("User not found from token", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError as e:
        # Invalid UUID format
        logger.warning("Invalid user ID format", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier",
            headers={"WWW-Authenticate": "Bearer"}
        )


# =========================================================================
# TYPE ALIASES FOR CLEANER ENDPOINT SIGNATURES
# =========================================================================

CurrentUser = Annotated[User, Depends(get_current_user)]
