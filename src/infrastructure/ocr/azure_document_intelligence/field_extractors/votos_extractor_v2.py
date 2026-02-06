from typing import Dict, Tuple, Optional
import structlog
import re

from src.domain.value_objects.confidence_score import ConfidenceScore

logger = structlog.get_logger(__name__)


class VotosExtractorV2:
    @staticmethod
    def extract(azure_response: dict) -> Dict[str, Tuple[int, Optional[ConfidenceScore]]]:
        try:
            documents = azure_response.get("documents", [])
            if not documents:
                logger.warning("no_documents_in_response")
                return {}

            doc = documents[0]
            fields = doc.get("fields", {})

            result = {}

            total_votos_urna = fields.get("TotalVotosUrna")
            if total_votos_urna:
                content = total_votos_urna.get("valueString", "")
                number_match = re.search(r"(-?\d+)", content)
                if number_match:
                    votos_value = int(number_match.group(1))
                    confidence = total_votos_urna.get("confidence", 0.0)
                    result["total_votos_urna"] = (
                        votos_value,
                        ConfidenceScore(confidence)
                    )

            total_sufragantes = fields.get("TotalSufragantes")
            if total_sufragantes:
                confidence = total_sufragantes.get("confidence", 0.0)
                result["total_sufragantes"] = (
                    0,
                    ConfidenceScore(confidence)
                )

            total_incinerados = fields.get("TotalVotosIncinerados")
            if total_incinerados:
                content = total_incinerados.get("valueString", "")
                number_match = re.search(r"(-?\d+)", content)
                if number_match:
                    votos_value = int(number_match.group(1))
                    confidence = total_incinerados.get("confidence", 0.0)
                    result["total_votos_incinerados"] = (
                        votos_value,
                        ConfidenceScore(confidence)
                    )

            result["votos_nulos"] = (0, None)
            result["votos_no_marcados"] = (0, None)
            result["votos_blanco"] = (0, None)
            result["total_votos_validos"] = (0, None)

            logger.info("votos_extracted", result_keys=list(result.keys()))
            return result

        except Exception as e:
            logger.error("votos_extraction_failed", error=str(e))
            return {}
