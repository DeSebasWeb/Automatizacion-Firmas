"""API Keys CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import structlog

from src.infrastructure.api.schemas.api_key_schemas import (
    CreateAPIKeyRequest,
    APIKeyResponse,
    APIKeyListItem,
    APIKeyListResponse,
    AvailableScopeResponse,
    ErrorResponse,
)
from src.application.use_cases.create_api_key_use_case import CreateAPIKeyUseCase
from src.application.use_cases.list_api_keys_use_case import ListAPIKeysUseCase
from src.application.use_cases.revoke_api_key_use_case import (
    RevokeAPIKeyUseCase,
    APIKeyNotFoundError,
    UnauthorizedError,
)
from src.application.use_cases.get_api_key_scopes_use_case import GetAPIKeyScopesUseCase
from src.domain.entities.user import User
from src.infrastructure.api.dependencies import (
    get_current_user,
    get_create_api_key_use_case,
    get_list_api_keys_use_case,
    get_revoke_api_key_use_case,
    get_api_key_scopes_use_case,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post(
    "",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API Key",
    description="""
    Create new API key for programmatic access.

    **⚠️ SECURITY WARNING:**
    The plaintext API key is returned ONLY ONCE in the response.
    Save it immediately - you will never see it again!

    **Authentication:**
    Requires JWT authentication (X-API-Key not allowed for this endpoint).

    **Scopes:**
    - Must specify at least one scope
    - All scopes must exist in the catalog (see GET /api-keys/scopes)
    - Invalid scopes will be rejected

    **Expiration:**
    - expires_in_days: null = never expires
    - Maximum: 3650 days (10 years)
    """,
    responses={
        201: {
            "description": "API key created successfully",
            "model": APIKeyResponse,
        },
        400: {
            "description": "Invalid request (bad scopes, invalid expiration, etc.)",
            "model": ErrorResponse,
        },
        401: {
            "description": "Not authenticated (JWT required)",
            "model": ErrorResponse,
        },
    },
)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateAPIKeyUseCase = Depends(get_create_api_key_use_case),
) -> APIKeyResponse:
    """
    Create new API key.

    Returns the plaintext key ONLY ONCE - save it immediately!
    """
    logger.info(
        "API key creation requested",
        user_id=str(current_user.id),
        name=request.name,
        scopes=request.scopes,
    )

    try:
        # Create API key
        api_key, plaintext_key = use_case.execute(
            user_id_str=str(current_user.id),
            name=request.name,
            scope_codes=request.scopes,
            expires_in_days=request.expires_in_days,
        )

        logger.info(
            "API key created successfully",
            api_key_id=api_key.id,
            user_id=str(current_user.id),
        )

        # Build response (includes plaintext key)
        return APIKeyResponse(
            id=api_key.id,
            key=plaintext_key,  # ⚠️ ONLY time plaintext is shown
            key_prefix=api_key.key_prefix,
            name=api_key.name,
            scopes=api_key.get_scope_codes(),
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
        )

    except ValueError as e:
        logger.warning("Invalid API key creation request", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=APIKeyListResponse,
    summary="List API Keys",
    description="""
    List all API keys for the current user.

    Returns both active and revoked keys for visibility.

    **Note:**
    Plaintext keys are NOT included (only shown on creation).
    Only the key prefix is shown for identification.

    **Authentication:**
    Requires JWT authentication.
    """,
    responses={
        200: {
            "description": "List of API keys",
            "model": APIKeyListResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
    },
)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    use_case: ListAPIKeysUseCase = Depends(get_list_api_keys_use_case),
) -> APIKeyListResponse:
    """
    List all API keys for current user.
    """
    logger.info("Listing API keys", user_id=str(current_user.id))

    api_keys = use_case.execute(
        user_id_str=str(current_user.id),
        active_only=False,  # Show all (active + revoked)
    )

    # Convert to DTOs
    api_key_items = [
        APIKeyListItem(
            id=key.id,
            key_prefix=key.key_prefix,
            name=key.name,
            scopes=key.get_scope_codes(),
            is_active=key.is_active,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            created_at=key.created_at,
            revoked_at=key.revoked_at,
        )
        for key in api_keys
    ]

    # Count active keys
    active_count = sum(1 for key in api_keys if key.is_valid())

    logger.info(
        "API keys listed",
        user_id=str(current_user.id),
        total=len(api_keys),
        active=active_count,
    )

    return APIKeyListResponse(
        api_keys=api_key_items,
        total=len(api_keys),
        active_count=active_count,
    )


@router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API Key",
    description="""
    Revoke API key (soft delete).

    **Effects:**
    - Sets is_active = false
    - Sets revoked_at = current timestamp
    - Future API requests with this key will be rejected

    **Important:**
    - Revocation is PERMANENT (cannot be undone)
    - The key record is preserved for audit trail
    - Only the key owner can revoke it

    **Authentication:**
    Requires JWT authentication.
    """,
    responses={
        204: {"description": "API key revoked successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        403: {
            "description": "Forbidden (not your key)",
            "model": ErrorResponse,
        },
        404: {"description": "API key not found", "model": ErrorResponse},
    },
)
async def revoke_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user),
    use_case: RevokeAPIKeyUseCase = Depends(get_revoke_api_key_use_case),
):
    """
    Revoke API key (cannot be undone).
    """
    logger.info(
        "API key revocation requested",
        api_key_id=api_key_id,
        user_id=str(current_user.id),
    )

    try:
        use_case.execute(
            api_key_id=api_key_id,
            user_id_str=str(current_user.id),
        )

        logger.info(
            "API key revoked successfully",
            api_key_id=api_key_id,
            user_id=str(current_user.id),
        )

        return  # 204 No Content

    except APIKeyNotFoundError as e:
        logger.warning("API key not found for revocation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except UnauthorizedError as e:
        logger.warning("Unauthorized revocation attempt", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get(
    "/scopes",
    response_model=List[AvailableScopeResponse],
    summary="Get Available Scopes",
    description="""
    Get list of all available permission scopes.

    Use this endpoint to:
    - Populate UI dropdowns for scope selection
    - Show scope descriptions to users
    - Validate scope codes before creating keys

    **Authentication:**
    Requires JWT authentication.
    """,
    responses={
        200: {
            "description": "List of available scopes",
            "model": List[AvailableScopeResponse],
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
    },
)
async def get_available_scopes(
    current_user: User = Depends(get_current_user),
    use_case: GetAPIKeyScopesUseCase = Depends(get_api_key_scopes_use_case),
) -> List[AvailableScopeResponse]:
    """
    Get list of available permission scopes.
    """
    logger.info("Available scopes requested", user_id=str(current_user.id))

    scopes = use_case.execute()

    # Convert to DTOs
    scope_responses = [
        AvailableScopeResponse(
            code=scope["code"],
            name=scope["name"],
            description=scope["description"],
            category=scope["category"],
        )
        for scope in scopes
    ]

    logger.info("Available scopes returned", count=len(scope_responses))

    return scope_responses
