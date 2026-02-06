import pytest
from src.infrastructure.ocr.azure_document_intelligence.field_extractors.divipol_extractor import DivipolExtractor


class TestDivipolExtractor:
    def test_extract_all_fields(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "CodDep": {"content": "16", "confidence": 0.98},
                        "CodMun": {"content": "001", "confidence": 0.97},
                        "zona": {"content": "01", "confidence": 0.95},
                        "Puesto": {"content": "02", "confidence": 0.96},
                        "Mesa": {"content": "066", "confidence": 0.94}
                    }
                }
            ]
        }

        result = DivipolExtractor.extract(azure_response)

        assert result["CodDep"] == "16"
        assert result["CodMun"] == "001"
        assert result["zona"] == "01"
        assert result["Puesto"] == "02"
        assert result["Mesa"] == "066"

    def test_extract_missing_field(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "CodDep": {"content": "16", "confidence": 0.98},
                        "CodMun": {"content": "001", "confidence": 0.97}
                    }
                }
            ]
        }

        result = DivipolExtractor.extract(azure_response)

        assert result["CodDep"] == "16"
        assert result["CodMun"] == "001"
        assert result["zona"] == ""
        assert result["Puesto"] == ""
        assert result["Mesa"] == ""

    def test_extract_empty_content(self):
        azure_response = {
            "documents": [
                {
                    "fields": {
                        "CodDep": {"content": "", "confidence": 0.5}
                    }
                }
            ]
        }

        result = DivipolExtractor.extract(azure_response)

        assert result["CodDep"] == ""

    def test_extract_no_documents(self):
        azure_response = {"documents": []}

        result = DivipolExtractor.extract(azure_response)

        assert all(v == "" for v in result.values())
