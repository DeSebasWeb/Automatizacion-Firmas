"""Implementación de OCR usando Google Cloud Vision API - Óptimo para escritura manual."""
import re
import os
from PIL import Image
from typing import List, Dict
import io

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("ADVERTENCIA: Google Cloud Vision no está instalado. Instalar con: pip install google-cloud-vision")

from ...domain.entities import CedulaRecord, RowData
from ...domain.ports import OCRPort, ConfigPort
from ..image import ImagePreprocessor


class GoogleVisionAdapter(OCRPort):
    """
    Implementación de OCR usando Google Cloud Vision API con preprocesamiento avanzado.

    Google Cloud Vision es:
    - Estado del arte para escritura manual
    - Extremadamente preciso con números manuscritos
    - 1,000 detecciones gratis al mes
    - Después: $1.50 por cada 1,000 detecciones

    Para 15 cédulas por imagen:
    - 1,000 imágenes gratis = 15,000 cédulas gratis/mes

    MEJORAS DE PREPROCESAMIENTO:
    - Upscaling 3x para mejor resolución (distingue 1 vs 7)
    - Reducción de ruido con fastNlMeansDenoising
    - Aumento de contraste adaptativo (CLAHE)
    - Sharpening para nitidez
    - Binarización método Otsu
    - Operaciones morfológicas para limpieza

    Attributes:
        config: Servicio de configuración
        client: Cliente de Google Cloud Vision
        preprocessor: Pipeline de preprocesamiento de imágenes
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el servicio de OCR con Google Cloud Vision.

        Args:
            config: Servicio de configuración
        """
        if not GOOGLE_VISION_AVAILABLE:
            raise ImportError("Google Cloud Vision no está instalado. Instalar con: pip install google-cloud-vision")

        self.config = config
        self.client = None
        self.last_raw_response = None  # Para guardar respuesta completa y extraer confianza por dígito

        # Inicializar preprocesador con configuración
        preprocessing_config = self.config.get('image_preprocessing', {})
        self.preprocessor = ImagePreprocessor(preprocessing_config)

        self._initialize_ocr()

    def _initialize_ocr(self) -> None:
        """Inicializa Google Cloud Vision API."""
        print("DEBUG Google Vision: Inicializando cliente...")

        try:
            # Intentar crear cliente con Application Default Credentials (ADC)
            # ADC busca credenciales en este orden:
            # 1. GOOGLE_APPLICATION_CREDENTIALS (archivo JSON)
            # 2. gcloud auth application-default login (credenciales de usuario)
            # 3. Compute Engine/App Engine/Cloud Run (credenciales de servicio)

            self.client = vision.ImageAnnotatorClient()

            print("✓ Google Cloud Vision inicializado correctamente")
            print("✓ Usando Application Default Credentials (ADC)")
            print("✓ Modelo optimizado para escritura manual")

        except Exception as e:
            print(f"ERROR Google Vision: No se pudo inicializar: {e}")
            print("\n💡 Soluciones:")
            print("   1. Ejecutar: gcloud auth application-default login")
            print("   2. O configurar: GOOGLE_APPLICATION_CREDENTIALS con ruta a JSON")
            print("   3. Asegúrate de habilitar Cloud Vision API en tu proyecto")
            raise

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen para Google Vision usando pipeline robusto.

        Aplica preprocesamiento intensivo para maximizar precisión sin aumentar costos:
        1. Upscaling (3x) - CRÍTICO para distinguir 1 vs 7
        2. Conversión a escala de grises
        3. Reducción de ruido (fastNlMeansDenoising)
        4. Aumento de contraste adaptativo (CLAHE)
        5. Sharpening para nitidez
        6. Binarización método Otsu
        7. Operaciones morfológicas (Close + Open)

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada y optimizada
        """
        print(f"\nDEBUG Google Vision: Imagen original {image.width}x{image.height}")

        # Verificar si el preprocesamiento está habilitado
        if not self.config.get('image_preprocessing.enabled', True):
            print("DEBUG Google Vision: Preprocesamiento deshabilitado, usando imagen original")
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image

        # Aplicar pipeline completo de preprocesamiento
        processed_image = self.preprocessor.preprocess(image)

        # Google Vision requiere RGB, convertir de vuelta si es necesario
        if processed_image.mode != 'RGB':
            processed_image = processed_image.convert('RGB')

        print(f"DEBUG Google Vision: Imagen procesada {processed_image.width}x{processed_image.height}")

        return processed_image

    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen usando Google Cloud Vision.

        Estrategia OPTIMIZADA:
        1. Enviar la imagen COMPLETA a Google Vision (1 SOLA llamada API)
        2. Google Vision detecta automáticamente todas las líneas de texto
        3. Extraer solo números de 6-10 dígitos que sean cédulas válidas

        Esto consume solo 1 petición API en lugar de 15.

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista de registros de cédulas extraídas
        """
        if self.client is None:
            print("ERROR: Google Cloud Vision no está inicializado")
            return []

        print("DEBUG Google Vision: Iniciando extracción...")
        print("DEBUG Google Vision: Enviando imagen completa a API (1 sola llamada)")

        try:
            # Convertir imagen PIL a bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Crear objeto Image de Google Vision
            vision_image = vision.Image(content=img_byte_arr)

            # OPTIMIZACIÓN: Language hints para mejorar precisión en español
            image_context = vision.ImageContext(language_hints=['es'])

            # Llamar a la API - DOCUMENT_TEXT_DETECTION detecta texto línea por línea
            # Esta es la ÚNICA llamada API que hacemos
            print("DEBUG Google Vision: Llamando a DOCUMENT_TEXT_DETECTION (es)...")
            response = self.client.document_text_detection(
                image=vision_image,
                image_context=image_context
            )

            # Guardar respuesta completa para análisis de confianza por dígito
            self.last_raw_response = response

            if response.error.message:
                print(f"ERROR Google Vision API: {response.error.message}")
                return []

            print("✓ Google Vision: Respuesta recibida (1 llamada API)")

            # Procesar respuesta - Google Vision detecta texto organizado por bloques/líneas
            records = []

            # Opción 1: Usar full_text_annotation para obtener todo el texto
            if response.full_text_annotation:
                full_text = response.full_text_annotation.text
                print(f"DEBUG Google Vision: Texto completo detectado:\n{full_text}")

                # Procesar línea por línea
                lines = full_text.split('\n')
                print(f"DEBUG Google Vision: Detectadas {len(lines)} líneas de texto")

                for idx, line in enumerate(lines):
                    if not line.strip():
                        continue

                    print(f"DEBUG Google Vision: Línea {idx+1}: '{line.strip()}'")

                    # Extraer números del texto
                    numbers = self._extract_numbers_from_text(line)

                    for num in numbers:
                        # Validar longitud de cédula (3-11 dígitos)
                        if 3 <= len(num) <= 11:
                            # Usar factory method para crear con Value Objects
                            record = CedulaRecord.from_primitives(
                                cedula=num,
                                confidence=95.0  # Google Vision es muy confiable
                            )
                            records.append(record)
                            print(f"✓ Cédula extraída: '{num}' ({len(num)} dígitos)")
                        elif len(num) < 3:
                            print(f"✗ Descartada (muy corta): '{num}' ({len(num)} dígitos)")
                        else:
                            print(f"✗ Descartada (muy larga): '{num}' ({len(num)} dígitos)")

            print(f"✓ Google Vision: Total llamadas API: 1 (óptimo)")

            # Eliminar duplicados
            unique_records = self._remove_duplicates(records)

            print(f"DEBUG Google Vision: Total cédulas únicas: {len(unique_records)}")

            return unique_records

        except Exception as e:
            print(f"ERROR Google Vision: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _split_image_into_lines(self, image: Image.Image) -> List[Image.Image]:
        """
        Divide la imagen en líneas individuales (una por cédula).

        Usa división uniforme: imagen de 490px / 15 líneas = ~32px por línea

        Args:
            image: Imagen completa

        Returns:
            Lista de sub-imágenes (una por línea)
        """
        height = image.height
        width = image.width

        # Dividir en 15 líneas uniformes
        expected_lines = 15
        line_height = height // expected_lines

        print(f"DEBUG Google Vision: Dividiendo imagen en {expected_lines} líneas de {line_height}px cada una")

        regions = []

        for i in range(expected_lines):
            y1 = i * line_height
            y2 = min((i + 1) * line_height, height)

            if y2 - y1 > 10:  # Altura mínima
                region = image.crop((0, y1, width, y2))
                regions.append(region)

        return regions

    def _extract_numbers_from_text(self, text: str) -> List[str]:
        """
        Extrae números del texto reconocido.

        ESTRATEGIA MEJORADA:
        Cuando hay letras entre dígitos (ej: "107 116C1931"), NO separar
        en múltiples números. En su lugar, eliminar TODAS las letras y
        espacios, dejando solo dígitos continuos.

        Esto evita que una cédula de 10 dígitos se divida en múltiples fragmentos.

        Args:
            text: Texto reconocido por Google Vision (ej: "107 116C1931")

        Returns:
            Lista con UN string numérico por línea (ej: ["1071161931"])
        """
        # Eliminar TODOS los caracteres que no sean dígitos
        # Esto incluye: letras, espacios, puntos, comas, guiones, etc.
        text_clean = re.sub(r'[^\d]', '', text)

        # Si queda algún número, retornarlo como una sola cédula
        if text_clean:
            return [text_clean]
        else:
            return []

    def _remove_duplicates(self, records: List[CedulaRecord]) -> List[CedulaRecord]:
        """
        Elimina registros duplicados, manteniendo el de mayor confianza.

        Args:
            records: Lista de registros

        Returns:
            Lista sin duplicados
        """
        seen = {}

        for record in records:
            # Usar .value ya que cedula es ahora CedulaNumber (Value Object)
            cedula_key = record.cedula.value
            # Comparar confidence usando .as_percentage() ya que es ConfidenceScore
            if cedula_key not in seen or record.confidence.as_percentage() > seen[cedula_key].confidence.as_percentage():
                seen[cedula_key] = record

        return list(seen.values())

    def get_character_confidences(self, text: str) -> Dict[str, any]:
        """
        Extrae la confianza individual de cada carácter en el texto detectado.

        Google Vision API retorna confianza a nivel de símbolo/carácter en:
        - full_text_annotation.pages[].blocks[].paragraphs[].words[].symbols[]

        Args:
            text: El texto (cédula) para el cual queremos las confianzas

        Returns:
            Dict con:
            - 'confidences': List[float] con confianza de cada carácter (0.0-1.0)
            - 'positions': List[int] con posición de cada carácter
            - 'average': float con confianza promedio
            - 'source': str identificando el origen

        Example:
            >>> confidences = adapter.get_character_confidences("1036221525")
            >>> confidences
            {
                'confidences': [0.98, 0.95, 0.97, 0.94, ...],
                'positions': [0, 1, 2, 3, ...],
                'average': 0.956,
                'source': 'google_vision'
            }

        Raises:
            ValueError: Si no hay respuesta disponible (ejecuta extract_cedulas() primero)
        """
        if not self.last_raw_response:
            raise ValueError("No hay respuesta disponible. Ejecuta extract_cedulas() primero.")

        if not self.last_raw_response.full_text_annotation:
            print("ADVERTENCIA: No hay full_text_annotation en respuesta de Google Vision")
            # Fallback: confianza uniforme
            return {
                'confidences': [0.85] * len(text),
                'positions': list(range(len(text))),
                'average': 0.85,
                'source': 'google_vision'
            }

        # Limpiar el texto buscado (eliminar espacios, puntos, etc)
        text_clean = text.replace(' ', '').replace('.', '').replace(',', '').replace('-', '')

        # Extraer todos los símbolos con sus confianzas
        all_symbols = []

        # Iterar sobre la estructura jerárquica de Google Vision
        for page in self.last_raw_response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        # Construir el texto de la palabra
                        word_text = ''.join([symbol.text for symbol in word.symbols])

                        # Obtener confianza de la palabra (si existe)
                        # Google Vision da confidence a nivel de palabra, no de símbolo individual
                        word_confidence = word.confidence if hasattr(word, 'confidence') else 0.95

                        # Agregar cada símbolo con la confianza de su palabra
                        for symbol in word.symbols:
                            symbol_conf = symbol.confidence if hasattr(symbol, 'confidence') else word_confidence
                            all_symbols.append({
                                'text': symbol.text,
                                'confidence': symbol_conf
                            })

        # Buscar el texto en los símbolos detectados
        # Construir string de todos los símbolos
        all_text = ''.join([s['text'] for s in all_symbols])
        all_text_clean = ''.join([c for c in all_text if c.isdigit()])

        # Intentar encontrar el texto buscado en el texto detectado
        confidences = []
        positions = []

        if text_clean in all_text_clean:
            # Encontrado - extraer confianzas correspondientes
            start_idx = all_text_clean.index(text_clean)

            # Mapear índices de all_text_clean a all_symbols
            digit_counter = 0
            symbol_idx = 0

            for symbol in all_symbols:
                if symbol['text'].isdigit():
                    if digit_counter >= start_idx and digit_counter < start_idx + len(text_clean):
                        confidences.append(symbol['confidence'])
                        positions.append(digit_counter - start_idx)
                    digit_counter += 1
        else:
            # No encontrado - usar confianza uniforme basada en promedio general
            print(f"ADVERTENCIA: Texto '{text_clean}' no encontrado en respuesta de Google Vision")
            print(f"DEBUG: Texto detectado: '{all_text_clean[:100]}...'")

            # Calcular confianza promedio de todos los símbolos numéricos
            numeric_symbols = [s for s in all_symbols if s['text'].isdigit()]
            avg_conf = sum(s['confidence'] for s in numeric_symbols) / len(numeric_symbols) if numeric_symbols else 0.90

            confidences = [avg_conf] * len(text_clean)
            positions = list(range(len(text_clean)))

        # Calcular promedio
        average = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            'confidences': confidences,
            'positions': positions,
            'average': average,
            'source': 'google_vision'
        }

    def extract_full_form_data(self, image: Image.Image, expected_rows: int = 15) -> List[RowData]:
        """
        Extrae datos completos del formulario manuscrito (nombres + cédulas).

        ⚡ OPTIMIZADO - UNA SOLA LLAMADA API (antes: 15 llamadas)

        ESTRATEGIA OPTIMIZADA:
        1. Enviar imagen COMPLETA a Google Vision (1 llamada API)
        2. Google Vision detecta TODO el texto con coordenadas (bounding boxes)
        3. Organizar texto en renglones basado en coordenada Y
        4. Separar nombres/cédulas por columna basado en coordenada X
        5. Detectar renglones vacíos

        Esto reduce de 15 llamadas API a 1 SOLA llamada.
        Mejora: 93% reducción de llamadas API
        Costo: 93% menor
        Velocidad: ~10x más rápido

        Args:
            image: Imagen PIL del formulario manuscrito completo
            expected_rows: Número esperado de renglones (default: 15)

        Returns:
            Lista de RowData (uno por renglón)
        """
        if self.client is None:
            print("ERROR: Google Cloud Vision no está inicializado")
            return []

        print(f"\n{'='*70}")
        print("⚡ EXTRACCIÓN OPTIMIZADA - Nombres + Cédulas (1 SOLA LLAMADA API)")
        print(f"{'='*70}")
        print(f"Imagen: {image.width}x{image.height} px")
        print(f"Renglones esperados: {expected_rows}")

        try:
            # ========== PASO 1: UNA SOLA LLAMADA API ==========
            print("\n[PASO 1] Enviando imagen completa a Google Vision API...")

            # Convertir imagen PIL a bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Crear objeto Image de Google Vision
            vision_image = vision.Image(content=img_byte_arr)

            # OPTIMIZACIÓN: Language hints para mejorar precisión en español
            image_context = vision.ImageContext(language_hints=['es'])

            # ⚡ ÚNICA LLAMADA API - DOCUMENT_TEXT_DETECTION
            response = self.client.document_text_detection(
                image=vision_image,
                image_context=image_context
            )

            if response.error.message:
                print(f"✗ Error API: {response.error.message}")
                return [self._create_empty_row(i) for i in range(expected_rows)]

            print("✓ Respuesta recibida (1 llamada API - ÓPTIMO)")

            # Verificar si hay texto detectado
            if not response.full_text_annotation or not response.full_text_annotation.text.strip():
                print("✗ No se detectó texto en la imagen")
                return [self._create_empty_row(i) for i in range(expected_rows)]

            # ========== PASO 2: ORGANIZAR TEXTO POR RENGLONES ==========
            print(f"\n[PASO 2] Organizando texto en {expected_rows} renglones...")

            # Extraer todos los bloques de texto con coordenadas
            all_blocks = self._extract_text_blocks_with_coords(response)
            print(f"✓ Detectados {len(all_blocks)} bloques de texto")

            # Dividir bloques en renglones basados en coordenada Y
            rows_blocks = self._assign_blocks_to_rows(
                all_blocks,
                image.height,
                expected_rows
            )

            # ========== PASO 3: PROCESAR CADA RENGLÓN ==========
            print(f"\n[PASO 3] Procesando {expected_rows} renglones...")

            all_rows_data = []

            for row_idx in range(expected_rows):
                blocks_in_row = rows_blocks.get(row_idx, [])

                if not blocks_in_row:
                    # Renglón vacío - no hay bloques de texto
                    row_data = self._create_empty_row(row_idx)
                    all_rows_data.append(row_data)
                    print(f"  [{row_idx + 1:2d}] → [VACÍO]")
                else:
                    # Procesar bloques del renglón
                    row_data = self._process_row_blocks(
                        blocks_in_row,
                        row_idx,
                        image.width
                    )
                    all_rows_data.append(row_data)

                    # Log resultado
                    if row_data.is_empty:
                        print(f"  [{row_idx + 1:2d}] → [VACÍO] (confianza baja)")
                    else:
                        print(f"  [{row_idx + 1:2d}] → Nombres: '{row_data.nombres_manuscritos}' | Cédula: '{row_data.cedula}'")

            # ========== RESUMEN ==========
            print(f"\n{'='*70}")
            print(f"RESUMEN: {len(all_rows_data)} renglones procesados")
            vacios = sum(1 for r in all_rows_data if r.is_empty)
            con_datos = len(all_rows_data) - vacios
            print(f"  - Con datos: {con_datos}")
            print(f"  - Vacíos: {vacios}")
            print(f"  - ⚡ Total llamadas API: 1 (93% reducción vs antes)")
            print(f"{'='*70}\n")

            return all_rows_data

        except Exception as e:
            print(f"✗ Error en extracción: {e}")
            import traceback
            traceback.print_exc()
            return [self._create_empty_row(i) for i in range(expected_rows)]

    def _extract_text_blocks_with_coords(self, response) -> List[Dict]:
        """
        Extrae todos los bloques de texto con sus coordenadas de bounding box.

        Args:
            response: Respuesta de Google Vision API

        Returns:
            Lista de diccionarios con:
                - text: Texto del bloque
                - x: Coordenada X promedio (centro horizontal)
                - y: Coordenada Y promedio (centro vertical)
                - confidence: Confianza del OCR
                - vertices: Vértices del bounding box
        """
        blocks = []

        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                # Calcular coordenadas promedio del bloque
                vertices = block.bounding_box.vertices
                if not vertices:
                    continue

                avg_x = sum(v.x for v in vertices) / len(vertices)
                avg_y = sum(v.y for v in vertices) / len(vertices)

                # Extraer texto del bloque
                block_text = ""
                block_confidence = 0.0
                word_count = 0

                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        block_text += word_text + " "
                        block_confidence += word.confidence
                        word_count += 1

                block_text = block_text.strip()

                if word_count > 0:
                    block_confidence /= word_count

                if block_text:  # Solo agregar bloques con texto
                    blocks.append({
                        'text': block_text,
                        'x': avg_x,
                        'y': avg_y,
                        'confidence': block_confidence,
                        'vertices': vertices
                    })

        return blocks

    def _assign_blocks_to_rows(
        self,
        blocks: List[Dict],
        image_height: int,
        num_rows: int
    ) -> Dict[int, List[Dict]]:
        """
        Asigna bloques de texto a renglones basándose en coordenada Y.

        Divide la imagen en renglones uniformes y asigna cada bloque
        al renglón más cercano según su coordenada Y.

        Args:
            blocks: Lista de bloques con coordenadas
            image_height: Altura de la imagen en píxeles
            num_rows: Número de renglones esperados

        Returns:
            Diccionario {row_index: [bloques]}
        """
        row_height = image_height / num_rows
        rows_blocks = {i: [] for i in range(num_rows)}

        for block in blocks:
            # Determinar a qué renglón pertenece según coordenada Y
            row_idx = int(block['y'] / row_height)

            # Asegurar que está dentro del rango
            row_idx = max(0, min(row_idx, num_rows - 1))

            rows_blocks[row_idx].append(block)

        return rows_blocks

    def _process_row_blocks(
        self,
        blocks: List[Dict],
        row_index: int,
        image_width: int
    ) -> RowData:
        """
        Procesa bloques de un renglón separando nombres y cédula.

        Separa los bloques en dos columnas basándose en coordenada X:
        - Columna izquierda (0-60% del ancho): NOMBRES
        - Columna derecha (60-100% del ancho): CÉDULA

        Args:
            blocks: Bloques de texto del renglón
            row_index: Índice del renglón
            image_width: Ancho de la imagen

        Returns:
            RowData con nombres, cédula y confianza
        """
        # Límite de columnas (60% del ancho)
        column_boundary = image_width * 0.6

        nombres_parts = []
        cedula_parts = []
        nombres_confidences = []
        cedula_confidences = []

        # Clasificar bloques por columna
        for block in blocks:
            if block['x'] < column_boundary:
                # Columna izquierda - NOMBRES
                nombres_parts.append(block['text'])
                nombres_confidences.append(block['confidence'])
            else:
                # Columna derecha - CÉDULA
                cedula_parts.append(block['text'])
                cedula_confidences.append(block['confidence'])

        # Combinar partes
        nombres = ' '.join(nombres_parts).strip()
        cedula_raw = ' '.join(cedula_parts).strip()

        # OPTIMIZACIÓN: Corregir errores comunes de OCR antes de limpiar
        cedula = self._corregir_errores_ocr_cedula(cedula_raw)

        # Calcular confianza promedio
        nombres_conf = sum(nombres_confidences) / len(nombres_confidences) if nombres_confidences else 0.0
        cedula_conf = sum(cedula_confidences) / len(cedula_confidences) if cedula_confidences else 0.0

        confidence = {
            'nombres': nombres_conf,
            'cedula': cedula_conf
        }

        # Crear texto raw para debugging
        raw_text = f"{nombres} | {cedula_raw}".strip()

        # Detectar si es renglón vacío basado en umbral de confianza
        min_confidence = self.config.get('ocr.google_vision.confidence_threshold', 0.30)
        is_empty = (
            (not nombres and not cedula) or
            (confidence.get('nombres', 0) < min_confidence and confidence.get('cedula', 0) < min_confidence) or
            (len(nombres) < 2 and len(cedula) < 6)  # Muy poco texto
        )

        # Usar factory method para crear RowData con Value Objects
        return RowData.from_primitives(
            row_index=row_index,
            nombres_manuscritos=nombres,
            cedula=cedula,
            is_empty=is_empty,
            confidence=confidence,
            raw_text=raw_text
        )

    # ========== MÉTODOS LEGACY (DEPRECADOS) ==========
    # Los siguientes métodos ya NO se usan en extract_full_form_data optimizado.
    # Se mantienen por compatibilidad pero no se llaman.

    def _split_image_into_rows(self, image: Image.Image, num_rows: int) -> List[Image.Image]:
        """
        [DEPRECADO] Divide la imagen en renglones horizontales uniformes.

        Este método ya NO se usa en la versión optimizada de extract_full_form_data.
        La versión optimizada procesa la imagen completa en 1 sola llamada API.

        Args:
            image: Imagen completa del formulario
            num_rows: Número de renglones a crear

        Returns:
            Lista de sub-imágenes (una por renglón)
        """
        height = image.height
        width = image.width
        row_height = height // num_rows

        print(f"División: {height}px / {num_rows} renglones = {row_height}px por renglón")

        rows = []
        for i in range(num_rows):
            y1 = i * row_height
            y2 = min((i + 1) * row_height, height)

            if y2 - y1 > 5:  # Altura mínima
                row = image.crop((0, y1, width, y2))
                rows.append(row)

        return rows

    def _process_single_row(self, row_image: Image.Image, row_index: int) -> RowData:
        """
        Procesa un renglón individual extrayendo nombres y cédula.

        Estrategia de separación por columnas:
        - Columna izquierda (0-50% del ancho): NOMBRES
        - Columna centro (50-100% del ancho): CÉDULA

        Args:
            row_image: Imagen del renglón a procesar
            row_index: Índice del renglón (0-14)

        Returns:
            RowData con nombres, cédula, y estado de vacío
        """
        try:
            # Convertir imagen PIL a bytes
            img_byte_arr = io.BytesIO()
            row_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Crear objeto Image de Google Vision
            vision_image = vision.Image(content=img_byte_arr)

            # OPTIMIZACIÓN: Language hints para mejorar precisión en español
            image_context = vision.ImageContext(language_hints=['es'])

            # Llamar a la API - DOCUMENT_TEXT_DETECTION
            response = self.client.document_text_detection(
                image=vision_image,
                image_context=image_context
            )

            if response.error.message:
                print(f"  ✗ Error API: {response.error.message}")
                return self._create_empty_row(row_index)

            # Verificar si hay texto detectado
            if not response.full_text_annotation or not response.full_text_annotation.text.strip():
                print(f"  → Sin texto detectado (renglón vacío)")
                return self._create_empty_row(row_index)

            # Extraer texto completo para debugging
            full_text = response.full_text_annotation.text.strip()
            print(f"  → Texto detectado: '{full_text}'")

            # Separar nombres y cédula usando coordenadas de boundingBox
            nombres, cedula, confidence = self._separate_nombres_cedula(
                response,
                row_image.width
            )

            # Detectar si es renglón vacío basado en umbral de confianza
            min_confidence = self.config.get('ocr.google_vision.confidence_threshold', 0.30)
            is_empty = (
                (not nombres and not cedula) or
                (confidence.get('nombres', 0) < min_confidence and confidence.get('cedula', 0) < min_confidence) or
                (len(nombres) < 2 and len(cedula) < 6)  # Muy poco texto
            )

            # Usar factory method para crear RowData con Value Objects
            return RowData.from_primitives(
                row_index=row_index,
                nombres_manuscritos=nombres,
                cedula=cedula,
                is_empty=is_empty,
                confidence=confidence,
                raw_text=full_text
            )

        except Exception as e:
            print(f"  ✗ Error procesando renglón: {e}")
            return self._create_empty_row(row_index)

    def _separate_nombres_cedula(
        self,
        response,
        image_width: int
    ) -> tuple[str, str, Dict[str, float]]:
        """
        Separa nombres y cédula basándose en posición horizontal del texto.

        Columnas del formulario manuscrito:
        - Izquierda (0-60% del ancho): NOMBRES
        - Centro (60-100% del ancho): CÉDULA

        Args:
            response: Respuesta de Google Vision API
            image_width: Ancho de la imagen del renglón

        Returns:
            (nombres, cedula, confidence_dict)
        """
        # Límite de columnas (60% del ancho)
        column_boundary = image_width * 0.6

        nombres_parts = []
        cedula_parts = []
        nombres_confidences = []
        cedula_confidences = []

        # Iterar sobre los bloques/palabras detectadas
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    # Obtener bounding box del párrafo
                    vertices = paragraph.bounding_box.vertices
                    if not vertices:
                        continue

                    # Calcular posición X promedio
                    avg_x = sum(v.x for v in vertices) / len(vertices)

                    # Extraer texto del párrafo
                    paragraph_text = ""
                    paragraph_confidence = 0.0
                    word_count = 0

                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        paragraph_text += word_text + " "
                        paragraph_confidence += word.confidence
                        word_count += 1

                    paragraph_text = paragraph_text.strip()
                    if word_count > 0:
                        paragraph_confidence /= word_count

                    # Clasificar en columna izquierda (nombres) o centro (cédula)
                    if avg_x < column_boundary:
                        # Columna izquierda - NOMBRES
                        nombres_parts.append(paragraph_text)
                        nombres_confidences.append(paragraph_confidence)
                    else:
                        # Columna centro - CÉDULA
                        cedula_parts.append(paragraph_text)
                        cedula_confidences.append(paragraph_confidence)

        # Combinar partes
        nombres = ' '.join(nombres_parts).strip()
        cedula_raw = ' '.join(cedula_parts).strip()

        # OPTIMIZACIÓN: Corregir errores comunes de OCR antes de limpiar
        cedula = self._corregir_errores_ocr_cedula(cedula_raw)

        # Calcular confianza promedio
        nombres_conf = sum(nombres_confidences) / len(nombres_confidences) if nombres_confidences else 0.0
        cedula_conf = sum(cedula_confidences) / len(cedula_confidences) if cedula_confidences else 0.0

        confidence = {
            'nombres': nombres_conf,
            'cedula': cedula_conf
        }

        return nombres, cedula, confidence

    def _corregir_errores_ocr_cedula(self, cedula: str) -> str:
        """
        Corrige errores comunes de OCR en cédulas manuscritas.

        OPTIMIZACIÓN CRÍTICA del prompt.txt:
        Aplica matriz de confusión para errores típicos en escritura manual.

        Correcciones implementadas:
        - l, I, | → 1 (confusión con número 1)
        - O, o → 0 (confusión con cero)
        - S, s → 5 (confusión con 5)
        - B → 8 (confusión con 8)
        - Z, z → 2 (confusión con 2)
        - G → 6 (confusión con 6)

        Args:
            cedula: String de cédula potencialmente con errores

        Returns:
            Cédula corregida con solo dígitos numéricos

        Example:
            "lO23456" → "1023456"
            "B765432I" → "87654321"
        """
        if not cedula:
            return cedula

        # Matriz de corrección de errores comunes
        COMMON_ERRORS = {
            'l': '1', 'I': '1', '|': '1',  # Confusión con 1
            'O': '0', 'o': '0',             # Confusión con 0
            'S': '5', 's': '5',             # Confusión con 5
            'B': '8',                        # Confusión con 8
            'Z': '2', 'z': '2',             # Confusión con 2
            'G': '6',                        # Confusión con 6
        }

        # Aplicar correcciones carácter por carácter
        cedula_corregida = ""
        correcciones_aplicadas = []

        for char in cedula:
            if char in COMMON_ERRORS:
                char_corregido = COMMON_ERRORS[char]
                cedula_corregida += char_corregido
                correcciones_aplicadas.append(f"{char}→{char_corregido}")
            else:
                cedula_corregida += char

        # Log correcciones si se aplicaron
        if correcciones_aplicadas:
            print(f"  🔧 Correcciones OCR aplicadas: {', '.join(correcciones_aplicadas)}")
            print(f"     Antes: '{cedula}' → Después: '{cedula_corregida}'")

        # Filtrar solo dígitos numéricos
        cedula_final = ''.join(filter(str.isdigit, cedula_corregida))

        return cedula_final

    def _create_empty_row(self, row_index: int) -> RowData:
        """
        Crea un RowData vacío para renglones sin datos.

        Args:
            row_index: Índice del renglón

        Returns:
            RowData marcado como vacío
        """
        # Usar factory method para crear RowData con Value Objects
        return RowData.from_primitives(
            row_index=row_index,
            nombres_manuscritos="",
            cedula="",
            is_empty=True,
            confidence={},
            raw_text=None
        )

    def _extract_text_blocks_with_positions(self, response) -> List[Dict]:
        """
        Extrae palabras individuales con coordenadas (NO bloques completos).

        CAMBIO IMPORTANTE: Ahora extrae a nivel de PALABRA en lugar de BLOCK.
        Esto permite que filter_nombres() agrupe correctamente nombres que están
        separados espacialmente, evitando que Google Vision agrupe nombres diferentes
        en un solo bloque gigante.

        Args:
            response: Respuesta de Google Vision API

        Returns:
            Lista de palabras con {text, x, y, width, height, confidence}
        """
        word_blocks = []

        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        # Obtener vertices de esta palabra específica
                        vertices = word.bounding_box.vertices
                        if not vertices or len(vertices) < 4:
                            continue

                        # Calcular bounding box de la palabra
                        min_x = min(v.x for v in vertices)
                        max_x = max(v.x for v in vertices)
                        min_y = min(v.y for v in vertices)
                        max_y = max(v.y for v in vertices)

                        # Extraer texto de la palabra
                        word_text = ''.join([symbol.text for symbol in word.symbols])

                        if word_text.strip():
                            word_blocks.append({
                                'text': word_text.strip(),
                                'x': min_x,
                                'y': min_y,
                                'width': max_x - min_x,
                                'height': max_y - min_y,
                                'confidence': word.confidence
                            })

        return word_blocks

    def extract_name_cedula_pairs(self, image: Image.Image) -> List[Dict]:
        """
        Extrae pares nombre-cédula usando post-procesamiento + proximidad espacial.

        Flujo:
        1. Extraer TODO el texto con coordenadas
        2. Post-procesamiento: filtrar nombres
        3. Post-procesamiento: filtrar cédulas
        4. Emparejar por proximidad espacial

        Returns:
            Lista de pares nombre-cédula correctamente emparejados
        """
        from .spatial_pairing import SpatialPairing

        print("\n" + "="*80)
        print("GOOGLE VISION: Extracción de pares nombre-cédula")
        print("="*80)

        # 1. Preprocesar imagen
        processed_image = self.preprocess_image(image)

        # 2. Extraer TODO el texto con coordenadas
        print("[1/4] Extrayendo texto con coordenadas...")
        img_byte_arr = io.BytesIO()
        processed_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        vision_image = vision.Image(content=img_byte_arr)
        image_context = vision.ImageContext(language_hints=['es'])

        response = self.client.document_text_detection(
            image=vision_image,
            image_context=image_context
        )

        self.last_raw_response = response

        if response.error.message:
            raise Exception(f"Google Vision error: {response.error.message}")

        # Extraer bloques con posiciones
        all_blocks = self._extract_text_blocks_with_positions(response)
        print(f"  ✓ Extraídos {len(all_blocks)} bloques de texto")

        # 3. Post-procesamiento: filtrar nombres
        print("[2/4] Post-procesando nombres...")
        nombres = SpatialPairing.filter_nombres(all_blocks)
        print(f"  ✓ Detectados {len(nombres)} nombres")
        for n in nombres:
            print(f"    - {n['text']} (conf: {n['confidence']:.2%})")

        # 4. Post-procesamiento: filtrar cédulas
        print("[3/4] Post-procesando cédulas...")
        cedulas = SpatialPairing.filter_cedulas(all_blocks)
        print(f"  ✓ Detectadas {len(cedulas)} cédulas")
        for c in cedulas:
            print(f"    - {c['text']} (conf: {c['confidence']:.2%})")

        # 5. Emparejar por proximidad espacial
        print("[4/4] Emparejando por proximidad espacial...")
        pares = SpatialPairing.pair_by_proximity(nombres, cedulas, verbose=True)
        print(f"  ✓ Emparejados {len(pares)} pares")

        print("="*80 + "\n")

        return pares

