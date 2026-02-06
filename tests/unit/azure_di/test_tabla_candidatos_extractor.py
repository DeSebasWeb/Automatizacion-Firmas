import pytest
from src.infrastructure.ocr.azure_document_intelligence.field_extractors.tabla_candidatos_extractor import TablaCandidatosExtractor


class TestTablaCandidatosExtractor:
    def test_extract_single_partido(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "tabla_candidatos": {
                            "valueArray": [
                                {
                                    "valueObject": {
                                        "partido": {"content": "PARTIDO A", "confidence": 0.95},
                                        "numero_lista": {"content": "001", "confidence": 0.96},
                                        "votos_partido": {"content": "50", "confidence": 0.94},
                                        "candidato_numero": {"content": "101", "confidence": 0.93},
                                        "candidato_nombre": {"content": "Juan Perez", "confidence": 0.92},
                                        "candidato_votos": {"content": "25", "confidence": 0.91}
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        }

        result = TablaCandidatosExtractor.extract(azure_response)

        assert len(result) == 1
        assert result[0].partido == "PARTIDO A"
        assert result[0].numero_lista == "001"
        assert result[0].votos_partido == 50
        assert len(result[0].candidatos) == 1
        assert result[0].candidatos[0].numero == "101"
        assert result[0].candidatos[0].nombre == "Juan Perez"
        assert result[0].candidatos[0].votos == 25

    def test_extract_partido_with_multiple_candidatos(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "tabla_candidatos": {
                            "valueArray": [
                                {
                                    "valueObject": {
                                        "partido": {"content": "PARTIDO A", "confidence": 0.95},
                                        "numero_lista": {"content": "001", "confidence": 0.96},
                                        "votos_partido": {"content": "50", "confidence": 0.94},
                                        "candidato_numero": {"content": "101", "confidence": 0.93},
                                        "candidato_nombre": {"content": "Juan Perez", "confidence": 0.92},
                                        "candidato_votos": {"content": "25", "confidence": 0.91}
                                    }
                                },
                                {
                                    "valueObject": {
                                        "partido": {"content": "PARTIDO A", "confidence": 0.95},
                                        "numero_lista": {"content": "001", "confidence": 0.96},
                                        "votos_partido": {"content": "50", "confidence": 0.94},
                                        "candidato_numero": {"content": "102", "confidence": 0.93},
                                        "candidato_nombre": {"content": "Maria Lopez", "confidence": 0.92},
                                        "candidato_votos": {"content": "15", "confidence": 0.91}
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        }

        result = TablaCandidatosExtractor.extract(azure_response)

        assert len(result) == 1
        assert len(result[0].candidatos) == 2
        assert result[0].candidatos[0].nombre == "Juan Perez"
        assert result[0].candidatos[1].nombre == "Maria Lopez"

    def test_extract_multiple_partidos(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "tabla_candidatos": {
                            "valueArray": [
                                {
                                    "valueObject": {
                                        "partido": {"content": "PARTIDO A", "confidence": 0.95},
                                        "numero_lista": {"content": "001", "confidence": 0.96},
                                        "votos_partido": {"content": "50", "confidence": 0.94},
                                        "candidato_numero": {"content": "", "confidence": 0.0},
                                        "candidato_nombre": {"content": "", "confidence": 0.0},
                                        "candidato_votos": {"content": "", "confidence": 0.0}
                                    }
                                },
                                {
                                    "valueObject": {
                                        "partido": {"content": "PARTIDO B", "confidence": 0.93},
                                        "numero_lista": {"content": "002", "confidence": 0.94},
                                        "votos_partido": {"content": "30", "confidence": 0.92},
                                        "candidato_numero": {"content": "", "confidence": 0.0},
                                        "candidato_nombre": {"content": "", "confidence": 0.0},
                                        "candidato_votos": {"content": "", "confidence": 0.0}
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        }

        result = TablaCandidatosExtractor.extract(azure_response)

        assert len(result) == 2
        assert result[0].partido == "PARTIDO A"
        assert result[1].partido == "PARTIDO B"
        assert len(result[0].candidatos) == 0
        assert len(result[1].candidatos) == 0

    def test_extract_no_documents(self):
        azure_response = {"documents": []}

        result = TablaCandidatosExtractor.extract(azure_response)

        assert len(result) == 0

    def test_extract_empty_tabla(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "tabla_candidatos": {
                            "valueArray": []
                        }
                    }
                }
            ]
        }

        result = TablaCandidatosExtractor.extract(azure_response)

        assert len(result) == 0
