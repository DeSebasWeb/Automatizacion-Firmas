"""
Script de diagnóstico para ver las posiciones exactas de las palabras detectadas.

Esto ayuda a entender por qué los nombres no se están agrupando correctamente.
"""

import sys
from pathlib import Path
from PIL import Image
import io

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.config import YAMLConfig
from src.infrastructure.ocr.google_vision_adapter import GoogleVisionAdapter


def main():
    """Función principal."""
    print("=" * 80)
    print("DIAGNÓSTICO: Posiciones de palabras detectadas")
    print("=" * 80)
    print()

    # Cargar configuración
    config = YAMLConfig('config/settings.yaml')

    # Crear adapter de Google Vision
    ocr = GoogleVisionAdapter(config)

    # Cargar imagen
    test_image_path = input("Ingresa la ruta de la imagen: ").strip().strip('"').strip("'")

    try:
        image = Image.open(test_image_path)
        print(f"✓ Imagen cargada: {image.size}")
        image.load()

        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
    except Exception as e:
        print(f"✗ Error: {e}")
        return

    # Preprocesar
    processed = ocr.preprocess_image(image)

    # Llamar a Google Vision
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

    # Extraer palabras con coordenadas
    words = ocr._extract_text_blocks_with_positions(response)

    print(f"\n✓ Total palabras detectadas: {len(words)}\n")

    # Mostrar las primeras 30 palabras con coordenadas
    print("PALABRAS DETECTADAS (primeras 30):")
    print("-" * 80)
    for i, word in enumerate(words[:30], 1):
        print(f"[{i:2d}] '{word['text']:20s}' x={word['x']:4.0f} y={word['y']:4.0f} "
              f"w={word['width']:3.0f} h={word['height']:2.0f}")

    print("\n" + "=" * 80)
    print("ANÁLISIS DE AGRUPAMIENTO")
    print("=" * 80)

    # Analizar distancias entre palabras consecutivas que parecen nombres
    nombre_words = [w for w in words if w['text'].isalpha() and len(w['text']) >= 4]

    print(f"\nPalabras que parecen nombres: {len(nombre_words)}\n")

    for i in range(min(10, len(nombre_words) - 1)):
        w1 = nombre_words[i]
        w2 = nombre_words[i + 1]

        # Calcular distancias
        v_gap = abs(w2['y'] - w1['y'])
        h_gap = w2['x'] - (w1['x'] + w1['width'])

        print(f"{w1['text']:15s} → {w2['text']:15s}")
        print(f"  V_gap: {v_gap:4.0f}px | H_gap: {h_gap:4.0f}px", end="")

        # ¿Se agruparían con los umbrales actuales?
        if v_gap > 80 or h_gap > 400:
            print(" → SEPARADOS ❌")
        else:
            print(" → AGRUPADOS ✓")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
