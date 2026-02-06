from typing import Optional
import structlog

from ..models.tipo_lista import TipoLista

logger = structlog.get_logger(__name__)


class TipoVotoExtractorV2:
    @staticmethod
    def extract(azure_response: dict) -> Optional[TipoLista]:
        try:
            documents = azure_response.get("documents", [])
            if not documents:
                logger.warning("no_documents_in_response")
                return None

            doc = documents[0]
            fields = doc.get("fields", {})

            tipo_documento_field = fields.get("TipoDeDocumento")
            if not tipo_documento_field:
                logger.warning("TipoDeDocumento_field_not_found")
                return None

            content = tipo_documento_field.get("valueString", "").strip()
            if not content:
                logger.warning("tipo_documento_empty")
                return None

            return TipoLista.from_string(content)

        except ValueError as e:
            logger.error("invalid_tipo_lista", error=str(e))
            return None
        except Exception as e:
            logger.error("tipo_voto_extraction_failed", error=str(e))
            return None
