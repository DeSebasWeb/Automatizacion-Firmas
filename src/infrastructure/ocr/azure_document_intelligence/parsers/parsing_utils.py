from typing import Optional
import re
import structlog

logger = structlog.get_logger(__name__)


class ParsingUtils:

    @staticmethod
    def parse_votos_preserve_format(value: str) -> str:
        if not value or not value.strip():
            return "---"

        clean = value.strip()

        if re.match(r'^[\-\*\/]+$', clean):
            return clean

        digits = ''.join(re.findall(r'\d', clean))

        if digits:
            return digits

        return "---"

    @staticmethod
    def extract_page_number(field_name: str) -> Optional[int]:
        match = re.search(r'Pag(\d+)', field_name)
        if match:
            return int(match.group(1))

        match = re.search(r'Pagina(\d+)', field_name)
        if match:
            return int(match.group(1))

        match = re.search(r'PartidoHoja(\d+)', field_name)
        if match:
            return int(match.group(1))

        match = re.search(r'Partido(\d+)Pag', field_name)
        if match:
            partido_num = int(match.group(1))
            pag_match = re.search(r'Pag(?:ina)?(\d+)', field_name)
            if pag_match:
                return int(pag_match.group(1))

        return None

    @staticmethod
    def extract_partido_number(field_name: str) -> Optional[int]:
        match = re.search(r'TipoDeVotoPartido(\d+)', field_name)
        if match:
            return int(match.group(1))

        match = re.search(r'Partido(\d+)', field_name)
        if match:
            return int(match.group(1))

        match = re.search(r'Prt(\d+)', field_name)
        if match:
            return int(match.group(1))

        match = re.search(r'Ptd(\d+)', field_name)
        if match:
            return int(match.group(1))

        return None

    @staticmethod
    def is_table_field(field_name: str) -> bool:
        patterns = [
            r'^PartidoHoja\d+$',
            r'^Partido\d+Pag(?:ina)?\d+$',
            r'^ConsolidadoVotos.*Pag\d+$'
        ]
        return any(re.match(pattern, field_name) for pattern in patterns)

    @staticmethod
    def is_partido_field(field_name: str) -> bool:
        return "TipoDeVotoPartido" in field_name

    @staticmethod
    def is_total_field(field_name: str) -> bool:
        return "TotalVotosAgrupacion" in field_name

    @staticmethod
    def is_consolidado_field(field_name: str) -> bool:
        return "ConsolidadoVotos" in field_name

    @staticmethod
    def parse_divipol(value_string: str) -> dict:
        pattern = r'DEPARTAMENTO:\s*(\d+).*?MUNICIPIO:\s*(\d+).*?ZONA:\s*(\d+).*?PUESTO:\s*(\d+).*?MESA:\s*(\d+)'
        match = re.search(pattern, value_string, re.DOTALL)

        if match:
            return {
                "CodDep": match.group(1),
                "CodMun": match.group(2),
                "zona": match.group(3),
                "Puesto": match.group(4),
                "Mesa": match.group(5)
            }

        return {}

    @staticmethod
    def format_page_number(page_num: int, total_pages: int = 11) -> str:
        return f"{page_num:02d} de {total_pages:02d}"

    @staticmethod
    def extract_total_from_string(total_string: str) -> str:
        match = re.search(r'CANDIDATOS\s+(.+)', total_string)
        if match:
            return ParsingUtils.parse_votos_preserve_format(match.group(1))

        return "---"
