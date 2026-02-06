from typing import Optional
import structlog

from ..models.tipo_lista import TipoLista

logger = structlog.get_logger(__name__)


class TipoVotoExtractor:
    @staticmethod
    def extract(azure_response: dict) -> Optional[TipoLista]:
        try:
            documents = azure_response.get("documents", [])
            if not documents:
                logger.warning("no_documents_in_response")
                return None

            doc = documents[0]
            fields = doc.get("fields", {})

            tipo_voto_field = fields.get("tipo_voto_partido")
            if not tipo_voto_field:
                logger.warning("tipo_voto_partido_field_not_found")
                return None

            value = tipo_voto_field.get("content", "").strip()
            if not value:
                logger.warning("tipo_voto_partido_empty")
                return None

            return TipoLista.from_string(value)

        except ValueError as e:
            logger.error("invalid_tipo_lista", error=str(e))
            return None
        except Exception as e:
            logger.error("tipo_voto_extraction_failed", error=str(e))
            return None
