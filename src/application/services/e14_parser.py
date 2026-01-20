"""E-14 electoral document parser - extracts structured data from OCR text."""
import re
from typing import Dict, List, Optional
import structlog

from src.shared.logging import LoggerFactory

logger = LoggerFactory.get_application_logger("e14_parser")


class E14Parser:
    """
    Parser for E-14 electoral documents.

    Extracts structured data from OCR text using regex patterns.
    Handles variations in spacing, formatting, and punctuation.
    """

    @staticmethod
    def extract_divipol(text: str) -> Dict:
        """
        Extract DIVIPOL (electoral location data) from text.

        Patterns:
        - DEPARTAMENTO: XX - NOMBRE
        - MUNICIPIO: XXX - NOMBRE
        - LUGAR: NOMBRE
        - ZONA: XX  PUESTO: XX  MESA: XXX

        Args:
            text: Full OCR text

        Returns:
            Dictionary with DIVIPOL fields

        Raises:
            ValueError: If DIVIPOL cannot be extracted
        """
        divipol = {}

        # DEPARTAMENTO: 16 - BOGOTA D.C.
        dept_match = re.search(
            r'DEPARTAMENTO[:\s]+(\d+)\s*[-–—]\s*(.+?)(?:\n|MUNICIPIO)',
            text,
            re.IGNORECASE
        )
        if dept_match:
            divipol['departamento_codigo'] = dept_match.group(1).strip()
            divipol['departamento_nombre'] = dept_match.group(2).strip()

        # MUNICIPIO: 001 - BOGOTA. D.C.
        muni_match = re.search(
            r'MUNICIPIO[:\s]+(\d+)\s*[-–—]\s*(.+?)(?:\n|LUGAR)',
            text,
            re.IGNORECASE
        )
        if muni_match:
            divipol['municipio_codigo'] = muni_match.group(1).strip()
            divipol['municipio_nombre'] = muni_match.group(2).strip()

        # LUGAR: USAQUÉN
        lugar_match = re.search(
            r'LUGAR[:\s]+(.+?)(?:\n|ZONA)',
            text,
            re.IGNORECASE
        )
        if lugar_match:
            divipol['lugar'] = lugar_match.group(1).strip()

        # ZONA: 01  PUESTO: 01  MESA: 066
        zona_match = re.search(
            r'ZONA[:\s]+(\d+)\s+PUESTO[:\s]+(\d+)\s+MESA[:\s]+(\d+)',
            text,
            re.IGNORECASE
        )
        if zona_match:
            divipol['zona'] = zona_match.group(1).strip()
            divipol['puesto'] = zona_match.group(2).strip()
            divipol['mesa'] = zona_match.group(3).strip()

        # Validate all fields present
        required_fields = [
            'departamento_codigo', 'departamento_nombre',
            'municipio_codigo', 'municipio_nombre',
            'lugar', 'zona', 'puesto', 'mesa'
        ]

        missing = [f for f in required_fields if f not in divipol]
        if missing:
            logger.error("divipol_extraction_incomplete", missing_fields=missing)
            raise ValueError(f"Could not extract DIVIPOL fields: {missing}")

        logger.debug("divipol_extracted", divipol=divipol)
        return divipol

    @staticmethod
    def extract_partidos(text: str) -> List[Dict]:
        """
        Extract party basic info (number and name).

        Pattern: XXXX + PARTY_NAME
        Example: 0261 COALICIÓN CENTRO ESPERANZA

        Args:
            text: Full OCR text

        Returns:
            List of dicts with numero_lista and nombre_partido
        """
        partidos = []

        # Pattern: 4 digits followed by party name
        partido_matches = re.finditer(
            r'(\d{4})\s+([A-ZÁÉÍÓÚÑ\s]+?)(?=\n|\d{4}|CON VOTO|SIN VOTO|VOTOS)',
            text,
            re.IGNORECASE
        )

        for match in partido_matches:
            numero_lista = match.group(1).strip()
            nombre_partido = match.group(2).strip()

            # Skip if looks like year or other number
            if nombre_partido and len(nombre_partido) > 3:
                partidos.append({
                    'numero_lista': numero_lista,
                    'nombre_partido': nombre_partido
                })

        logger.debug("partidos_extracted", count=len(partidos))
        return partidos

    @staticmethod
    def extract_tipo_voto(text: str, numero_lista: str) -> str:
        """
        Detect vote type for specific party.

        Types:
        - CON_VOTO_PREFERENTE: voters can choose candidates
        - SIN_VOTO_PREFERENTE: votes go to party only

        Args:
            text: Full OCR text
            numero_lista: Party number to search for

        Returns:
            "CON_VOTO_PREFERENTE" or "SIN_VOTO_PREFERENTE"
        """
        # Search for party number context
        party_section = E14Parser._extract_party_section(text, numero_lista)

        if not party_section:
            return "CON_VOTO_PREFERENTE"  # Default

        if re.search(r'SIN VOTO PREFERENTE', party_section, re.IGNORECASE):
            return "SIN_VOTO_PREFERENTE"
        else:
            return "CON_VOTO_PREFERENTE"

    @staticmethod
    def extract_votos_agrupacion(text: str, numero_lista: str) -> int:
        """
        Extract votes for party list (agrupación).

        Pattern: VOTOS SOLO POR LA AGRUPACIÓN POLÍTICA | NUMBER

        Args:
            text: Full OCR text
            numero_lista: Party number

        Returns:
            Vote count (0 if not found)
        """
        party_section = E14Parser._extract_party_section(text, numero_lista)

        if not party_section:
            return 0

        # Pattern: VOTOS SOLO POR LA AGRUPACIÓN | number
        votos_match = re.search(
            r'VOTOS\s+SOLO\s+POR\s+LA\s+AGRUPACI[OÓ]N.*?\|\s*(\d+)',
            party_section,
            re.IGNORECASE | re.DOTALL
        )

        if votos_match:
            return int(votos_match.group(1))

        return 0

    @staticmethod
    def extract_candidatos(text: str, numero_lista: str) -> List[Dict]:
        """
        Extract candidate votes for specific party.

        Pattern: XXX | NUMBER or ---
        Candidate IDs: 101-118, 201-206, 301-303

        Args:
            text: Full OCR text
            numero_lista: Party number

        Returns:
            List of {id: int, votos: int|None}
        """
        candidatos = []
        party_section = E14Parser._extract_party_section(text, numero_lista)

        if not party_section:
            return candidatos

        # Pattern: 3-digit ID | votes or ---
        candidato_matches = re.finditer(
            r'(\d{3})\s*\|\s*(\d+|---|\s+)',
            party_section
        )

        for match in candidato_matches:
            candidato_id = int(match.group(1))
            votos_str = match.group(2).strip()

            # Parse votes (None if empty or ---)
            if votos_str in ['---', '']:
                votos = None
            else:
                try:
                    votos = int(votos_str)
                except ValueError:
                    votos = None

            candidatos.append({
                'id': candidato_id,
                'votos': votos
            })

        return candidatos

    @staticmethod
    def extract_total_partido(text: str, numero_lista: str) -> int:
        """
        Extract total votes for party.

        Pattern: TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS | NUMBER

        Args:
            text: Full OCR text
            numero_lista: Party number

        Returns:
            Total vote count (0 if not found)
        """
        party_section = E14Parser._extract_party_section(text, numero_lista)

        if not party_section:
            return 0

        # Pattern: TOTAL = ... | number
        total_match = re.search(
            r'TOTAL\s*=.*?\|\s*(\d+)',
            party_section,
            re.IGNORECASE | re.DOTALL
        )

        if total_match:
            return int(total_match.group(1))

        return 0

    @staticmethod
    def extract_votos_especiales(text: str) -> Dict:
        """
        Extract special votes (blank, null, unmarked).

        Patterns:
        - VOTOS EN BLANCO | NUMBER
        - VOTOS NULOS | NUMBER
        - VOTOS NO MARCADOS | NUMBER

        Args:
            text: Full OCR text

        Returns:
            Dict with votos_blanco, votos_nulos, votos_no_marcados
        """
        votos_especiales = {
            'votos_blanco': 0,
            'votos_nulos': 0,
            'votos_no_marcados': 0
        }

        # VOTOS EN BLANCO
        blanco_match = re.search(
            r'VOTOS\s+EN\s+BLANCO.*?\|\s*(\d+)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if blanco_match:
            votos_especiales['votos_blanco'] = int(blanco_match.group(1))

        # VOTOS NULOS
        nulos_match = re.search(
            r'VOTOS\s+NULOS.*?\|\s*(\d+)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if nulos_match:
            votos_especiales['votos_nulos'] = int(nulos_match.group(1))

        # VOTOS NO MARCADOS
        no_marcados_match = re.search(
            r'VOTOS\s+NO\s+MARCADOS.*?\|\s*(\d+)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if no_marcados_match:
            votos_especiales['votos_no_marcados'] = int(no_marcados_match.group(1))

        logger.debug("votos_especiales_extracted", votos=votos_especiales)
        return votos_especiales

    @staticmethod
    def determine_election_type(text: str) -> str:
        """
        Determine election type from header text.

        Types: CAMARA or SENADO

        Args:
            text: Full OCR text

        Returns:
            "CAMARA" or "SENADO"
        """
        if re.search(r'C[AÁ]MARA', text, re.IGNORECASE):
            return "CAMARA"
        elif re.search(r'SENADO', text, re.IGNORECASE):
            return "SENADO"
        else:
            return "CAMARA"  # Default

    @staticmethod
    def _extract_party_section(text: str, numero_lista: str) -> Optional[str]:
        """
        Extract text section for specific party.

        Args:
            text: Full OCR text
            numero_lista: Party number (e.g., "0261")

        Returns:
            Section text or None if not found
        """
        # Find party number and extract until next party or end
        pattern = rf'{numero_lista}.*?(?=\d{{4}}(?:\s+[A-ZÁÉÍÓÚÑ]{{5,}})|$)'

        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(0)

        return None
