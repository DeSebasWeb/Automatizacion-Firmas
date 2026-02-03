from typing import Dict, List
import structlog

logger = structlog.get_logger(__name__)


class QueriesBuilder:

    def build_queries(self, structure: Dict) -> List[Dict]:
        queries = []

        queries.extend(self._build_metadata_queries())
        queries.extend(self._build_totales_queries())
        queries.extend(self._build_partido_queries(structure))

        logger.info("queries_constructed", total=len(queries))

        return queries

    def _build_metadata_queries(self) -> List[Dict]:
        return [
            {
                "Text": "What is the complete page number after Pag, including 'de'",
                "Alias": "pagina",
                "Pages": ["1"]
            },
            {
                "Text": "What is the 2-digit number after DEPARTAMENTO in the DIVIPOL section",
                "Alias": "cod_dep",
                "Pages": ["1"]
            },
            {
                "Text": "What is the 3-digit number after MUNICIPIO in the DIVIPOL section",
                "Alias": "cod_mun",
                "Pages": ["1"]
            },
            {
                "Text": "What is the number after Puesto in the DIVIPOL section",
                "Alias": "puesto",
                "Pages": ["1"]
            },
            {
                "Text": "What is the number after ZONA in the DIVIPOL section",
                "Alias": "zona",
                "Pages": ["1"]
            },
            {
                "Text": "What is the number after MESA in the DIVIPOL section",
                "Alias": "mesa",
                "Pages": ["1"]
            },
            {
                "Text": "Does the document say SENADO or CAMARA DE REPRESENTANTES",
                "Alias": "tipo_eleccion",
                "Pages": ["1"]
            }
        ]

    def _build_totales_queries(self) -> List[Dict]:
        return [
            {
                "Text": "What is the number in the TOTAL row for SUFRAGANTES column",
                "Alias": "total_sufragantes",
                "Pages": ["1"]
            },
            {
                "Text": "What is the number in the TOTAL row for VOTOS EN LA URNA column",
                "Alias": "total_votos_urna",
                "Pages": ["1"]
            },
            {
                "Text": "What is the number in the TOTAL row for VOTOS INCINERADOS column",
                "Alias": "total_incinerados",
                "Pages": ["1"]
            }
        ]

    def _build_partido_queries(self, structure: Dict) -> List[Dict]:
        queries = []

        partidos = structure.get('partidos', [])

        for idx, partido in enumerate(partidos, start=1):
            codigo = partido.get('codigo', '')

            queries.append({
                "Text": f"What is the complete full party name written in the row with code {codigo}, after the party logo",
                "Alias": f"partido_{idx}_nombre",
                "Pages": ["1"]
            })

            queries.append({
                "Text": f"In the row with party code {codigo}, does it say LISTA CON VOTO PREFERENTE or LISTA SIN VOTO PREFERENTE",
                "Alias": f"partido_{idx}_tipo_lista",
                "Pages": ["1"]
            })

            queries.append({
                "Text": f"In the row with party {codigo}, what is the number in the cell next to the arrow that says VOTOS SOLO POR LA AGRUPACION POLITICA",
                "Alias": f"partido_{idx}_votos_agrupacion",
                "Pages": ["1"]
            })

        return queries
