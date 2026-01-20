"""Get document type by code use case."""
import structlog
from typing import Optional

from src.domain.repositories.document_type_repository import IDocumentTypeRepository
from src.domain.entities.document_type import DocumentType
from src.domain.exceptions.exceptions import RepositoryError

logger = structlog.get_logger(__name__)


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
        logger.info("getting_document_type", code=code)

        document_type = self._document_type_repo.find_by_code(code)

        if document_type:
            logger.info("document_type_found", code=code)
        else:
            logger.warning("document_type_not_found", code=code)

        return document_type
