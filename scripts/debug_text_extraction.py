"""
Script de diagnóstico para ver QUÉ texto está detectando el OCR.

Muestra TODOS los bloques de texto sin filtrar para debugging.
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
    """Función principal."""
    print("=" * 80)
    print("DIAGNÓSTICO: ¿QUÉ TEXTO DETECTA EL OCR?")
    print("=" * 80)
    print()

    # Cargar configuración
    config = YAMLConfig('config/settings.yaml')

    # Cambiar temporalmente a google_vision para ver qué detecta
    original_provider = config.get('ocr.provider')

    print("Probando con Google Vision...")
    from src.infrastructure.ocr.google_vision_adapter import GoogleVisionAdapter

    try:
        ocr = GoogleVisionAdapter(config)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Solicitar imagen
    test_image_path = input("\nIngresa la ruta de la imagen: ").strip().strip('"').strip("'")

    try:
        image = Image.open(test_image_path)
        print(f"✓ Imagen cargada: {image.size}")
        image.load()

        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
    except Exception as e:
        print(f"✗ Error: {e}")
        return

    print("\n" + "=" * 80)
    print("EXTRAYENDO TODO EL TEXTO (SIN FILTROS)")
    print("=" * 80)

    # Preprocesar
    processed = ocr.preprocess_image(image)

    # Llamar a Google Vision
    import io
    from google.cloud import vision

    img_byte_arr = io.BytesIO()
    processed.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    vision_image = vision.Image(content=img_byte_arr)
    image_context = vision.ImageContext(language_hints=['es'])

    response = ocr.client.document_text_detection(
        image=vision_image,
        image_context=image_context
    )

    if response.error.message:
        print(f"Error: {response.error.message}")
        return

    # Extraer bloques
    blocks = ocr._extract_text_blocks_with_positions(response)

    print(f"\n✓ Total bloques detectados: {len(blocks)}\n")

    if not blocks:
        print("⚠ NO SE DETECTÓ NINGÚN TEXTO")
        print("\nPosibles causas:")
        print("  - Imagen completamente en blanco")
        print("  - Texto demasiado borroso")
        print("  - Imagen corrupta")
        return

    # Mostrar TODOS los bloques
    print("BLOQUES DETECTADOS:")
    print("-" * 80)
    for i, block in enumerate(blocks, 1):
        print(f"\n[{i}] Texto: '{block['text']}'")
        print(f"    Posición: x={block['x']:.0f}, y={block['y']:.0f}")
        print(f"    Tamaño: w={block['width']:.0f}, h={block['height']:.0f}")
        print(f"    Confianza: {block['confidence']:.2%}")

        # Analizar qué tipo de contenido es
        text = block['text']

        # ¿Es número?
        if text.replace(' ', '').replace('.', '').replace(',', '').isdigit():
            print(f"    → Parece NÚMERO")

        # ¿Es principalmente letras?
        elif sum(c.isalpha() or c.isspace() for c in text) / len(text) > 0.7:
            print(f"    → Parece TEXTO/NOMBRE")

        # ¿Es mixto?
        else:
            print(f"    → Mixto (letras + números)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
