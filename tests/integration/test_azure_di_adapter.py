import pytest
import os
from unittest.mock import Mock, patch
from src.infrastructure.ocr.azure_document_intelligence import AzureDocumentIntelligenceAdapter
from src.shared.config.yaml_config import YAMLConfig


class TestAzureDocumentIntelligenceAdapter:
    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=YAMLConfig)
        config.get.return_value = "prebuilt-layout"
        return config

    def test_adapter_initialization_without_credentials(self, mock_config):
        adapter = AzureDocumentIntelligenceAdapter(mock_config)
        assert adapter.is_available() == False

    @patch.dict(os.environ, {
        "AZURE_DI_ENDPOINT": "https://test.cognitiveservices.azure.com/",
        "AZURE_DI_KEY": "test_key_123"
    })
    @patch("src.infrastructure.ocr.azure_document_intelligence.azure_di_adapter.DocumentIntelligenceClient")
    def test_adapter_initialization_with_credentials(self, mock_client_class, mock_config):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        adapter = AzureDocumentIntelligenceAdapter(mock_config)
        assert adapter.is_available() == True

    @patch.dict(os.environ, {
        "AZURE_DI_ENDPOINT": "https://test.cognitiveservices.azure.com/",
        "AZURE_DI_KEY": "test_key_123"
    })
    @patch("src.infrastructure.ocr.azure_document_intelligence.azure_di_adapter.DocumentIntelligenceClient")
    def test_analyze_e14_document(self, mock_client_class, mock_config):
        mock_client = Mock()
        mock_poller = Mock()
        mock_result = Mock()
        mock_result.as_dict.return_value = {"documents": [{"fields": {}}]}

        mock_poller.result.return_value = mock_result
        mock_client.begin_analyze_document.return_value = mock_poller
        mock_client_class.return_value = mock_client

        adapter = AzureDocumentIntelligenceAdapter(mock_config)
        image_bytes = b"fake_image_data"

        result = adapter.analyze_e14_document(image_bytes)

        assert result is not None
        assert "documents" in result
        mock_client.begin_analyze_document.assert_called_once()

    def test_analyze_e14_document_without_client(self, mock_config):
        adapter = AzureDocumentIntelligenceAdapter(mock_config)
        image_bytes = b"fake_image_data"

        result = adapter.analyze_e14_document(image_bytes)

        assert result is None
