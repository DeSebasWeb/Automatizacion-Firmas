from typing import List
import re
import structlog

logger = structlog.get_logger(__name__)


class SmartTokenizer:

    def __init__(self):
        self.logger = logger.bind(component="SmartTokenizer")

    def tokenize(self, bloque: List[str]) -> List[str]:
        tokens = []

        for line in bloque:
            line_clean = line.strip()
            if not line_clean:
                continue

            line_normalized = line_clean.replace("O", "0").replace("o", "0")

            if ' ' in line_normalized:
                tokens.extend(line_normalized.split())
                continue

            if re.search(r'[*/\#\-]', line_normalized):
                parts = re.findall(r'\d+|[*/\#\-]+', line_normalized)
                tokens.extend(parts)
                continue

            tokens.append(line_normalized)

        clean_tokens = [t for t in tokens if t]
        self.logger.debug("tokenization_completed", input_lines=len(bloque), output_tokens=len(clean_tokens))
        return clean_tokens
