from typing import Optional, Dict
import structlog
import json
from pathlib import Path

from src.domain.ports.azure_di_port import AzureDIPort
from src.infrastructure.ocr.azure_document_intelligence.response_cleaner import (
    AzureResponseCleaner,
    AzureResponseValidator
)
from src.infrastructure.ocr.azure_document_intelligence.parsers import E14SenadoParser

logger = structlog.get_logger(__name__)


class ProcessE14SenadoUseCase:

    def __init__(self, azure_di_adapter: AzureDIPort):
        self.adapter = azure_di_adapter
        self.cleaner = AzureResponseCleaner()
        self.validator = AzureResponseValidator()
        self.parser = E14SenadoParser()

    def execute(self, image_bytes: bytes) -> Optional[Dict]:
        logger.info("process_e14_senado_started", size_bytes=len(image_bytes))

        if not self.adapter.is_available():
            logger.error("adapter_not_available")
            return None

        azure_response = self.adapter.analyze_e14_document(image_bytes)
        if not azure_response:
            logger.error("azure_analysis_failed")
            return None

        try:
            if not self.validator.validate_response(azure_response):
                logger.error("invalid_azure_response")
                return None

            fields = self.validator.extract_fields(azure_response)

            cleaned_fields = self.cleaner.clean(fields)

            self._save_debug_output(cleaned_fields)

            parsed_data = self.parser.parse(cleaned_fields)

            self._save_parsed_output(parsed_data)

            logger.info("e14_senado_parsing_completed")
            return parsed_data

        except Exception as e:
            logger.error("e14_senado_parsing_failed", error=str(e))
            return None

    def _save_debug_output(self, cleaned_fields: dict) -> None:
        try:
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)

            output_file = temp_dir / "cleaned_fields.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({"fields": cleaned_fields}, f, indent=2, ensure_ascii=False)

            logger.info("debug_output_saved", file=str(output_file))
        except Exception as e:
            logger.warning("failed_to_save_debug_output", error=str(e))

    def _save_parsed_output(self, parsed_data: dict) -> None:
        try:
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)

            output_file = temp_dir / "e14_senado_parsed.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)

            logger.info("parsed_output_saved", file=str(output_file))
        except Exception as e:
            logger.warning("failed_to_save_parsed_output", error=str(e))
