import pytest
from src.infrastructure.ocr.azure_document_intelligence.parsers.e14_senado_parser import E14SenadoParser


class TestE14SenadoParser:

    def test_filter_partido_fields_sin_voto_preferente_elimina_total(self):
        parser = E14SenadoParser()

        partido = {
            "numPartido": "0013",
            "nombrePartido": "PARTIDO COMUNES",
            "tipoDeVoto": "ListaSinVotoPreferente",
            "id": "0",
            "votosSoloPorLaAgrupacionPolitica": "1",
            "candidatos": [],
            "TotalVotosAgrupacion+VotosCandidatos": "1"
        }

        result = parser._filter_partido_fields(partido)

        assert "TotalVotosAgrupacion+VotosCandidatos" not in result
        assert result["tipoDeVoto"] == "ListaSinVotoPreferente"
        assert result["numPartido"] == "0013"
        assert result["votosSoloPorLaAgrupacionPolitica"] == "1"
        assert result["candidatos"] == []

    def test_filter_partido_fields_sin_voto_preferente_con_total_guiones(self):
        parser = E14SenadoParser()

        partido = {
            "numPartido": "0013",
            "nombrePartido": "PARTIDO COMUNES",
            "tipoDeVoto": "ListaSinVotoPreferente",
            "id": "0",
            "votosSoloPorLaAgrupacionPolitica": "0",
            "candidatos": [],
            "TotalVotosAgrupacion+VotosCandidatos": "---"
        }

        result = parser._filter_partido_fields(partido)

        assert "TotalVotosAgrupacion+VotosCandidatos" not in result

    def test_filter_partido_fields_con_voto_preferente_mantiene_total(self):
        parser = E14SenadoParser()

        partido = {
            "numPartido": "0255",
            "nombrePartido": "COALICIÓN ALIANZA VERDE Y CENTRO ESPERANZA",
            "tipoDeVoto": "ListaConVotoPreferente",
            "id": "0",
            "votosSoloPorLaAgrupacionPolitica": "1",
            "candidatos": [
                {"idcandidato": "1", "votos": "5"},
                {"idcandidato": "2", "votos": "6"}
            ],
            "TotalVotosAgrupacion+VotosCandidatos": "12"
        }

        result = parser._filter_partido_fields(partido)

        assert "TotalVotosAgrupacion+VotosCandidatos" in result
        assert result["TotalVotosAgrupacion+VotosCandidatos"] == "12"
        assert result["tipoDeVoto"] == "ListaConVotoPreferente"
        assert len(result["candidatos"]) == 2

    def test_filter_partido_fields_con_voto_preferente_mantiene_total_guiones(self):
        parser = E14SenadoParser()

        partido = {
            "numPartido": "0002",
            "nombrePartido": "PARTIDO CONSERVADOR",
            "tipoDeVoto": "ListaConVotoPreferente",
            "id": "0",
            "votosSoloPorLaAgrupacionPolitica": "0",
            "candidatos": [],
            "TotalVotosAgrupacion+VotosCandidatos": "---"
        }

        result = parser._filter_partido_fields(partido)

        assert "TotalVotosAgrupacion+VotosCandidatos" in result
        assert result["TotalVotosAgrupacion+VotosCandidatos"] == "---"

    def test_asignar_total_sin_numero_a_unico_partido_en_pagina(self):
        parser = E14SenadoParser()

        fields = {
            "TipoDeVotoPartido1Pag2": {
                "valueString": "LISTA CON VOTO PREFERENTE\n0255\nCOALICIÓN ALIANZA VERDE Y CENTRO ESPERANZA\n0\n1"
            },
            "TotalVotosAgrupacion+VotosCandidatosPag2": {
                "valueString": "TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS -- 7"
            },
            "Partido1Pag2": {
                "valueObject": {}
            }
        }

        result = parser.parse(fields)

        partidos_pag2 = result["e14"].get("Partido2", [])
        assert len(partidos_pag2) == 1

        partido = partidos_pag2[0]
        assert partido["numPartido"] == "0255"
        assert partido["TotalVotosAgrupacion+VotosCandidatos"] == "7"

    def test_no_asignar_total_sin_numero_cuando_multiple_partidos(self):
        parser = E14SenadoParser()

        fields = {
            "TipoDeVotoPartido1Pag10": {
                "valueString": "LISTA CON VOTO PREFERENTE\n0001\nPARTIDO UNO\n0"
            },
            "TipoDeVotoPartido2Pag10": {
                "valueString": "LISTA CON VOTO PREFERENTE\n0002\nPARTIDO DOS\n0"
            },
            "TotalVotosAgrupacion+VotosCandidatosPag10": {
                "valueString": "TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS -- 10"
            }
        }

        result = parser.parse(fields)

        partidos_pag10 = result["e14"].get("Partido10", [])
        assert len(partidos_pag10) == 2

        for partido in partidos_pag10:
            assert partido["TotalVotosAgrupacion+VotosCandidatos"] == "---"
