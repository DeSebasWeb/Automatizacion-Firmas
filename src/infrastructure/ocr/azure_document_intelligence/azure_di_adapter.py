import os
from typing import Optional
import structlog
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

from src.domain.ports.azure_di_port import AzureDIPort
from src.domain.ports.config_port import ConfigPort

logger = structlog.get_logger(__name__)


class AzureDocumentIntelligenceAdapter(AzureDIPort):
    def __init__(self, config: ConfigPort):
        self.config = config
        self.client: Optional[DocumentIntelligenceClient] = None
        self.model_id: str = config.get("azure_di.model_id", "prebuilt-layout")
        self._initialize_client()

    def _initialize_client(self) -> None:
        try:
            endpoint = os.getenv("AZURE_DI_ENDPOINT")
            api_key = os.getenv("AZURE_DI_KEY")

            if not endpoint or not api_key:
                logger.error("azure_di_credentials_missing",
                           endpoint_present=bool(endpoint),
                           key_present=bool(api_key))
                return

            self.client = DocumentIntelligenceClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(api_key)
            )
            logger.info("azure_di_client_initialized", model_id=self.model_id)

        except Exception as e:
            logger.error("azure_di_initialization_failed", error=str(e))
            self.client = None

    def is_available(self) -> bool:
        return self.client is not None

    def analyze_e14_document(self, image_bytes: bytes) -> Optional[dict]:
        if not self.is_available():
            logger.error("azure_di_client_not_available")
            return None

        timeout_seconds = self.config.get("azure_di.polling_timeout_seconds", 60)

        def _analyze_with_poller():
            poller = self.client.begin_analyze_document(
                model_id=self.model_id,
                body=image_bytes,
                content_type="application/pdf"
            )
            return poller.result(timeout=timeout_seconds)

        try:
            logger.info("analyzing_e14_document", size_bytes=len(image_bytes), timeout_seconds=timeout_seconds)

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_analyze_with_poller)

                try:
                    result = future.result(timeout=timeout_seconds)
                except FuturesTimeoutError:
                    logger.error("azure_di_timeout_exceeded",
                               timeout_seconds=timeout_seconds,
                               message="Azure DI did not respond in time. Cancelling request.")
                    future.cancel()
                    return None

            response_dict = result.as_dict()
            logger.info("e14_document_analyzed", pages=len(response_dict.get("pages", [])))

            import json
            from pathlib import Path
            output_file = Path("azure_full_response.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(response_dict, f, indent=2, ensure_ascii=False, default=str)
            logger.info("full_response_saved", file=str(output_file))

            return response_dict

        except AzureError as e:
            logger.error("azure_di_api_error", error=str(e), error_type=type(e).__name__)
            return None
        except FuturesTimeoutError:
            logger.error("azure_di_hard_timeout", timeout_seconds=timeout_seconds)
            return None
        except Exception as e:
            logger.error("azure_di_unexpected_error", error=str(e), error_type=type(e).__name__)
            return None
