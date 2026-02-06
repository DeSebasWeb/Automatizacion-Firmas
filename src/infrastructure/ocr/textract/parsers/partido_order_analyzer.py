from typing import List, Dict, Tuple
import structlog
import re

logger = structlog.get_logger(__name__)


class PartidoOrderAnalyzer:

    def __init__(self):
        self.logger = logger.bind(component="PartidoOrderAnalyzer")

    def analyze_and_extract(self, bloque: List[str], tipo_voto: str) -> Dict:
        self.logger.info("analyzing_partido_block", size=len(bloque), tipo=tipo_voto)

        num_partido = self._extract_num_partido(bloque)
        nombre_partido = self._extract_nombre_partido(bloque, num_partido)
        votos_agrupacion_data = self._extract_votos_agrupacion_section(bloque)

        return {
            "numPartido": num_partido,
            "nombrePartido": nombre_partido,
            "tipo_voto": tipo_voto,
            "votos_agrupacion_section": votos_agrupacion_data
        }

    def _extract_num_partido(self, bloque: List[str]) -> str:
        for i, line in enumerate(bloque[:20]):
            line_clean = line.strip()
            if re.match(r'^0\d{3}$', line_clean):
                self.logger.debug("num_partido_found", num=line_clean, line_idx=i)
                return line_clean

        self.logger.warning("num_partido_not_found")
        return ""

    def _extract_nombre_partido(self, bloque: List[str], num_partido: str) -> str:
        nombre_lines = []
        found_num = False
        search_limit = min(30, len(bloque))

        for i in range(search_limit):
            line = bloque[i].strip()

            if line == num_partido:
                found_num = True
                continue

            if not found_num:
                line_upper = line.upper()
                if any(kw in line_upper for kw in ['PARTIDO', 'COALICI', 'MOVIMIENTO', 'LIBERAL', 'CONSERVADOR']):
                    nombre_lines.append(line)
                continue

            if self._is_end_of_nombre(line):
                break

            line_upper = line.upper()
            if any(kw in line_upper for kw in ['PARTIDO', 'COALICI', 'MOVIMIENTO', 'LIBERAL', 'CONSERVADOR', 'DIGNIDAD', 'COLOMBIANO', 'MIRA', 'GENTE', 'HUMANA']):
                nombre_lines.append(line)
                continue

            if line and not re.match(r'^[*/#\-X0]+$', line) and not line.isdigit():
                nombre_lines.append(line)

            if len(nombre_lines) > 6:
                break

        nombre = ' '.join(nombre_lines).strip()
        nombre = re.sub(r'\b\d{1,3}\b', '', nombre).strip()
        nombre = re.sub(r'\s+', ' ', nombre).strip()
        nombre_final = nombre[:200]

        if not nombre_final:
            nombre_final = f"PARTIDO_{num_partido}"

        self.logger.debug("nombre_partido_extracted", nombre=nombre_final, lines_used=len(nombre_lines))
        return nombre_final

    def _is_end_of_nombre(self, line: str) -> bool:
        line_upper = line.upper()
        end_markers = [
            'VOTOS SOLO POR LA AGRUPACI',
            'VOTOS POR LA AGRUPACI',
            'TOTAL',
            'CANDIDATO'
        ]
        return any(marker in line_upper for marker in end_markers)

    def _extract_votos_agrupacion_section(self, bloque: List[str]) -> Dict:
        anchor_idx = self._find_votos_agrupacion_anchor(bloque)

        if anchor_idx is None:
            self.logger.warning("votos_agrupacion_anchor_not_found")
            return {
                "start_idx": -1,
                "end_idx": -1,
                "lines": []
            }

        end_idx = self._find_votos_section_end(bloque, anchor_idx)
        section_lines = bloque[anchor_idx:end_idx]

        self.logger.debug(
            "votos_agrupacion_section_extracted",
            start=anchor_idx,
            end=end_idx,
            size=len(section_lines)
        )

        return {
            "start_idx": anchor_idx,
            "end_idx": end_idx,
            "lines": section_lines
        }

    def _find_votos_agrupacion_anchor(self, bloque: List[str]) -> int:
        for i, line in enumerate(bloque):
            line_upper = line.upper()
            if 'VOTOS SOLO POR LA AGRUPACI' in line_upper:
                return i
            if 'VOTOS POR LA AGRUPACI' in line_upper:
                return i
        return None

    def _find_votos_section_end(self, bloque: List[str], start_idx: int) -> int:
        max_search = min(start_idx + 50, len(bloque))

        for i in range(start_idx + 1, max_search):
            line_upper = bloque[i].upper()

            if 'TOTAL' in line_upper and ('VOTOS' in line_upper or 'AGRUPACI' in line_upper):
                return min(i + 3, len(bloque))

            if 'LISTA CON VOTO PREFERENTE' in line_upper and i > start_idx + 5:
                return i

            if 'LISTA SIN VOTO PREFERENTE' in line_upper and i > start_idx + 5:
                return i

        return max_search
