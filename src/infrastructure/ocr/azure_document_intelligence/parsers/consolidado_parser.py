from typing import List, Dict
import structlog
from .parsing_utils import ParsingUtils

logger = structlog.get_logger(__name__)


class ConsolidadoVotosParser:

    @staticmethod
    def parse_consolidado_votos(consolidado_field: dict) -> List[dict]:
        if not consolidado_field:
            return []

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
