from typing import Optional
import structlog

from src.domain.ports.azure_di_port import AzureDIPort
from src.infrastructure.ocr.azure_document_intelligence.models import E14Document, TipoLista
from src.infrastructure.ocr.azure_document_intelligence.field_extractors.tipo_voto_extractor_v2 import TipoVotoExtractorV2
from src.infrastructure.ocr.azure_document_intelligence.field_extractors.votos_extractor_v2 import VotosExtractorV2
from src.infrastructure.ocr.azure_document_intelligence.field_extractors.divipol_extractor_v2 import DivipolExtractorV2
from src.infrastructure.ocr.azure_document_intelligence.field_extractors.tabla_candidatos_extractor_v2 import TablaCandidatosExtractorV2

logger = structlog.get_logger(__name__)


class ProcessE14AzureDIUseCase:
    def __init__(self, azure_di_adapter: AzureDIPort):
        self.adapter = azure_di_adapter

    def execute(self, image_bytes: bytes) -> Optional[E14Document]:
        logger.info("process_e14_started", size_bytes=len(image_bytes))

        if not self.adapter.is_available():
            logger.error("adapter_not_available")
            return None

        azure_response = self.adapter.analyze_e14_document(image_bytes)
        if not azure_response:
            logger.error("azure_analysis_failed")
            return None

        return self._build_e14_document(azure_response)

    def _build_e14_document(self, azure_response: dict) -> Optional[E14Document]:
        try:
            tipo_lista = TipoVotoExtractorV2.extract(azure_response)
            if not tipo_lista:
                logger.error("tipo_lista_extraction_failed")
                return None

            divipol = DivipolExtractorV2.extract(azure_response)
            votos_data = VotosExtractorV2.extract(azure_response)
            partidos = TablaCandidatosExtractorV2.extract(azure_response)

            codigo_departamento = None
            if tipo_lista == TipoLista.CAMARA:
                codigo_departamento = divipol.get("CodDep", "")

            votos_nulos = votos_data.get("votos_nulos", (0, None))[0]
            votos_no_marcados = votos_data.get("votos_no_marcados", (0, None))[0]
            votos_blanco = votos_data.get("votos_blanco", (0, None))[0]
            total_votos_validos = votos_data.get("total_votos_validos", (0, None))[0]

            from src.domain.value_objects.confidence_score import ConfidenceScore

            confidences = []
            for _, conf in votos_data.values():
                if conf:
                    if isinstance(conf, ConfidenceScore):
                        confidences.append(conf.value)
                    elif isinstance(conf, float):
                        confidences.append(conf)

            confidences.extend([p.confidence.value if isinstance(p.confidence, ConfidenceScore) else p.confidence for p in partidos])

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            document = E14Document(
                tipo_lista=tipo_lista,
                codigo_departamento=codigo_departamento,
                divipol=divipol,
                votos_nulos=votos_nulos,
                votos_no_marcados=votos_no_marcados,
                votos_blanco=votos_blanco,
                total_votos_validos=total_votos_validos,
                partidos=partidos,
                confidence_promedio=avg_confidence
            )

            logger.info("e14_document_built", tipo_lista=tipo_lista.value, partidos_count=len(partidos))
            return document

        except Exception as e:
            logger.error("e14_document_build_failed", error=str(e))
            return None
