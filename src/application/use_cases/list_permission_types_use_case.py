"""List permission types use case."""
from typing import List

from src.domain.repositories.permission_type_repository import IPermissionTypeRepository


class ListPermissionTypesUseCase:
    """Use case: List available permission types."""

    def __init__(self, permission_type_repo: IPermissionTypeRepository):
        self._permission_type_repo = permission_type_repo

    def execute(self, active_only: bool = True) -> List[dict]:
        """
        List permission types.

        Args:
            active_only: If True, return only active types

        Returns:
            List of permission type dictionaries
        """
        return self._permission_type_repo.list_all(active_only=active_only)
