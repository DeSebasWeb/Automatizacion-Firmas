"""
E14ParserService - Orchestrator for parsing E-14 electoral documents.

This service coordinates multiple specialized parsers following the
Dependency Inversion Principle and Strategy Pattern.
"""

from typing import Dict, Any, List
import structlog

from .base_parser import BaseParser
from .pagina_parser import PaginaParser
from .totales_mesa_parser import TotalesMesaParser
from .divipol_parser import DivipolParser
from .partido_parser import PartidoParser

logger = structlog.get_logger(__name__)


class E14ParserService:
    """
    Service that orchestrates all E-14 parsers.

    Principles applied:
    - SRP: Only coordinates parsers, does not parse directly
    - DIP: Depends on BaseParser interfaces, not concrete implementations
    - Strategy Pattern: Each parser is a strategy for extracting specific data
    - Chain of Responsibility: Parsers process text sequentially

    Attributes:
        pagina_parser: Parser for extracting page number
        totales_parser: Parser for extracting mesa totals
        divipol_parser: Parser for extracting DIVIPOL codes
        partido_parser: Parser for extracting parties and candidates
    """

    def __init__(
        self,
        pagina_parser: BaseParser = None,
        totales_parser: BaseParser = None,
        divipol_parser: BaseParser = None,
        partido_parser: BaseParser = None
    ):
        """
        Initialize E14ParserService with parser dependencies.

        Args:
            pagina_parser: Parser for page number (defaults to PaginaParser)
            totales_parser: Parser for totals (defaults to TotalesMesaParser)
            divipol_parser: Parser for DIVIPOL (defaults to DivipolParser)
            partido_parser: Parser for parties (defaults to PartidoParser)

        Examples:
            >>> # Use default parsers
            >>> service = E14ParserService()
            >>>
            >>> # Or inject custom parsers
            >>> service = E14ParserService(
            ...     totales_parser=CustomTotalesParser(),
            ...     divipol_parser=CustomDivipolParser()
            ... )
        """
        self.logger = logger.bind(service="E14ParserService")

        # Dependency Injection with defaults
        self.pagina_parser = pagina_parser or PaginaParser()
        self.totales_parser = totales_parser or TotalesMesaParser()
        self.divipol_parser = divipol_parser or DivipolParser()
        self.partido_parser = partido_parser or PartidoParser()

        self.logger.info(
            "service_initialized",
            pagina_parser=self.pagina_parser.__class__.__name__,
            totales_parser=self.totales_parser.__class__.__name__,
            divipol_parser=self.divipol_parser.__class__.__name__,
            partido_parser=self.partido_parser.__class__.__name__
        )

    def parse_e14(self, ocr_text: str) -> Dict[str, Any]:
        """
        Parse complete E-14 document using specialized parsers.

        Order of execution:
        1. Split text into lines
        2. Extract page number (critical for tracking)
        3. Extract DIVIPOL codes
        4. Extract mesa totals (TotalesMesaParser)
        5. Extract parties and candidates

        Args:
            ocr_text: Full OCR text from AWS Textract (horizontal extraction)

        Returns:
            Dict with complete E-14 structure:
            {
                "pagina": "01 de 09",
                "divipol": {...},
                "TotalSufragantesE14": "134",
                "TotalVotosEnUrna": "131",
                "TotalIncinerados": "***",
                "Partido": [...]
            }

        Examples:
            >>> service = E14ParserService()
            >>> ocr_text = "Ver: 01 Pag: 01 de 09\\nTOTAL\\nTOTAL\\n..."
            >>> result = service.parse_e14(ocr_text)
            >>> result["pagina"]
            "01 de 09"
            >>> result["TotalSufragantesE14"]
            "134"
        """
        self.logger.info("parse_e14_started", text_length=len(ocr_text))

        # Step 1: Split text into lines
        lines = self._split_into_lines(ocr_text)
        self.logger.debug("text_split_into_lines", line_count=len(lines))

        # Step 2: Extract page number (critical)
        pagina_data = self.pagina_parser.parse(lines)
        pagina = pagina_data.get("pagina", "")

        if not pagina:
            self.logger.warning("pagina_not_extracted")

        # Step 3: Extract DIVIPOL codes
        divipol_data = self.divipol_parser.parse(lines)

        # Step 4: Extract mesa totals (TotalesMesaParser)
        totales_data = self.totales_parser.parse(lines)

        # Step 5: Extract parties and candidates
        partido_data = self.partido_parser.parse(lines)

        # Assemble complete E-14 document
        result = {
            "pagina": pagina,
            "divipol": divipol_data,
            **totales_data,  # TotalSufragantesE14, TotalVotosEnUrna, TotalIncinerados
            "Partido": partido_data.get("Partido", [])
        }

        # Collect warnings from all parsers
        all_warnings = (
            self.pagina_parser.warnings +
            self.divipol_parser.warnings +
            self.totales_parser.warnings +
            self.partido_parser.warnings
        )

        if all_warnings:
            self.logger.warning("parsing_completed_with_warnings", warnings=all_warnings)
        else:
            self.logger.info("parsing_completed_successfully")

        self.logger.info(
            "parse_e14_completed",
            pagina=pagina,
            divipol_complete=all(divipol_data.values()),
            totales_complete=all(totales_data.values()),
            partido_count=len(partido_data.get("Partido", []))
        )

        return result

    def _split_into_lines(self, ocr_text: str) -> List[str]:
        """
        Split OCR text into lines.

        Args:
            ocr_text: Full OCR text string

        Returns:
            List of text lines with whitespace stripped

        Examples:
            >>> text = "Line 1\\nLine 2\\n  Line 3  \\n"
            >>> service._split_into_lines(text)
            ["Line 1", "Line 2", "Line 3"]
        """
        if not ocr_text:
            return []

        lines = ocr_text.split('\n')
        # Strip whitespace but keep empty lines for structure
        lines = [line.strip() for line in lines]

        return lines

    def get_all_warnings(self) -> List[str]:
        """
        Get accumulated warnings from all parsers.

        Returns:
            List of warning messages from all parsers

        Examples:
            >>> service = E14ParserService()
            >>> service.parse_e14(ocr_text)
            >>> warnings = service.get_all_warnings()
            >>> print(warnings)
            ["campo_vacio: TotalIncinerados", ...]
        """
        all_warnings = (
            self.pagina_parser.warnings +
            self.divipol_parser.warnings +
            self.totales_parser.warnings +
            self.partido_parser.warnings
        )

        return all_warnings

    def reset_all_parsers(self) -> None:
        """
        Reset warning state in all parsers.

        Call this before parsing a new document to clear previous warnings.

        Examples:
            >>> service = E14ParserService()
            >>> service.parse_e14(doc1)
            >>> service.reset_all_parsers()
            >>> service.parse_e14(doc2)  # Fresh start
        """
        self.pagina_parser.reset_warnings()
        self.divipol_parser.reset_warnings()
        self.totales_parser.reset_warnings()
        self.partido_parser.reset_warnings()

        self.logger.debug("all_parsers_reset")
