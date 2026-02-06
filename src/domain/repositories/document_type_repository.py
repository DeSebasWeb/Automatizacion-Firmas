"""Document Type repository port."""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.document_type import DocumentType


class IDocumentTypeRepository(ABC):
    """
    Document Type repository interface (Port).

    Defines contract for document type persistence operations.
    Implementations provided by infrastructure layer.
    """

    @abstractmethod
    def list_all(self, active_only: bool = True) -> List[DocumentType]:
        """
        List all document types.

        Args:
            active_only: If True, return only active document types

        Returns:
            List of document type entities

        Raises:
            RepositoryError: If query fails
        """
        pass

    @abstractmethod
    def find_by_code(self, code: str) -> Optional[DocumentType]:
        """
        Find document type by code.

        Args:
            code: Document type code (e.g., 'cedula_form')

        Returns:
            Document type entity if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        pass

    @abstractmethod
    def find_by_id(self, document_type_id: int) -> Optional[DocumentType]:
        """
        Find document type by ID.

        Args:
            document_type_id: Document type identifier

        Returns:
            Document type entity if found, None otherwise
        """
        pass

    @abstractmethod
    def exists_by_code(self, code: str) -> bool:
        """
        Check if document type exists.

        Args:
            code: Document type code

        Returns:
            True if exists, False otherwise
        """
        pass
