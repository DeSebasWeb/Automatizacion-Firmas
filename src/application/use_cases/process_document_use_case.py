"""Process document use case."""
from typing import Dict

from src.application.factories.document_processor_factory import DocumentProcessorFactory
from src.domain.repositories.document_type_repository import IDocumentTypeRepository


class DocumentTypeNotFoundError(Exception):
    """Document type not found."""
    pass


class ProcessDocumentUseCase:
    """
    Use case: Process document and extract structured data.

    Single Responsibility: ONLY orchestrate document processing.
    """

    def __init__(
        self,
        processor_factory: DocumentProcessorFactory,
        document_type_repo: IDocumentTypeRepository
    ):
        """
        Initialize use case.

        Args:
            processor_factory: Factory for creating processors
            document_type_repo: Repository for document type validation
        """
        self._processor_factory = processor_factory
        self._document_type_repo = document_type_repo

    def execute(
        self,
        file_bytes: bytes,
        filename: str,
        document_type_code: str
    ) -> Dict:
        """
        Execute document processing.

        Args:
            file_bytes: Raw file bytes
            filename: Original filename
            document_type_code: Document type code (e.g., "e14")

        Returns:
            Processed document data

        Raises:
            DocumentTypeNotFoundError: If document type doesn't exist
            ValueError: If file is invalid
            RuntimeError: If processing fails
        """
        # Validate document type exists and is active
        doc_type = self._document_type_repo.find_by_code(document_type_code)

        if not doc_type:
            raise DocumentTypeNotFoundError(
                f"Document type '{document_type_code}' not found"
            )

        if not doc_type.is_active:
            raise DocumentTypeNotFoundError(
                f"Document type '{document_type_code}' is not active"
            )

        # Create appropriate processor
        processor = self._processor_factory.create_processor(document_type_code)

        # Process document
        result = processor.process(file_bytes, filename)

        return result
