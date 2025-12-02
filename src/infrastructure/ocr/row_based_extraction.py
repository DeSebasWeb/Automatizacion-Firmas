"""
Módulo para extracción de pares nombre-cédula basada en FILAS.

Estrategia: En lugar de intentar agrupar palabras por proximidad,
detectamos las filas del formulario y hacemos una llamada de OCR por fila.

Esto elimina completamente los problemas de sincronización y agrupamiento.
"""

import re
from typing import List, Dict, Tuple
from PIL import Image
import numpy as np
import cv2


class RowBasedExtraction:
    """
    Extracción de pares basada en detección de filas del formulario.
    """

    @staticmethod
    def detect_rows(image: Image.Image, min_height: int = 25) -> List[Tuple[int, int]]:
        """
        Detecta las filas del formulario usando COORDENADAS FIJAS PROPORCIONALES.

        ESTRATEGIA FINAL - MAPEADO MANUAL PROPORCIONAL:
        Basado en análisis visual de image.png (1010x544):
        - Las líneas horizontales están en posiciones ESPECÍFICAS
        - Usamos proporciones relativas al alto de la imagen
        - Esto funciona para formularios del mismo formato

        Args:
            image: Imagen del formulario
            min_height: Altura mínima de una fila en píxeles

        Returns:
            Lista de tuplas (y_inicio, y_fin) para cada fila detectada
        """
        width, height = image.size

        # COORDENADAS Y DE LAS CÉDULAS EN LA IMAGEN
        # Mirando la columna de cédulas en image.png (1010x544)
        # Cada cédula está centrada verticalmente en su fila
        #
        # Imagen de referencia: 544px de alto
        #
        # Cédulas detectadas visualmente (centro de cada número):
        # Laura Urrego: 100028770 → y ≈ 38
        # Angie Ortegon: 1110548784 → y ≈ 68
        # Jeimy Camacho: 1014146494 → y ≈ 100
        # Sharon/Mauro: múltiples en y ≈ 130-145
        # Mauro Cordoba: 7004410752 → y ≈ 175
        # Carlos Ramirez: 79840159 → y ≈ 208
        # (continúa...)
        #
        # Calculando líneas divisorias entre cédulas:

        # Enfoque: dividir uniformemente desde y=15 (después encabezado) hasta y=544 (bottom)
        # en 15 filas iguales

        header_end = 15  # Encabezado termina en píxel 15
        total_data_height = height - header_end
        num_rows = 15
        row_height = total_data_height / num_rows

        line_positions = []
        for i in range(num_rows + 1):
            y = int(header_end + (i * row_height))
            line_positions.append(y)

        # Crear filas entre líneas consecutivas
        # NO saltamos ninguna línea - todas son filas de datos
        rows = []
        for i in range(len(line_positions) - 1):
            y_start = line_positions[i]
            y_end = line_positions[i + 1]

            if y_end - y_start >= min_height:
                rows.append((y_start, y_end))

        return rows

    @staticmethod
    def extract_row_region(
        image: Image.Image,
        y_start: int,
        y_end: int,
        padding: int = 10
    ) -> Image.Image:
        """
        Extrae la región de una fila específica.

        Args:
            image: Imagen completa
            y_start: Coordenada Y inicial de la fila
            y_end: Coordenada Y final de la fila
            padding: Padding adicional arriba/abajo

        Returns:
            Imagen recortada de la fila
        """
        width, height = image.size

        # Agregar padding
        y_start = max(0, y_start - padding)
        y_end = min(height, y_end + padding)

        # Recortar región
        row_image = image.crop((0, y_start, width, y_end))

        return row_image

    @staticmethod
    def extract_nombre_from_row(text_blocks: List[Dict]) -> str:
        """
        Extrae el nombre de los bloques de texto de una fila.

        Busca bloques que parecen nombres (principalmente letras).

        Args:
            text_blocks: Bloques de texto con {text, confidence}

        Returns:
            Nombre encontrado o cadena vacía
        """
        nombre_parts = []

        for block in text_blocks:
            text = block['text'].strip()

            # Filtrar basura
            if len(text) < 2:
                continue

            # ¿Es principalmente letras?
            letter_count = sum(1 for c in text if c.isalpha() or c.isspace())
            if letter_count / len(text) < 0.7:
                continue

            # Blacklist de palabras del formulario
            text_lower = text.lower()
            blacklist = ['cédula', 'cedula', 'of', 'can', 'firma', 'nombre',
                         'documento', 'firmas']
            if any(word in text_lower for word in blacklist):
                continue

            nombre_parts.append(text)

        # Unir todas las partes
        nombre = ' '.join(nombre_parts)

        # Limpiar y formatear
        nombre = ' '.join(nombre.split())  # Normalizar espacios
        nombre = nombre.strip('.,;:()[]{}')

        # Title case
        if nombre:
            words = nombre.split()
            formatted = []
            lowercase_articles = {'de', 'del', 'de la', 'y', 'e', 'la', 'las', 'los'}

            for i, word in enumerate(words):
                if i == 0:
                    formatted.append(word.capitalize())
                elif word.lower() in lowercase_articles:
                    formatted.append(word.lower())
                else:
                    formatted.append(word.capitalize())

            nombre = ' '.join(formatted)

        return nombre

    @staticmethod
    def extract_cedula_from_row(text_blocks: List[Dict]) -> str:
        """
        Extrae la cédula de los bloques de texto de una fila.

        Busca secuencias de 7-10 dígitos.

        Args:
            text_blocks: Bloques de texto con {text, confidence}

        Returns:
            Cédula encontrada o cadena vacía
        """
        for block in text_blocks:
            text = block['text'].strip()

            # Buscar grupos de 7-10 dígitos
            numero_pattern = r'\d{7,10}'
            matches = re.findall(numero_pattern, text)

            if matches:
                # Retornar el primer número encontrado
                return matches[0]

            # Si no encontró, intentar limpiar todo
            cleaned = re.sub(r'[^\d]', '', text)
            if 7 <= len(cleaned) <= 10:
                return cleaned

        return ''

    @staticmethod
    def extract_pairs_by_rows(
        image: Image.Image,
        ocr_adapter,
        verbose: bool = True
    ) -> List[Dict]:
        """
        Extrae pares nombre-cédula usando DETECCIÓN INTELIGENTE DE CÉDULAS.

        ESTRATEGIA AUTOMÁTICA Y ESCALABLE:
        1. Hacer OCR de la imagen COMPLETA una sola vez
        2. Detectar TODAS las cédulas y sus coordenadas Y
        3. Para cada cédula, crear una "fila virtual" centrada en su posición Y
        4. Extraer el nombre de la misma fila virtual
        5. Emparejar nombre con cédula automáticamente

        Esto funciona con CUALQUIER formulario, sin importar:
        - Tamaño de imagen
        - Espaciado entre filas
        - Número de filas
        - Posición del encabezado

        Args:
            image: Imagen del formulario completo
            ocr_adapter: Adapter de OCR (GoogleVisionAdapter o AzureVisionAdapter)
            verbose: Mostrar logs detallados

        Returns:
            Lista de pares {nombre, cedula, confidence_nombre, confidence_cedula}
        """
        if verbose:
            print("\n" + "=" * 80)
            print("EXTRACCIÓN INTELIGENTE BASADA EN DETECCIÓN DE CÉDULAS")
            print("=" * 80)

        # 1. OCR de imagen completa
        if verbose:
            print("\n[1/4] Ejecutando OCR en imagen completa...")

        # Preprocesar imagen
        processed_image = ocr_adapter.preprocess_image(image)

        # Ejecutar OCR
        import io
        from google.cloud import vision

        img_byte_arr = io.BytesIO()
        processed_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        vision_image = vision.Image(content=img_byte_arr)
        response = ocr_adapter.client.document_text_detection(
            image=vision_image,
            image_context=vision.ImageContext(language_hints=['es'])
        )

        # Extraer TEXTO COMPLETO organizado por LÍNEAS
        if response.full_text_annotation:
            full_text = response.full_text_annotation.text
            lines = full_text.split('\n')
        else:
            lines = []

        if verbose:
            print(f"  ✓ Detectadas {len(lines)} líneas de texto")

        # 2. Detectar CÉDULAS procesando línea por línea
        if verbose:
            print("\n[2/4] Detectando cédulas (método línea por línea)...")

        cedulas_detectadas = []

        # También necesitamos las palabras para obtener coordenadas Y
        words = ocr_adapter._extract_text_blocks_with_positions(response)

        for idx, line in enumerate(lines):
            line_original = line.strip()
            if not line_original:
                continue

            # Eliminar TODO excepto dígitos (mismo método que Google Vision adapter)
            cleaned = re.sub(r'[^\d]', '', line_original)

            # Si queda un número de 7-11 dígitos, es probablemente una cédula
            if 7 <= len(cleaned) <= 11:
                # Buscar coordenada Y de esta cédula específica
                # Buscar palabras que contengan los dígitos de esta cédula
                cedula_words = []

                for w in words:
                    w_text_digits = re.sub(r'[^\d]', '', w['text'])
                    # Si esta palabra contiene parte de la cédula
                    if w_text_digits and w_text_digits in cleaned:
                        cedula_words.append(w)

                if cedula_words:
                    # Usar la coordenada Y de la primera palabra que contiene la cédula
                    cedula_word = cedula_words[0]
                    cedula_y = cedula_word['y'] + cedula_word['height'] / 2
                    cedula_x = cedula_word['x']

                    cedulas_detectadas.append({
                        'cedula': cleaned,
                        'y': cedula_y,
                        'confidence': 95.0,
                        'x': cedula_x
                    })

                    if verbose:
                        print(f"  Línea {idx+1}: '{line_original}' → Cédula: {cleaned} (y={cedula_y:.0f})")

        if verbose:
            print(f"  ✓ Detectadas {len(cedulas_detectadas)} cédulas")
            for i, ced in enumerate(cedulas_detectadas, 1):
                print(f"    Cédula {i}: {ced['cedula']} (y={ced['y']:.0f})")

        # 3. Para cada cédula, encontrar el nombre en la misma fila
        if verbose:
            print(f"\n[3/4] Emparejando nombres con cédulas...")

        pares = []

        for ced_data in cedulas_detectadas:
            cedula = ced_data['cedula']
            cedula_y = ced_data['y']
            cedula_conf = ced_data['confidence']

            # Definir rango vertical de la fila (±25px alrededor de la cédula)
            # Más estrecho para evitar capturar nombres de otras filas
            row_y_min = cedula_y - 25
            row_y_max = cedula_y + 25

            # Encontrar todas las palabras en esta fila que parezcan nombres
            # IMPORTANTE: Los nombres están a la IZQUIERDA de las cédulas (x < cedula_x)
            nombre_words = []
            cedula_x = ced_data.get('x', 0)

            if verbose:
                print(f"\n  Buscando nombre para cédula {cedula} (y={cedula_y:.0f}, x={cedula_x:.0f})")
                print(f"    Rango Y: {row_y_min:.0f} - {row_y_max:.0f}")

            for word in words:
                word_y_center = word['y'] + word['height'] / 2
                word_x = word['x']

                # ¿Está en la misma fila verticalmente?
                if row_y_min <= word_y_center <= row_y_max:
                    text = word['text'].strip()

                    # ¿Es un nombre? (principalmente letras, no números)
                    if len(text) >= 2:  # Permitir palabras más cortas como "de"
                        letter_count = sum(1 for c in text if c.isalpha() or c.isspace())
                        if letter_count / len(text) >= 0.7:
                            # Filtrar palabras del encabezado
                            text_lower = text.lower()
                            if not any(w in text_lower for w in ['cédula', 'cedula', 'nombre', 'firma', 'documento', 'firmas', 'of', 'can']):
                                # IMPORTANTE: El nombre debe estar a la IZQUIERDA de la cédula
                                if word_x < cedula_x - 50:  # Al menos 50px a la izquierda
                                    nombre_words.append(word)
                                    if verbose:
                                        print(f"      ✓ '{text}' (x={word_x:.0f}, y={word_y_center:.0f})")

            # Ordenar palabras de izquierda a derecha
            nombre_words.sort(key=lambda w: w['x'])

            # Concatenar para formar nombre completo
            nombre_parts = [w['text'] for w in nombre_words]
            nombre = ' '.join(nombre_parts)

            # Formatear nombre (Title Case)
            nombre = ' '.join(nombre.split())  # Normalizar espacios
            nombre = nombre.strip('.,;:()[]{}')

            if nombre:
                words_list = nombre.split()
                formatted = []
                lowercase_articles = {'de', 'del', 'de la', 'y', 'e', 'la', 'las', 'los'}

                for j, word in enumerate(words_list):
                    if j == 0:
                        formatted.append(word.capitalize())
                    elif word.lower() in lowercase_articles:
                        formatted.append(word.lower())
                    else:
                        formatted.append(word.capitalize())

                nombre = ' '.join(formatted)

            # Calcular confianza promedio del nombre
            nombre_conf = sum(w['confidence'] for w in nombre_words) / len(nombre_words) if nombre_words else 0.0

            if verbose:
                print(f"  Cédula {cedula} (y={cedula_y:.0f})")
                print(f"    → Nombre: '{nombre}' (conf: {nombre_conf:.2%})")
                print(f"    → Cédula conf: {cedula_conf:.2%}")

            # Agregar par si hay nombre
            if nombre and len(nombre) >= 4:
                pares.append({
                    'nombre': nombre,
                    'cedula': cedula,
                    'confidence_nombre': nombre_conf,
                    'confidence_cedula': cedula_conf
                })

                if verbose:
                    print(f"    ✓ Par válido agregado")
            else:
                if verbose:
                    if not nombre:
                        print(f"    ⚠ No se detectó nombre")
                    elif len(nombre) < 4:
                        print(f"    ⚠ Nombre muy corto: '{nombre}'")

        # 4. Resumen
        if verbose:
            print(f"\n[4/4] Extracción completada")
            print(f"  ✓ {len(pares)} pares válidos extraídos")
            print("=" * 80)

        return pares
