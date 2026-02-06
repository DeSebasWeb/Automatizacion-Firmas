import pytest
from src.infrastructure.ocr.azure_document_intelligence.field_extractors.votos_extractor import VotosExtractor
from src.domain.value_objects.confidence_score import ConfidenceScore


class TestVotosExtractor:
    def test_extract_all_fields(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "votos_nulos": {"content": "5", "confidence": 0.95},
                        "votos_no_marcados": {"content": "2", "confidence": 0.92},
                        "votos_blanco": {"content": "3", "confidence": 0.88},
                        "total_votos_validos": {"content": "150", "confidence": 0.97}
                    }
                }
            ]
        }

        result = VotosExtractor.extract(azure_response)

        assert result["votos_nulos"][0] == 5
        assert result["votos_nulos"][1].value == 0.95

        assert result["votos_no_marcados"][0] == 2
        assert result["votos_no_marcados"][1].value == 0.92

        assert result["votos_blanco"][0] == 3
        assert result["votos_blanco"][1].value == 0.88

        assert result["total_votos_validos"][0] == 150
        assert result["total_votos_validos"][1].value == 0.97

    def test_extract_missing_field(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "votos_nulos": {"content": "5", "confidence": 0.95}
                    }
                }
            ]
        }

        result = VotosExtractor.extract(azure_response)

        assert result["votos_nulos"][0] == 5
        assert result["votos_no_marcados"][0] == 0
        assert result["votos_no_marcados"][1].value == 0.0

    def test_extract_empty_content(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "votos_nulos": {"content": "", "confidence": 0.5}
                    }
                }
            ]
        }

        result = VotosExtractor.extract(azure_response)

        assert result["votos_nulos"][0] == 0
        assert result["votos_nulos"][1].value == 0.5

    def test_extract_invalid_integer(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "votos_nulos": {"content": "ABC", "confidence": 0.3}
                    }
                }
            ]
        }

        result = VotosExtractor.extract(azure_response)

        assert result["votos_nulos"][0] == 0
        assert result["votos_nulos"][1].value == 0.3

    def test_extract_no_documents(self):
        azure_response = {"documents": []}

        result = VotosExtractor.extract(azure_response)

        assert len(result) == 0
