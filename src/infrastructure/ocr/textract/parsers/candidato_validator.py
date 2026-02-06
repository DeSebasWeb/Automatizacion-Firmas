from typing import List, Dict, Tuple
import structlog

logger = structlog.get_logger(__name__)


class CandidatoValidator:

    @staticmethod
    def validate_candidatos(candidatos: List[Dict], tipo_voto: str) -> Tuple[List[Dict], List[str]]:
        errores = []

        if tipo_voto == "ListaSinVotoPreferente":
            if len(candidatos) > 0:
                errores.append(f"Lista SIN voto tiene {len(candidatos)} candidatos")
        else:
            if len(candidatos) > 20:
                errores.append(f"Lista CON voto tiene {len(candidatos)} candidatos (max 20)")

        ids_vistos = set()
        for cand in candidatos:
            id_cand = cand["idcandidato"]
            if id_cand in ids_vistos:
                errores.append(f"ID duplicado: {id_cand}")
            ids_vistos.add(id_cand)

        for cand in candidatos:
            votos = cand["votos"]
            if votos.isdigit() and int(votos) > 9999:
                errores.append(f"Candidato {cand['idcandidato']} con votos sospechosos: {votos}")

        ids_sorted = sorted([int(c["idcandidato"]) for c in candidatos])
        gaps = []
        for i in range(len(ids_sorted) - 1):
            diff = ids_sorted[i+1] - ids_sorted[i]
            if diff > 5:
                gaps.append((ids_sorted[i], ids_sorted[i+1]))

        if gaps:
            logger.warning("gaps_in_candidato_ids", gaps=gaps)

        return candidatos, errores
