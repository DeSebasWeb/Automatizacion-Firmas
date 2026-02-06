from typing import List, Dict, Optional
import re
import structlog
from .parsing_utils import ParsingUtils

logger = structlog.get_logger(__name__)


class PartidoParser:

    @staticmethod
    def parse_tipo_voto_partido(value_string: str) -> dict:
        lines = [l.strip() for l in value_string.split('\n') if l.strip()]

        tipo_raw = lines[0] if lines else ""
        tipo = "ListaConVotoPreferente" if "CON" in tipo_raw.upper() else "ListaSinVotoPreferente"

        codigo = None
        for line in lines:
            match = re.search(r'\b(\d{4})\b', line)
            if match:
                codigo = match.group(1)
                break

        nombres = [
            l for l in lines
            if l and
            not l.isdigit() and
            "LISTA" not in l.upper() and
            len(l) > 5
        ]
        nombre = max(nombres, key=len) if nombres else ""

        id_val = "0"

        votos = None
        for line in reversed(lines[-2:]):
            parsed = ParsingUtils.parse_votos_preserve_format(line)
            if parsed != "---":
                votos = parsed
                break

        return {
            "numPartido": codigo or "",
            "nombrePartido": nombre,
            "tipoDeVoto": tipo,
            "id": id_val,
            "votosSoloPorLaAgrupacionPolitica": votos or "---"
        }

    @staticmethod
    def parse_tabla_candidatos(tabla_obj: dict) -> List[dict]:
        if not tabla_obj:
            return []

        column_names = list(tabla_obj.keys())
        candidatos = []

        for i in range(0, len(column_names), 4):
            if i + 3 >= len(column_names):
                break

            id_col_data = tabla_obj.get(column_names[i], {})
            cas1_data = tabla_obj.get(column_names[i + 1], {})
            cas2_data = tabla_obj.get(column_names[i + 2], {})
            cas3_data = tabla_obj.get(column_names[i + 3], {})

            id_col = id_col_data.get("valueObject", {})
            cas1 = cas1_data.get("valueObject", {})
            cas2 = cas2_data.get("valueObject", {})
            cas3 = cas3_data.get("valueObject", {})

            for row_key in id_col.keys():
                id_cand = id_col.get(row_key, {}).get("valueString", "")

                v1 = cas1.get(row_key, {}).get("valueString", "")
                v2 = cas2.get(row_key, {}).get("valueString", "")
                v3 = cas3.get(row_key, {}).get("valueString", "")

                total = 0
                for v in [v1, v2, v3]:
                    parsed = ParsingUtils.parse_votos_preserve_format(v)
                    if parsed.isdigit():
                        total += int(parsed)

                candidatos.append({
                    "idcandidato": id_cand,
                    "votos": str(total)
                })

        return candidatos
