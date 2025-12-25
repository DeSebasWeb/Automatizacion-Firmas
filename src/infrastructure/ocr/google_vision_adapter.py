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

from ...domain.entities import CedulaRecord
from ...domain.ports import ConfigPort
from .base_ocr_adapter import BaseOCRAdapter
from .image_converter import ImageConverter
from .vision import GoogleSymbolExtractor, ConfidenceMapper
from ...shared.logging import (
    LoggerFactory,
    log_operation,
    log_info_message,
    log_warning_message,
    log_error_message,
    log_debug_message,
    log_api_call,
    log_api_response,
    log_success,
    log_failure,
    log_processing_step,
    log_ocr_extraction
)


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

        # Inicializar logger
        self.logger = LoggerFactory.get_ocr_logger("google_vision")

        self.client = None
        self._initialize_ocr()

    def _initialize_ocr(self) -> None:
        """Inicializa Google Cloud Vision API."""
        self.logger.debug("Inicializando cliente Google Vision")

        try:
            # Intentar crear cliente con Application Default Credentials (ADC)
            # ADC busca credenciales en este orden:
            # 1. GOOGLE_APPLICATION_CREDENTIALS (archivo JSON)
            # 2. gcloud auth application-default login (credenciales de usuario)
            # 3. Compute Engine/App Engine/Cloud Run (credenciales de servicio)

            self.client = vision.ImageAnnotatorClient()

            self.logger.info(
                "Google Cloud Vision inicializado correctamente",
                auth_method="Application Default Credentials",
                model="optimized_for_handwriting"
            )

        except Exception as e:
            self.logger.error(
                "Error al inicializar Google Cloud Vision",
                error_type=type(e).__name__,
                error_message=str(e),
                solutions=[
                    "Ejecutar: gcloud auth application-default login",
                    "O configurar: GOOGLE_APPLICATION_CREDENTIALS con ruta a JSON",
                    "Asegurarse de habilitar Cloud Vision API en el proyecto"
                ]
            )
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
            self.logger.error("Google Cloud Vision no esta inicializado")
            return []

        with log_operation(
            self.logger,
            "extract_cedulas",
            image_size=f"{image.width}x{image.height}"
        ) as op:
            try:
                # Preprocesar imagen usando método heredado
                processed_image = self.preprocess_image(image)

                # Convertir imagen PIL a bytes usando ImageConverter
                img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

                # Llamar a la API
                log_api_call(self.logger, "google_vision", "document_text_detection", language="es")
                response = self._call_ocr_api(img_bytes)

                # Guardar respuesta completa para análisis de confianza por dígito
                self.last_raw_response = response

                log_api_response(self.logger, "google_vision", True, api_calls=1)

                # Procesar respuesta - Google Vision detecta texto organizado por bloques/líneas
                records = []

                # Opción 1: Usar full_text_annotation para obtener todo el texto
                if response.full_text_annotation:
                    full_text = response.full_text_annotation.text
                    self.logger.debug("Texto completo detectado", full_text=full_text)

                    # Procesar línea por línea
                    lines = full_text.split('\n')
                    self.logger.debug("Lineas de texto detectadas", total_lines=len(lines))

                    for idx, line in enumerate(lines):
                        if not line.strip():
                            continue

                        self.logger.debug("Procesando linea", line_number=idx+1, content=line.strip())

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
                                log_success(self.logger, "cedula_extraida", cedula=num, digits=len(num))
                            elif len(num) < 3:
                                log_failure(self.logger, "cedula_descartada", reason="too_short", cedula=num, length=len(num))
                            else:
                                log_failure(self.logger, "cedula_descartada", reason="too_long", cedula=num, length=len(num))

                # Eliminar duplicados usando método heredado
                unique_records = self._remove_duplicates(records)

                # Agregar métricas
                op.add_metric("cedulas_extraidas", len(unique_records))
                op.add_metric("cedulas_duplicadas", len(records) - len(unique_records))

                log_ocr_extraction(self.logger, "google_vision", len(unique_records))

                return unique_records

            except Exception as e:
                log_error_message(self.logger, "Error en extraccion de cedulas", error=e)
                return []

    # MÉTODO REMOVIDO: extract_full_form_data ya no es necesario para API
    # Usaba RowData que es específico de la UI de escritorio

    def _extract_full_form_data_DEPRECATED(self, image: Image.Image, expected_rows: int = 15):
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
            self.logger.error("Google Cloud Vision no esta inicializado")
            return []

        with log_operation(
            self.logger,
            "extract_full_form_data",
            image_size=f"{image.width}x{image.height}",
            expected_rows=expected_rows
        ) as op:
            try:
                # ========== PASO 1: UNA SOLA LLAMADA API ==========
                log_processing_step(
                    self.logger,
                    "Enviando imagen completa a Google Vision API",
                    step_number=1,
                    optimization="single_api_call"
                )

                # Preprocesar imagen
                processed_image = self.preprocess_image(image)

                # Convertir imagen PIL a bytes
                img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

                # ⚡ ÚNICA LLAMADA API - DOCUMENT_TEXT_DETECTION
                log_api_call(self.logger, "google_vision", "document_text_detection")
                response = self._call_ocr_api(img_bytes)
                log_api_response(self.logger, "google_vision", True, api_calls=1, optimization="93% reduction vs before")

                # Verificar si hay texto detectado
                if not response.full_text_annotation or not response.full_text_annotation.text.strip():
                    log_warning_message(self.logger, "No se detecto texto en la imagen")
                    return [self._create_empty_row(i) for i in range(expected_rows)]

                # ========== PASO 2: ORGANIZAR TEXTO POR RENGLONES ==========
                log_processing_step(
                    self.logger,
                    f"Organizando texto en {expected_rows} renglones",
                    step_number=2
                )

                # Extraer todos los bloques de texto con coordenadas
                all_blocks = self._extract_text_blocks_with_coords(response)
                self.logger.info("Bloques de texto detectados", blocks_count=len(all_blocks))

                # Dividir bloques en renglones basados en coordenada Y (método heredado)
                rows_blocks = self._assign_blocks_to_rows(
                    all_blocks,
                    processed_image.height,
                    expected_rows
                )

                # ========== PASO 3: PROCESAR CADA RENGLÓN ==========
                log_processing_step(
                    self.logger,
                    f"Procesando {expected_rows} renglones",
                    step_number=3
                )

                all_rows_data = []

                for row_idx in range(expected_rows):
                    blocks_in_row = rows_blocks.get(row_idx, [])

                    if not blocks_in_row:
                        # Renglón vacío - no hay bloques de texto
                        row_data = self._create_empty_row(row_idx)
                        all_rows_data.append(row_data)
                        self.logger.debug("Renglon vacio", row_number=row_idx+1)
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
                            self.logger.debug(
                                "Renglon vacio por confianza baja",
                                row_number=row_idx+1
                            )
                        else:
                            self.logger.debug(
                                "Renglon procesado",
                                row_number=row_idx+1,
                                nombres=row_data.nombres_manuscritos,
                                cedula=row_data.cedula
                            )

                # Calcular métricas
                vacios = sum(1 for r in all_rows_data if r.is_empty)
                con_datos = len(all_rows_data) - vacios

                # Agregar métricas a la operación
                op.add_metric("renglones_totales", len(all_rows_data))
                op.add_metric("renglones_con_datos", con_datos)
                op.add_metric("renglones_vacios", vacios)
                op.add_metric("api_calls", 1)

                self.logger.info(
                    "Extraccion de formulario completada",
                    renglones_procesados=len(all_rows_data),
                    con_datos=con_datos,
                    vacios=vacios,
                    api_calls=1
                )

                return all_rows_data

            except Exception as e:
                log_error_message(self.logger, "Error en extraccion de formulario", error=e)
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
            log_warning_message(
                self.logger,
                "No hay full_text_annotation en respuesta de Google Vision"
            )
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
            log_warning_message(
                self.logger,
                "Error extrayendo simbolos",
                error_type=type(e).__name__,
                error_message=str(e)
            )
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
            log_warning_message(
                self.logger,
                "Texto no encontrado en respuesta",
                text=text
            )

        # PASO 4: Agregar source y retornar
        result['source'] = 'google_vision'
        return result
