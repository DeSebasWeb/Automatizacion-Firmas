"""
DivipolParser - Specialized parser for extracting DIVIPOL codes from E-14 forms.

DIVIPOL codes identify the geographic location:
- CodDep: Department code (e.g., "16" for Bogotá)
- CodMun: Municipality code (e.g., "001")
- zona: Electoral zone (e.g., "01")
- Puesto: Voting station (e.g., "01")
- Mesa: Voting table (e.g., "001")
"""

import re
from typing import List, Dict, Optional
import structlog

from .base_parser import BaseParser

logger = structlog.get_logger(__name__)


class DivipolParser(BaseParser):
    """
    Parser specialized in extracting DIVIPOL codes from E-14 forms.

    Principles applied:
    - SRP: Only extracts DIVIPOL codes
    - OCP: Extensible via inheritance from BaseParser
    - DIP: Depends on BaseParser abstraction

    Patterns matched:
    - "DEPARTAMENTO: 16 - BOGOTA D.C."
    - "MUNICIPIO: 001 - BOGOTA. D.C."
    - "ZONA: 01 PUESTO: 01 MESA: 001"
    """

    def parse(self, lines: List[str]) -> Dict[str, str]:
        """
        Extract DIVIPOL codes from OCR lines.

        Args:
            lines: List of OCR text lines

        Returns:
            Dict with DIVIPOL codes:
            {
                "CodDep": "16",
                "CodMun": "001",
                "zona": "01",
                "Puesto": "01",
                "Mesa": "001"
            }

        Examples:
            >>> lines = ["DEPARTAMENTO: 16 - BOGOTA D.C.", ...]
            >>> parser = DivipolParser()
            >>> result = parser.parse(lines)
            >>> result["CodDep"]
            "16"
        """
        self.logger.info("parse_started", lines_count=len(lines))
        self.reset_warnings()

        result = {
            "CodDep": "",
            "CodMun": "",
            "zona": "",
            "Puesto": "",
            "Mesa": ""
        }

        if not self._validate_lines(lines):
            return result

        # Search in first 20 lines (DIVIPOL info is always at top)
        search_lines = lines[:min(20, len(lines))]

        for i, line in enumerate(search_lines):
            line_clean = self._clean_line(line)

            # Extract department code
            if 'DEPARTAMENTO' in line_clean.upper():
                match = re.search(r'DEPARTAMENTO:\s*(\d+)', line_clean, re.IGNORECASE)
                if match:
                    result["CodDep"] = match.group(1)
                    self.logger.debug("departamento_detected", value=result["CodDep"], line=line)

            # Extract municipality code
            elif 'MUNICIPIO' in line_clean.upper():
                match = re.search(r'MUNICIPIO:\s*(\d+)', line_clean, re.IGNORECASE)
                if match:
                    result["CodMun"] = match.group(1)
                    self.logger.debug("municipio_detected", value=result["CodMun"], line=line)

            # Extract zona, puesto, mesa (all in same line)
            elif 'ZONA' in line_clean.upper() and 'PUESTO' in line_clean.upper():
                # Pattern: "ZONA: 01 PUESTO: 01 MESA: 001"
                zona_match = re.search(r'ZONA:\s*(\d+)', line_clean, re.IGNORECASE)
                puesto_match = re.search(r'PUESTO:\s*(\d+)', line_clean, re.IGNORECASE)
                mesa_match = re.search(r'MESA:\s*(\d+)', line_clean, re.IGNORECASE)

                if zona_match:
                    result["zona"] = zona_match.group(1)
                if puesto_match:
                    result["Puesto"] = puesto_match.group(1)
                if mesa_match:
                    result["Mesa"] = mesa_match.group(1)

                self.logger.debug(
                    "zona_puesto_mesa_detected",
                    zona=result["zona"],
                    puesto=result["Puesto"],
                    mesa=result["Mesa"],
                    line=line
                )

        # Validate all fields were found
        missing_fields = [k for k, v in result.items() if not v]
        if missing_fields:
            self.add_warning("divipol_campos_faltantes", campos=missing_fields)
            self.logger.warning("divipol_incomplete", missing=missing_fields)

        self.logger.info("divipol_extracted", divipol=result)

        return result
