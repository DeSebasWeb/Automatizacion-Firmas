import pytest
from src.infrastructure.ocr.azure_document_intelligence.parsers.partido_parser import PartidoParser


class TestPartidoParser:

    def test_parse_tipo_voto_partido_con_voto_preferente(self):
        value_string = "LISTA CON VOTO PREFERENTE\n0255\nCOALICIÓN ALIANZA VERDE Y CENTRO ESPERANZA\n0"

        result = PartidoParser.parse_tipo_voto_partido(value_string)

        assert result["numPartido"] == "0255"
        assert result["nombrePartido"] == "COALICIÓN ALIANZA VERDE Y CENTRO ESPERANZA"
        assert result["tipoDeVoto"] == "ListaConVotoPreferente"
        assert result["id"] == "0"
        assert result["votosSoloPorLaAgrupacionPolitica"] == "0"

    def test_parse_tipo_voto_partido_sin_voto_preferente(self):
        value_string = "LISTA SIN VOTO PREFERENTE\n0013\nPARTIDO COMUNES\n0"

        result = PartidoParser.parse_tipo_voto_partido(value_string)

        assert result["numPartido"] == "0013"
        assert result["nombrePartido"] == "PARTIDO COMUNES"
        assert result["tipoDeVoto"] == "ListaSinVotoPreferente"
        assert result["id"] == "0"

    def test_parse_tipo_voto_partido_with_votos(self):
        value_string = "LISTA CON VOTO PREFERENTE\n0002\nPARTIDO CONSERVADOR COLOMBIANO\n0\n-- 4-"

        result = PartidoParser.parse_tipo_voto_partido(value_string)

        assert result["numPartido"] == "0002"
        assert result["nombrePartido"] == "PARTIDO CONSERVADOR COLOMBIANO"
        assert result["votosSoloPorLaAgrupacionPolitica"] == "4"

    def test_parse_tabla_candidatos_empty(self):
        result = PartidoParser.parse_tabla_candidatos({})
        assert result == []

    def test_parse_tabla_candidatos_basic(self):
        tabla_obj = {
            "ID Candidato1": {
                "type": "object",
                "valueObject": {
                    "ROW1": {
                        "type": "string",
                        "valueString": "1"
                    },
                    "ROW2": {
                        "type": "string",
                        "valueString": "2"
                    }
                }
            },
            "casilla 1": {
                "type": "object",
                "valueObject": {
                    "ROW1": {
                        "type": "string",
                        "valueString": "5"
                    },
                    "ROW2": {
                        "type": "string",
                        "valueString": ""
                    }
                }
            },
            "casilla 2": {
                "type": "object",
                "valueObject": {
                    "ROW1": {
                        "type": "string",
                        "valueString": "3"
                    },
                    "ROW2": {
                        "type": "string",
                        "valueString": "2"
                    }
                }
            },
            "casilla 3": {
                "type": "object",
                "valueObject": {
                    "ROW1": {
                        "type": "string",
                        "valueString": "2"
                    },
                    "ROW2": {
                        "type": "string",
                        "valueString": "1"
                    }
                }
            }
        }

        result = PartidoParser.parse_tabla_candidatos(tabla_obj)

        assert len(result) == 2
        assert result[0]["idcandidato"] == "1"
        assert result[0]["votos"] == "10"
        assert result[1]["idcandidato"] == "2"
        assert result[1]["votos"] == "3"

    def test_parse_tabla_candidatos_with_dashes(self):
        tabla_obj = {
            "IDCandidato1": {
                "type": "object",
                "valueObject": {
                    "ROW1": {
                        "type": "string",
                        "valueString": "34"
                    }
                }
            },
            "Casilla1": {
                "type": "object",
                "valueObject": {
                    "ROW1": {
                        "type": "string",
                        "valueString": ""
                    }
                }
            },
            "Casilla2": {
                "type": "object",
                "valueObject": {
                    "ROW1": {
                        "type": "string",
                        "valueString": "--"
                    }
                }
            },
            "Casilla3": {
                "type": "object",
                "valueObject": {
                    "ROW1": {
                        "type": "string",
                        "valueString": "12"
                    }
                }
            }
        }

        result = PartidoParser.parse_tabla_candidatos(tabla_obj)

        assert len(result) == 1
        assert result[0]["idcandidato"] == "34"
        assert result[0]["votos"] == "12"
