import pytest
from src.infrastructure.ocr.azure_document_intelligence.response_cleaner import (
    AzureResponseCleaner,
    AzureResponseValidator,
    CleaningVerifier
)


class TestAzureResponseCleaner:

    def test_clean_simple_field(self):
        cleaner = AzureResponseCleaner()

        input_data = {
            "type": "string",
            "valueString": "test",
            "boundingRegions": [{"pageNumber": 1, "polygon": [1, 2, 3, 4]}],
            "spans": [{"offset": 0, "length": 4}],
            "confidence": 0.9
        }

        result = cleaner.clean(input_data)

        assert "boundingRegions" not in result
        assert "spans" not in result
        assert result["valueString"] == "test"
        assert result["confidence"] == 0.9
        assert result["type"] == "string"

    def test_clean_nested_object(self):
        cleaner = AzureResponseCleaner()

        input_data = {
            "type": "object",
            "valueObject": {
                "Field1": {
                    "type": "string",
                    "valueString": "test",
                    "boundingRegions": [{"pageNumber": 1}],
                    "spans": [{"offset": 0, "length": 4}],
                    "confidence": 0.8
                }
            },
            "boundingRegions": [{"pageNumber": 1}],
            "confidence": 0.9
        }

        result = cleaner.clean(input_data)

        assert "boundingRegions" not in result
        assert "boundingRegions" not in result["valueObject"]["Field1"]
        assert "spans" not in result["valueObject"]["Field1"]
        assert result["valueObject"]["Field1"]["valueString"] == "test"
        assert result["valueObject"]["Field1"]["confidence"] == 0.8

    def test_clean_array(self):
        cleaner = AzureResponseCleaner()

        input_data = {
            "type": "array",
            "valueArray": [
                {
                    "type": "object",
                    "valueObject": {
                        "name": {
                            "type": "string",
                            "valueString": "test",
                            "boundingRegions": []
                        }
                    },
                    "boundingRegions": [],
                    "confidence": 0.8
                }
            ],
            "confidence": 0.9
        }

        result = cleaner.clean(input_data)

        assert "boundingRegions" not in result
        assert "boundingRegions" not in result["valueArray"][0]
        assert "boundingRegions" not in result["valueArray"][0]["valueObject"]["name"]
        assert result["valueArray"][0]["valueObject"]["name"]["valueString"] == "test"

    def test_clean_deeply_nested_structure(self):
        cleaner = AzureResponseCleaner()

        input_data = {
            "type": "object",
            "valueObject": {
                "Level1": {
                    "type": "object",
                    "valueObject": {
                        "Level2": {
                            "type": "object",
                            "valueObject": {
                                "Level3": {
                                    "type": "string",
                                    "valueString": "deep",
                                    "boundingRegions": [],
                                    "spans": []
                                }
                            },
                            "boundingRegions": []
                        }
                    },
                    "boundingRegions": []
                }
            },
            "boundingRegions": []
        }

        result = cleaner.clean(input_data)

        assert "boundingRegions" not in result
        assert "boundingRegions" not in result["valueObject"]["Level1"]
        assert "boundingRegions" not in result["valueObject"]["Level1"]["valueObject"]["Level2"]
        assert "boundingRegions" not in result["valueObject"]["Level1"]["valueObject"]["Level2"]["valueObject"]["Level3"]
        assert result["valueObject"]["Level1"]["valueObject"]["Level2"]["valueObject"]["Level3"]["valueString"] == "deep"

    def test_count_fields(self):
        cleaner = AzureResponseCleaner()

        data = {
            "field1": "value1",
            "field2": {
                "nested1": "value2",
                "nested2": "value3"
            }
        }

        count = cleaner.count_fields(data)
        assert count == 4

    def test_clean_preserves_all_value_types(self):
        cleaner = AzureResponseCleaner()

        input_data = {
            "type": "object",
            "valueString": "string value",
            "valueObject": {"nested": "object"},
            "valueArray": [1, 2, 3],
            "content": "content value",
            "confidence": 0.95,
            "boundingRegions": [],
            "spans": []
        }

        result = cleaner.clean(input_data)

        assert result["type"] == "object"
        assert result["valueString"] == "string value"
        assert result["valueObject"] == {"nested": "object"}
        assert result["valueArray"] == [1, 2, 3]
        assert result["content"] == "content value"
        assert result["confidence"] == 0.95
        assert "boundingRegions" not in result
        assert "spans" not in result


class TestAzureResponseValidator:

    def test_validate_valid_response(self):
        valid_response = {
            "analyzeResult": {
                "documents": [
                    {
                        "fields": {
                            "Field1": {"type": "string", "valueString": "test"}
                        }
                    }
                ]
            }
        }

        assert AzureResponseValidator.validate_response(valid_response) is True

    def test_validate_missing_analyzeResult(self):
        invalid_response = {
            "documents": [{"fields": {}}]
        }

        assert AzureResponseValidator.validate_response(invalid_response) is False

    def test_validate_missing_documents(self):
        invalid_response = {
            "analyzeResult": {
                "pages": []
            }
        }

        assert AzureResponseValidator.validate_response(invalid_response) is False

    def test_validate_empty_documents(self):
        invalid_response = {
            "analyzeResult": {
                "documents": []
            }
        }

        assert AzureResponseValidator.validate_response(invalid_response) is False

    def test_validate_missing_fields(self):
        invalid_response = {
            "analyzeResult": {
                "documents": [
                    {
                        "docType": "form"
                    }
                ]
            }
        }

        assert AzureResponseValidator.validate_response(invalid_response) is False

    def test_extract_fields_valid(self):
        valid_response = {
            "analyzeResult": {
                "documents": [
                    {
                        "fields": {
                            "Field1": {"type": "string", "valueString": "test"}
                        }
                    }
                ]
            }
        }

        fields = AzureResponseValidator.extract_fields(valid_response)

        assert "Field1" in fields
        assert fields["Field1"]["valueString"] == "test"

    def test_extract_fields_invalid_raises_error(self):
        invalid_response = {
            "analyzeResult": {}
        }

        with pytest.raises(ValueError, match="Invalid Azure DI response structure"):
            AzureResponseValidator.extract_fields(invalid_response)


class TestCleaningVerifier:

    def test_verify_cleaning_statistics(self):
        cleaner = AzureResponseCleaner()
        verifier = CleaningVerifier(cleaner)

        original = {
            "field1": "value1",
            "boundingRegions": [],
            "spans": [],
            "nested": {
                "field2": "value2",
                "boundingRegions": []
            }
        }

        cleaned = cleaner.clean(original)

        stats = verifier.verify_cleaning(original, cleaned)

        assert stats["original_fields"] > stats["cleaned_fields"]
        assert stats["removed_fields"] > 0
        assert 0 < stats["retention_rate"] < 100

    def test_verify_cleaning_preserves_important_fields(self):
        cleaner = AzureResponseCleaner()
        verifier = CleaningVerifier(cleaner)

        original = {
            "type": "string",
            "valueString": "test",
            "confidence": 0.9,
            "boundingRegions": [],
            "spans": []
        }

        cleaned = cleaner.clean(original)

        stats = verifier.verify_cleaning(original, cleaned)

        assert stats["retention_rate"] >= 60
