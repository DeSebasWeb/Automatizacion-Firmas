"""
Módulo para emparejamiento espacial de nombres y cédulas.

Este módulo implementa estrategias de post-procesamiento y emparejamiento
basadas en proximidad espacial en lugar de índices.
"""

import re
import math
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher


class SpatialPairing:
    """
    Clase utilitaria para emparejar nombres y cédulas por proximidad espacial.
    """

    @staticmethod
    def filter_nombres(blocks: List[Dict]) -> List[Dict]:
        """
        Filtra bloques que son nombres usando CLUSTERING ESPACIAL.

        Nueva estrategia:
        1. Filtrar palabras que parecen nombres
        2. Agrupar palabras cercanas en clusters (mismo nombre)
        3. Cada cluster = un nombre completo
        4. Ordenar palabras dentro del cluster de izquierda a derecha

        Args:
            blocks: Lista de bloques con {text, x, y, width, height, confidence}

        Returns:
            Lista de bloques que son nombres, post-procesados
        """
        # 1. Filtrar palabras que parecen nombres
        palabra_blocks = [b for b in blocks if SpatialPairing._is_nombre_pattern(b['text'])]

        if not palabra_blocks:
            return []

        # 2. Clustering espacial - agrupar palabras cercanas
        clusters = []
        used = set()

        for i, block in enumerate(palabra_blocks):
            if i in used:
                continue

            # Iniciar nuevo cluster con este bloque
            cluster = [block]
            used.add(i)

            # Buscar palabras cercanas recursivamente
            queue = [block]
            while queue:
                current = queue.pop(0)

                for j, other in enumerate(palabra_blocks):
                    if j in used:
                        continue

                    # Calcular distancia entre current y other
                    v_dist = abs(other['y'] - current['y'])
                    h_dist = abs(other['x'] - current['x'])

                    # ¿Están cerca? (mismo cluster/nombre)
                    # Criterio: misma fila (< 60px vertical) Y cerca horizontal (< 350px)
                    if v_dist < 60 and h_dist < 350:
                        cluster.append(other)
                        used.add(j)
                        queue.append(other)  # Buscar vecinos de este también

            clusters.append(cluster)

        # 3. Mergear cada cluster en un solo nombre
        nombres = []
        for cluster in clusters:
            # Ordenar palabras del cluster de izquierda a derecha
            cluster_sorted = sorted(cluster, key=lambda b: b['x'])
            merged = SpatialPairing._merge_nombre_blocks(cluster_sorted)
            if merged:
                nombres.append(merged)

        return nombres

    @staticmethod
    def filter_cedulas(blocks: List[Dict]) -> List[Dict]:
        """
        Filtra bloques que son cédulas.

        Post-procesamiento aplicado:
        1. Identificar si es cédula (números, 7-10 dígitos)
        2. Si un bloque tiene MÚLTIPLES cédulas, separarlas
        3. Limpiar (remover puntos, espacios)
        4. Asignar coordenadas proporcionales

        Args:
            blocks: Lista de bloques con texto y coordenadas

        Returns:
            Lista de bloques que son cédulas, post-procesadas
        """
        cedulas = []

        for block in blocks:
            text = block['text']

            # Buscar todos los grupos de 7-10 dígitos consecutivos
            # Esto separa múltiples cédulas que Google Vision agrupa en un solo bloque
            numero_pattern = r'\d{7,10}'
            matches = re.finditer(numero_pattern, text)

            found_any = False
            for match in matches:
                cedula_text = match.group()
                found_any = True

                # Calcular posición aproximada dentro del bloque
                # Si hay múltiples cédulas en un bloque vertical, distribuirlas
                match_start = match.start()
                text_before = text[:match_start]

                # Estimar offset vertical basado en posición en el texto
                # Asumiendo distribución vertical uniforme
                relative_position = match_start / len(text) if len(text) > 0 else 0
                estimated_y_offset = block['height'] * relative_position

                cedulas.append({
                    'text': cedula_text,
                    'x': block['x'],
                    'y': block['y'] + estimated_y_offset,
                    'width': block['width'],
                    'height': block['height'] / max(1, len(list(re.finditer(numero_pattern, text)))),
                    'confidence': block['confidence']
                })

            # Si no encontró ninguna cédula con el patrón, intentar limpiar todo el texto
            if not found_any:
                cleaned = re.sub(r'[^\d]', '', text)
                if 7 <= len(cleaned) <= 10:
                    cedulas.append({
                        'text': cleaned,
                        'x': block['x'],
                        'y': block['y'],
                        'width': block['width'],
                        'height': block['height'],
                        'confidence': block['confidence']
                    })

        return cedulas

    @staticmethod
    def _is_nombre_pattern(text: str) -> bool:
        """
        Determina si un texto parece ser parte de un nombre.

        Criterios:
        - Principalmente letras (> 70%)
        - No es solo números
        - Puede tener espacios, acentos, ñ
        - NO contiene palabras del encabezado del formulario
        """
        if not text or len(text) < 2:
            return False

        text_lower = text.lower()

        # Filtrar palabras del formulario/encabezado que NO son nombres
        blacklist = ['cédula', 'cedula', 'of', 'can', 'firma', 'nombre',
                     'documento', 'hicx6', 'hicx', 'firmas']
        if any(word in text_lower for word in blacklist):
            return False

        # Contar letras
        letter_count = sum(1 for c in text if c.isalpha() or c.isspace())
        letter_ratio = letter_count / len(text) if text else 0

        # Debe ser principalmente letras
        if letter_ratio < 0.7:
            return False

        # No debe ser solo números
        if text.replace(" ", "").isdigit():
            return False

        return True

    @staticmethod
    def _merge_nombre_blocks(blocks: List[Dict]) -> Optional[Dict]:
        """
        Combina múltiples bloques que forman un nombre completo.

        Ejemplo:
          Block 1: "Juan Sebastian" (x=100, y=100)
          Block 2: "Lopez Hernandez" (x=100, y=130)
          → Merged: "Juan Sebastian Lopez Hernandez" (x=100, y=100, height=60)

        Args:
            blocks: Lista de bloques consecutivos que forman un nombre

        Returns:
            Bloque merged o None si no es válido
        """
        if not blocks:
            return None

        # Concatenar textos
        full_text = ' '.join(b['text'] for b in blocks)
        full_text = ' '.join(full_text.split())  # Normalizar espacios

        # Validar que es un nombre completo válido
        if not SpatialPairing._is_valid_nombre(full_text):
            return None

        # Formatear (Title Case)
        formatted_text = SpatialPairing._format_nombre(full_text)

        # Calcular bounding box combinado
        min_x = min(b['x'] for b in blocks)
        min_y = min(b['y'] for b in blocks)
        max_x = max(b['x'] + b['width'] for b in blocks)
        max_y = max(b['y'] + b['height'] for b in blocks)

        # Confianza promedio
        avg_confidence = sum(b['confidence'] for b in blocks) / len(blocks)

        return {
            'text': formatted_text,
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x,
            'height': max_y - min_y,
            'confidence': avg_confidence
        }

    @staticmethod
    def _is_valid_nombre(text: str) -> bool:
        """
        Verifica si es un nombre completo válido.

        Criterios RELAJADOS para permitir nombres cortos:
        - Longitud >= 4 caracteres (permite "Mauro", "Jeimy")
        - Si tiene >= 2 palabras: nombre + apellido (mejor caso)
        - Si tiene 1 palabra: debe tener >= 4 letras (nombre simple)
        - Cada palabra >= 2 caracteres (evita iniciales sueltas)
        """
        text = text.strip()

        # Remover puntos al final que OCR agrega erróneamente
        text = text.rstrip('.')

        if len(text) < 4:
            return False

        words = [w for w in text.split() if len(w) >= 2]  # Filtrar palabras muy cortas

        if len(words) < 1:
            return False

        # Aceptar si:
        # - Tiene 2+ palabras (nombre completo) O
        # - Tiene 1 palabra con >= 4 letras (nombre simple como "Mauro")
        if len(words) >= 2:
            return True

        if len(words) == 1 and len(words[0]) >= 4:
            return True

        return False

    @staticmethod
    def _format_nombre(text: str) -> str:
        """
        Formatea un nombre con Title Case.

        Respeta:
        - Nombres compuestos: "Juan Sebastian"
        - Artículos: "de", "del", "de la"
        - Limpia puntos y símbolos erróneamente detectados por OCR
        """
        # Remover puntos al final (OCR error común)
        text = text.strip().rstrip('.')

        # Filtrar palabras muy cortas (< 2 chars) que suelen ser ruido
        words = [w for w in text.split() if len(w) >= 2]
        formatted = []

        lowercase_articles = {'de', 'del', 'de la', 'y', 'e', 'la', 'las', 'los'}

        for i, word in enumerate(words):
            # Limpiar caracteres no alfabéticos al inicio/final (excepto acentos)
            word_clean = word.strip('.,;:()[]{}')

            if not word_clean:
                continue

            # Primera palabra siempre mayúscula
            if i == 0:
                formatted.append(word_clean.capitalize())
            # Artículos en minúscula (excepto al inicio)
            elif word_clean.lower() in lowercase_articles:
                formatted.append(word_clean.lower())
            # Resto con mayúscula inicial
            else:
                formatted.append(word_clean.capitalize())

        return ' '.join(formatted)

    @staticmethod
    def pair_by_proximity(
        nombres: List[Dict],
        cedulas: List[Dict],
        max_distance: int = 2000,  # Aumentado para formularios con columnas muy separadas
        verbose: bool = True
    ) -> List[Dict]:
        """
        Empareja cada cédula con el nombre MÁS CERCANO espacialmente.

        Estrategia:
        1. Para cada cédula, calcular distancia a todos los nombres
        2. Elegir el nombre con menor distancia
        3. Priorizar proximidad VERTICAL (mismo renglón) con factor 2x
        4. Marcar nombres como usados para evitar duplicados

        Args:
            nombres: Lista de bloques de nombres con coordenadas
            cedulas: Lista de bloques de cédulas con coordenadas
            max_distance: Distancia máxima en píxeles para emparejar
            verbose: Si mostrar logging detallado

        Returns:
            Lista de pares nombre-cédula
        """
        pares = []
        used_nombres = set()

        # Ordenar cédulas por posición vertical (top → bottom)
        cedulas_sorted = sorted(cedulas, key=lambda c: c['y'])

        for cedula in cedulas_sorted:
            # Centro de la cédula
            cedula_cx = cedula['x'] + cedula['width'] / 2
            cedula_cy = cedula['y'] + cedula['height'] / 2

            best_nombre = None
            best_distance = float('inf')

            for nombre in nombres:
                # Skip si ya fue usado
                if nombre['text'] in used_nombres:
                    continue

                # Centro del nombre
                nombre_cx = nombre['x'] + nombre['width'] / 2
                nombre_cy = nombre['y'] + nombre['height'] / 2

                # Calcular distancia
                # IMPORTANTE: Dar más peso a la distancia vertical (factor 2x)
                # porque en formularios, nombre y cédula están en el mismo renglón
                dx = cedula_cx - nombre_cx
                dy = (cedula_cy - nombre_cy) * 2  # Peso 2x en Y

                distance = math.sqrt(dx**2 + dy**2)

                # Penalizar si el nombre está MUY ABAJO de la cédula
                # (normalmente el nombre va antes/arriba de la cédula)
                if nombre_cy > cedula_cy + 50:  # Nombre 50px+ abajo
                    distance *= 2  # Penalizar 2x

                # Penalizar si están MUY LEJOS horizontalmente
                # (mismo renglón implica distancia horizontal razonable)
                if abs(dx) > 500:  # Más de 500px de separación horizontal
                    distance *= 1.5  # Penalizar 1.5x

                if distance < best_distance:
                    best_distance = distance
                    best_nombre = nombre

            # Empareja si encontró nombre cercano
            if best_nombre and best_distance < max_distance:
                pares.append({
                    'nombre': best_nombre['text'],
                    'cedula': cedula['text'],
                    'confidence_nombre': best_nombre['confidence'],
                    'confidence_cedula': cedula['confidence'],
                    'distance_pixels': int(best_distance),
                    'nombre_coords': {
                        'x': best_nombre['x'],
                        'y': best_nombre['y']
                    },
                    'cedula_coords': {
                        'x': cedula['x'],
                        'y': cedula['y']
                    }
                })

                used_nombres.add(best_nombre['text'])

                if verbose:
                    print(f"✓ Emparejado: '{best_nombre['text']}' ↔ '{cedula['text']}' "
                          f"(distancia: {best_distance:.0f}px)")
            else:
                if verbose:
                    print(f"⚠ Cédula '{cedula['text']}' sin nombre cercano "
                          f"(distancia mínima: {best_distance:.0f}px)")

        return pares

    @staticmethod
    def match_pairs(
        google_pairs: List[Dict],
        azure_pairs: List[Dict],
        min_similarity: float = 0.6
    ) -> List[Tuple[Dict, Dict]]:
        """
        Empareja pares similares entre Google y Azure.

        Usa similitud de cédulas (más confiable que nombres).

        Args:
            google_pairs: Pares extraídos por Google Vision
            azure_pairs: Pares extraídos por Azure Vision
            min_similarity: Similitud mínima para emparejar (0-1)

        Returns:
            Lista de tuplas (google_pair, azure_pair)
        """
        matched = []
        used_azure = set()

        for g_pair in google_pairs:
            best_match = None
            best_similarity = 0.0
            best_idx = None

            for a_idx, a_pair in enumerate(azure_pairs):
                if a_idx in used_azure:
                    continue

                # Similitud de cédulas (peso 80%)
                cedula_sim = SequenceMatcher(
                    None,
                    g_pair['cedula'],
                    a_pair['cedula']
                ).ratio()

                # Similitud de nombres (peso 20%)
                nombre_sim = SequenceMatcher(
                    None,
                    g_pair['nombre'].lower(),
                    a_pair['nombre'].lower()
                ).ratio()

                similarity = (cedula_sim * 0.8) + (nombre_sim * 0.2)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = a_pair
                    best_idx = a_idx

            if best_match and best_similarity >= min_similarity:
                matched.append((g_pair, best_match))
                used_azure.add(best_idx)

        return matched
