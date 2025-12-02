"""
Script de prueba para extraer pares nombre-cédula con proximidad espacial.

Este script prueba el nuevo sistema de extracción de pares que usa:
- Post-procesamiento inteligente de nombres y cédulas
- Emparejamiento por proximidad espacial (NO por índice)
- Ensemble de Google + Azure con votación por dígito
"""

import sys
from pathlib import Path
from PIL import Image

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ocr import create_ocr_adapter
from src.shared.config import YAMLConfig


def main():
    """Función principal del script de prueba."""
    print("=" * 80)
    print("SCRIPT DE PRUEBA - EXTRACCIÓN DE PARES NOMBRE-CÉDULA")
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

        # Verificar si la imagen está corrupta
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

        # Convertir a RGB si es necesario
        if image.mode not in ('RGB', 'L'):
            print(f"  Convirtiendo de {image.mode} a RGB...")
            image = image.convert('RGB')

        print()
    except Exception as e:
        print(f"✗ Error cargando imagen: {e}")
        return

    # Extraer pares nombre-cédula
    print("=" * 80)
    print("INICIANDO EXTRACCIÓN DE PARES")
    print("=" * 80)
    print()

    try:
        pares = ocr.extract_name_cedula_pairs(image)

        print()
        print("=" * 80)
        print("RESULTADOS FINALES")
        print("=" * 80)

        if pares:
            print(f"✓ {len(pares)} par(es) extraído(s):")
            print()
            for i, par in enumerate(pares, 1):
                print(f"{i}. {par['nombre']}")
                print(f"   Cédula: {par['cedula']}")
                print(f"   Confianza nombre: {par['confidence_nombre']:.1%}")
                print(f"   Confianza cédula: {par['confidence_cedula']:.1%}")
                print()
        else:
            print("✗ No se extrajo ningún par")
            print()
            print("Posibles razones:")
            print("  - No se detectaron nombres o cédulas")
            print("  - Los nombres y cédulas están muy separados (> 300px)")
            print("  - Confianzas muy bajas")
            print()
            print("Sugerencias:")
            print("  1. Verificar que la imagen tenga nombres Y cédulas visibles")
            print("  2. Asegurar buena calidad de imagen (iluminación, contraste)")
            print("  3. Revisar logs anteriores para ver qué se detectó")

    except Exception as e:
        print()
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
