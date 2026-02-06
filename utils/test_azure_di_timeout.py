import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ocr.azure_document_intelligence import AzureDocumentIntelligenceAdapter
from src.shared.config.yaml_config import YAMLConfig
from src.application.use_cases.process_e14_senado_use_case import ProcessE14SenadoUseCase
import time


def test_timeout():
    print("Testing Azure DI timeout configuration...")

    config = YAMLConfig("config/settings.yaml")

    timeout_seconds = config.get("azure_di.polling_timeout_seconds", 120)
    print(f"Configured timeout: {timeout_seconds} seconds")

    adapter = AzureDocumentIntelligenceAdapter(config)

    if not adapter.is_available():
        print("Azure DI adapter not available. Check credentials.")
        return

    print("Azure DI adapter initialized successfully")
    print(f"Model ID: {adapter.model_id}")

    test_pdf = Path("temp/test_e14_senado.pdf")
    if not test_pdf.exists():
        print(f"Test PDF not found at: {test_pdf}")
        print("Please place a test E-14 PDF at that location")
        return

    with open(test_pdf, "rb") as f:
        pdf_bytes = f.read()

    print(f"Loaded test PDF: {len(pdf_bytes)} bytes")
    print("Sending to Azure DI for analysis...")
    print("(This should timeout after 120 seconds if processing takes too long)")

    start_time = time.time()

    try:
        use_case = ProcessE14SenadoUseCase(adapter)
        result = use_case.execute(pdf_bytes)

        elapsed = time.time() - start_time

        if result:
            print(f"\nSuccess! Analysis completed in {elapsed:.2f} seconds")
            print(f"Pages parsed: {len([k for k in result.get('e14', {}).keys() if 'pagina' in k]) + 1}")
        else:
            print(f"\nFailed to process document (took {elapsed:.2f} seconds)")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\nError after {elapsed:.2f} seconds: {str(e)}")
        print(f"Error type: {type(e).__name__}")

        if elapsed >= timeout_seconds:
            print("Timeout worked correctly!")
        else:
            print("Error occurred before timeout")


if __name__ == "__main__":
    test_timeout()
