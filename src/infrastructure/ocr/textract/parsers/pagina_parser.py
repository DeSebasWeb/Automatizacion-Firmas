"""
PaginaParser - Specialized parser for extracting page number from E-14 forms.

This parser extracts the page information in format "01 de 09".
"""

import re
from typing import List, Dict, Optional
import structlog

from .base_parser import BaseParser

logger = structlog.get_logger(__name__)


class PaginaParser(BaseParser):
    """
    Parser specialized in extracting page number from E-14 forms.

    Principles applied:
    - SRP: Only extracts page number
    - OCP: Extensible via inheritance from BaseParser
    - DIP: Depends on BaseParser abstraction

    Patterns matched:
    - "Pag: 01 de 09"
    - "Pag: 1 de 9"
    - "Ver: 01 Pag: 01 de 09"
    """

    def parse(self, lines: List[str]) -> Dict[str, str]:
        """
        Extract page number from OCR lines.

        Args:
            lines: List of OCR text lines

        Returns:
            Dict with key "pagina": "01 de 09" (or empty if not found)

        Examples:
            >>> lines = ["720955161010109", "Ver: 01 Pag: 01 de 09", ...]
            >>> parser = PaginaParser()
            >>> result = parser.parse(lines)
            >>> result["pagina"]
            "01 de 09"
        """
        self.logger.info("parse_started", lines_count=len(lines))
        self.reset_warnings()

        result = {"pagina": ""}

        if not self._validate_lines(lines):
            return result

        # Search in first 10 lines (page info is always at top)
        search_lines = lines[:min(10, len(lines))]

        for i, line in enumerate(search_lines):
            # Pattern: "Pag: 01 de 09" or "Ver: 01 Pag: 01 de 09"
            match = re.search(
                r'Pag:\s*(\d{1,2})\s+de\s+(\d{1,2})',
                line,
                re.IGNORECASE
            )

            if match:
                pagina_actual = match.group(1).zfill(2)  # Pad with zero
                pagina_total = match.group(2).zfill(2)
                result["pagina"] = f"{pagina_actual} de {pagina_total}"

                self.logger.info(
                    "pagina_detected",
                    line_index=i,
                    line=line,
                    pagina=result["pagina"]
                )
                return result

        # Not found
        self.add_warning("pagina_not_found")
        self.logger.warning("parse_failed_no_pagina")

        return result
