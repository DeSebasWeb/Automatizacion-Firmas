from typing import List, Optional, Tuple
import structlog
import re

logger = structlog.get_logger(__name__)


class PartidoBlockDetector:

    PARTIDO_ANCHORS = [
        "LISTA CON VOTO PREFERENTE",
        "LISTA SIN VOTO PREFERENTE"
    ]

    END_MARKERS = [
        "CIRCUNSCRIPCIÓN",
        "CIRCUNSCRIPCION",
        "TERRITORIAL"
    ]

    def __init__(self):
        self.logger = logger.bind(component="PartidoBlockDetector")

    def find_all_partido_blocks(self, lines: List[str]) -> List[Tuple[int, int, str]]:
        blocks = []
        anchors = self._find_all_lista_anchors(lines)

        if not anchors:
            self.logger.warning("no_lista_anchors_found")
            return blocks

        for i in range(len(anchors)):
            start_idx, tipo_voto = anchors[i]

            if i + 1 < len(anchors):
                end_idx = anchors[i + 1][0]
            else:
                end_idx = len(lines)

            blocks.append((start_idx, end_idx, tipo_voto))
            self.logger.debug(
                "partido_block_detected",
                start=start_idx,
                end=end_idx,
                tipo=tipo_voto,
                size=end_idx - start_idx
            )

        self.logger.info("partido_blocks_found", count=len(blocks))
        return blocks

    def _find_all_lista_anchors(self, lines: List[str]) -> List[Tuple[int, str]]:
        anchors = []

        for i, line in enumerate(lines):
            line_upper = line.upper().strip()

            if 'LISTA CON VOTO PREFERENTE' in line_upper:
                anchors.append((i, "ListaConVotoPreferente"))
                self.logger.debug("lista_anchor_found", idx=i, tipo="ListaConVotoPreferente")
            elif 'LISTA SIN VOTO PREFERENTE' in line_upper:
                anchors.append((i, "ListaSinVotoPreferente"))
                self.logger.debug("lista_anchor_found", idx=i, tipo="ListaSinVotoPreferente")

        return anchors

    def _find_num_partido_nearby(self, lines: List[str], idx: int) -> Optional[int]:
        window_size = 10
        for i in range(idx, min(idx + window_size, len(lines))):
            line_clean = lines[i].strip()
            if re.match(r'^0\d{3}$', line_clean):
                self.logger.debug("num_partido_found", num=line_clean, idx=i)
                return i
        return None

    def _infer_tipo_voto_from_context(self, lines: List[str], num_partido_idx: int) -> str:
        search_range = 15
        start = max(0, num_partido_idx - 5)
        end = min(len(lines), num_partido_idx + search_range)

        for i in range(start, end):
            line_upper = lines[i].upper()
            if 'LISTA SIN VOTO PREFERENTE' in line_upper or 'SIN VOTO' in line_upper:
                return "ListaSinVotoPreferente"

        return "ListaConVotoPreferente"

    def _is_partido_anchor(self, lines: List[str], idx: int) -> Optional[str]:
        window_size = 5
        for i in range(idx, min(idx + window_size, len(lines))):
            line_upper = lines[i].upper().strip()

            if 'LISTA CON VOTO PREFERENTE' in line_upper:
                return "ListaConVotoPreferente"
            if 'LISTA SIN VOTO PREFERENTE' in line_upper:
                return "ListaSinVotoPreferente"

        return None

    def _find_block_end(self, lines: List[str], start_idx: int) -> int:
        max_search = min(start_idx + 100, len(lines))

        for i in range(start_idx + 5, max_search):
            line_upper = lines[i].upper().strip()

            if 'LISTA CON VOTO PREFERENTE' in line_upper:
                return i
            if 'LISTA SIN VOTO PREFERENTE' in line_upper:
                return i

            for marker in self.END_MARKERS:
                if marker in line_upper:
                    return i

            if re.match(r'^X\s*\d+-\d+-\d+-\d+\s*X', lines[i]):
                return i

        return max_search
