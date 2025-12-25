"""Implementación de OCR usando Azure Computer Vision Read API v4.0 - Para comparación con Google Vision (REFACTORIZADA)."""
import os
from PIL import Image
from typing import List, Dict

try:
    from azure.ai.vision.imageanalysis import ImageAnalysisClient
    from azure.ai.vision.imageanalysis.models import VisualFeatures
    from azure.core.credentials import AzureKeyCredential
    AZURE_VISION_AVAILABLE = True
except ImportError:
    AZURE_VISION_AVAILABLE = False
    print("ADVERTENCIA: Azure Computer Vision no está instalado. Instalar con: pip install azure-ai-vision-imageanalysis")

from ...domain.entities import CedulaRecord
from ...domain.ports import ConfigPort
from .base_ocr_adapter import BaseOCRAdapter
from .image_converter import ImageConverter
from .vision import AzureWordExtractor, ConfidenceMapper
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
    log_ocr_extraction
)


class AzureVisionAdapter(BaseOCRAdapter):
    """
    Implementación de OCR usando Azure Computer Vision Read API v4.0.

    **REFACTORIZADA** - Ahora hereda de BaseOCRAdapter eliminando ~350 LOC de duplicación.

    Azure Computer Vision es:
    - Especializado en lectura de texto (Read API)
    - Alta precisión con números manuscritos
    - 5,000 transacciones gratis al mes (free tier)
    - Después: $1 USD por cada 1,000 transacciones

    Para 15 cédulas por imagen:
    - 5,000 imágenes gratis = 75,000 cédulas gratis/mes

    Attributes:
        config: Servicio de configuración
        client: Cliente de Azure Computer Vision
        preprocessor: Pipeline de preprocesamiento de imágenes (heredado)
        last_raw_response: Última respuesta raw de la API (heredado)
        endpoint: URL del endpoint de Azure
        max_retries: Número máximo de reintentos
        timeout: Timeout en segundos
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el servicio de OCR con Azure Computer Vision.

        Args:
            config: Servicio de configuración

        Raises:
            ImportError: Si Azure SDK no está instalado
            ValueError: Si faltan credenciales en configuración
        """
        if not AZURE_VISION_AVAILABLE:
            raise ImportError(
                "Azure Computer Vision no está instalado. "
                "Instalar con: pip install azure-ai-vision-imageanalysis"
            )

        # Inicializar clase base (preprocessor, config, last_raw_response)
        super().__init__(config)

        # Inicializar logger
        self.logger = LoggerFactory.get_ocr_logger("azure_vision")

        self.client = None
        self.endpoint = None
        self.max_retries = self.config.get('ocr.azure_vision.max_retries', 3)
        self.timeout = self.config.get('ocr.azure_vision.timeout', 30)

        self._initialize_ocr()

    def _initialize_ocr(self) -> None:
        """
        Inicializa Azure Computer Vision API.

        Busca credenciales en este orden:
        1. Variables de entorno (AZURE_VISION_ENDPOINT, AZURE_VISION_KEY)
        2. Configuración en settings.yaml

        Raises:
            ValueError: Si no se encuentran las credenciales
        """
        self.logger.debug("Inicializando cliente Azure Vision")

        # 1. Intentar desde variables de entorno
        endpoint = os.getenv('AZURE_VISION_ENDPOINT')
        subscription_key = os.getenv('AZURE_VISION_KEY')

        # 2. Si no están en env, intentar desde config
        if not endpoint:
            endpoint = self.config.get('ocr.azure_vision.endpoint')
            # Expandir variables de entorno si están en formato ${VAR}
            if endpoint and endpoint.startswith('${') and endpoint.endswith('}'):
                var_name = endpoint[2:-1]
                endpoint = os.getenv(var_name)

        if not subscription_key:
            subscription_key = self.config.get('ocr.azure_vision.subscription_key')
            # Expandir variables de entorno si están en formato ${VAR}
            if subscription_key and subscription_key.startswith('${') and subscription_key.endswith('}'):
                var_name = subscription_key[2:-1]
                subscription_key = os.getenv(var_name)

        # Validar que tenemos las credenciales
        if not endpoint or not subscription_key:
            self.logger.error(
                "Credenciales de Azure Vision no configuradas",
                solutions=[
                    "Configura AZURE_VISION_ENDPOINT y AZURE_VISION_KEY",
                    "O agrega credenciales en config/settings.yaml"
                ]
            )
            raise ValueError("Credenciales de Azure Vision no configuradas")

        try:
            # Crear cliente con credenciales
            self.client = ImageAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(subscription_key)
            )
            self.endpoint = endpoint

            self.logger.info(
                "Azure Computer Vision inicializado correctamente",
                endpoint=endpoint,
                api_version="Read API v4.0",
                optimized_for="handwritten_text"
            )

        except Exception as e:
            self.logger.error(
                "Error al inicializar Azure Computer Vision",
                error_type=type(e).__name__,
                error_message=str(e),
                solutions=[
                    "Verifica que el endpoint sea correcto",
                    "Verifica que la subscription key sea válida",
                    "Asegúrate de tener Computer Vision API habilitado en Azure"
                ]
            )
            raise

    def _call_ocr_api(self, image_bytes: bytes) -> any:
        """
        Realiza la llamada a Azure Read API.

        Args:
            image_bytes: Imagen en bytes (PNG format)

        Returns:
            Respuesta de analyze() con feature READ

        Raises:
            Exception: Si hay error en la llamada API
        """
        # Llamar a Azure Read API v4.0
        result = self.client.analyze(
            image_data=image_bytes,
            visual_features=[VisualFeatures.READ]
        )

        return result

    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen usando Azure Read API.

        Estrategia:
        1. Preprocesar imagen (mismo pipeline que Google Vision)
        2. Enviar a Azure Read API
        3. Extraer solo números de 6-10 dígitos (cédulas colombianas)
        4. Filtrar y validar longitud
        5. Retornar como CedulaRecord con Value Objects

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista de CedulaRecord extraídos
        """
        if self.client is None:
            self.logger.error("Azure Computer Vision no esta inicializado")
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

                # Llamar a Azure Read API
                log_api_call(self.logger, "azure_vision", "analyze", feature="READ", api_version="v4.0")
                result = self._call_ocr_api(img_bytes)

                # Guardar respuesta completa para análisis de confianza por dígito
                self.last_raw_response = result

                log_api_response(self.logger, "azure_vision", True, api_calls=1)

                # Procesar resultados
                records = []

                if result.read and result.read.blocks:
                    self.logger.debug(
                        "Bloques detectados por Azure Vision",
                        bloques_count=len(result.read.blocks)
                    )

                    for block in result.read.blocks:
                        for line in block.lines:
                            text = line.text
                            confidence = line.confidence if hasattr(line, 'confidence') else 0.95

                            self.logger.debug(
                                "Linea detectada",
                                text=text,
                                confidence=round(confidence, 2)
                            )

                            # Extraer números del texto usando método heredado
                            numbers = self._extract_numbers_from_text(text)

                            for num in numbers:
                                # Validar longitud de cédula colombiana (3-11 dígitos)
                                if 3 <= len(num) <= 11:
                                    # Usar factory method para crear con Value Objects
                                    record = CedulaRecord.from_primitives(
                                        cedula=num,
                                        confidence=confidence * 100  # Convertir a porcentaje
                                    )
                                    records.append(record)
                                    log_success(
                                        self.logger,
                                        "cedula_extraida",
                                        cedula=num,
                                        digits=len(num),
                                        confidence=round(confidence, 2)
                                    )
                                elif len(num) < 3:
                                    log_failure(
                                        self.logger,
                                        "cedula_descartada",
                                        reason="too_short",
                                        cedula=num,
                                        length=len(num)
                                    )
                                else:
                                    log_failure(
                                        self.logger,
                                        "cedula_descartada",
                                        reason="too_long",
                                        cedula=num,
                                        length=len(num)
                                    )

                # Eliminar duplicados usando método heredado
                unique_records = self._remove_duplicates(records)

                # Agregar métricas a la operación
                op.add_metric("cedulas_extraidas", len(unique_records))
                op.add_metric("cedulas_duplicadas", len(records) - len(unique_records))

                log_ocr_extraction(
                    self.logger,
                    "azure_vision",
                    len(unique_records),
                    duplicates=len(records) - len(unique_records)
                )

                return unique_records

            except Exception as e:
                log_error_message(self.logger, "Error en extraccion de cedulas", error=e)
                return []

    # MÉTODO REMOVIDO: extract_full_form_data ya no es necesario para API
    # Usaba RowData que es específico de la UI de escritorio

    def _extract_full_form_data_DEPRECATED(
        self,
        image: Image.Image,
        expected_rows: int = 15
    ):
        """
        Extrae datos completos del formulario (nombres + cédulas) por renglón.

        ESTRATEGIA OPTIMIZADA (UNA SOLA LLAMADA API):
        1. Enviar imagen COMPLETA a Azure Read API (1 llamada)
        2. Azure detecta TODO el texto con coordenadas
        3. Organizar texto en renglones basado en coordenada Y
        4. Separar nombres (izquierda) y cédulas (derecha) por coordenada X

        Args:
            image: Imagen PIL del formulario completo
            expected_rows: Número esperado de renglones (default: 15)

        Returns:
            Lista de RowData, uno por renglón
        """
        if self.client is None:
            self.logger.error("Azure Computer Vision no esta inicializado")
            return []

        with log_operation(
            self.logger,
            "extract_full_form_data",
            image_size=f"{image.width}x{image.height}",
            expected_rows=expected_rows
        ) as op:
            try:
                log_processing_step(
                    self.logger,
                    "Enviando imagen completa a Azure Vision API",
                    step_number=1,
                    optimization="single_api_call"
                )

                # Preprocesar imagen
                processed_image = self.preprocess_image(image)

                # Convertir a bytes
                img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

                # Llamar a Azure Read API
                log_api_call(self.logger, "azure_vision", "analyze", feature="READ", api_version="v4.0")
                result = self._call_ocr_api(img_bytes)

                log_api_response(self.logger, "azure_vision", True, api_calls=1, optimization="single_call")

                # Extraer bloques con coordenadas
                all_blocks = self._extract_text_blocks_with_coords(result)

                log_processing_step(
                    self.logger,
                    "Organizando bloques de texto en renglones",
                    step_number=2,
                    bloques_count=len(all_blocks)
                )

                # Asignar bloques a renglones por coordenada Y (método heredado)
                rows_blocks = self._assign_blocks_to_rows(
                    all_blocks,
                    processed_image.height,
                    expected_rows
                )

                # Procesar cada renglón
                all_rows_data = []

                for row_idx in range(expected_rows):
                    blocks_in_row = rows_blocks.get(row_idx, [])

                    if not blocks_in_row:
                        # Renglón vacío
                        row_data = self._create_empty_row(row_idx)
                    else:
                        # Procesar bloques usando método heredado (50% boundary para Azure)
                        row_data = self._process_row_blocks(
                            blocks_in_row,
                            row_idx,
                            processed_image.width,
                            column_boundary_ratio=0.5  # 50% para Azure Vision
                        )

                    all_rows_data.append(row_data)

                # Contar renglones con datos
                con_datos = sum(1 for row in all_rows_data if row.nombre or row.cedula)

                # Agregar métricas
                op.add_metric("renglones_totales", len(all_rows_data))
                op.add_metric("renglones_con_datos", con_datos)
                op.add_metric("renglones_vacios", len(all_rows_data) - con_datos)
                op.add_metric("api_calls", 1)

                log_info_message(
                    self.logger,
                    "Extraccion completa de formulario finalizada",
                    renglones_procesados=len(all_rows_data),
                    renglones_con_datos=con_datos,
                    api_calls=1
                )

                return all_rows_data

            except Exception as e:
                log_error_message(self.logger, "Error en extraccion de formulario completo", error=e)
                return []

    def _extract_text_blocks_with_coords(
        self,
        result
    ) -> List[Dict]:
        """
        Extrae bloques de texto con coordenadas desde resultado de Azure.

        Args:
            result: Resultado de Azure analyze()

        Returns:
            Lista de dicts con: text, x, y, confidence
        """
        blocks = []

        if not result.read or not result.read.blocks:
            return blocks

        for block in result.read.blocks:
            for line in block.lines:
                # Azure devuelve bounding box como lista de puntos
                if hasattr(line, 'bounding_polygon') and line.bounding_polygon:
                    # Tomar el primer punto como referencia (esquina superior izquierda)
                    x = line.bounding_polygon[0].x
                    y = line.bounding_polygon[0].y
                else:
                    # Fallback si no hay coordenadas
                    x = 0
                    y = 0

                confidence = line.confidence if hasattr(line, 'confidence') else 0.95

                blocks.append({
                    'text': line.text,
                    'x': x,
                    'y': y,
                    'confidence': confidence
                })

        return blocks

    def get_character_confidences(self, text: str) -> Dict[str, any]:
        """
        Extrae la confianza individual de cada caracter en el texto detectado.

        REFACTORIZADO - Ahora usa AzureWordExtractor y ConfidenceMapper.

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

        if not self.last_raw_response.read or not self.last_raw_response.read.blocks:
            log_warning_message(
                self.logger,
                "No hay datos de lectura en respuesta de Azure Vision",
                fallback="confianza_uniforme"
            )
            # Fallback: confianza uniforme
            return {
                'confidences': [0.85] * len(text),
                'positions': list(range(len(text))),
                'average': 0.85,
                'source': 'azure_vision'
            }

        # PASO 1: Extraer palabras usando AzureWordExtractor
        try:
            words = AzureWordExtractor.extract_all_words(self.last_raw_response)
        except ValueError as e:
            log_warning_message(
                self.logger,
                "Error extrayendo palabras de respuesta",
                error=str(e),
                fallback="confianza_uniforme"
            )
            return {
                'confidences': [0.85] * len(text),
                'positions': list(range(len(text))),
                'average': 0.85,
                'source': 'azure_vision'
            }

        # PASO 2: Mapear texto a confianzas usando ConfidenceMapper
        result = ConfidenceMapper.map_from_words(text, words)

        # PASO 3: Agregar advertencia si no se encontro
        if not result['found']:
            log_warning_message(
                self.logger,
                "Texto no encontrado en respuesta de Azure Vision",
                text=text,
                fallback="confianza_uniforme"
            )

        # PASO 4: Agregar source y retornar
        result['source'] = 'azure_vision'
        return result
