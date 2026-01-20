"""E-14 electoral document processor."""
from typing import Dict
from datetime import datetime
from PIL import Image
import structlog

from src.domain.ports.document_processor_port import IDocumentProcessor
from src.domain.ports.ocr_port import OCRPort
from src.infrastructure.ocr.pdf_processor import PDFProcessor
from src.application.services.e14_parser import E14Parser
from src.shared.logging import LoggerFactory

logger = LoggerFactory.get_application_logger("e14_processor")


class E14Processor(IDocumentProcessor):
    """
    E-14 electoral document processor.

    Handles PDF and image E-14 forms, extracts text via OCR,
    and parses structured electoral data.
    """

    SUPPORTED_MIME_TYPES = [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/tiff'
    ]

    def __init__(
        self,
        ocr_provider: OCRPort,
        pdf_processor: PDFProcessor,
        parser: E14Parser
    ):
        """
        Initialize E14 processor.

        Args:
            ocr_provider: OCR service (DigitLevelEnsembleOCR, GoogleVisionOCR, etc.)
            pdf_processor: PDF to image converter
            parser: E14 text parser
        """
        self.ocr_provider = ocr_provider
        self.pdf_processor = pdf_processor
        self.parser = parser

    def process(self, file_bytes: bytes, filename: str) -> Dict:
        """
        Process E-14 document and extract structured data.

        Steps:
        1. Detect if PDF or image
        2. If PDF: convert to images (all pages)
        3. For each page: extract text with OCR
        4. Parse full text to extract structured data
        5. Return JSON

        Args:
            file_bytes: Raw file bytes
            filename: Original filename

        Returns:
            Dictionary with E-14 structured data

        Raises:
            ValueError: If document is invalid
            RuntimeError: If processing fails
        """
        logger.info("e14_processing_started", filename=filename)

        try:
            # Step 1: Convert to images
            images = self._get_images(file_bytes)

            logger.info("images_extracted", count=len(images))

            # Step 2: Extract text from all pages
            full_text = self._extract_text_from_images(images)

            if not full_text or len(full_text) < 100:
                raise ValueError("Insufficient text extracted from document")

            logger.debug("text_extracted", length=len(full_text))

            # Step 3: Parse structured data
            result = self._parse_e14_data(full_text, filename)

            logger.info("e14_processing_complete", mesa=result.get('divipol', {}).get('mesa'))

            return result

        except ValueError as e:
            logger.error("e14_validation_failed", error=str(e), filename=filename)
            raise

        except Exception as e:
            logger.error("e14_processing_failed", error=str(e), filename=filename)
            raise RuntimeError(f"Failed to process E-14: {e}") from e

    def supports_file_type(self, mime_type: str) -> bool:
        """Check if processor supports file type."""
        return mime_type in self.SUPPORTED_MIME_TYPES

    def _get_images(self, file_bytes: bytes) -> list[Image.Image]:
        """
        Convert file to images.

        Args:
            file_bytes: Raw file bytes

        Returns:
            List of PIL Images
        """
        if self._is_pdf(file_bytes):
            logger.debug("converting_pdf_to_images")
            return self.pdf_processor.pdf_to_images(file_bytes)
        else:
            # Single image file
            logger.debug("processing_single_image")
            import io
            return [Image.open(io.BytesIO(file_bytes))]

    def _extract_text_from_images(self, images: list[Image.Image]) -> str:
        """
        Extract text from all images using OCR.

        Args:
            images: List of PIL Images

        Returns:
            Combined text from all pages
        """
        all_text = []

        for idx, image in enumerate(images):
            logger.debug("ocr_processing_page", page=idx + 1)

            # Use OCR provider - note: we need to adapt this
            # since OCRPort returns CedulaRecord, not raw text
            # For E-14, we need raw text extraction
            # We'll call the underlying OCR service directly

            # This is a simplification - in production, we'd need
            # to either extend OCRPort or create a TextExtractorPort
            text = self._extract_raw_text(image)

            all_text.append(text)

        return "\n\n".join(all_text)

    def _extract_raw_text(self, image: Image.Image) -> str:
        """
        Extract raw text from image.

        Args:
            image: PIL Image

        Returns:
            Extracted text
        """
        # Use OCR provider's full text extraction method
        if hasattr(self.ocr_provider, 'extract_full_text'):
            return self.ocr_provider.extract_full_text(image)

        # Fallback for OCR providers without full text extraction
        logger.warning(
            "ocr_provider_missing_full_text_extraction",
            provider=type(self.ocr_provider).__name__
        )
        return ""

    def _parse_e14_data(self, text: str, filename: str) -> Dict:
        """
        Parse E-14 structured data from OCR text.

        Args:
            text: Full OCR text
            filename: Original filename

        Returns:
            Structured E-14 data
        """
        # Extract DIVIPOL
        divipol = self.parser.extract_divipol(text)

        # Determine election type
        tipo_eleccion = self.parser.determine_election_type(text)

        # Extract parties
        partidos_info = self.parser.extract_partidos(text)

        # For each party, extract votes data
        partidos = []
        for partido_info in partidos_info:
            numero_lista = partido_info['numero_lista']

            partido_data = {
                'numero_lista': numero_lista,
                'nombre_partido': partido_info['nombre_partido'],
                'tipo_voto': self.parser.extract_tipo_voto(text, numero_lista),
                'votos_agrupacion': self.parser.extract_votos_agrupacion(text, numero_lista),
                'candidatos': self.parser.extract_candidatos(text, numero_lista),
                'total': self.parser.extract_total_partido(text, numero_lista)
            }

            partidos.append(partido_data)

        # Extract special votes
        votos_especiales = self.parser.extract_votos_especiales(text)

        # Build result
        result = {
            'metadata': {
                'pdf_filename': filename,
                'tipo_documento': 'E-14',
                'tipo_eleccion': tipo_eleccion,
                'processed_at': datetime.utcnow().isoformat() + 'Z'
            },
            'divipol': divipol,
            'partidos': partidos,
            'votos_especiales': votos_especiales
        }

        return result

    @staticmethod
    def _is_pdf(file_bytes: bytes) -> bool:
        """Check if file is PDF."""
        if len(file_bytes) < 4:
            return False
        return file_bytes[:4] == b'%PDF'
