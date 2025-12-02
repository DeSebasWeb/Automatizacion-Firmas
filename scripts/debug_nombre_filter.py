"""
Script de diagnóstico para ver por qué filter_nombres() no retorna nombres.

Simula los bloques detectados en el log.txt y muestra qué pasa en cada etapa del filtrado.
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ocr.spatial_pairing import SpatialPairing


def test_filter_nombres():
    """Prueba el filtrado de nombres con los bloques del log.txt."""

    print("=" * 80)
    print("DIAGNÓSTICO: ¿Por qué filter_nombres() no retorna nada?")
    print("=" * 80)
    print()

    # Simular bloques de nombres del log.txt
    test_blocks = [
        {
            'text': 'Laura Orego Anyce ortagon',
            'x': 144, 'y': 0,
            'width': 617, 'height': 163,
            'confidence': 0.753
        },
        {
            'text': 'Camacho Modine .',
            'x': 612, 'y': 142,
            'width': 625, 'height': 83,
            'confidence': 0.7513
        },
        {
            'text': 'Jeimy .',
            'x': 299, 'y': 155,
            'width': 280, 'height': 76,
            'confidence': 0.7641
        },
        {
            'text': 'Sharon matiz',
            'x': 661, 'y': 231,
            'width': 354, 'height': 56,
            'confidence': 0.7601
        },
        {
            'text': 'Mauro',
            'x': 300, 'y': 290,
            'width': 173, 'height': 56,
            'confidence': 0.9493
        },
        {
            'text': 'Cordoba R',
            'x': 581, 'y': 291,
            'width': 407, 'height': 76,
            'confidence': 0.8332
        },
        {
            'text': 'CANCOS MACMIREZ G. Cristian Mejid Clavelia',
            'x': 212, 'y': 372,
            'width': 772, 'height': 358,
            'confidence': 0.6129
        },
    ]

    print("BLOQUES DE PRUEBA:")
    print("-" * 80)
    for i, block in enumerate(test_blocks, 1):
        text = block['text']
        print(f"\n[{i}] '{text}'")
        print(f"    Longitud: {len(text)} chars")
        print(f"    Palabras: {len(text.split())}")

        # Test _is_nombre_pattern
        is_pattern = SpatialPairing._is_nombre_pattern(text)
        print(f"    _is_nombre_pattern: {'✓ PASS' if is_pattern else '✗ FAIL'}")

        # Test _is_valid_nombre
        is_valid = SpatialPairing._is_valid_nombre(text)
        print(f"    _is_valid_nombre: {'✓ PASS' if is_valid else '✗ FAIL (< 10 chars o < 2 palabras)'}")

    print("\n" + "=" * 80)
    print("APLICANDO filter_nombres()...")
    print("=" * 80)

    nombres = SpatialPairing.filter_nombres(test_blocks)

    print(f"\n✓ Nombres extraídos: {len(nombres)}")
    print()

    if nombres:
        for i, nombre in enumerate(nombres, 1):
            print(f"{i}. '{nombre['text']}'")
            print(f"   Posición: x={nombre['x']:.0f}, y={nombre['y']:.0f}")
            print(f"   Confianza: {nombre['confidence']:.2%}")
            print()
    else:
        print("✗ NO SE EXTRAJO NINGÚN NOMBRE")
        print()
        print("Posibles causas:")
        print("  1. _is_nombre_pattern() rechaza el texto (< 70% letras)")
        print("  2. _is_valid_nombre() rechaza el nombre merged (< 10 chars o < 2 palabras)")
        print("  3. Bloques no consecutivos no se están mergeando correctamente")


if __name__ == "__main__":
    test_filter_nombres()
