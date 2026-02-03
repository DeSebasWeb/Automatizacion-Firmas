import pytest
from src.infrastructure.ocr.textract.parsers.partido_parser import PartidoParser


class TestPartidoParserRealOCR:

    def test_ejemplo_usuario_desordenado(self):
        ocr_lines = """CIRCUNSCRIPCIÓN TERRITORIAL
LISTA CON VOTO PREFERENTE
PARTIDO POLÍTICO DIGNIDAD
DIGNIDAD
0017
VOTOS SOLO POR LA AGRUPACIÓN POLÍTICA
0
-
-
-
1
1
104
101
103
-
1
-
-
-
-
-
- - 2
TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS
LISTA CON VOTO PREFERENTE
PARTIDO CONSERVADOR COLOMBIANO
0002
VOTOS SOLO POR LA AGRUPACIÓN POLÍTICA
0
-
-
-
6
2
101
103
-
-
-
-
9
104
102
-
-
-
-
-
- 17
TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS
LISTA CON VOTO PREFERENTE
PARTIDO LIBERAL COLOMBIANO
0001
1
VOTOS SOLO POR LA AGRUPACIÓN POLÍTICA
O
-
-
1
12
103
101
-
-
-
17
8
104
102
-
I
-
- 39
TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS
LISTA CON VOTO PREFERENTE
-
Lived
COALICIÓN MIRA COLOMBIA JUSTA LIBRES.
0222
MIRA
VOTOS SOLO POR LA AGRUPACIÓN POLÍTICA
0
-
-
-
4
4
102
103
101
-
-
-
-
-
-
-
- - 8
TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS
LISTA CON VOTO PREFERENTE
0
PARTIDO DE LA UNIÓN POR LA GENTE "PARTIDO DE LA U"
0008
VOTOS SOLO POR LA AGRUPACIÓN POLÍTICA
-
0
-
-
1
1
103
101
-
-
-
-
6
102
104
-
-
-
-
-
-14 -
TOTAL = VOTOS AGRUPACIÓN + votos CANDIDATOS
LISTA SIN VOTO PREFERENTE
MOVIMIENTO POLÍTICO COLOMBIA HUMANA
0301
1
- 26
VOTOS POR LA AGRUPACIÓN POLÍTICA
0""".split('\n')

        parser = PartidoParser()
        result = parser.parse(ocr_lines)

        partidos = result["Partido"]

        assert len(partidos) >= 5, f"Esperaba al menos 5 partidos, encontró {len(partidos)}"

        partido_0017 = next((p for p in partidos if p["numPartido"] == "0017"), None)
        assert partido_0017 is not None, "No se encontró partido 0017 (DIGNIDAD)"
        assert "DIGNIDAD" in partido_0017["nombrePartido"]
        assert partido_0017["tipoDeVoto"] == "ListaConVotoPreferente"

        partido_0002 = next((p for p in partidos if p["numPartido"] == "0002"), None)
        assert partido_0002 is not None, "No se encontró partido 0002 (CONSERVADOR)"
        assert "CONSERVADOR" in partido_0002["nombrePartido"]

        partido_0001 = next((p for p in partidos if p["numPartido"] == "0001"), None)
        assert partido_0001 is not None, "No se encontró partido 0001 (LIBERAL)"
        assert "LIBERAL" in partido_0001["nombrePartido"]

        partido_0222 = next((p for p in partidos if p["numPartido"] == "0222"), None)
        assert partido_0222 is not None, "No se encontró partido 0222 (MIRA)"
        assert "MIRA" in partido_0222["nombrePartido"] or "COALICI" in partido_0222["nombrePartido"]

        partido_0008 = next((p for p in partidos if p["numPartido"] == "0008"), None)
        assert partido_0008 is not None, "No se encontró partido 0008 (PARTIDO DE LA U)"

        partido_0301 = next((p for p in partidos if p["numPartido"] == "0301"), None)
        assert partido_0301 is not None, "No se encontró partido 0301 (COLOMBIA HUMANA)"
        assert partido_0301["tipoDeVoto"] == "ListaSinVotoPreferente"
        assert len(partido_0301["candidatos"]) == 0

    def test_partido_0017_candidatos(self):
        ocr_lines = """LISTA CON VOTO PREFERENTE
PARTIDO POLÍTICO DIGNIDAD
DIGNIDAD
0017
VOTOS SOLO POR LA AGRUPACIÓN POLÍTICA
0
-
-
-
1
1
104
101
103
-
1
-
-
-
-
-
- - 2
TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS""".split('\n')

        parser = PartidoParser()
        result = parser.parse(ocr_lines)

        partidos = result["Partido"]
        assert len(partidos) == 1

        partido = partidos[0]
        assert partido["numPartido"] == "0017"
        assert partido["votosSoloPorLaAgrupacionPolitica"] in ["0", "1"]

        candidatos = partido["candidatos"]
        assert len(candidatos) > 0, "Debería haber detectado candidatos"

        ids_encontrados = {c["idcandidato"] for c in candidatos}
        assert "101" in ids_encontrados or "103" in ids_encontrados or "104" in ids_encontrados
