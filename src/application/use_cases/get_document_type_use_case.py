"""Get document type by code use case."""
from typing import Optional

from src.domain.repositories.document_type_repository import IDocumentTypeRepository
from src.domain.entities.document_type import DocumentType


class GetDocumentTypeUseCase:
    """
    Use case: Get specific document type by code.

    Single Responsibility: ONLY retrieve ONE document type.
    """

    def __init__(self, document_type_repo: IDocumentTypeRepository):
        self._document_type_repo = document_type_repo

    def execute(self, code: str) -> Optional[DocumentType]:
        """
        Get document type by code.

        Args:
            code: Document type code (e.g., 'cedula_form')

        Returns:
            Document type entity if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        return self._document_type_repo.find_by_code(code)
