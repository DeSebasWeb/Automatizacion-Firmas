"""
AWS Textract OCR Adapter.

Adaptador para AWS Textract siguiendo Clean Architecture.
Extrae texto de imágenes y PDFs usando AWS Textract.
"""

import structlog
from typing import Optional, Dict, Any
from PIL import Image
import io
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.domain.ports.config_port import ConfigPort

logger = structlog.get_logger(__name__)


class TextractAdapter:
    """
    Adaptador para AWS Textract OCR.

    Implementa extracción de texto usando AWS Textract con soporte
    para imágenes y PDFs (multi-página).

    Responsabilidades:
    - Conectar con AWS Textract
    - Convertir imágenes PIL a formato bytes
    - Extraer texto completo de documentos
    - Manejar errores de AWS
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el adaptador de AWS Textract.

        Args:
            config: Servicio de configuración
        """
        self.config = config
        self.logger = logger.bind(adapter="textract")

        # Inicializar cliente de AWS Textract
        try:
            aws_region = self.config.get('aws.region', 'us-east-1')

            # Intentar obtener credenciales explícitas (pueden no estar configuradas)
            aws_access_key = None
            aws_secret_key = None

            try:
                aws_access_key = self.config.get('aws.access_key_id', None)
                aws_secret_key = self.config.get('aws.secret_access_key', None)
            except Exception:
                # Si falla la lectura del config (ej: variable de entorno no existe), ignorar
                pass

            # Si hay credenciales explícitas Y no son strings vacías, usarlas
            if aws_access_key and aws_secret_key and aws_access_key.strip() and aws_secret_key.strip():
                self.client = boto3.client(
                    'textract',
                    region_name=aws_region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key
                )
                self.logger.info("textract_client_initialized", region=aws_region, auth="explicit_credentials")
            else:
                # Usar cadena de credenciales por defecto de boto3
                # Busca en: variables de entorno → ~/.aws/credentials → IAM role
                self.client = boto3.client('textract', region_name=aws_region)

                # Obtener método de credenciales usado
                try:
                    credentials = self.client._get_credentials()
                    if credentials:
                        method = credentials.method if hasattr(credentials, 'method') else 'default'
                        self.logger.info(
                            "textract_client_initialized",
                            region=aws_region,
                            auth="default_credentials",
                            credentials_method=method
                        )
                    else:
                        self.logger.warning(
                            "textract_client_initialized_no_credentials",
                            region=aws_region
                        )
                except Exception:
                    self.logger.info("textract_client_initialized", region=aws_region, auth="default_credentials")

        except Exception as e:
            self.logger.error("textract_client_init_failed", error=str(e))
            self.client = None

    def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extrae texto completo de una imagen usando AWS Textract.

        Args:
            image: Imagen PIL a procesar

        Returns:
            Texto completo extraído (líneas concatenadas con \\n)
        """
        if self.client is None:
            self.logger.error("textract_client_not_initialized")
            return ""

        try:
            # Convertir imagen PIL a bytes
            img_bytes = self._pil_to_bytes(image)

            self.logger.info("calling_textract_api", image_size=f"{image.width}x{image.height}")

            # Llamar a Textract API
            response = self.client.detect_document_text(
                Document={'Bytes': img_bytes}
            )

            # Extraer texto línea por línea
            text = self._extract_text_from_response(response)

            blocks_count = len(response.get('Blocks', []))
            self.logger.info(
                "textract_extraction_completed",
                blocks_count=blocks_count,
                text_length=len(text)
            )

            return text

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(
                "textract_client_error",
                error_code=error_code,
                error_message=error_message
            )
            return ""

        except BotoCoreError as e:
            self.logger.error("textract_botocore_error", error=str(e))
            return ""

        except Exception as e:
            self.logger.error("textract_unexpected_error", error=str(e), error_type=type(e).__name__)
            return ""

    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """
        Extrae texto de bytes de imagen directamente.

        Args:
            image_bytes: Bytes de la imagen

        Returns:
            Texto completo extraído
        """
        if self.client is None:
            self.logger.error("textract_client_not_initialized")
            return ""

        try:
            self.logger.info("calling_textract_api", source="bytes")

            # Llamar a Textract API
            response = self.client.detect_document_text(
                Document={'Bytes': image_bytes}
            )

            # Extraer texto línea por línea
            text = self._extract_text_from_response(response)

            blocks_count = len(response.get('Blocks', []))
            self.logger.info(
                "textract_extraction_completed",
                blocks_count=blocks_count,
                text_length=len(text)
            )

            return text

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            self.logger.error(
                "textract_client_error",
                error_code=error_code,
                error_message=error_message
            )
            return ""

        except BotoCoreError as e:
            self.logger.error("textract_botocore_error", error=str(e))
            return ""

        except Exception as e:
            self.logger.error("textract_unexpected_error", error=str(e), error_type=type(e).__name__)
            return ""

    def get_raw_response(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """
        Obtiene la respuesta raw de Textract para debugging.

        Args:
            image: Imagen PIL a procesar

        Returns:
            Diccionario con la respuesta completa de Textract o None si falla
        """
        if self.client is None:
            self.logger.error("textract_client_not_initialized")
            return None

        try:
            img_bytes = self._pil_to_bytes(image)
            response = self.client.detect_document_text(
                Document={'Bytes': img_bytes}
            )
            return response

        except Exception as e:
            self.logger.error("textract_raw_response_error", error=str(e))
            return None

    def _pil_to_bytes(self, image: Image.Image, format: str = 'PNG') -> bytes:
        """
        Convierte imagen PIL a bytes.

        Args:
            image: Imagen PIL
            format: Formato de salida (PNG, JPEG)

        Returns:
            Bytes de la imagen
        """
        # Convertir a RGB si es necesario
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Guardar en buffer
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)

        return buffer.getvalue()

    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """
        Extrae texto de la respuesta de Textract preservando orden de lectura.

        AWS Textract devuelve bloques de tipo:
        - PAGE: página completa
        - LINE: línea de texto
        - WORD: palabra individual

        Para E-14, necesitamos el texto línea por línea en orden horizontal.

        Args:
            response: Respuesta de Textract API

        Returns:
            Texto completo línea por línea separado por \\n
        """
        blocks = response.get('Blocks', [])

        # Filtrar solo bloques tipo LINE (líneas de texto)
        lines = [
            block for block in blocks
            if block['BlockType'] == 'LINE'
        ]

        # Ordenar por posición vertical (Top) y luego horizontal (Left)
        # Esto asegura lectura izquierda→derecha, arriba→abajo
        lines.sort(key=lambda b: (
            round(b['Geometry']['BoundingBox']['Top'], 3),
            round(b['Geometry']['BoundingBox']['Left'], 3)
        ))

        # Extraer texto de cada línea
        text_lines = [line.get('Text', '') for line in lines]

        # Unir con saltos de línea
        full_text = '\n'.join(text_lines)

        self.logger.debug(
            "text_extraction_completed",
            total_blocks=len(blocks),
            lines_extracted=len(text_lines)
        )

        return full_text

    def is_available(self) -> bool:
        """
        Verifica si el cliente de Textract está disponible.

        Returns:
            True si el cliente está inicializado correctamente
        """
        return self.client is not None
