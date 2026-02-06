import json
from pathlib import Path
from typing import Dict
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.ocr.azure_document_intelligence.response_cleaner import (
    AzureResponseCleaner,
    AzureResponseValidator,
    CleaningVerifier
)


def extract_and_save_fields(
    azure_response: Dict,
    output_path: str = "temp/cleaned_fields.json"
) -> None:
    validator = AzureResponseValidator()
    cleaner = AzureResponseCleaner()
    verifier = CleaningVerifier(cleaner)

    fields = validator.extract_fields(azure_response)

    cleaned_fields = cleaner.clean(fields)

    output = {"fields": cleaned_fields}

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open('w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    stats = verifier.verify_cleaning(fields, cleaned_fields)

    print(f"JSON limpio guardado en: {output_path}")
    print(f"Total de campos originales: {stats['original_fields']}")
    print(f"Total de campos limpios: {stats['cleaned_fields']}")
    print(f"Campos eliminados: {stats['removed_fields']}")
    print(f"Tasa de retención: {stats['retention_rate']}%")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python utils/clean_azure_response.py <input_file> [output_file]")
        print("Ejemplo: python utils/clean_azure_response.py data/results/azure_response.json temp/cleaned.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "temp/cleaned_fields.json"

    with open(input_file, "r", encoding='utf-8') as f:
        azure_response = json.load(f)

    extract_and_save_fields(azure_response, output_path=output_file)
