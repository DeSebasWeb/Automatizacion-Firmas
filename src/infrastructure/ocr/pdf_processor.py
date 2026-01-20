"""PDF processing utility for converting PDFs to images."""
from typing import List
import fitz  # PyMuPDF
from PIL import Image
import io
import structlog

from src.shared.logging import LoggerFactory

logger = LoggerFactory.get_infrastructure_logger("pdf_processor")


class PDFProcessor:
    """
    PDF to image converter.

    Converts PDF documents to PIL Images in memory (no disk I/O).
    Uses PyMuPDF (fitz) for fast, accurate rendering.
    """

    def __init__(self, dpi: int = 300):
        """
        Initialize PDF processor.

        Args:
            dpi: Resolution for rendering pages (default: 300)
        """
        self.dpi = dpi
        self._zoom = dpi / 72  # PDF default is 72 DPI

    def pdf_to_images(self, pdf_bytes: bytes) -> List[Image.Image]:
        """
        Convert PDF to list of PIL Images.

        Args:
            pdf_bytes: Raw PDF file bytes

        Returns:
            List of PIL Images, one per page

        Raises:
            ValueError: If PDF is invalid or corrupted
            RuntimeError: If conversion fails
        """
        if not self._is_valid_pdf(pdf_bytes):
            raise ValueError("Invalid PDF file format")

        images = []

        try:
            # Open PDF from memory
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            logger.info(
                "pdf_opened",
                page_count=pdf_document.page_count,
                dpi=self.dpi
            )

            # Convert each page to image
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]

                # Render page to pixmap at specified DPI
                matrix = fitz.Matrix(self._zoom, self._zoom)
                pixmap = page.get_pixmap(matrix=matrix)

                # Convert pixmap to PIL Image
                img_bytes = pixmap.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_bytes))

                images.append(pil_image)

                logger.debug(
                    "page_converted",
                    page_num=page_num + 1,
                    size=pil_image.size
                )

            pdf_document.close()

            logger.info("pdf_conversion_complete", total_pages=len(images))

            return images

        except fitz.FileDataError as e:
            logger.error("pdf_corrupted", error=str(e))
            raise ValueError(f"Corrupted PDF file: {e}") from e

        except Exception as e:
            logger.error("pdf_conversion_failed", error=str(e))
            raise RuntimeError(f"Failed to convert PDF: {e}") from e

    @staticmethod
    def _is_valid_pdf(pdf_bytes: bytes) -> bool:
        """
        Check if bytes represent a valid PDF file.

        Args:
            pdf_bytes: Raw file bytes

        Returns:
            True if valid PDF format
        """
        if len(pdf_bytes) < 4:
            return False

        # PDF files start with "%PDF"
        return pdf_bytes[:4] == b'%PDF'
