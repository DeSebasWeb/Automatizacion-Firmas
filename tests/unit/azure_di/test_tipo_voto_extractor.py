import pytest
from src.infrastructure.ocr.azure_document_intelligence.field_extractors.tipo_voto_extractor import TipoVotoExtractor
from src.infrastructure.ocr.azure_document_intelligence.models.tipo_lista import TipoLista


class TestTipoVotoExtractor:
    def test_extract_senado(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "tipo_voto_partido": {
                            "content": "SENADO",
                            "confidence": 0.95
                        }
                    }
                }
            ]
        }

        result = TipoVotoExtractor.extract(azure_response)
        assert result == TipoLista.SENADO

    def test_extract_camara(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "tipo_voto_partido": {
                            "content": "CAMARA",
                            "confidence": 0.93
                        }
                    }
                }
            ]
        }

        result = TipoVotoExtractor.extract(azure_response)
        assert result == TipoLista.CAMARA

    def test_extract_no_documents(self):
        azure_response = {"documents": []}

        result = TipoVotoExtractor.extract(azure_response)
        assert result is None

    def test_extract_field_not_found(self):
        azure_response = {
            "documents": [
                {
                    "fields": {}
                }
            ]
        }

        result = TipoVotoExtractor.extract(azure_response)
        assert result is None

    def test_extract_empty_content(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "tipo_voto_partido": {
                            "content": "",
                            "confidence": 0.0
                        }
                    }
                }
            ]
        }

        result = TipoVotoExtractor.extract(azure_response)
        assert result is None

    def test_extract_invalid_value(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "tipo_voto_partido": {
                            "content": "INVALID",
                            "confidence": 0.5
                        }
                    }
                }
            ]
        }

        result = TipoVotoExtractor.extract(azure_response)
        assert result is None
