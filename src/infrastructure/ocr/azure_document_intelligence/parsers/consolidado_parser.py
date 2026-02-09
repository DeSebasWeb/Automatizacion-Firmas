from typing import List, Dict
import structlog
from .parsing_utils import ParsingUtils

logger = structlog.get_logger(__name__)


class ConsolidadoVotosParser:

    @staticmethod
    def parse_consolidado_votos(consolidado_field: dict) -> List[dict]:
        if not consolidado_field:
            return []

        field_type = consolidado_field.get("type", "")

        if field_type == "array":
            return ConsolidadoVotosParser._parse_array_format(consolidado_field)
        elif field_type == "object":
            return ConsolidadoVotosParser._parse_object_format(consolidado_field)
        else:
            logger.warning("unknown_consolidado_format", field_type=field_type)
            return []

    @staticmethod
    def _parse_array_format(consolidado_field: dict) -> List[dict]:
        value_array = consolidado_field.get("valueArray", [])
        if not value_array:
            return []

        resultado = []

        for item in value_array:
            value_obj = item.get("valueObject", {})
            if not value_obj:
                continue

            column1 = value_obj.get("COLUMN1", {})
            column2 = value_obj.get("COLUMN2", {})
            column3 = value_obj.get("COLUMN3", {})
            column4 = value_obj.get("COLUMN4", {})

            tipo = column1.get("valueString", "")
            if not tipo:
                continue

            votos = "---"
            for col in [column4, column3, column2]:
                val = col.get("valueString", "")
                if val and val != "--":
                    votos = ParsingUtils.parse_votos_preserve_format(val)
                    break

            resultado.append({
                "tipo": tipo,
                "votos": votos
            })

        return resultado

    @staticmethod
    def _parse_object_format(consolidado_field: dict) -> List[dict]:
        value_obj = consolidado_field.get("valueObject", {})
        if not value_obj:
            return []

        column1_data = value_obj.get("COLUMN1", {})
        column2_data = value_obj.get("COLUMN2", {})
        column3_data = value_obj.get("COLUMN3", {})
        column4_data = value_obj.get("COLUMN4", {})

        column1_rows = column1_data.get("valueObject", {})
        column2_rows = column2_data.get("valueObject", {})
        column3_rows = column3_data.get("valueObject", {})
        column4_rows = column4_data.get("valueObject", {})

        resultado = []

        row_keys = list(column1_rows.keys())

        for row_key in row_keys:
            tipo = column1_rows.get(row_key, {}).get("valueString", "")

            votos = "---"
            for col_rows in [column4_rows, column3_rows, column2_rows]:
                val = col_rows.get(row_key, {}).get("valueString", "")
                if val and val != "--":
                    votos = ParsingUtils.parse_votos_preserve_format(val)
                    break

            if tipo:
                resultado.append({
                    "tipo": tipo,
                    "votos": votos
                })

        return resultado
