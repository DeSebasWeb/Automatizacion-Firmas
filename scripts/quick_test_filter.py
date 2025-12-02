"""
Script rápido para verificar que filter_cedulas() separa correctamente bloques gigantes.

Simula el bloque [10] del log.txt que contenía múltiples cédulas agrupadas.
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ocr.spatial_pairing import SpatialPairing


def test_filter_cedulas():
    """Prueba la separación de múltiples cédulas en un bloque gigante."""

    print("=" * 80)
    print("TEST: Separación de cédulas en bloques gigantes")
    print("=" * 80)
    print()

    # Simular el bloque [10] del log.txt
    giant_block = {
        'text': '100028470 ) 1110548784 201414649L 107376 3070 4004410752 79840159 770 15902 ( hicx6 0774769 56 57 7812387018',
        'x': 1124,
        'y': 30,
        'width': 895,
        'height': 718,
        'confidence': 0.7658
    }

    print("BLOQUE ORIGINAL:")
    print(f"  Texto: '{giant_block['text']}'")
    print(f"  Posición: x={giant_block['x']}, y={giant_block['y']}")
    print(f"  Tamaño: w={giant_block['width']}, h={giant_block['height']}")
    print(f"  Confianza: {giant_block['confidence']:.2%}")
    print()

    # Aplicar filter_cedulas
    cedulas = SpatialPairing.filter_cedulas([giant_block])

    print("CÉDULAS EXTRAÍDAS:")
    print("-" * 80)

    if cedulas:
        print(f"✓ Se extrajeron {len(cedulas)} cédulas:\n")
        for i, cedula in enumerate(cedulas, 1):
            print(f"[{i}] {cedula['text']}")
            print(f"    Posición: x={cedula['x']:.0f}, y={cedula['y']:.0f}")
            print(f"    Tamaño: w={cedula['width']:.0f}, h={cedula['height']:.0f}")
            print(f"    Confianza: {cedula['confidence']:.2%}")
            print()
    else:
        print("✗ No se extrajo ninguna cédula")
        print()

    # Simular el bloque [16] también
    print("=" * 80)
    print("TEST 2: Segundo bloque gigante")
    print("=" * 80)
    print()

    second_block = {
        'text': '1018459356 830 90834 7922420972 77173011 80741499',
        'x': 1453,
        'y': 750,
        'width': 468,
        'height': 329,
        'confidence': 0.8747
    }

    print("BLOQUE ORIGINAL:")
    print(f"  Texto: '{second_block['text']}'")
    print(f"  Posición: x={second_block['x']}, y={second_block['y']}")
    print()

    cedulas2 = SpatialPairing.filter_cedulas([second_block])

    print(f"✓ Se extrajeron {len(cedulas2)} cédulas:\n")
    for i, cedula in enumerate(cedulas2, 1):
        print(f"[{i}] {cedula['text']}")
        print(f"    Posición: y={cedula['y']:.0f}")
        print()

    print("=" * 80)
    print(f"RESUMEN: Total de {len(cedulas) + len(cedulas2)} cédulas extraídas de 2 bloques")
    print("=" * 80)


if __name__ == "__main__":
    test_filter_cedulas()
