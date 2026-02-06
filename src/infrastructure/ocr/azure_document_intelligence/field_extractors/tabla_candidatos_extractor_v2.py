from typing import List, Dict
import structlog
import re

from src.infrastructure.ocr.azure_document_intelligence.models import PartidoResult
from src.domain.value_objects.confidence_score import ConfidenceScore

logger = structlog.get_logger(__name__)


class TablaCandidatosExtractorV2:
    @staticmethod
    def extract(azure_response: dict) -> List[PartidoResult]:
        try:
            documents = azure_response.get("documents", [])
            if not documents:
                logger.warning("no_documents_in_response")
                return []

            doc = documents[0]
            fields = doc.get("fields", {})

            partidos_map: Dict[str, dict] = {}

            for field_name, field_data in fields.items():
                if field_name.startswith("TipoDeVotoPartido") and "Pag" in field_name:
                    content = field_data.get("valueString", "").strip()
                    confidence = field_data.get("confidence", 0.0)

                    if not content:
                        continue

                    lines = [line.strip() for line in content.split("\n") if line.strip()]

                    if len(lines) < 3:
                        logger.warning("partido_insufficient_lines", field_name=field_name, lines=len(lines))
                        continue

                    numero_partido = lines[1]
                    nombre_partido = lines[2]

                    if numero_partido not in partidos_map:
                        partidos_map[numero_partido] = {
                            "numero_lista": numero_partido,
                            "partido": nombre_partido,
                            "votos_partido": 0,
                            "confidence": confidence
                        }

            for field_name, field_data in fields.items():
                if "TotalVotosAgrupacion+VotosCandidatos" in field_name or "Total=VotosAgrupacion+VotosCandidatos" in field_name:
                    content = field_data.get("valueString", "").strip()
                    number_match = re.search(r"(\d+)", content)
                    if number_match:
                        votos_total = int(number_match.group(1))

                        for numero_partido in partidos_map.keys():
                            if partidos_map[numero_partido]["votos_partido"] == 0:
                                partidos_map[numero_partido]["votos_partido"] = votos_total
                                break

            partidos = []
            for partido_data in partidos_map.values():
                partido = PartidoResult(
                    numero_lista=partido_data["numero_lista"],
                    partido=partido_data["partido"],
                    votos_partido=partido_data["votos_partido"],
                    candidatos=[],
                    confidence=ConfidenceScore(partido_data["confidence"])
                )
                partidos.append(partido)

            logger.info("partidos_extracted", count=len(partidos))
            return partidos

        except Exception as e:
            logger.error("tabla_candidatos_extraction_failed", error=str(e))
            return []
