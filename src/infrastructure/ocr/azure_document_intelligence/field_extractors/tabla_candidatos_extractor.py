from typing import List, Dict, Optional
import structlog

from ..models.candidato_voto import CandidatoVoto
from ..models.partido_result import PartidoResult
from src.domain.value_objects.confidence_score import ConfidenceScore

logger = structlog.get_logger(__name__)


class TablaCandidatosExtractor:
    @staticmethod
    def extract(azure_response: dict) -> List[PartidoResult]:
        try:
            documents = azure_response.get("documents", [])
            if not documents:
                logger.warning("no_documents_in_response")
                return []

            doc = documents[0]
            fields = doc.get("fields", {})

            tabla_field = fields.get("tabla_candidatos")
            if not tabla_field:
                logger.warning("tabla_candidatos_field_not_found")
                return []

            rows = tabla_field.get("valueArray", [])
            if not rows:
                logger.warning("tabla_candidatos_empty")
                return []

            return TablaCandidatosExtractor._parse_rows_optimized(rows)

        except Exception as e:
            logger.error("tabla_candidatos_extraction_failed", error=str(e))
            return []

    @staticmethod
    def _parse_rows_optimized(rows: List[dict]) -> List[PartidoResult]:
        partidos: Dict[str, dict] = {}

        for row in rows:
            row_data = TablaCandidatosExtractor._extract_row_data(row)
            if not row_data:
                continue

            partido_key = row_data["numero_lista"]

            if partido_key not in partidos:
                partidos[partido_key] = {
                    "partido": row_data["partido"],
                    "numero_lista": row_data["numero_lista"],
                    "votos_partido": row_data["votos_partido"],
                    "candidatos": [],
                    "confidences": [row_data["confidence_partido"]]
                }

            if row_data["candidato_numero"] and row_data["candidato_nombre"]:
                candidato = CandidatoVoto.create(
                    numero=row_data["candidato_numero"],
                    nombre=row_data["candidato_nombre"],
                    votos=row_data["candidato_votos"],
                    confidence=row_data["confidence_candidato"]
                )
                partidos[partido_key]["candidatos"].append(candidato)
                partidos[partido_key]["confidences"].append(row_data["confidence_candidato"])

        results = []
        for partido_data in partidos.values():
            avg_confidence = sum(c.value for c in partido_data["confidences"]) / len(partido_data["confidences"])

            result = PartidoResult(
                partido=partido_data["partido"],
                numero_lista=partido_data["numero_lista"],
                votos_partido=partido_data["votos_partido"],
                candidatos=partido_data["candidatos"],
                confidence=avg_confidence
            )
            results.append(result)

        return results

    @staticmethod
    def _extract_row_data(row: dict) -> Optional[Dict]:
        try:
            row_fields = row.get("valueObject", {})

            partido = row_fields.get("partido", {}).get("content", "").strip()
            numero_lista = row_fields.get("numero_lista", {}).get("content", "").strip()
            votos_partido_str = row_fields.get("votos_partido", {}).get("content", "").strip()
            confidence_partido = row_fields.get("votos_partido", {}).get("confidence", 0.0)

            candidato_numero = row_fields.get("candidato_numero", {}).get("content", "").strip()
            candidato_nombre = row_fields.get("candidato_nombre", {}).get("content", "").strip()
            candidato_votos_str = row_fields.get("candidato_votos", {}).get("content", "").strip()
            confidence_candidato = row_fields.get("candidato_votos", {}).get("confidence", 0.0)

            if not partido or not numero_lista:
                logger.warning("missing_partido_or_numero_lista")
                return None

            votos_partido = int(votos_partido_str) if votos_partido_str else 0
            candidato_votos = int(candidato_votos_str) if candidato_votos_str else 0

            return {
                "partido": partido,
                "numero_lista": numero_lista,
                "votos_partido": votos_partido,
                "confidence_partido": ConfidenceScore(confidence_partido),
                "candidato_numero": candidato_numero,
                "candidato_nombre": candidato_nombre,
                "candidato_votos": candidato_votos,
                "confidence_candidato": ConfidenceScore(confidence_candidato)
            }

        except Exception as e:
            logger.error("row_extraction_failed", error=str(e))
            return None
