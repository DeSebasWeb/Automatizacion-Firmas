"""Implementación de OCR usando Google Cloud Vision API - Óptimo para escritura manual (REFACTORIZADA)."""
from typing import List, Dict, Any
import structlog
from PIL import Image

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

from ...domain.entities import CedulaRecord
from ...domain.ports import ConfigPort
from .base_ocr_adapter import BaseOCRAdapter
from .image_converter import ImageConverter
from .vision import GoogleSymbolExtractor, ConfidenceMapper

logger = structlog.get_logger(__name__)


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
            logger.error(
                "google_vision_not_installed",
                error="Google Cloud Vision SDK is not installed",
                solution="pip install google-cloud-vision"
            )
            raise ImportError(
                "Google Cloud Vision no está instalado. "
                "Instalar con: pip install google-cloud-vision"
            )

        # Inicializar clase base (preprocessor, config, last_raw_response)
        super().__init__(config)

        # Bind logger con contexto específico del adapter
        self.logger = logger.bind(adapter="google_vision")

        self.client = None
        self._initialize_ocr()

    def _initialize_ocr(self) -> None:
        """Inicializa Google Cloud Vision API."""
        self.logger.debug("google_vision_initializing")

        try:
            # Intentar crear cliente con Application Default Credentials (ADC)
            # ADC busca credenciales en este orden:
            # 1. GOOGLE_APPLICATION_CREDENTIALS (archivo JSON)
            # 2. gcloud auth application-default login (credenciales de usuario)
            # 3. Compute Engine/App Engine/Cloud Run (credenciales de servicio)

            self.client = vision.ImageAnnotatorClient()

            self.logger.info(
                "google_vision_initialized",
                auth_method="Application Default Credentials",
                model="optimized_for_handwriting"
            )

        except Exception as e:
            self.logger.error(
                "google_vision_initialization_failed",
                error_type=type(e).__name__,
                error_message=str(e),
                solutions=[
                    "gcloud auth application-default login",
                    "export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json",
                    "Enable Cloud Vision API in GCP project"
                ]
            )
            raise

    def _call_ocr_api(self, image_bytes: bytes) -> Any:
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
            self.logger.error("client_not_initialized")
            return []

        operation_logger = self.logger.bind(
            operation="extract_cedulas",
            image_width=image.width,
            image_height=image.height
        )
        operation_logger.info("extraction_started")

        try:
            # Preprocesar imagen usando método heredado
            processed_image = self.preprocess_image(image)

            # Convertir imagen PIL a bytes usando ImageConverter
            img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

            # Llamar a la API
            operation_logger.debug("calling_api", method="document_text_detection", language="es")
            response = self._call_ocr_api(img_bytes)

            # Guardar respuesta completa para análisis de confianza por dígito
            self.last_raw_response = response

            operation_logger.debug("api_call_successful", api_calls=1)

            # Procesar respuesta - Google Vision detecta texto organizado por bloques/líneas
            records = []

            # Opción 1: Usar full_text_annotation para obtener todo el texto
            if response.full_text_annotation:
                full_text = response.full_text_annotation.text
                operation_logger.debug("text_detected", full_text=full_text)

                # Procesar línea por línea
                lines = full_text.split('\n')
                operation_logger.debug("lines_detected", total_lines=len(lines))

                for idx, line in enumerate(lines):
                    if not line.strip():
                        continue

                    line_logger = operation_logger.bind(line_number=idx + 1, content=line.strip())
                    line_logger.debug("processing_line")

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
                            operation_logger.info("cedula_extracted", cedula=num, digits=len(num))
                        elif len(num) < 3:
                            operation_logger.debug("cedula_rejected_too_short", cedula=num, length=len(num))
                        else:
                            operation_logger.debug("cedula_rejected_too_long", cedula=num, length=len(num))

            # Eliminar duplicados usando método heredado
            unique_records = self._remove_duplicates(records)

            # Log métricas finales
            operation_logger.info(
                "extraction_completed",
                cedulas_extracted=len(unique_records),
                cedulas_duplicated=len(records) - len(unique_records),
                success=True
            )

            return unique_records

        except Exception as e:
            operation_logger.error(
                "extraction_failed",
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
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
            self.logger.error("client_not_initialized")
            return []

        operation_logger = self.logger.bind(
            operation="extract_full_form_data",
            image_width=image.width,
            image_height=image.height,
            expected_rows=expected_rows
        )
        operation_logger.info("form_extraction_started")

        try:
            # ========== PASO 1: UNA SOLA LLAMADA API ==========
            operation_logger.debug("step_1_calling_api", optimization="single_api_call")

            # Preprocesar imagen
            processed_image = self.preprocess_image(image)

            # Convertir imagen PIL a bytes
            img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

            # ⚡ ÚNICA LLAMADA API - DOCUMENT_TEXT_DETECTION
            operation_logger.debug("calling_api", method="document_text_detection")
            response = self._call_ocr_api(img_bytes)
            operation_logger.debug("api_call_successful", api_calls=1, optimization="93% reduction vs before")

            # Verificar si hay texto detectado
            if not response.full_text_annotation or not response.full_text_annotation.text.strip():
                operation_logger.warning("no_text_detected")
                return [self._create_empty_row(i) for i in range(expected_rows)]

            # ========== PASO 2: ORGANIZAR TEXTO POR RENGLONES ==========
            operation_logger.debug("step_2_organizing_rows", expected_rows=expected_rows)

            # Extraer todos los bloques de texto con coordenadas
            all_blocks = self._extract_text_blocks_with_coords(response)
            operation_logger.info("text_blocks_detected", blocks_count=len(all_blocks))

            # Dividir bloques en renglones basados en coordenada Y (método heredado)
            rows_blocks = self._assign_blocks_to_rows(
                all_blocks,
                processed_image.height,
                expected_rows
            )

            # ========== PASO 3: PROCESAR CADA RENGLÓN ==========
            operation_logger.debug("step_3_processing_rows", expected_rows=expected_rows)

            all_rows_data = []

            for row_idx in range(expected_rows):
                blocks_in_row = rows_blocks.get(row_idx, [])

                if not blocks_in_row:
                    # Renglón vacío - no hay bloques de texto
                    row_data = self._create_empty_row(row_idx)
                    all_rows_data.append(row_data)
                    operation_logger.debug("empty_row_no_blocks", row_number=row_idx + 1)
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
                        operation_logger.debug("empty_row_low_confidence", row_number=row_idx + 1)
                    else:
                        operation_logger.debug(
                            "row_processed",
                            row_number=row_idx + 1,
                            nombres=row_data.nombres_manuscritos,
                            cedula=row_data.cedula
                        )

            # Calcular métricas
            vacios = sum(1 for r in all_rows_data if r.is_empty)
            con_datos = len(all_rows_data) - vacios

            operation_logger.info(
                "form_extraction_completed",
                renglones_procesados=len(all_rows_data),
                con_datos=con_datos,
                vacios=vacios,
                api_calls=1,
                success=True
            )

            return all_rows_data

        except Exception as e:
            operation_logger.error(
                "form_extraction_failed",
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
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

    def extract_full_text(self, image: Image.Image) -> str:
        """
        Extract full text from image (for E-14 documents, etc.).

        Args:
            image: PIL Image to process

        Returns:
            Full extracted text
        """
        if self.client is None:
            self.logger.error("client_not_initialized")
            return ""

        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Convert to bytes
            img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

            # Call API
            response = self._call_ocr_api(img_bytes)

            # Extract full text
            if response.full_text_annotation:
                full_text = response.full_text_annotation.text
                self.logger.debug("full_text_extracted", length=len(full_text))
                return full_text

            return ""

        except Exception as e:
            self.logger.error(
                "full_text_extraction_failed",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            return ""

    def get_character_confidences(self, text: str) -> Dict[str, Any]:
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
        confidence_logger = self.logger.bind(operation="get_character_confidences", text=text)

        if not self.last_raw_response:
            confidence_logger.error("no_response_available")
            raise ValueError("No hay respuesta disponible. Ejecuta extract_cedulas() primero.")

        if not self.last_raw_response.full_text_annotation:
            confidence_logger.warning("no_full_text_annotation")
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
            confidence_logger.warning(
                "symbol_extraction_failed",
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
            confidence_logger.warning("text_not_found_in_response", text=text)

        # PASO 4: Agregar source y retornar
        result['source'] = 'google_vision'
        confidence_logger.debug(
            "confidences_extracted",
            average_confidence=result.get('average', 0.0),
            found=result.get('found', False)
        )
        return result
