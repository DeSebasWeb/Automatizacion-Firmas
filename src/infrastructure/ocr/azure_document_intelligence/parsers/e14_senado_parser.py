from typing import Dict, List, Optional
import re
import structlog
from collections import defaultdict

from .parsing_utils import ParsingUtils
from .partido_parser import PartidoParser
from .consolidado_parser import ConsolidadoVotosParser

logger = structlog.get_logger(__name__)


class E14SenadoParser:

    def parse(self, fields: dict) -> dict:
        logger.info("e14_senado_parser_started", total_fields=len(fields))

        grouped = self._group_fields_by_page(fields)
        logger.info("fields_grouped_by_page", page_count=len(grouped))

        metadata = self._parse_metadata_page1(grouped.get(1, {}), fields)

        output = {"e14": metadata}

        for page_num in sorted(grouped.keys()):
            page_data = grouped[page_num]

            partidos = self._parse_partidos_in_page(page_data, page_num, fields)

            consolidado = self._parse_consolidado_in_page(page_data)

            if page_num == 1:
                output["e14"]["Partido"] = partidos
                if consolidado:
                    output["e14"]["ConsolidadoVotos"] = consolidado
            else:
                output["e14"][f"pagina{page_num}"] = ParsingUtils.format_page_number(page_num)

                divipol_field_name = f"DivipolPag{page_num}"
                divipol_field = fields.get(divipol_field_name)
                if divipol_field:
                    divipol_str = divipol_field.get("valueString", "")
                    output["e14"][f"divipol{page_num}"] = ParsingUtils.parse_divipol(divipol_str)

                output["e14"][f"Partido{page_num}"] = partidos
                if consolidado:
                    output["e14"][f"ConsolidadoVotos{page_num}"] = consolidado

        logger.info("e14_senado_parser_completed")
        return output

    def _group_fields_by_page(self, fields: dict) -> Dict[int, dict]:
        grouped = defaultdict(lambda: {
            "metadata": [],
            "partidos_info": [],
            "partidos_tabla": [],
            "totales": [],
            "consolidado": []
        })

        for field_name, field_value in fields.items():
            page_num = ParsingUtils.extract_page_number(field_name)

            if not page_num:
                continue

            if ParsingUtils.is_partido_field(field_name):
                partido_num = ParsingUtils.extract_partido_number(field_name)
                grouped[page_num]["partidos_info"].append({
                    "name": field_name,
                    "value": field_value,
                    "partido_num": partido_num
                })

            elif ParsingUtils.is_table_field(field_name):
                if "PartidoHoja" in field_name or re.match(r'^Partido\d+Pag', field_name):
                    grouped[page_num]["partidos_tabla"].append({
                        "name": field_name,
                        "value": field_value
                    })
                elif ParsingUtils.is_consolidado_field(field_name):
                    grouped[page_num]["consolidado"].append({
                        "name": field_name,
                        "value": field_value
                    })

            elif ParsingUtils.is_total_field(field_name):
                partido_num = ParsingUtils.extract_partido_number(field_name)
                grouped[page_num]["totales"].append({
                    "name": field_name,
                    "value": field_value,
                    "partido_num": partido_num
                })

            elif field_name.startswith("Pagina") or field_name == "pagina2":
                grouped[page_num]["metadata"].append({
                    "type": "pagina",
                    "value": field_value
                })

            elif "Divipol" in field_name:
                grouped[page_num]["metadata"].append({
                    "type": "divipol",
                    "value": field_value
                })

        return dict(grouped)

    def _parse_partidos_in_page(self, page_data: dict, page_num: int, all_fields: dict) -> List[dict]:
        partidos_result = []

        partidos_por_numero = {}

        for partido_info in page_data["partidos_info"]:
            num = partido_info["partido_num"]
            if num not in partidos_por_numero:
                partidos_por_numero[num] = {
                    "info": None,
                    "tabla": None,
                    "total": None
                }
            partidos_por_numero[num]["info"] = partido_info

        tabla_index = 0
        for num in sorted(partidos_por_numero.keys()):
            if partidos_por_numero[num]["info"]:
                info_value = partidos_por_numero[num]["info"]["value"]["valueString"]
                if "CON VOTO PREFERENTE" in info_value:
                    if tabla_index < len(page_data["partidos_tabla"]):
                        partidos_por_numero[num]["tabla"] = page_data["partidos_tabla"][tabla_index]
                        tabla_index += 1

        for total in page_data["totales"]:
            num = total["partido_num"]
            if num in partidos_por_numero:
                partidos_por_numero[num]["total"] = total
            elif num is None and len(partidos_por_numero) == 1:
                unico_partido_num = list(partidos_por_numero.keys())[0]
                partidos_por_numero[unico_partido_num]["total"] = total

        for num in sorted(partidos_por_numero.keys()):
            partido_data = partidos_por_numero[num]

            if not partido_data["info"]:
                continue

            partido = PartidoParser.parse_tipo_voto_partido(
                partido_data["info"]["value"]["valueString"]
            )

            if partido_data["tabla"]:
                tabla_obj = partido_data["tabla"]["value"].get("valueObject", {})
                partido["candidatos"] = PartidoParser.parse_tabla_candidatos(tabla_obj)
            else:
                partido["candidatos"] = []

            if partido_data["total"]:
                total_str = partido_data["total"]["value"]["valueString"]
                total_parsed = ParsingUtils.extract_total_from_string(total_str)
                partido["TotalVotosAgrupacion+VotosCandidatos"] = total_parsed
            else:
                partido["TotalVotosAgrupacion+VotosCandidatos"] = "---"

            partido = self._filter_partido_fields(partido)
            partidos_result.append(partido)

        return partidos_result

    def _filter_partido_fields(self, partido: dict) -> dict:
        if partido.get("tipoDeVoto") == "ListaSinVotoPreferente":
            return {k: v for k, v in partido.items()
                    if k != "TotalVotosAgrupacion+VotosCandidatos"}
        return partido

    def _parse_metadata_page1(self, page_data: dict, all_fields: dict) -> dict:
        metadata = {}

        pagina_field = all_fields.get("Pagina")
        if pagina_field:
            pagina_str = pagina_field.get("valueString", "")
            metadata["pagina"] = pagina_str.replace("Pag: ", "")

        divipol_field = all_fields.get("DivipolPag1")
        if divipol_field:
            metadata["divipol"] = ParsingUtils.parse_divipol(divipol_field.get("valueString", ""))

        total_suf = all_fields.get("TotalSufragantes")
        if total_suf:
            total_str = total_suf.get("valueString", "")
            num = re.search(r'(\d+)$', total_str)
            metadata["TotalSufragantesE14"] = num.group(1) if num else "---"

        total_urna = all_fields.get("TotalVotosUrna")
        if total_urna:
            total_str = total_urna.get("valueString", "")
            num = re.search(r'(-?\d+)', total_str)
            metadata["TotalVotosEnUrna"] = num.group(1) if num else "---"

        total_inc = all_fields.get("TotalVotosIncinerados")
        if total_inc:
            total_str = total_inc.get("valueString", "")
            metadata["TotalIncinerados"] = ParsingUtils.parse_votos_preserve_format(total_str)

        return metadata

    def _parse_consolidado_in_page(self, page_data: dict) -> List[dict]:
        if not page_data["consolidado"]:
            return []

        consolidado_field = page_data["consolidado"][0]
        consolidado_value = consolidado_field["value"]

        return ConsolidadoVotosParser.parse_consolidado_votos(consolidado_value)
