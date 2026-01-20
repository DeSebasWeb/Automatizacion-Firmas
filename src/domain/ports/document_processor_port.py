"""Port for document processing services."""
from abc import ABC, abstractmethod
from typing import Dict


class IDocumentProcessor(ABC):
    """
    Interface for document processing services.

    Processes different types of documents (E-14, cedula forms, generic text)
    and extracts structured data.
    """

    @abstractmethod
    def process(self, file_bytes: bytes, filename: str) -> Dict:
        """
        Process document and extract structured data.

        Args:
            file_bytes: Raw file bytes (PDF, image, etc.)
            filename: Original filename for context

        Returns:
            Dictionary with structured data

        Raises:
            ValueError: If document is invalid
            RuntimeError: If processing fails
        """
        pass

    @abstractmethod
    def supports_file_type(self, mime_type: str) -> bool:
        """
        Check if processor supports given file type.

        Args:
            mime_type: MIME type of file

        Returns:
            True if supported
        """
        pass
