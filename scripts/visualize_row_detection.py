"""
Script para VISUALIZAR la detección de líneas horizontales.
Guarda una imagen mostrando las líneas detectadas.
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import cv2

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))


def detect_horizontal_lines_visual(image_path: str):
    """Detecta líneas horizontales y visualiza el resultado."""

    # Cargar imagen
    image = Image.open(image_path)
    if image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')

    print(f"✓ Imagen cargada: {image.size}")

    # Convertir a escala de grises
    img_gray = np.array(image.convert('L'))
    height, width = img_gray.shape

    print(f"✓ Dimensiones: {width}x{height}")
    print()

    # ===================================================================
    # MÉTODO 1: Binarización + Kernel Morfológico
    # ===================================================================
    print("=" * 70)
    print("MÉTODO 1: Detección con Kernel Morfológico")
    print("=" * 70)

    # Binarización adaptativa
    binary = cv2.adaptiveThreshold(
        img_gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2
    )

    # Kernel horizontal
    kernel_length = width // 3
    print(f"Kernel horizontal: {kernel_length}x1 px")
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))

    # Extraer líneas horizontales
    horizontal_lines_img = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

    # Proyección horizontal
    horizontal_projection = np.sum(horizontal_lines_img, axis=1)

    # Normalizar
    max_val = np.max(horizontal_projection)
    print(f"Proyección máxima: {max_val}")

    # Encontrar picos
    threshold_line = max_val * 0.3
    print(f"Threshold (30%): {threshold_line}")

    line_rows = []
    for y in range(height):
        if horizontal_projection[y] > threshold_line:
            line_rows.append(y)

    print(f"Píxeles con líneas detectados: {len(line_rows)}")

    # Agrupar líneas consecutivas
    line_positions = []
    if line_rows:
        start = line_rows[0]
        for i in range(1, len(line_rows)):
            if line_rows[i] - line_rows[i-1] > 5:
                line_positions.append((start + line_rows[i-1]) // 2)
                start = line_rows[i]
        line_positions.append((start + line_rows[-1]) // 2)

    print(f"✓ Líneas detectadas: {len(line_positions)}")
    print()
    for i, y in enumerate(line_positions, 1):
        print(f"  Línea {i}: y={y}")

    # ===================================================================
    # VISUALIZACIÓN
    # ===================================================================
    print()
    print("=" * 70)
    print("GENERANDO VISUALIZACIÓN")
    print("=" * 70)

    # Crear copia para dibujar
    vis_image = image.copy()
    draw = ImageDraw.Draw(vis_image)

    # Dibujar líneas detectadas en ROJO
    for y in line_positions:
        draw.line([(0, y), (width, y)], fill=(255, 0, 0), width=3)

    # Dibujar filas entre líneas en VERDE (semi-transparente)
    for i in range(len(line_positions) - 1):
        y_start = line_positions[i]
        y_end = line_positions[i + 1]
        y_mid = (y_start + y_end) // 2

        # Línea verde en el medio de cada fila
        draw.line([(0, y_mid), (width, y_mid)], fill=(0, 255, 0), width=1)

        # Texto con número de fila
        draw.text((10, y_mid - 10), f"Fila {i+1}", fill=(0, 255, 0))

    # Guardar
    output_path = "temp/row_detection_visualization.png"
    Path("temp").mkdir(exist_ok=True)
    vis_image.save(output_path)

    print(f"✓ Visualización guardada: {output_path}")
    print()
    print("=" * 70)
    print("ABRE LA IMAGEN PARA VER LAS LÍNEAS DETECTADAS")
    print("Líneas ROJAS = Separadores detectados")
    print("Líneas VERDES = Centro de cada fila")
    print("=" * 70)

    # También guardar la imagen de proyección
    projection_img = (horizontal_lines_img).astype(np.uint8)
    cv2.imwrite("temp/horizontal_lines_morphology.png", projection_img)
    print(f"✓ Imagen morfológica guardada: temp/horizontal_lines_morphology.png")


if __name__ == "__main__":
    print("=" * 70)
    print("VISUALIZADOR DE DETECCIÓN DE FILAS")
    print("=" * 70)
    print()

    image_path = input("Ruta de la imagen: ").strip().strip('"').strip("'")

    try:
        detect_horizontal_lines_visual(image_path)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
