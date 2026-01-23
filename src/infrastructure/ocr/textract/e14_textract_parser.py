"""
E-14 Textract Parser.

Parser especializado para extraer datos estructurados de formularios E-14
a partir del texto extraído por AWS Textract.
"""

import re
import structlog
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from .parsers.totales_mesa_parser import TotalesMesaParser

logger = structlog.get_logger(__name__)


@dataclass
class ParserState:
    """Estado del parser durante el procesamiento."""

    dentro_partido: bool = False
    tipo_lista_actual: Optional[str] = None
    numero_partido_actual: Optional[str] = None
    nombre_partido_actual: Optional[str] = None
    id_partido_actual: str = "0"
    votos_agrupacion_actual: str = "0"
    candidatos_actuales: List[Dict[str, Any]] = field(default_factory=list)
    total_votos_partido_actual: str = "0"
    partido_necesita_auditoria: bool = False


class E14TextractParser:
    """
    Parser de formularios E-14 desde texto de AWS Textract.

    Extrae datos estructurados siguiendo las reglas de negocio:
    - DIVIPOL (códigos geográficos)
    - Totales de mesa
    - Partidos políticos
    - Candidatos y votos
    - Marcado de auditoría para datos sospechosos

    Principios SOLID:
    - SRP: Responsabilidad única de parsing E-14
    - OCP: Extensible para nuevos patrones vía métodos
    - DIP: No depende de implementación concreta de OCR
    """

    def __init__(self):
        """Inicializa el parser."""
        self.logger = logger.bind(parser="e14_textract")
        self.warnings: List[str] = []
        self.state = ParserState()
        # Usar el nuevo TotalesMesaParser modular
        self.totales_parser = TotalesMesaParser()

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parsea texto OCR de Textract y genera JSON estructurado.

        Args:
            text: Texto completo extraído por Textract (línea por línea)

        Returns:
            Diccionario con estructura E-14 completa
        """
        self.warnings = []
        self.state = ParserState()

        self.logger.info("starting_e14_parsing", text_length=len(text))

        # Dividir en líneas para procesamiento secuencial
        lines = text.split('\n')

        # Estructura de resultado
        result: Dict[str, Any] = {
            "e14": {
                "pagina": "",
                "divipol": {
                    "CodDep": "",
                    "CodMun": "",
                    "zona": "",
                    "Puesto": "",
                    "Mesa": ""
                },
                "TotalSufragantesE14": "",
                "TotalVotosEnUrna": "",
                "TotalIncinerados": "***",
                "Partido": []
            }
        }

        # 1. Extraer página (CRÍTICO - primero)
        result["e14"]["pagina"] = self._extract_pagina(lines)

        # 2. Extraer DIVIPOL
        divipol = self._extract_divipol(lines)
        result["e14"]["divipol"].update(divipol)

        # 3. Extraer totales de mesa (usando nuevo TotalesMesaParser)
        totales = self.totales_parser.parse(lines)
        result["e14"]["TotalSufragantesE14"] = totales.get("TotalSufragantesE14", "")
        result["e14"]["TotalVotosEnUrna"] = totales.get("TotalVotosEnUrna", "")
        result["e14"]["TotalIncinerados"] = totales.get("TotalIncinerados", "***")

        # Agregar warnings del TotalesMesaParser
        self.warnings.extend(self.totales_parser.warnings)

        # 4. Extraer partidos
        partidos = self._extract_partidos(lines)
        result["e14"]["Partido"] = partidos

        # Validaciones finales
        self._validate_result(result)

        self.logger.info(
            "e14_parsing_completed",
            partidos_count=len(result["e14"]["Partido"]),
            warnings_count=len(self.warnings)
        )

        return result

    def _extract_pagina(self, lines: List[str]) -> str:
        """
        Extrae número de página del formato 'XX de YY'.

        Args:
            lines: Líneas del documento

        Returns:
            Cadena de página (ej: "01 de 09") o "" si no se encuentra
        """
        # Patrón: 01 de 09, 1 de 9, etc.
        pattern = r'\b(\d{1,2})\s+de\s+(\d{1,2})\b'

        for line in lines:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                page_num = match.group(1).zfill(2)
                total_pages = match.group(2).zfill(2)
                pagina = f"{page_num} de {total_pages}"
                self.logger.debug("pagina_found", pagina=pagina)
                return pagina

        self.warnings.append("Campo 'pagina' no encontrado")
        self.logger.warning("pagina_not_found")
        return ""

    def _extract_divipol(self, lines: List[str]) -> Dict[str, str]:
        """
        Extrae códigos DIVIPOL (geográficos y de mesa).

        Args:
            lines: Líneas del documento

        Returns:
            Diccionario con campos DIVIPOL
        """
        divipol = {
            "CodDep": "",
            "CodMun": "",
            "zona": "",
            "Puesto": "",
            "Mesa": ""
        }

        # Unir todas las líneas para búsqueda de patrones
        full_text = '\n'.join(lines)

        # Patrones de búsqueda (case-insensitive, flexible con espacios)
        patterns = {
            "zona": r'ZONA[:\s]*(\d+)',
            "Puesto": r'PUESTO[:\s]*(\d+)',
            "Mesa": r'MESA[:\s]*(\d+)',
            "CodDep": r'DEPARTAMENTO[:\s]*(\d+)',
            "CodMun": r'MUNICIPIO[:\s]*(\d+)'
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                divipol[field] = match.group(1)
                self.logger.debug(f"divipol_{field}_found", value=divipol[field])
            else:
                self.logger.debug(f"divipol_{field}_not_found")

        # Validar que al menos un campo fue encontrado
        if not any(divipol.values()):
            self.warnings.append("Ningún campo DIVIPOL encontrado")
            self.logger.warning("divipol_empty")

        return divipol

    def _extract_totales_mesa(self, lines: List[str]) -> Dict[str, str]:
        """
        Extrae totales de mesa (sufragantes, votos en urna, incinerados).

        Args:
            lines: Líneas del documento

        Returns:
            Diccionario con totales
        """
        totales = {
            "sufragantes": "",
            "votos_urna": "",
            "incinerados": "***"
        }

        full_text = '\n'.join(lines)

        # Buscar después de "FORMATO E-11" o "E-11" o "E11"
        e11_match = re.search(r'FORMATO\s*E-?11|E-?11', full_text, re.IGNORECASE)

        if e11_match:
            # Buscar desde esa posición en adelante
            search_text = full_text[e11_match.end():]

            # Total sufragantes
            sufragantes_pattern = r'TOTAL.*?SUFRAGANTES.*?(\d{1,3})'
            match = re.search(sufragantes_pattern, search_text, re.IGNORECASE | re.DOTALL)
            if match:
                totales["sufragantes"] = match.group(1)
                self.logger.debug("sufragantes_found", value=totales["sufragantes"])

            # Total votos en urna
            votos_pattern = r'TOTAL.*?VOTOS.*?URNA.*?(\d{1,3})'
            match = re.search(votos_pattern, search_text, re.IGNORECASE | re.DOTALL)
            if match:
                totales["votos_urna"] = match.group(1)
                self.logger.debug("votos_urna_found", value=totales["votos_urna"])

            # Total incinerados (puede ser símbolos)
            incinerados_pattern = r'TOTAL.*?INCINERADOS.*?([*#X\d]{1,3})'
            match = re.search(incinerados_pattern, search_text, re.IGNORECASE | re.DOTALL)
            if match:
                totales["incinerados"] = match.group(1)
                self.logger.debug("incinerados_found", value=totales["incinerados"])

        if not totales["sufragantes"]:
            self.warnings.append("Total sufragantes no encontrado")

        if not totales["votos_urna"]:
            self.warnings.append("Total votos en urna no encontrado")

        return totales

    def _extract_partidos(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Extrae todos los partidos y sus datos.

        Args:
            lines: Líneas del documento

        Returns:
            Lista de diccionarios con datos de cada partido
        """
        partidos: List[Dict[str, Any]] = []

        full_text = '\n'.join(lines)

        # Buscar todos los bloques de partidos
        # Patrón: LISTA (CON|SIN) VOTO PREFERENTE + número partido (0XXX)
        partido_pattern = r'LISTA\s+(CON|SIN)\s+VOTO\s+PREFERENTE.*?\b(0\d{3})\b'

        matches = re.finditer(partido_pattern, full_text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            tipo_voto = match.group(1).upper()
            numero_partido = match.group(2)

            tipo_lista = "ListaConVotoPreferente" if tipo_voto == "CON" else "ListaSinVotoPreferente"

            self.logger.debug(
                "partido_detected",
                numero=numero_partido,
                tipo=tipo_lista
            )

            # Extraer datos del partido
            partido_data = self._extract_partido_completo(
                full_text,
                numero_partido,
                tipo_lista,
                match.start()
            )

            if partido_data:
                partidos.append(partido_data)

        self.logger.info("partidos_extracted", count=len(partidos))

        return partidos

    def _extract_partido_completo(
        self,
        text: str,
        numero_partido: str,
        tipo_lista: str,
        start_pos: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extrae datos completos de un partido específico.

        Args:
            text: Texto completo del documento
            numero_partido: Número del partido (0XXX)
            tipo_lista: Tipo de lista (con o sin voto preferente)
            start_pos: Posición de inicio del partido en el texto

        Returns:
            Diccionario con datos del partido o None si falla
        """
        # Buscar nombre del partido (después del número, antes del ID "0")
        nombre_pattern = rf'{numero_partido}\s+(.*?)\s+0\s'
        nombre_match = re.search(nombre_pattern, text[start_pos:start_pos + 500], re.DOTALL)

        nombre_partido = ""
        if nombre_match:
            nombre_partido = self._clean_nombre_partido(nombre_match.group(1))
            self.logger.debug("nombre_partido_found", nombre=nombre_partido)
        else:
            self.warnings.append(f"Nombre de partido {numero_partido} no encontrado")
            self.logger.warning("nombre_partido_not_found", numero=numero_partido)

        # Extraer votos por agrupación política
        votos_agrupacion = self._extract_votos_agrupacion(text, start_pos)

        # Extraer candidatos (solo si es con voto preferente)
        candidatos = []
        if tipo_lista == "ListaConVotoPreferente":
            candidatos = self._extract_candidatos(text, start_pos)

        # Extraer total de votos del partido
        total_votos = self._extract_total_votos_partido(text, start_pos)

        # Determinar si necesita auditoría
        necesita_auditoria = (
            self._contains_non_numeric(votos_agrupacion) or
            self._contains_non_numeric(total_votos) or
            any(c.get("necesita_auditoria", False) for c in candidatos)
        )

        if necesita_auditoria:
            self.warnings.append(f"Partido {numero_partido} necesita auditoría")

        partido = {
            "numPartido": numero_partido,
            "nombrePartido": nombre_partido,
            "tipoDeVoto": tipo_lista,
            "id": "0",
            "votosSoloPorLaAgrupacionPolitica": votos_agrupacion,
            "candidatos": candidatos,
            "TotalVotosAgrupacion+VotosCandidatos": total_votos,
            "necesita_auditoria": necesita_auditoria
        }

        return partido

    def _extract_votos_agrupacion(self, text: str, start_pos: int) -> str:
        """
        Extrae votos por agrupación política.

        Busca después de "AGRUPACIÓN POLÍTICA" o "AGRUPACION POLITICA".

        Args:
            text: Texto completo
            start_pos: Posición de inicio de búsqueda

        Returns:
            Votos como string (puede contener símbolos)
        """
        # Buscar en las siguientes 800 caracteres
        search_text = text[start_pos:start_pos + 800]

        pattern = r'AGRUPACI[OÓ]N\s+POL[IÍ]TICA\s+([*#X/\d]+)'
        match = re.search(pattern, search_text, re.IGNORECASE)

        if match:
            votos = match.group(1).strip()
            self.logger.debug("votos_agrupacion_found", votos=votos)
            return votos

        self.logger.debug("votos_agrupacion_not_found", using_default="0")
        return "0"

    def _extract_candidatos(self, text: str, start_pos: int) -> List[Dict[str, Any]]:
        """
        Extrae candidatos y sus votos (solo para listas con voto preferente).

        Patrón de candidatos:
        - ID: 3 dígitos (101-999)
        - Votos: 0-3 dígitos O símbolos (/, *, etc.)

        Interpretación:
        - 101 / 15 → candidato 101 = 15 votos
        - 101 / / 1 → candidato 101 = 1 voto
        - 101 / / / → candidato 101 = 0 votos
        - 101 / 107 → candidato 101 = 0, candidato 107 inicia

        Args:
            text: Texto completo
            start_pos: Posición de inicio

        Returns:
            Lista de candidatos con sus votos
        """
        candidatos: List[Dict[str, Any]] = []

        # Buscar en las siguientes 2000 caracteres
        search_text = text[start_pos:start_pos + 2000]

        # Buscar todos los IDs de candidatos (3 dígitos)
        candidato_ids = re.findall(r'\b([1-9]\d{2})\b', search_text)

        # Filtrar solo IDs válidos (101-999, excluyendo números de partido 0XXX)
        candidato_ids = [cid for cid in candidato_ids if not cid.startswith('0')]

        self.logger.debug("candidatos_ids_found", count=len(candidato_ids), ids=candidato_ids)

        # Para cada ID, buscar sus votos
        for i, cid in enumerate(candidato_ids):
            # Buscar desde el ID actual hasta el siguiente ID (o fin de sección)
            id_pos = search_text.find(cid)
            if id_pos == -1:
                continue

            # Determinar fin de sección del candidato
            next_id_pos = len(search_text)
            if i + 1 < len(candidato_ids):
                next_id = candidato_ids[i + 1]
                next_pos = search_text.find(next_id, id_pos + len(cid))
                if next_pos != -1:
                    next_id_pos = next_pos

            # Extraer texto entre este ID y el siguiente
            candidato_text = search_text[id_pos:next_id_pos]

            # Buscar votos (número o símbolos después del ID)
            votos = self._parse_votos_candidato(candidato_text, cid)

            necesita_auditoria = self._contains_non_numeric(votos)

            candidatos.append({
                "idcandidato": cid,
                "votos": votos,
                "necesita_auditoria": necesita_auditoria
            })

        self.logger.debug("candidatos_extracted", count=len(candidatos))

        return candidatos

    def _parse_votos_candidato(self, candidato_text: str, candidato_id: str) -> str:
        """
        Parsea votos de un candidato desde su sección de texto.

        Args:
            candidato_text: Texto de la sección del candidato
            candidato_id: ID del candidato (para logging)

        Returns:
            Votos como string (puede ser "0" o símbolos)
        """
        # Eliminar el ID del inicio
        text = candidato_text.replace(candidato_id, '', 1).strip()

        # Buscar primer token que no sea símbolo de separación puro
        # Puede ser: número (15, 1, 0), o símbolos (/, *, etc.)
        tokens = text.split()

        for token in tokens[:10]:  # Limitar búsqueda a primeros 10 tokens
            # Ignorar separadores puros
            if token in ['/', '|', '-', '—']:
                continue

            # Si es número, es el voto
            if re.match(r'^\d{1,3}$', token):
                self.logger.debug("votos_candidato_found", candidato=candidato_id, votos=token)
                return token

            # Si contiene símbolos + números (ej: "/15", "//1")
            num_match = re.search(r'\d+', token)
            if num_match:
                votos = num_match.group()
                self.logger.debug("votos_candidato_found_mixed", candidato=candidato_id, votos=votos)
                return votos

            # Si es solo símbolos (///, ***, etc.) → 0 votos
            if re.match(r'^[/*#X]+$', token):
                self.logger.debug("votos_candidato_simbolos", candidato=candidato_id, simbolos=token)
                return "0"

        # No se encontraron votos → asumir 0
        self.logger.debug("votos_candidato_not_found", candidato=candidato_id, using_default="0")
        return "0"

    def _extract_total_votos_partido(self, text: str, start_pos: int) -> str:
        """
        Extrae total de votos del partido.

        Busca después de "TOTAL ... AGRUPACIÓN ... VOTOS ... CANDIDATOS"
        o "TOTAL =".

        Args:
            text: Texto completo
            start_pos: Posición de inicio

        Returns:
            Total de votos como string
        """
        # Buscar en las siguientes 2000 caracteres
        search_text = text[start_pos:start_pos + 2000]

        # Patrón 1: TOTAL ... AGRUPACIÓN ... VOTOS ... CANDIDATOS ... [número]
        pattern1 = r'TOTAL.*?AGRUPACI[OÓ]N.*?VOTOS.*?CANDIDATOS.*?([*#X/\d]+)'
        match = re.search(pattern1, search_text, re.IGNORECASE | re.DOTALL)

        if match:
            total = match.group(1).strip()
            self.logger.debug("total_votos_partido_found_pattern1", total=total)
            return total

        # Patrón 2: TOTAL = [número]
        pattern2 = r'TOTAL\s*=\s*([*#X/\d]+)'
        match = re.search(pattern2, search_text, re.IGNORECASE)

        if match:
            total = match.group(1).strip()
            self.logger.debug("total_votos_partido_found_pattern2", total=total)
            return total

        self.logger.debug("total_votos_partido_not_found", using_default="0")
        return "0"

    def _clean_nombre_partido(self, raw_name: str) -> str:
        """
        Limpia nombre de partido removiendo símbolos y normalizando.

        Args:
            raw_name: Nombre crudo extraído

        Returns:
            Nombre limpio en mayúsculas
        """
        # Remover símbolos comunes de logos/ruido
        cleaned = re.sub(r'[●○◆◇■□▪▫★☆✓✗►◄▲▼]', '', raw_name)

        # Remover múltiples espacios
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Trim y uppercase
        cleaned = cleaned.strip().upper()

        return cleaned

    def _contains_non_numeric(self, value: str) -> bool:
        """
        Verifica si un valor contiene caracteres no numéricos.

        Args:
            value: Valor a verificar

        Returns:
            True si contiene símbolos no numéricos
        """
        return not re.match(r'^\d+$', value)

    def _validate_result(self, result: Dict[str, Any]) -> None:
        """
        Valida el resultado final antes de retornarlo.

        Args:
            result: Diccionario de resultado

        Agrega warnings si falta información crítica.
        """
        e14 = result["e14"]

        # Validar página
        if not e14["pagina"]:
            self.warnings.append("CRÍTICO: Campo 'pagina' está vacío")

        # Validar DIVIPOL (al menos un campo debe tener valor)
        if not any(e14["divipol"].values()):
            self.warnings.append("CRÍTICO: Todos los campos DIVIPOL están vacíos")

        # Validar partidos
        if not e14["Partido"]:
            self.warnings.append("CRÍTICO: No se encontraron partidos")

        # Validar candidatos por tipo de lista
        for partido in e14["Partido"]:
            if partido["tipoDeVoto"] == "ListaConVotoPreferente":
                if not partido["candidatos"]:
                    self.warnings.append(
                        f"Partido {partido['numPartido']} con voto preferente no tiene candidatos"
                    )
            elif partido["tipoDeVoto"] == "ListaSinVotoPreferente":
                if partido["candidatos"]:
                    self.warnings.append(
                        f"Partido {partido['numPartido']} sin voto preferente tiene candidatos (no debería)"
                    )

        self.logger.info("validation_completed", warnings_count=len(self.warnings))
