from typing import List, Dict, Tuple
import re
import structlog
from .base_parser import BaseParser
from .partido_block_detector import PartidoBlockDetector
from .partido_order_analyzer import PartidoOrderAnalyzer
from .partido_token_reconstructor import PartidoTokenReconstructor
from .candidato_state_machine import CandidatoStateMachine
from .candidato_validator import CandidatoValidator

logger = structlog.get_logger(__name__)


class PartidoParser(BaseParser):

    def __init__(self):
        super().__init__()
        self.block_detector = PartidoBlockDetector()
        self.order_analyzer = PartidoOrderAnalyzer()
        self.token_reconstructor = PartidoTokenReconstructor()

    def parse(self, lines: List[str]) -> Dict:
        self.logger.info("parse_started", lines_count=len(lines))
        self.reset_warnings()

        blocks = self.block_detector.find_all_partido_blocks(lines)

        if not blocks:
            self.logger.warning("no_partido_blocks_found")
            return {"Partido": []}

        partidos = []
        for start_idx, end_idx, tipo_voto in blocks:
            bloque = lines[start_idx:end_idx]

            try:
                partido_data = self._parse_single_partido(bloque, tipo_voto)
                partidos.append(partido_data)
            except Exception as e:
                self.logger.error(
                    "partido_parsing_failed",
                    error=str(e),
                    start=start_idx,
                    end=end_idx,
                    tipo=tipo_voto
                )
                self.add_warning(f"Error parsing partido at lines {start_idx}-{end_idx}: {str(e)}")

        self.logger.info("partidos_extracted", count=len(partidos))
        return {"Partido": partidos}

    def _parse_single_partido(self, bloque: List[str], tipo_voto: str) -> Dict:
        self.logger.debug("parsing_single_partido", size=len(bloque), tipo=tipo_voto)

        metadata = self.order_analyzer.analyze_and_extract(bloque, tipo_voto)

        num_partido = metadata["numPartido"]
        nombre_partido = metadata["nombrePartido"]
        votos_section = metadata["votos_agrupacion_section"]

        if tipo_voto == "ListaSinVotoPreferente":
            datos = self._parse_partido_sin_candidatos(votos_section["lines"])
        else:
            datos = self._parse_partido_con_candidatos(votos_section["lines"])

        partido = {
            "numPartido": num_partido,
            "nombrePartido": nombre_partido,
            "tipoDeVoto": tipo_voto,
            "id": "0",
            **datos
        }

        return partido

    def _parse_partido_sin_candidatos(self, section_lines: List[str]) -> Dict:
        votos_agrupacion = "0"
        skip_zero = False

        for line in section_lines:
            line_clean = line.strip()

            if line_clean in ["0", "O"]:
                skip_zero = True
                continue

            if not skip_zero:
                continue

            if line_clean and not self._is_keyword_line(line_clean):
                votos_agrupacion = line_clean.replace("O", "0")
                break

        return {
            "votosSoloPorLaAgrupacionPolitica": votos_agrupacion,
            "candidatos": [],
            "TotalVotosAgrupacion+VotosCandidatos": votos_agrupacion,
            "necesita_auditoria": not votos_agrupacion.isdigit()
        }

    def _parse_partido_con_candidatos(self, section_lines: List[str]) -> Dict:
        self.logger.info("parsing_partido_con_candidatos", section_size=len(section_lines))

        reconstruction = self.token_reconstructor.reconstruct_tokens(section_lines)

        votos_agrupacion = reconstruction["votos_agrupacion"]
        candidatos_tokens = reconstruction["candidatos_tokens"]

        self.logger.debug(
            "reconstruction_completed",
            pattern=reconstruction["pattern_name"],
            votos=votos_agrupacion,
            tokens_count=len(candidatos_tokens)
        )

        page_offset = self._detect_page_offset(candidatos_tokens)

        state_machine = CandidatoStateMachine(page_offset)
        candidatos_raw = state_machine.parse_candidatos(candidatos_tokens)

        self.logger.debug("candidatos_raw_extracted", count=len(candidatos_raw))

        validator = CandidatoValidator()
        candidatos, errores = validator.validate_candidatos(candidatos_raw, "ListaConVotoPreferente")

        if errores:
            self.logger.warning("validation_errors", errores=errores)

        total_partido = self._extract_total_partido(candidatos_tokens)

        necesita_auditoria = (
            not votos_agrupacion.isdigit() or
            not total_partido.isdigit() or
            len(errores) > 0 or
            any(c["necesita_auditoria"] for c in candidatos)
        )

        resultado = {
            "votosSoloPorLaAgrupacionPolitica": votos_agrupacion,
            "candidatos": candidatos,
            "TotalVotosAgrupacion+VotosCandidatos": total_partido,
            "necesita_auditoria": necesita_auditoria,
            "errores_validacion": errores,
            "page_offset_detected": page_offset,
            "pattern_used": reconstruction["pattern_name"]
        }

        self.logger.info(
            "partido_con_candidatos_parsed",
            votos_agrup=votos_agrupacion,
            num_candidatos=len(candidatos),
            total=total_partido,
            auditoria=necesita_auditoria,
            pattern=reconstruction["pattern_name"]
        )

        return resultado

    def _detect_page_offset(self, tokens: List[str]) -> int:
        for token in tokens:
            if re.match(r'^\d{3}$', token):
                num = int(token)
                if 101 <= num <= 999:
                    offset = (num // 100) * 100
                    self.logger.info("page_offset_detected", offset=offset, first_id=token)
                    return offset

        self.logger.warning("page_offset_not_detected_using_default", offset=100)
        return 100

    def _extract_total_partido(self, tokens: List[str]) -> str:
        for token in reversed(tokens):
            if re.match(r'^\d{1,5}$', token):
                return token
        return "0"

    def _is_keyword_line(self, line: str) -> bool:
        line_upper = line.upper()
        keywords = ['VOTOS', 'AGRUPACI', 'POLÍTICA', 'TOTAL', 'CANDIDATO', 'LISTA']
        return any(kw in line_upper for kw in keywords)
