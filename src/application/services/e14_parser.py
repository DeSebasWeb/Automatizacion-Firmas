"""E-14 electoral document parser - extracts structured data from OCR text."""
import re
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)


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
        Extract party basic info (number, name, and vote type).

        Searches for "LISTA CON/SIN VOTO PREFERENTE" followed by party number and name.

        Args:
            text: Full OCR text

        Returns:
            List of dicts with numero_lista, nombre_partido, and tipo_voto
        """
        partidos = []

        # Pattern: LISTA CON/SIN VOTO PREFERENTE followed by 4-digit number and party name
        # Example: "LISTA CON VOTO PREFERENTE 0261 COALICIÓN CENTRO ESPERANZA"
        lista_matches = re.finditer(
            r'LISTA\s+(CON|SIN)\s+VOTO\s+PREFERENTE.*?(\d{4})\s+([A-ZÑÁÉÍÓÚÜ][^\n]{10,100})',
            text,
            re.DOTALL | re.IGNORECASE
        )

        seen_numbers = set()

        for match in lista_matches:
            tipo_voto_raw = match.group(1).upper()  # "CON" or "SIN"
            numero_lista = match.group(2)
            nombre_partido = match.group(3).strip()

            # Clean party name (remove extra whitespace, line breaks)
            nombre_partido = re.sub(r'\s+', ' ', nombre_partido)
            nombre_partido = nombre_partido.split('\n')[0]  # Take only first line

            # Filter out document headers/garbage
            garbage_keywords = [
                'ACTA DE ESCRUTINIO',
                'CÁMARA',
                'SENADO',
                'CLAVEROS',
                'VOTOS',
                'TOTAL',
                'ELECCIONES'
            ]

            if any(keyword in nombre_partido.upper() for keyword in garbage_keywords):
                continue

            # Validate party number range (0001-9999)
            try:
                num_val = int(numero_lista)
                if not (1 <= num_val <= 9999):
                    continue
            except ValueError:
                continue

            # Skip duplicates
            if numero_lista in seen_numbers:
                continue

            seen_numbers.add(numero_lista)

            tipo_voto = "CON_VOTO_PREFERENTE" if tipo_voto_raw == "CON" else "SIN_VOTO_PREFERENTE"

            partidos.append({
                'numero_lista': numero_lista,
                'nombre_partido': nombre_partido,
                'tipo_voto': tipo_voto
            })

        logger.info("partidos_extracted", count=len(partidos), party_numbers=[p['numero_lista'] for p in partidos])
        return partidos

    @staticmethod
    def extract_tipo_voto(text: str, numero_lista: str) -> str:
        """
        Detect vote type for specific party.

        NOTE: This method is deprecated in favor of extracting tipo_voto
        directly in extract_partidos(). Kept for backwards compatibility.

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

        Pattern: VOTOS SOLO POR LA AGRUPACIÓN POLÍTICA followed by number.
        Handles cases with X (illegible) or clean numbers.

        Args:
            text: Full OCR text
            numero_lista: Party number

        Returns:
            Vote count (0 if not found or illegible)
        """
        party_section = E14Parser._extract_party_section(text, numero_lista)

        if not party_section:
            logger.debug("votos_agrupacion_no_section", numero_lista=numero_lista)
            return 0

        # Pattern: VOTOS SOLO POR LA AGRUPACIÓN POLÍTICA followed by → | ► and number
        # May have X characters mixed in: "X X 2 9" → "29"
        votos_match = re.search(
            r'VOTOS\s+SOLO\s+POR\s+LA\s+AGRUPACI[OÓ]N\s+POL[IÍ]TICA.*?(?:→|➜|►|->)?\s*[|│]?\s*([X\d\s]+)',
            party_section,
            re.IGNORECASE | re.DOTALL
        )

        if votos_match:
            votos_str = votos_match.group(1).strip()

            # If all X → illegible
            if all(c in 'Xx\s' for c in votos_str):
                logger.debug("votos_agrupacion_illegible", numero_lista=numero_lista)
                return 0

            # Extract digits only: "X X 2 9" → "29"
            digits_only = re.sub(r'[^0-9]', '', votos_str)

            if digits_only:
                votos = int(digits_only)
                logger.debug("votos_agrupacion_extracted", numero_lista=numero_lista, votos=votos)
                return votos

        logger.debug("votos_agrupacion_not_found", numero_lista=numero_lista)
        return 0

    @staticmethod
    def extract_candidatos(text: str, numero_lista: str) -> List[Dict]:
        """
        Extract candidate votes for specific party.

        Formats:
        - "101 | X X 5" → candidate 101 with 5 votes
        - "102 | ---" → candidate 102 with no votes (null)
        - "103 | X X X" → candidate 103 illegible (null)

        Valid candidate ID ranges: 101-118, 201-206, 301-303

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

        # Pattern: 3-digit ID followed by | and votes (may contain X, spaces, dashes)
        candidato_pattern = re.compile(
            r'(\d{3})\s*[|│]\s*([X\d\s\-—─]+?)(?=\s*(?:\d{3}\s*[|│]|TOTAL|VOTOS|$))',
            re.MULTILINE | re.DOTALL
        )

        for match in candidato_pattern.finditer(party_section):
            candidato_id = int(match.group(1))
            votos_str = match.group(2).strip()

            # Validate candidate ID ranges
            valid_ranges = [
                (101, 118),  # Cámara candidates
                (201, 206),  # Senado candidates (special)
                (301, 303)   # Additional range
            ]

            is_valid = any(start <= candidato_id <= end for start, end in valid_ranges)
            if not is_valid:
                continue

            # Parse votes
            # All dashes or X → null
            if all(c in '—─-Xx\s' for c in votos_str):
                votos = None
            else:
                # Extract all digit sequences: "X X 5" → ["5"]
                digit_sequences = re.findall(r'\d+', votos_str)
                if digit_sequences:
                    # Take the last digit sequence (handles "X X 5" → "5")
                    votos = int(digit_sequences[-1])
                else:
                    votos = None

            candidatos.append({
                'id': candidato_id,
                'votos': votos
            })

        logger.debug("candidatos_extracted", numero_lista=numero_lista, count=len(candidatos))
        return candidatos

    @staticmethod
    def extract_total_partido(text: str, numero_lista: str) -> int:
        """
        Extract total votes for party.

        Pattern: TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS | NUMBER
        Handles cases with X or spaces: "X X 8" → "8"

        Args:
            text: Full OCR text
            numero_lista: Party number

        Returns:
            Total vote count (0 if not found)
        """
        party_section = E14Parser._extract_party_section(text, numero_lista)

        if not party_section:
            return 0

        # Pattern: TOTAL = ... | number (may have X X digits)
        total_match = re.search(
            r'TOTAL\s*=.*?[|│]\s*([X\d\s]+)',
            party_section,
            re.IGNORECASE | re.DOTALL
        )

        if total_match:
            total_str = total_match.group(1).strip()

            # Extract digits only: "X X 8" → "8"
            digit_sequences = re.findall(r'\d+', total_str)

            if digit_sequences:
                # Take last digit sequence
                total = int(digit_sequences[-1])
                logger.debug("total_partido_extracted", numero_lista=numero_lista, total=total)
                return total

        logger.debug("total_partido_not_found", numero_lista=numero_lista)
        return 0

    @staticmethod
    def extract_votos_especiales(text: str) -> Dict:
        """
        Extract special votes (blank, null, unmarked).

        Handles illegible cases marked with X.
        Returns None for illegible values instead of 0.

        Args:
            text: Full OCR text

        Returns:
            Dict with votos_blanco, votos_nulos, votos_no_marcados (int or None)
        """
        votos_especiales = {
            'votos_blanco': None,
            'votos_nulos': None,
            'votos_no_marcados': None
        }

        # VOTOS EN BLANCO
        blanco_match = re.search(
            r'VOTOS\s+EN\s+BLANCO\s*[|│]?\s*([X\d\s]+)',
            text,
            re.IGNORECASE
        )
        if blanco_match:
            val_str = blanco_match.group(1).strip()
            if not all(c in 'Xx\s' for c in val_str):
                digit_sequences = re.findall(r'\d+', val_str)
                if digit_sequences:
                    votos_especiales['votos_blanco'] = int(digit_sequences[-1])

        # VOTOS NULOS
        nulos_match = re.search(
            r'VOTOS\s+NULOS\s*[|│]?\s*([X\d\s]+)',
            text,
            re.IGNORECASE
        )
        if nulos_match:
            val_str = nulos_match.group(1).strip()
            if not all(c in 'Xx\s' for c in val_str):
                digit_sequences = re.findall(r'\d+', val_str)
                if digit_sequences:
                    votos_especiales['votos_nulos'] = int(digit_sequences[-1])

        # VOTOS NO MARCADOS
        no_marcados_match = re.search(
            r'VOTOS\s+NO\s+MARCADOS\s*[|│]?\s*([X\d\s]+)',
            text,
            re.IGNORECASE
        )
        if no_marcados_match:
            val_str = no_marcados_match.group(1).strip()
            if not all(c in 'Xx\s' for c in val_str):
                digit_sequences = re.findall(r'\d+', val_str)
                if digit_sequences:
                    votos_especiales['votos_no_marcados'] = int(digit_sequences[-1])

        logger.info(
            "votos_especiales_extracted",
            blanco=votos_especiales['votos_blanco'],
            nulos=votos_especiales['votos_nulos'],
            no_marcados=votos_especiales['votos_no_marcados']
        )
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
