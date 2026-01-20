"""List available scopes use case."""
import structlog
from typing import List, Optional

from src.domain.repositories.permission_type_repository import IPermissionTypeRepository

logger = structlog.get_logger(__name__)


class ListAvailableScopesUseCase:
    """
    Use case: List available permission scopes.

    Can filter by document type or list all.
    """

    def __init__(self, permission_type_repo: IPermissionTypeRepository):
        self._permission_type_repo = permission_type_repo

    def execute(
        self,
        document_type_code: Optional[str] = None,
        active_only: bool = True
    ) -> List[dict]:
        """
        List available scopes.

        Args:
            document_type_code: Optional filter by document type
            active_only: If True, return only active scopes

        Returns:
            List of scope dictionaries
        """
        if document_type_code:
            logger.info("listing_scopes_by_document_type", document_type=document_type_code)
            return self._permission_type_repo.list_scopes_by_document_type(document_type_code)
        else:
            logger.info("listing_all_scopes")
            return self._permission_type_repo.list_all_scopes(active_only=active_only)
