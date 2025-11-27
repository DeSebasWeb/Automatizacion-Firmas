"""
Script de diagnóstico para verificar el ensemble con imagen real.

Este script permite probar el Dual Ensemble OCR (Google + Azure) con una imagen
real y ver logs detallados de cómo funciona la votación dígito por dígito.
"""

import sys
from pathlib import Path
from PIL import Image

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ocr import create_ocr_adapter
from src.shared.config import YAMLConfig


def main():
    """Función principal del script de diagnóstico."""
    print("=" * 80)
    print("SCRIPT DE DIAGNÓSTICO - DUAL ENSEMBLE OCR")
    print("=" * 80)
    print()

    # Cargar configuración
    try:
        config = YAMLConfig('config/settings.yaml')
        print("✓ Configuración cargada correctamente")
    except Exception as e:
        print(f"✗ Error cargando configuración: {e}")
        return

    # Crear OCR (debe ser digit_ensemble)
    try:
        ocr = create_ocr_adapter(config)
        print(f"✓ OCR Type: {type(ocr).__name__}")

        if type(ocr).__name__ != 'DigitLevelEnsembleOCR':
            print(f"⚠ ADVERTENCIA: Se esperaba DigitLevelEnsembleOCR")
            print(f"   Verifica que config/settings.yaml tenga provider: digit_ensemble")
        print()
    except Exception as e:
        print(f"✗ Error creando OCR adapter: {e}")
        import traceback
        traceback.print_exc()
        return

    # Solicitar ruta de imagen
    print("=" * 80)
    test_image_path = input("Ingresa la ruta de la imagen de prueba: ").strip()

    # Eliminar comillas si las hay
    test_image_path = test_image_path.strip('"').strip("'")

    # Cargar imagen de prueba
    try:
        image = Image.open(test_image_path)
        print(f"✓ Imagen cargada: {test_image_path}")
        print(f"  Tamaño: {image.size}")
        print(f"  Modo: {image.mode}")

        # Verificar si la imagen está corrupta intentando cargarla completamente
        try:
            image.load()
        except Exception as load_error:
            print(f"✗ La imagen está corrupta: {load_error}")
            print()
            print("SOLUCIÓN:")
            print("  1. Usa una imagen original (captura de pantalla directa)")
            print("  2. No uses imágenes de temp/processed/ (pueden estar corruptas)")
            print("  3. Usa formatos PNG o JPG estándar")
            return

        # Convertir a RGB si es necesario para evitar problemas
        if image.mode not in ('RGB', 'L'):
            print(f"  Convirtiendo de {image.mode} a RGB...")
            image = image.convert('RGB')

        print()
    except Exception as e:
        print(f"✗ Error cargando imagen: {e}")
        return

    # Extraer cédulas con logging detallado
    print("=" * 80)
    print("INICIANDO EXTRACCIÓN CON DUAL ENSEMBLE")
    print("=" * 80)
    print()

    try:
        cedulas = ocr.extract_cedulas(image)

        print()
        print("=" * 80)
        print("RESULTADOS FINALES")
        print("=" * 80)

        if cedulas:
            print(f"✓ {len(cedulas)} cédula(s) extraída(s):")
            for i, record in enumerate(cedulas, 1):
                print(f"  {i}. {record.cedula.value} (confianza: {record.confidence.as_percentage():.1f}%)")
        else:
            print("✗ No se extrajo ninguna cédula")
            print()
            print("Posibles razones:")
            print("  - Confianzas muy bajas (< 75%)")
            print("  - Muchos conflictos ambiguos (diferencia < 10%)")
            print("  - Imagen de mala calidad")
            print()
            print("Sugerencias:")
            print("  1. Mejorar iluminación/contraste de la imagen")
            print("  2. Aumentar upscale_factor en config/settings.yaml")
            print("  3. Verificar que el área capturada contiene solo cédulas legibles")

    except Exception as e:
        print()
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
