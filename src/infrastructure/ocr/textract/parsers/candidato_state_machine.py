from typing import List, Dict, Optional
import re
import structlog
from .parser_state import ParserState

logger = structlog.get_logger(__name__)


class CandidatoStateMachine:

    def __init__(self, page_offset: int = 100):
        self.state = ParserState.BUSCANDO_ID
        self.page_offset = page_offset
        self.current_id: Optional[str] = None
        self.simbolos_buffer: List[str] = []
        self.logger = logger.bind(component="CandidatoStateMachine", offset=page_offset)

    def parse_candidatos(self, tokens: List[str]) -> List[Dict]:
        candidatos = []

        for token in tokens:
            token_clean = self._normalize_token(token)

            if self.state == ParserState.BUSCANDO_ID:
                if self._is_candidato_id(token_clean):
                    self.current_id = token_clean
                    self.state = ParserState.BUSCANDO_VOTO
                    self.simbolos_buffer = []

            elif self.state == ParserState.BUSCANDO_VOTO:
                if self._is_candidato_id(token_clean):
                    candidatos.append({
                        "idcandidato": self.current_id,
                        "votos": "0",
                        "necesita_auditoria": True,
                        "razon_auditoria": "sin_voto_explícito"
                    })
                    self.current_id = token_clean
                    self.simbolos_buffer = []

                elif self._is_simbolo(token_clean):
                    self.simbolos_buffer.append(token_clean)
                    self.state = ParserState.SIMBOLOS_INTERMEDIOS

                elif self._is_voto_valido(token_clean):
                    candidatos.append({
                        "idcandidato": self.current_id,
                        "votos": token_clean,
                        "necesita_auditoria": False
                    })
                    self.current_id = None
                    self.state = ParserState.BUSCANDO_ID
                    self.simbolos_buffer = []

            elif self.state == ParserState.SIMBOLOS_INTERMEDIOS:
                if self._is_candidato_id(token_clean):
                    candidatos.append({
                        "idcandidato": self.current_id,
                        "votos": "0",
                        "necesita_auditoria": True,
                        "razon_auditoria": f"símbolos_intermedios: {self.simbolos_buffer}"
                    })
                    self.current_id = token_clean
                    self.state = ParserState.BUSCANDO_VOTO
                    self.simbolos_buffer = []

                elif self._is_voto_valido(token_clean):
                    candidatos.append({
                        "idcandidato": self.current_id,
                        "votos": token_clean,
                        "necesita_auditoria": True,
                        "razon_auditoria": f"símbolos_previos: {self.simbolos_buffer}"
                    })
                    self.current_id = None
                    self.state = ParserState.BUSCANDO_ID
                    self.simbolos_buffer = []

                elif self._is_simbolo(token_clean):
                    self.simbolos_buffer.append(token_clean)

        if self.current_id:
            candidatos.append({
                "idcandidato": self.current_id,
                "votos": "0",
                "necesita_auditoria": True,
                "razon_auditoria": "fin_de_bloque"
            })

        self.logger.debug("parsing_completed", candidatos_found=len(candidatos))
        return candidatos

    def _normalize_token(self, token: str) -> str:
        return token.strip().replace("O", "0").replace("o", "0")

    def _is_candidato_id(self, token: str) -> bool:
        if not re.match(r'^\d{3}$', token):
            return False
        num = int(token)
        min_id = self.page_offset + 1
        max_id = self.page_offset + 99
        return min_id <= num <= max_id

    def _is_voto_valido(self, token: str) -> bool:
        if not re.match(r'^\d{1,4}$', token):
            return False
        return not self._is_candidato_id(token)

    def _is_simbolo(self, token: str) -> bool:
        return bool(re.match(r'^[*/\#\-XAO]+$', token))
