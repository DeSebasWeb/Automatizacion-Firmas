"""Manual test script for E14 processing."""
import requests
from pathlib import Path
import json


def test_e14_processing():
    """
    Test E14 processing with uploaded PDFs.

    Prerequisites:
    1. API server running: uvicorn src.infrastructure.api.main:app --reload
    2. Valid API key or JWT token
    3. Sample E-14 PDFs in tests/data/e14_samples/
    """

    api_url = "http://localhost:8000/api/v1/documents/process"

    # Get API key from user
    api_key = input("Enter your API key (or press Enter to use test key): ").strip()
    if not api_key:
        api_key = "vfy_test_..."  # Replace with actual test key

    # Test PDFs directory
    pdf_dir = Path("tests/data/e14_samples")

    if not pdf_dir.exists():
        print(f"❌ Directory not found: {pdf_dir}")
        print(f"   Create it and add E-14 PDF samples")
        return

    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_dir}")
        return

    print(f"Found {len(pdf_files)} PDF files to process\n")

    # Process each PDF
    results = []

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        print("-" * 60)

        try:
            with open(pdf_path, 'rb') as f:
                response = requests.post(
                    api_url,
                    headers={"X-API-Key": api_key},
                    data={"document_type": "e14"},
                    files={"file": (pdf_path.name, f, "application/pdf")}
                )

            if response.status_code == 200:
                result = response.json()
                results.append({
                    "file": pdf_path.name,
                    "status": "success",
                    "result": result
                })

                print(f"✅ Success!")
                print(f"   Mesa: {result['divipol']['mesa']}")
                print(f"   Departamento: {result['divipol']['departamento_nombre']}")
                print(f"   Tipo Elección: {result['metadata']['tipo_eleccion']}")
                print(f"   Partidos: {len(result['partidos'])}")
                print(f"   Saved to: {result['metadata'].get('saved_to', 'N/A')}")

                # Show vote summary
                total_votos = sum(p['total'] for p in result['partidos'])
                print(f"   Total votos partidos: {total_votos}")
                print(f"   Votos en blanco: {result['votos_especiales']['votos_blanco']}")
                print(f"   Votos nulos: {result['votos_especiales']['votos_nulos']}")

            else:
                results.append({
                    "file": pdf_path.name,
                    "status": "error",
                    "error_code": response.status_code,
                    "error_message": response.text
                })

                print(f"❌ Error: {response.status_code}")
                print(f"   {response.text[:200]}")

        except Exception as e:
            results.append({
                "file": pdf_path.name,
                "status": "exception",
                "error": str(e)
            })

            print(f"❌ Exception: {e}")

        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = len(results) - success_count

    print(f"Total files: {len(results)}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {error_count}")

    # Save test results
    results_file = Path("tests/manual/test_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nTest results saved to: {results_file}")


def test_supported_types():
    """Test listing supported document types."""
    api_url = "http://localhost:8000/api/v1/documents/supported-types"

    api_key = input("Enter your API key: ").strip()

    try:
        response = requests.get(
            api_url,
            headers={"X-API-Key": api_key}
        )

        if response.status_code == 200:
            supported = response.json()
            print(f"✅ Supported document types:")
            for doc_type in supported:
                print(f"   - {doc_type}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "types":
        test_supported_types()
    else:
        test_e14_processing()
