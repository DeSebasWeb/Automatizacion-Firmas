"""Permission Type repository port."""
from abc import ABC, abstractmethod
from typing import List, Optional


class IPermissionTypeRepository(ABC):
    """Permission Type repository interface."""

    @abstractmethod
    def list_all(self, active_only: bool = True) -> List[dict]:
        """
        List all permission types.

        Args:
            active_only: If True, return only active permission types

        Returns:
            List of permission type dictionaries

        Note:
            Returns dicts instead of entities because PermissionType
            is a simple catalog without complex business logic.
        """
        pass

    @abstractmethod
    def find_by_code(self, code: str) -> Optional[dict]:
        """Find permission type by code."""
        pass

    @abstractmethod
    def list_scopes_by_document_type(
        self,
        document_type_code: str
    ) -> List[dict]:
        """
        List available scopes for a document type.

        Args:
            document_type_code: Document type code

        Returns:
            List of scope dictionaries with structure:
            {
                'code': 'cedula_form:read',
                'name': 'Leer Formulario de Cédulas',
                'description': '...',
                'document_type': 'cedula_form',
                'permission_type': 'read'
            }
        """
        pass

    @abstractmethod
    def list_all_scopes(self, active_only: bool = True) -> List[dict]:
        """List all available scopes."""
        pass
