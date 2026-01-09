"""FastAPI dependencies for dependency injection."""
from typing import Annotated, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import structlog

from src.infrastructure.database.dependencies import get_db
from src.infrastructure.database.repositories.user_repository_impl import UserRepository
from src.infrastructure.database.repositories.api_key_repository_impl import APIKeyRepository
from src.domain.repositories.user_repository import IUserRepository
from src.domain.repositories.api_key_repository import IAPIKeyRepository
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.authenticate_user_use_case import AuthenticateUserUseCase
from src.application.use_cases.get_user_by_id_use_case import GetUserByIdUseCase
from src.application.use_cases.create_api_key_use_case import CreateAPIKeyUseCase
from src.application.use_cases.validate_api_key_use_case import ValidateAPIKeyUseCase
from src.application.use_cases.list_api_keys_use_case import ListAPIKeysUseCase
from src.application.use_cases.revoke_api_key_use_case import RevokeAPIKeyUseCase
from src.application.use_cases.get_api_key_scopes_use_case import GetAPIKeyScopesUseCase
from src.application.use_cases.validate_api_key_use_case import InvalidCredentialsError
from src.infrastructure.security.jwt_handler import JWTHandler
from src.domain.entities.user import User
from src.domain.entities.api_key import APIKey
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
# API KEY REPOSITORY DEPENDENCIES
# =========================================================================

def get_api_key_repository(db: Session = Depends(get_db)) -> IAPIKeyRepository:
    """
    Get API key repository instance.

    Args:
        db: Database session from get_db dependency

    Returns:
        IAPIKeyRepository implementation
    """
    return APIKeyRepository(db)


# =========================================================================
# API KEY USE CASE DEPENDENCIES
# =========================================================================

def get_create_api_key_use_case(
    api_key_repo: IAPIKeyRepository = Depends(get_api_key_repository)
) -> CreateAPIKeyUseCase:
    """
    Get create API key use case.

    Args:
        api_key_repo: API key repository (injected)

    Returns:
        CreateAPIKeyUseCase instance
    """
    return CreateAPIKeyUseCase(api_key_repo)


def get_validate_api_key_use_case(
    api_key_repo: IAPIKeyRepository = Depends(get_api_key_repository)
) -> ValidateAPIKeyUseCase:
    """
    Get validate API key use case.

    Args:
        api_key_repo: API key repository (injected)

    Returns:
        ValidateAPIKeyUseCase instance
    """
    return ValidateAPIKeyUseCase(api_key_repo)


def get_list_api_keys_use_case(
    api_key_repo: IAPIKeyRepository = Depends(get_api_key_repository)
) -> ListAPIKeysUseCase:
    """
    Get list API keys use case.

    Args:
        api_key_repo: API key repository (injected)

    Returns:
        ListAPIKeysUseCase instance
    """
    return ListAPIKeysUseCase(api_key_repo)


def get_revoke_api_key_use_case(
    api_key_repo: IAPIKeyRepository = Depends(get_api_key_repository)
) -> RevokeAPIKeyUseCase:
    """
    Get revoke API key use case.

    Args:
        api_key_repo: API key repository (injected)

    Returns:
        RevokeAPIKeyUseCase instance
    """
    return RevokeAPIKeyUseCase(api_key_repo)


def get_api_key_scopes_use_case(
    api_key_repo: IAPIKeyRepository = Depends(get_api_key_repository)
) -> GetAPIKeyScopesUseCase:
    """
    Get API key scopes use case.

    Args:
        api_key_repo: API key repository (injected)

    Returns:
        GetAPIKeyScopesUseCase instance
    """
    return GetAPIKeyScopesUseCase(api_key_repo)


# =========================================================================
# API KEY AUTHENTICATION DEPENDENCIES
# =========================================================================

async def get_api_key_from_header(
    x_api_key: Optional[str] = Header(None, description="API Key for authentication"),
    use_case: ValidateAPIKeyUseCase = Depends(get_validate_api_key_use_case),
) -> APIKey:
    """
    Validate API key from X-API-Key header.

    Alternative authentication to JWT for programmatic access.

    Args:
        x_api_key: API key from X-API-Key header
        use_case: ValidateAPIKeyUseCase dependency

    Returns:
        Valid APIKey entity

    Raises:
        HTTPException 401: If API key is missing or invalid

    Usage:
        @router.get("/protected")
        async def protected_endpoint(
            api_key: APIKey = Depends(get_api_key_from_header)
        ):
            user_id = api_key.user_id
            ...

    Example Request:
        curl -H "X-API-Key: vfy_abc123..." http://localhost:8000/api/v1/documents
    """
    if not x_api_key:
        logger.warning("API key authentication attempted but no key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    try:
        # Validate key (no scope checking - done by require_scope)
        api_key = use_case.validate_without_scopes(x_api_key)
        return api_key

    except InvalidCredentialsError as e:
        logger.warning("Invalid API key provided", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "ApiKey"},
        )


async def get_optional_api_key(
    x_api_key: Optional[str] = Header(None),
    use_case: ValidateAPIKeyUseCase = Depends(get_validate_api_key_use_case),
) -> Optional[APIKey]:
    """
    Optional API key authentication.

    Returns APIKey if valid key provided, None otherwise.
    Does NOT raise exception if key is missing.

    Use for endpoints that support both authenticated and anonymous access.

    Args:
        x_api_key: Optional API key from header
        use_case: ValidateAPIKeyUseCase dependency

    Returns:
        APIKey if valid key provided, None otherwise

    Usage:
        @router.get("/public-or-private")
        async def flexible_endpoint(
            api_key: Optional[APIKey] = Depends(get_optional_api_key)
        ):
            if api_key:
                # Authenticated - full data
                ...
            else:
                # Anonymous - limited data
                ...
    """
    if not x_api_key:
        return None

    try:
        api_key = use_case.validate_without_scopes(x_api_key)
        return api_key
    except InvalidCredentialsError:
        # Invalid key provided - treat as anonymous
        logger.debug("Invalid API key provided, treating as anonymous")
        return None


# =========================================================================
# TYPE ALIASES FOR CLEANER ENDPOINT SIGNATURES
# =========================================================================

CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAPIKey = Annotated[APIKey, Depends(get_api_key_from_header)]
OptionalAPIKey = Annotated[Optional[APIKey], Depends(get_optional_api_key)]
