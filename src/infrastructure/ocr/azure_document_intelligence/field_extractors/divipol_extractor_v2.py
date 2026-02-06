from typing import Optional, Dict
import structlog
import re

logger = structlog.get_logger(__name__)


class DivipolExtractorV2:
    @staticmethod
    def extract(azure_response: dict) -> Dict[str, str]:
        try:
            documents = azure_response.get("documents", [])
            if not documents:
                logger.warning("no_documents_in_response")
                return {}

            doc = documents[0]
            fields = doc.get("fields", {})

            divipol_field = fields.get("DivipolPag1")
            if not divipol_field:
                logger.warning("DivipolPag1_field_not_found")
                return {}

            content = divipol_field.get("valueString", "").strip()
            if not content:
                logger.warning("divipol_empty")
                return {}

            result = {}

            dep_match = re.search(r"DEPARTAMENTO:\s*(\d+)", content)
            if dep_match:
                result["CodDep"] = dep_match.group(1)

            mun_match = re.search(r"MUNICIPIO:\s*(\d+)", content)
            if mun_match:
                result["CodMun"] = mun_match.group(1)

            zona_match = re.search(r"ZONA:\s*(\d+)", content)
            if zona_match:
                result["Zona"] = zona_match.group(1)

            puesto_match = re.search(r"PUESTO:\s*(\d+)", content)
            if puesto_match:
                result["Puesto"] = puesto_match.group(1)

            mesa_match = re.search(r"MESA:\s*(\d+)", content)
            if mesa_match:
                result["Mesa"] = mesa_match.group(1)

            logger.info("divipol_extracted", result=result)
            return result

        except Exception as e:
            logger.error("divipol_extraction_failed", error=str(e))
            return {}
