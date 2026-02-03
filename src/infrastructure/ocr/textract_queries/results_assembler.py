from typing import Dict, List
import structlog

logger = structlog.get_logger(__name__)


class ResultsAssembler:

    def assemble(self, structure: Dict, query_results: Dict) -> Dict:
        e14 = {
            "e14": {
                "pagina": self._get_query_answer(query_results, "pagina"),
                "divipol": self._assemble_divipol(query_results),
                "TotalSufragantesE14": self._get_query_answer(query_results, "total_sufragantes"),
                "TotalVotosEnUrna": self._get_query_answer(query_results, "total_votos_urna"),
                "TotalIncinerados": self._get_query_answer(query_results, "total_incinerados", "***"),
                "Partido": self._assemble_partidos(structure, query_results)
            }
        }

        logger.info("results_assembled",
                   num_partidos=len(e14["e14"]["Partido"]))

        return e14

    def _assemble_divipol(self, query_results: Dict) -> Dict:
        return {
            "CodDep": self._get_query_answer(query_results, "cod_dep"),
            "CodMun": self._get_query_answer(query_results, "cod_mun"),
            "zona": self._get_query_answer(query_results, "zona"),
            "Puesto": self._get_query_answer(query_results, "puesto", ""),
            "Mesa": self._get_query_answer(query_results, "mesa")
        }

    def _assemble_partidos(self, structure: Dict, query_results: Dict) -> List[Dict]:
        partidos = []

        for idx, partido_structure in enumerate(structure['partidos'], start=1):
            partido = {
                "numPartido": partido_structure['codigo'],
                "nombrePartido": self._get_query_answer(
                    query_results, f"partido_{idx}_nombre"
                ),
                "tipoDeVoto": self._normalize_tipo_voto(
                    self._get_query_answer(query_results, f"partido_{idx}_tipo_lista")
                ),
                "id": "0",
                "votosSoloPorLaAgrupacionPolitica": self._get_query_answer(
                    query_results, f"partido_{idx}_votos_agrupacion"
                ),
                "candidatos": self._assemble_candidatos(partido_structure),
                "TotalVotosAgrupacion+VotosCandidatos": partido_structure.get('total', ''),
                "necesita_auditoria": False
            }

            partido['necesita_auditoria'] = self._needs_audit(partido)

            partidos.append(partido)

        return partidos

    def _assemble_candidatos(self, partido_structure: Dict) -> List[Dict]:
        if not partido_structure.get('tiene_candidatos'):
            return []

        candidatos = []
        for cand in partido_structure.get('candidatos', []):
            candidatos.append({
                "idcandidato": cand['id'],
                "votos": self._normalize_votos(cand['votos']),
                "necesita_auditoria": not cand['votos'].isdigit()
            })

        return candidatos

    def _get_query_answer(self, results: Dict, alias: str, default: str = "") -> str:
        return results.get(alias, {}).get('answer', default)

    def _normalize_tipo_voto(self, tipo: str) -> str:
        if 'CON VOTO PREFERENTE' in tipo.upper():
            return 'ListaConVotoPreferente'
        elif 'SIN VOTO PREFERENTE' in tipo.upper():
            return 'ListaSinVotoPreferente'
        return ''

    def _normalize_votos(self, votos: str) -> str:
        if votos in ['-', '/', '\\', '*', '#']:
            return '0'
        return votos

    def _needs_audit(self, partido: Dict) -> bool:
        if not partido['nombrePartido']:
            return True
        if not partido['votosSoloPorLaAgrupacionPolitica'].isdigit():
            return True
        return False
