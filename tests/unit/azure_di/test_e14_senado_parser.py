import pytest
from src.infrastructure.ocr.azure_document_intelligence.parsers.e14_senado_parser import E14SenadoParser
from src.infrastructure.ocr.azure_document_intelligence.parsers.consolidado_parser import ConsolidadoVotosParser


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

    def test_parse_consolidado_formato_array(self):
        consolidado_field = {
            "type": "array",
            "valueArray": [
                {
                    "type": "object",
                    "valueObject": {
                        "COLUMN1": {
                            "type": "string",
                            "valueString": "VOTOS EN BLANCO"
                        },
                        "COLUMN2": {
                            "type": "string",
                            "valueString": "11"
                        },
                        "COLUMN3": {
                            "type": "string"
                        },
                        "COLUMN4": {
                            "type": "string"
                        }
                    }
                },
                {
                    "type": "object",
                    "valueObject": {
                        "COLUMN1": {
                            "type": "string",
                            "valueString": "VOTOS NULOS"
                        },
                        "COLUMN2": {
                            "type": "string",
                            "valueString": "18"
                        }
                    }
                },
                {
                    "type": "object",
                    "valueObject": {
                        "COLUMN1": {
                            "type": "string",
                            "valueString": "VOTOS NO MARCADOS"
                        },
                        "COLUMN4": {
                            "type": "string",
                            "valueString": "6"
                        }
                    }
                }
            ]
        }

        result = ConsolidadoVotosParser.parse_consolidado_votos(consolidado_field)

        assert len(result) == 3
        assert result[0]["tipo"] == "VOTOS EN BLANCO"
        assert result[0]["votos"] == "11"
        assert result[1]["tipo"] == "VOTOS NULOS"
        assert result[1]["votos"] == "18"
        assert result[2]["tipo"] == "VOTOS NO MARCADOS"
        assert result[2]["votos"] == "6"

    def test_parse_consolidado_formato_object(self):
        consolidado_field = {
            "type": "object",
            "valueObject": {
                "COLUMN1": {
                    "type": "object",
                    "valueObject": {
                        "ROW1": {
                            "type": "string",
                            "valueString": "VOTOS EN BLANCO"
                        },
                        "ROW2": {
                            "type": "string",
                            "valueString": "VOTOS NULOS."
                        },
                        "ROW3": {
                            "type": "string",
                            "valueString": "VOTOS NO MARCADOS"
                        }
                    }
                },
                "COLUMN2": {
                    "type": "object",
                    "valueObject": {}
                },
                "COLUMN3": {
                    "type": "object",
                    "valueObject": {}
                },
                "COLUMN4": {
                    "type": "object",
                    "valueObject": {}
                }
            }
        }

        result = ConsolidadoVotosParser.parse_consolidado_votos(consolidado_field)

        assert len(result) == 3
        assert result[0]["tipo"] == "VOTOS EN BLANCO"
        assert result[0]["votos"] == "---"
        assert result[1]["tipo"] == "VOTOS NULOS."
        assert result[1]["votos"] == "---"
        assert result[2]["tipo"] == "VOTOS NO MARCADOS"
        assert result[2]["votos"] == "---"

    def test_parse_consolidado_formato_array_sin_votos(self):
        consolidado_field = {
            "type": "array",
            "valueArray": [
                {
                    "type": "object",
                    "valueObject": {
                        "COLUMN1": {
                            "type": "string",
                            "valueString": "VOTOS EN BLANCO"
                        },
                        "COLUMN2": {
                            "type": "string",
                            "valueString": "--"
                        }
                    }
                }
            ]
        }

        result = ConsolidadoVotosParser.parse_consolidado_votos(consolidado_field)

        assert len(result) == 1
        assert result[0]["tipo"] == "VOTOS EN BLANCO"
        assert result[0]["votos"] == "---"

    def test_consolidado_en_pagina_correcta(self):
        fields = {
            "ConsolidadoVotos1Pag10": {
                "type": "array",
                "valueArray": [
                    {
                        "type": "object",
                        "valueObject": {
                            "COLUMN1": {
                                "valueString": "VOTOS EN BLANCO"
                            },
                            "COLUMN2": {
                                "valueString": "11"
                            }
                        }
                    }
                ]
            },
            "TipoDeVotoPartido1Pag10": {
                "valueString": "LISTA SIN VOTO PREFERENTE\n0001\nPARTIDO TEST\n0"
            }
        }

        parser = E14SenadoParser()
        result = parser.parse(fields)

        assert "ConsolidadoVotos10" in result["e14"]
        assert "Partido10" in result["e14"]
        assert len(result["e14"]["ConsolidadoVotos10"]) == 1
        assert result["e14"]["ConsolidadoVotos10"][0]["tipo"] == "VOTOS EN BLANCO"
        assert result["e14"]["ConsolidadoVotos10"][0]["votos"] == "11"

    def test_multiples_consolidados_diferentes_paginas(self):
        fields = {
            "ConsolidadoVotos1Pag10": {
                "type": "array",
                "valueArray": [
                    {
                        "type": "object",
                        "valueObject": {
                            "COLUMN1": {
                                "valueString": "VOTOS EN BLANCO"
                            },
                            "COLUMN2": {
                                "valueString": "11"
                            }
                        }
                    }
                ]
            },
            "TipoDeVotoPartido1Pag10": {
                "valueString": "LISTA SIN VOTO PREFERENTE\n0001\nPARTIDO 1\n0"
            },
            "ConsolidadoVotos2Pag11": {
                "type": "object",
                "valueObject": {
                    "COLUMN1": {
                        "type": "object",
                        "valueObject": {
                            "ROW1": {
                                "valueString": "VOTOS EN BLANCO"
                            }
                        }
                    },
                    "COLUMN2": {
                        "type": "object",
                        "valueObject": {}
                    }
                }
            },
            "TipoDeVotoPartido1Pag11": {
                "valueString": "LISTA SIN VOTO PREFERENTE\n0002\nPARTIDO 2\n0"
            }
        }

        parser = E14SenadoParser()
        result = parser.parse(fields)

        assert "ConsolidadoVotos10" in result["e14"]
        assert "ConsolidadoVotos11" in result["e14"]
        assert result["e14"]["ConsolidadoVotos10"][0]["votos"] == "11"
        assert result["e14"]["ConsolidadoVotos11"][0]["votos"] == "---"

    def test_pagina_sin_consolidado_no_agrega_campo(self):
        fields = {
            "TipoDeVotoPartido1Pag5": {
                "valueString": "LISTA SIN VOTO PREFERENTE\n0001\nPARTIDO TEST\n0"
            }
        }

        parser = E14SenadoParser()
        result = parser.parse(fields)

        assert "ConsolidadoVotos5" not in result["e14"]
        assert "Partido5" in result["e14"]

    def test_integracion_consolidados_con_archivo_real(self):
        import json
        import os

        archivo_test = "temp/cleaned_fields.json"
        if not os.path.exists(archivo_test):
            pytest.skip("Archivo de prueba no disponible")

        with open(archivo_test, 'r', encoding='utf-8') as f:
            data = json.load(f)
            fields = data['fields']

        parser = E14SenadoParser()
        result = parser.parse(fields)

        assert "ConsolidadoVotos10" in result["e14"]
        assert "ConsolidadoVotos11" in result["e14"]

        consolidado_pag10 = result["e14"]["ConsolidadoVotos10"]
        assert len(consolidado_pag10) == 3
        assert consolidado_pag10[0]["tipo"] == "VOTOS EN BLANCO"
        assert consolidado_pag10[0]["votos"] == "11"

        consolidado_pag11 = result["e14"]["ConsolidadoVotos11"]
        assert len(consolidado_pag11) == 3
        assert consolidado_pag11[0]["tipo"] == "VOTOS EN BLANCO"
        assert consolidado_pag11[0]["votos"] == "---"

        for page_num in range(1, 12):
            partido_key = "Partido" if page_num == 1 else f"Partido{page_num}"
            assert partido_key in result["e14"]
