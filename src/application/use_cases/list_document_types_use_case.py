"""List document types use case."""
from typing import List

from src.domain.repositories.document_type_repository import IDocumentTypeRepository
from src.domain.entities.document_type import DocumentType


class ListDocumentTypesUseCase:
    """
    Use case: List available document types.

    Single Responsibility: ONLY list document types.
    Dependencies: Injected via constructor (DIP).
    """

    def __init__(self, document_type_repo: IDocumentTypeRepository):
        """
        Initialize use case.

        Args:
            document_type_repo: Document type repository (injected)
        """
        self._document_type_repo = document_type_repo

    def execute(self, active_only: bool = True) -> List[DocumentType]:
        """
        Execute use case.

        Args:
            active_only: If True, return only active document types

        Returns:
            List of document type entities
        """
        return self._document_type_repo.list_all(active_only=active_only)
