"""
API Key authentication middleware helpers.

Note: Main dependency functions are in dependencies.py to avoid circular imports.
This module provides helper functions for scope checking.
"""

from fastapi import HTTPException, status, Depends
from typing import List
import structlog

from src.domain.entities.api_key import APIKey

logger = structlog.get_logger(__name__)


def require_scope(required_scope: str):
    """
    Dependency factory to require specific scope.

    Creates a dependency that validates the API key has the required scope.

    Args:
        required_scope: Scope code required (e.g., "documents:read")

    Returns:
        FastAPI dependency function

    Usage:
        from src.infrastructure.api.dependencies import get_api_key_from_header

        @router.get(
            "/documents",
            dependencies=[Depends(require_scope("documents:read"))]
        )
        async def get_documents(
            api_key: APIKey = Depends(get_api_key_from_header)
        ):
            # User has documents:read scope
            ...

    Example with multiple scopes:
        @router.post(
            "/documents",
            dependencies=[
                Depends(require_scope("documents:write")),
                Depends(require_scope("documents:create"))
            ]
        )
        async def create_document():
            # User has both scopes
            ...
    """

    # Import here to avoid circular dependency
    from src.infrastructure.api.dependencies import get_api_key_from_header

    async def scope_checker(
        api_key: APIKey = Depends(get_api_key_from_header),
    ) -> APIKey:
        """
        Check if API key has required scope.

        Args:
            api_key: Validated API key from header

        Returns:
            APIKey if scope check passes

        Raises:
            HTTPException 403: If scope is missing
        """
        if not api_key.has_scope(required_scope):
            logger.warning(
                "API key lacks required scope",
                api_key_id=api_key.id,
                required_scope=required_scope,
                actual_scopes=api_key.get_scope_codes(),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {required_scope}",
            )

        return api_key

    return scope_checker


def require_scopes(required_scopes: List[str]):
    """
    Dependency factory to require ALL specified scopes.

    Args:
        required_scopes: List of scope codes ALL required

    Returns:
        FastAPI dependency function

    Usage:
        from src.infrastructure.api.dependencies import get_api_key_from_header

        @router.post(
            "/admin/users",
            dependencies=[
                Depends(require_scopes(["admin:all", "users:write"]))
            ]
        )
        async def admin_create_user():
            # User has ALL required scopes
            ...
    """

    # Import here to avoid circular dependency
    from src.infrastructure.api.dependencies import get_api_key_from_header

    async def scopes_checker(
        api_key: APIKey = Depends(get_api_key_from_header),
    ) -> APIKey:
        """
        Check if API key has ALL required scopes.

        Args:
            api_key: Validated API key from header

        Returns:
            APIKey if all scope checks pass

        Raises:
            HTTPException 403: If any scope is missing
        """
        if not api_key.has_scopes(required_scopes):
            missing_scopes = [
                scope for scope in required_scopes if not api_key.has_scope(scope)
            ]
            logger.warning(
                "API key lacks required scopes",
                api_key_id=api_key.id,
                required_scopes=required_scopes,
                missing_scopes=missing_scopes,
                actual_scopes=api_key.get_scope_codes(),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {missing_scopes}",
            )

        return api_key

    return scopes_checker
