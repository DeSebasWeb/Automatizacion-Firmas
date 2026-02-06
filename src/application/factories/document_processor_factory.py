"""Factory for creating document processors based on document type."""
from typing import Dict
import structlog

from src.domain.ports.document_processor_port import IDocumentProcessor
from src.domain.ports.ocr_port import OCRPort
from src.application.services.e14_processor import E14Processor
from src.infrastructure.ocr.pdf_processor import PDFProcessor
from src.application.services.e14_parser import E14Parser

logger = structlog.get_logger(__name__)


class DocumentProcessorFactory:
    """
    Factory for creating document processors.

    Creates appropriate processor based on document type code.
    """

    def __init__(self, ocr_provider: OCRPort):
        """
        Initialize factory.

        Args:
            ocr_provider: OCR service to inject into processors
        """
        self.ocr_provider = ocr_provider

        # Cache processors to avoid recreating
        self._processors: Dict[str, IDocumentProcessor] = {}

    def create_processor(self, document_type_code: str) -> IDocumentProcessor:
        """
        Create processor based on document type.

        Args:
            document_type_code: Document type code (e.g., "e14", "cedula_form")

        Returns:
            Document processor instance

        Raises:
            ValueError: If document type is unknown
        """
        # Return cached if exists
        if document_type_code in self._processors:
            return self._processors[document_type_code]

        # Create new processor
        processor = self._build_processor(document_type_code)

        # Cache it
        self._processors[document_type_code] = processor

        logger.debug("processor_created", document_type=document_type_code)

        return processor

    def _build_processor(self, document_type_code: str) -> IDocumentProcessor:
        """
        Build processor instance.

        Args:
            document_type_code: Document type code

        Returns:
            Processor instance

        Raises:
            ValueError: If unknown type
        """
        if document_type_code == "e14":
            return E14Processor(
                ocr_provider=self.ocr_provider,
                pdf_processor=PDFProcessor(dpi=300),
                parser=E14Parser()
            )

        elif document_type_code == "cedula_form":
            # TODO: Implement CedulaFormProcessor
            raise NotImplementedError(
                "Cedula form processor not yet implemented. "
                "Will be added in future sprint."
            )

        elif document_type_code == "generic_text":
            # TODO: Implement GenericTextProcessor
            raise NotImplementedError(
                "Generic text processor not yet implemented. "
                "Will be added in future sprint."
            )

        else:
            raise ValueError(
                f"Unknown document type: '{document_type_code}'. "
                f"Supported types: e14, cedula_form, generic_text"
            )

    def get_supported_types(self) -> list[str]:
        """
        Get list of supported document types.

        Returns:
            List of document type codes
        """
        return ["e14"]  # Will expand as we implement more processors
