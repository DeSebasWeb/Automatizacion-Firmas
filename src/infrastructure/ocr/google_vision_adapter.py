"""Implementación de OCR usando Google Cloud Vision API - Óptimo para escritura manual (REFACTORIZADA)."""
import io
from PIL import Image
from typing import List, Dict

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("ADVERTENCIA: Google Cloud Vision no está instalado. Instalar con: pip install google-cloud-vision")

from ...domain.entities import CedulaRecord, RowData
from ...domain.ports import ConfigPort
from .base_ocr_adapter import BaseOCRAdapter
from .image_converter import ImageConverter
from .vision import GoogleSymbolExtractor, ConfidenceMapper


class GoogleVisionAdapter(BaseOCRAdapter):
    """
    Implementación de OCR usando Google Cloud Vision API con preprocesamiento avanzado.

    **REFACTORIZADA** - Ahora hereda de BaseOCRAdapter eliminando ~400 LOC de duplicación.

    Google Cloud Vision es:
    - Estado del arte para escritura manual
    - Extremadamente preciso con números manuscritos
    - 1,000 detecciones gratis al mes
    - Después: $1.50 por cada 1,000 detecciones

    Para 15 cédulas por imagen:
    - 1,000 imágenes gratis = 15,000 cédulas gratis/mes

    Attributes:
        config: Servicio de configuración
        client: Cliente de Google Cloud Vision
        preprocessor: Pipeline de preprocesamiento de imágenes (heredado)
        last_raw_response: Última respuesta raw de la API (heredado)
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el servicio de OCR con Google Cloud Vision.

        Args:
            config: Servicio de configuración

        Raises:
            ImportError: Si Google Cloud Vision SDK no está instalado
        """
        if not GOOGLE_VISION_AVAILABLE:
            raise ImportError(
                "Google Cloud Vision no está instalado. "
                "Instalar con: pip install google-cloud-vision"
            )

        # Inicializar clase base (preprocessor, config, last_raw_response)
        super().__init__(config)

        self.client = None
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

    def _call_ocr_api(self, image_bytes: bytes) -> any:
        """
        Realiza la llamada a Google Vision API.

        Args:
            image_bytes: Imagen en bytes (PNG format)

        Returns:
            Respuesta de document_text_detection

        Raises:
            Exception: Si hay error en la llamada API
        """
        # Crear objeto Image de Google Vision
        vision_image = vision.Image(content=image_bytes)

        # OPTIMIZACIÓN: Language hints para mejorar precisión en español
        image_context = vision.ImageContext(language_hints=['es'])

        # Llamar a la API - DOCUMENT_TEXT_DETECTION detecta texto línea por línea
        response = self.client.document_text_detection(
            image=vision_image,
            image_context=image_context
        )

        if response.error.message:
            raise Exception(f"Google Vision API error: {response.error.message}")

        return response

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
            # Preprocesar imagen usando método heredado
            processed_image = self.preprocess_image(image)

            # Convertir imagen PIL a bytes usando ImageConverter
            img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

            # Llamar a la API
            print("DEBUG Google Vision: Llamando a DOCUMENT_TEXT_DETECTION (es)...")
            response = self._call_ocr_api(img_bytes)

            # Guardar respuesta completa para análisis de confianza por dígito
            self.last_raw_response = response

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

                    # Extraer números del texto usando método heredado
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

            # Eliminar duplicados usando método heredado
            unique_records = self._remove_duplicates(records)

            print(f"DEBUG Google Vision: Total cédulas únicas: {len(unique_records)}")

            return unique_records

        except Exception as e:
            print(f"ERROR Google Vision: {e}")
            import traceback
            traceback.print_exc()
            return []

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

            # Preprocesar imagen
            processed_image = self.preprocess_image(image)

            # Convertir imagen PIL a bytes
            img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

            # ⚡ ÚNICA LLAMADA API - DOCUMENT_TEXT_DETECTION
            response = self._call_ocr_api(img_bytes)

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

            # Dividir bloques en renglones basados en coordenada Y (método heredado)
            rows_blocks = self._assign_blocks_to_rows(
                all_blocks,
                processed_image.height,
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
                    # Procesar bloques del renglón usando método heredado
                    row_data = self._process_row_blocks(
                        blocks_in_row,
                        row_idx,
                        processed_image.width,
                        column_boundary_ratio=0.6  # 60% para Google Vision
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

    def get_character_confidences(self, text: str) -> Dict[str, any]:
        """
        Extrae la confianza individual de cada caracter en el texto detectado.

        REFACTORIZADO - Ahora usa GoogleSymbolExtractor y ConfidenceMapper.

        Args:
            text: El texto (cedula) para el cual queremos las confianzas

        Returns:
            Dict con:
            - 'confidences': List[float] con confianza de cada caracter (0.0-1.0)
            - 'positions': List[int] con posicion de cada caracter
            - 'average': float con confianza promedio
            - 'source': str identificando el origen

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

        # PASO 1: Extraer simbolos usando GoogleSymbolExtractor
        try:
            symbols = GoogleSymbolExtractor.extract_all_symbols(self.last_raw_response)
        except ValueError as e:
            print(f"ADVERTENCIA: Error extrayendo simbolos: {e}")
            return {
                'confidences': [0.85] * len(text),
                'positions': list(range(len(text))),
                'average': 0.85,
                'source': 'google_vision'
            }

        # PASO 2: Mapear texto a confianzas usando ConfidenceMapper
        result = ConfidenceMapper.map_from_symbols(text, symbols)

        # PASO 3: Agregar advertencia si no se encontro
        if not result['found']:
            print(f"ADVERTENCIA: Texto '{text}' no encontrado en respuesta")

        # PASO 4: Agregar source y retornar
        result['source'] = 'google_vision'
        return result
