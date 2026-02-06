from typing import Dict, Optional
import structlog

from src.domain.value_objects.confidence_score import ConfidenceScore

logger = structlog.get_logger(__name__)


class VotosExtractor:
    VOTO_FIELDS = [
        "votos_nulos",
        "votos_no_marcados",
        "votos_blanco",
        "total_votos_validos"
    ]

    @staticmethod
    def extract(azure_response: dict) -> Dict[str, tuple[int, ConfidenceScore]]:
        results = {}

        try:
            documents = azure_response.get("documents", [])
            if not documents:
                logger.warning("no_documents_in_response")
                return results

            doc = documents[0]
            fields = doc.get("fields", {})

            for field_name in VotosExtractor.VOTO_FIELDS:
                field_data = fields.get(field_name)
                if not field_data:
                    logger.warning("field_not_found", field=field_name)
                    results[field_name] = (0, ConfidenceScore.zero())
                    continue

                content = field_data.get("content", "").strip()
                confidence_raw = field_data.get("confidence", 0.0)

                if not content:
                    logger.warning("field_empty", field=field_name)
                    results[field_name] = (0, ConfidenceScore(confidence_raw))
                    continue

                try:
                    value = int(content)
                    confidence = ConfidenceScore(confidence_raw)
                    results[field_name] = (value, confidence)
                except ValueError:
                    logger.error("invalid_integer", field=field_name, content=content)
                    results[field_name] = (0, ConfidenceScore(confidence_raw))

        except Exception as e:
            logger.error("votos_extraction_failed", error=str(e))

        return results
