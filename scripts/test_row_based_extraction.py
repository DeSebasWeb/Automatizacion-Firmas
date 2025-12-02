"""
Script de prueba para extracción basada en FILAS.

Este nuevo enfoque hace una llamada de OCR por cada fila del formulario,
eliminando completamente los problemas de sincronización y agrupamiento.
"""

import sys
from pathlib import Path
from PIL import Image

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.ocr.google_vision_adapter import GoogleVisionAdapter
from src.infrastructure.ocr.row_based_extraction import RowBasedExtraction
from src.shared.config import YAMLConfig


def main():
    """Función principal del script de prueba."""
    print("=" * 80)
    print("SCRIPT DE PRUEBA - EXTRACCIÓN BASADA EN FILAS")
    print("=" * 80)
    print()
    print("Este enfoque:")
    print("  1. Detecta las filas del formulario automáticamente")
    print("  2. Hace una llamada de OCR por cada fila (15 llamadas)")
    print("  3. Extrae nombre + cédula de cada fila sin problemas de sincronización")
    print()

    # Cargar configuración
    try:
        config = YAMLConfig('config/settings.yaml')
        print("✓ Configuración cargada correctamente")
    except Exception as e:
        print(f"✗ Error cargando configuración: {e}")
        return

    # Crear OCR adapter (solo Google Vision por ahora)
    try:
        ocr = GoogleVisionAdapter(config)
        print(f"✓ Google Vision adapter creado")
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
            return

        # Convertir a RGB si es necesario
        if image.mode not in ('RGB', 'L'):
            print(f"  Convirtiendo de {image.mode} a RGB...")
            image = image.convert('RGB')

        print()
    except Exception as e:
        print(f"✗ Error cargando imagen: {e}")
        return

    # Extraer pares usando el enfoque basado en filas
    print("=" * 80)
    print("INICIANDO EXTRACCIÓN BASADA EN FILAS")
    print("=" * 80)

    try:
        pares = RowBasedExtraction.extract_pairs_by_rows(
            image=image,
            ocr_adapter=ocr,
            verbose=True
        )

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
            print("  - No se detectaron filas en el formulario")
            print("  - Las filas no contienen nombres o cédulas legibles")
            print("  - El formulario tiene un formato muy diferente al esperado")

    except Exception as e:
        print()
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
