from typing import List, Dict
import structlog
import re

logger = structlog.get_logger(__name__)


class PartidoTokenReconstructor:

    def __init__(self):
        self.logger = logger.bind(component="PartidoTokenReconstructor")

    def reconstruct_tokens(self, section_lines: List[str]) -> Dict:
        self.logger.debug("reconstructing_tokens", lines_count=len(section_lines))

        patterns = self._try_all_patterns(section_lines)
        best_pattern = self._select_best_pattern(patterns)

        self.logger.info(
            "pattern_selected",
            pattern=best_pattern["pattern_name"],
            score=best_pattern["score"],
            votos_agrupacion=best_pattern["votos_agrupacion"],
            candidatos_tokens_count=len(best_pattern["candidatos_tokens"])
        )

        return best_pattern

    def _try_all_patterns(self, section_lines: List[str]) -> List[Dict]:
        patterns = []

        horizontal = self._try_horizontal_pattern(section_lines)
        patterns.append(horizontal)

        vertical = self._try_vertical_pattern(section_lines)
        patterns.append(vertical)

        mixed = self._try_mixed_pattern(section_lines)
        patterns.append(mixed)

        return patterns

    def _try_horizontal_pattern(self, section_lines: List[str]) -> Dict:
        tokens = self._tokenize_lines(section_lines)
        votos_agrupacion, candidatos_start = self._extract_votos_and_candidatos(tokens)

        score = self._score_horizontal(tokens, votos_agrupacion)

        return {
            "pattern_name": "horizontal",
            "score": score,
            "votos_agrupacion": votos_agrupacion,
            "candidatos_tokens": tokens[candidatos_start:] if candidatos_start < len(tokens) else []
        }

    def _try_vertical_pattern(self, section_lines: List[str]) -> Dict:
        grouped_tokens = []
        for line in section_lines:
            line_tokens = self._tokenize_single_line(line)
            if line_tokens:
                grouped_tokens.extend(line_tokens)

        votos_agrupacion, candidatos_start = self._extract_votos_and_candidatos(grouped_tokens)
        score = self._score_vertical(grouped_tokens, votos_agrupacion)

        return {
            "pattern_name": "vertical",
            "score": score,
            "votos_agrupacion": votos_agrupacion,
            "candidatos_tokens": grouped_tokens[candidatos_start:] if candidatos_start < len(grouped_tokens) else []
        }

    def _try_mixed_pattern(self, section_lines: List[str]) -> Dict:
        tokens = []
        skip_next = False

        for i, line in enumerate(section_lines):
            if skip_next:
                skip_next = False
                continue

            line_upper = line.upper().strip()

            if 'VOTOS' in line_upper or 'AGRUPACI' in line_upper or 'POLÍTICA' in line_upper:
                skip_next = True
                continue

            line_tokens = self._tokenize_single_line(line)
            tokens.extend(line_tokens)

        votos_agrupacion, candidatos_start = self._extract_votos_and_candidatos(tokens)
        score = self._score_mixed(tokens, votos_agrupacion)

        return {
            "pattern_name": "mixed",
            "score": score,
            "votos_agrupacion": votos_agrupacion,
            "candidatos_tokens": tokens[candidatos_start:] if candidatos_start < len(tokens) else []
        }

    def _tokenize_lines(self, lines: List[str]) -> List[str]:
        tokens = []
        for line in lines:
            tokens.extend(self._tokenize_single_line(line))
        return tokens

    def _tokenize_single_line(self, line: str) -> List[str]:
        line_clean = line.strip()
        if not line_clean:
            return []

        line_upper = line_clean.upper()
        if any(kw in line_upper for kw in ['VOTOS', 'AGRUPACI', 'POLÍTICA', 'TOTAL', 'CANDIDATO']):
            return []

        line_normalized = line_clean.replace("O", "0").replace("o", "0")

        if ' ' in line_normalized:
            return [t for t in line_normalized.split() if t]

        if re.search(r'[*/\#\-]', line_normalized):
            parts = re.findall(r'\d+|[*/\#\-]+', line_normalized)
            return [p for p in parts if p]

        return [line_normalized] if line_normalized else []

    def _extract_votos_and_candidatos(self, tokens: List[str]) -> tuple:
        votos_agrupacion = "0"
        candidatos_start = 0

        for i, token in enumerate(tokens):
            if self._looks_like_candidato_id(token):
                candidatos_start = i
                break

            if token.isdigit() and len(token) <= 4:
                votos_agrupacion = token

        return votos_agrupacion, candidatos_start

    def _looks_like_candidato_id(self, token: str) -> bool:
        if not re.match(r'^\d{3}$', token):
            return False

        num = int(token)
        return 101 <= num <= 999

    def _score_horizontal(self, tokens: List[str], votos_agrupacion: str) -> int:
        score = 0

        if votos_agrupacion.isdigit() and votos_agrupacion != "0":
            score += 10

        candidato_ids = [t for t in tokens if self._looks_like_candidato_id(t)]
        if len(candidato_ids) >= 2:
            score += 15

        return score

    def _score_vertical(self, tokens: List[str], votos_agrupacion: str) -> int:
        score = 0

        if votos_agrupacion.isdigit():
            score += 8

        candidato_ids = [t for t in tokens if self._looks_like_candidato_id(t)]
        if len(candidato_ids) >= 2:
            score += 12

        return score

    def _score_mixed(self, tokens: List[str], votos_agrupacion: str) -> int:
        score = 0

        if votos_agrupacion.isdigit():
            score += 5

        candidato_ids = [t for t in tokens if self._looks_like_candidato_id(t)]
        if len(candidato_ids) >= 2:
            score += 10

        return score

    def _select_best_pattern(self, patterns: List[Dict]) -> Dict:
        best = max(patterns, key=lambda p: p["score"])

        for p in patterns:
            self.logger.debug(
                "pattern_scored",
                pattern=p["pattern_name"],
                score=p["score"],
                votos=p["votos_agrupacion"],
                candidatos_count=len(p["candidatos_tokens"])
            )

        return best
