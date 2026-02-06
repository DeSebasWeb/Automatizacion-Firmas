from typing import Dict
import structlog

logger = structlog.get_logger(__name__)


class DivipolExtractor:
    DIVIPOL_FIELDS = [
        "CodDep",
        "CodMun",
        "zona",
        "Puesto",
        "Mesa"
    ]

    @staticmethod
    def extract(azure_response: dict) -> Dict[str, str]:
        result = {field: "" for field in DivipolExtractor.DIVIPOL_FIELDS}

        try:
            documents = azure_response.get("documents", [])
            if not documents:
                logger.warning("no_documents_in_response")
                return result

            doc = documents[0]
            fields = doc.get("fields", {})

            for field_name in DivipolExtractor.DIVIPOL_FIELDS:
                field_data = fields.get(field_name)
                if not field_data:
                    logger.warning("divipol_field_not_found", field=field_name)
                    continue

                content = field_data.get("content", "").strip()
                if content:
                    result[field_name] = content
                else:
                    logger.warning("divipol_field_empty", field=field_name)

        except Exception as e:
            logger.error("divipol_extraction_failed", error=str(e))

        return result
