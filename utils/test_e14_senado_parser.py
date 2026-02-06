import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ocr.azure_document_intelligence.parsers import E14SenadoParser


def test_parser_with_real_data():
    input_file = Path("temp/cleaned_fields.json")

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    fields = data.get("fields", {})

    print(f"Total fields loaded: {len(fields)}")

    parser = E14SenadoParser()

    result = parser.parse(fields)

    output_file = Path("temp/e14_senado_parsed_test.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nParsed output saved to: {output_file}")

    e14_data = result.get("e14", {})

    print("\n=== PARSING SUMMARY ===")
    print(f"Pagina: {e14_data.get('pagina')}")
    print(f"Divipol: {e14_data.get('divipol')}")
    print(f"Total Sufragantes: {e14_data.get('TotalSufragantesE14')}")
    print(f"Total Votos En Urna: {e14_data.get('TotalVotosEnUrna')}")
    print(f"Total Incinerados: {e14_data.get('TotalIncinerados')}")

    partidos_pag1 = e14_data.get("Partido", [])
    print(f"\nPartidos en Página 1: {len(partidos_pag1)}")
    for i, partido in enumerate(partidos_pag1, 1):
        print(f"  {i}. {partido.get('nombrePartido')} ({partido.get('numPartido')})")
        print(f"     Tipo: {partido.get('tipoDeVoto')}")
        print(f"     Candidatos: {len(partido.get('candidatos', []))}")
        print(f"     Total: {partido.get('TotalVotosAgrupacion+VotosCandidatos')}")

    for page_num in range(2, 12):
        partido_key = f"Partido{page_num}"
        if partido_key in e14_data:
            partidos = e14_data[partido_key]
            print(f"\nPartidos en Página {page_num}: {len(partidos)}")
            for partido in partidos:
                print(f"  - {partido.get('nombrePartido')} ({partido.get('numPartido')})")

    consolidado_keys = [k for k in e14_data.keys() if k.startswith("ConsolidadoVotos")]
    if consolidado_keys:
        print(f"\n=== CONSOLIDADOS ===")
        for key in consolidado_keys:
            consolidado = e14_data[key]
            print(f"{key}: {len(consolidado)} items")
            for item in consolidado:
                print(f"  - {item.get('tipo')}: {item.get('votos')}")


if __name__ == "__main__":
    test_parser_with_real_data()
