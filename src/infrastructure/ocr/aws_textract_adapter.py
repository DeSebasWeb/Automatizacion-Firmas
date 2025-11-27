"""Implementación de OCR usando AWS Textract - Tercer OCR para triple ensemble."""
import re
import os
import io
from PIL import Image
from typing import List, Dict
from botocore.exceptions import ClientError

try:
    import boto3
    AWS_TEXTRACT_AVAILABLE = True
except ImportError:
    AWS_TEXTRACT_AVAILABLE = False
    print("ADVERTENCIA: boto3 no está instalado. Instalar con: pip install boto3")

from ...domain.entities import CedulaRecord, RowData
from ...domain.ports import OCRPort, ConfigPort
from ..image import ImagePreprocessor


class AWSTextractAdapter(OCRPort):
    """
    Implementación de OCR usando AWS Textract - Tercer motor para triple ensemble.

    AWS Textract es:
    - Especializado en detección de texto en documentos
    - Alta precisión con texto impreso y manuscrito
    - Free tier: 1,000 páginas gratis/mes por 3 meses
    - Después: $1.50 USD por cada 1,000 páginas (~6,450 COP)

    Para 15 cédulas por imagen:
    - 1,000 imágenes gratis = 15,000 cédulas gratis/mes (primeros 3 meses)

    PREPROCESAMIENTO:
    - Reutiliza el mismo pipeline que Google Vision y Azure Vision
    - Esto asegura comparación justa entre los 3 motores OCR

    Attributes:
        config: Servicio de configuración
        client: Cliente de AWS Textract (boto3)
        preprocessor: Pipeline de preprocesamiento de imágenes
        region: Región de AWS
        max_retries: Número máximo de reintentos
        last_raw_response: Respuesta cruda de la última llamada API
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el servicio de OCR con AWS Textract.

        Args:
            config: Servicio de configuración

        Raises:
            ImportError: Si boto3 no está instalado
            ValueError: Si faltan credenciales en configuración
        """
        if not AWS_TEXTRACT_AVAILABLE:
            raise ImportError(
                "boto3 no está instalado. "
                "Instalar con: pip install boto3"
            )

        self.config = config
        self.client = None
        self.last_raw_response = None  # Para guardar respuesta completa y extraer confianza por dígito

        # Inicializar preprocesador con la MISMA configuración que otros adapters
        preprocessing_config = self.config.get('image_preprocessing', {})
        self.preprocessor = ImagePreprocessor(preprocessing_config)

        # Configuración de AWS
        self.region = None
        self.max_retries = self.config.get('ocr.aws_textract.max_retries', 3)
        self.confidence_threshold = self.config.get('ocr.aws_textract.confidence_threshold', 0.85)

        self._initialize_ocr()

    def _initialize_ocr(self) -> None:
        """
        Inicializa AWS Textract API.

        Busca credenciales en este orden:
        1. Variables de entorno (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        2. Configuración en settings.yaml
        3. Archivo ~/.aws/credentials (credenciales por defecto)
        4. IAM role (si está ejecutando en EC2/Lambda/ECS)

        Raises:
            ValueError: Si no se pueden obtener las credenciales
        """
        print("DEBUG AWS Textract: Inicializando cliente...")

        # 1. Intentar desde variables de entorno primero
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

        # 2. Si no están en env, intentar desde config
        if not access_key:
            access_key = self.config.get('ocr.aws_textract.access_key')
        if not secret_key:
            secret_key = self.config.get('ocr.aws_textract.secret_key')
        if not region:
            region = self.config.get('ocr.aws_textract.region', 'us-east-1')

        self.region = region

        try:
            # Crear cliente de Textract
            # Si access_key y secret_key están vacíos, boto3 usa credenciales por defecto
            if access_key and secret_key:
                # Usar credenciales explícitas
                self.client = boto3.client(
                    'textract',
                    region_name=region,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key
                )
                print("✓ AWS Textract inicializado con credenciales explícitas")
            else:
                # Usar credenciales por defecto (IAM role, ~/.aws/credentials, etc.)
                self.client = boto3.client(
                    'textract',
                    region_name=region
                )
                print("✓ AWS Textract inicializado con credenciales por defecto")

            print(f"✓ Región: {region}")
            print("✓ API: detect_document_text")
            print("✓ Optimizado para texto manuscrito e impreso")

        except Exception as e:
            print(f"ERROR AWS Textract: No se pudo inicializar: {e}")
            print("\n💡 Soluciones:")
            print("   1. Configurar variables de entorno:")
            print("      AWS_ACCESS_KEY_ID=tu_access_key")
            print("      AWS_SECRET_ACCESS_KEY=tu_secret_key")
            print("      AWS_DEFAULT_REGION=us-east-1")
            print("   2. O ejecutar: aws configure")
            print("   3. O agregar en config/settings.yaml:")
            print("      ocr:")
            print("        aws_textract:")
            print("          access_key: tu_access_key")
            print("          secret_key: tu_secret_key")
            print("          region: us-east-1")
            raise

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen para AWS Textract usando el MISMO pipeline que otros OCR.

        Esto es CRÍTICO para comparación justa entre los 3 proveedores.

        Aplica preprocesamiento intensivo:
        1. Upscaling (3x) - distingue 1 vs 7
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
        print(f"\nDEBUG AWS Textract: Imagen original {image.width}x{image.height}")

        # Verificar si el preprocesamiento está habilitado
        if not self.config.get('image_preprocessing.enabled', True):
            print("DEBUG AWS Textract: Preprocesamiento deshabilitado, usando imagen original")
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image

        # Aplicar el MISMO pipeline que otros OCR
        processed_image = self.preprocessor.preprocess(image)

        # AWS Textract acepta RGB, PNG, JPEG
        if processed_image.mode != 'RGB':
            processed_image = processed_image.convert('RGB')

        print(f"DEBUG AWS Textract: Imagen procesada {processed_image.width}x{processed_image.height}")

        return processed_image

    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen usando AWS Textract.

        Estrategia:
        1. Preprocesar imagen (mismo pipeline que Google/Azure)
        2. Enviar a AWS Textract detect_document_text
        3. Extraer solo números de 6-10 dígitos (cédulas colombianas)
        4. Filtrar por confianza mínima
        5. Retornar como CedulaRecord con Value Objects

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista de CedulaRecord extraídos
        """
        if self.client is None:
            print("ERROR: AWS Textract no está inicializado")
            return []

        print("DEBUG AWS Textract: Iniciando extracción de cédulas...")
        print("DEBUG AWS Textract: Enviando imagen a detect_document_text")

        try:
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)

            # Convertir imagen PIL a bytes en formato PNG
            img_byte_arr = io.BytesIO()
            processed_image.save(img_byte_arr, format='PNG')
            image_bytes = img_byte_arr.getvalue()

            # Llamar a AWS Textract
            print("DEBUG AWS Textract: Llamando a detect_document_text...")
            response = self.client.detect_document_text(
                Document={'Bytes': image_bytes}
            )

            # Guardar respuesta completa para análisis de confianza por dígito
            self.last_raw_response = response

            print("✓ AWS Textract: Respuesta recibida")

            # Procesar resultados
            records = []

            if 'Blocks' in response:
                print(f"DEBUG AWS Textract: {len(response['Blocks'])} bloques detectados")

                # Filtrar solo bloques de tipo LINE (líneas de texto)
                lines = [block for block in response['Blocks'] if block['BlockType'] == 'LINE']
                print(f"DEBUG AWS Textract: {len(lines)} líneas detectadas")

                for line in lines:
                    text = line.get('Text', '')
                    confidence = line.get('Confidence', 0.0) / 100.0  # AWS da 0-100, convertir a 0-1

                    print(f"DEBUG AWS Textract: Línea detectada: '{text}' (confidence: {confidence:.2f})")

                    # Extraer números del texto
                    numbers = self._extract_numbers_from_text(text)

                    for num in numbers:
                        # Validar longitud de cédula colombiana (3-11 dígitos)
                        if 3 <= len(num) <= 11:
                            # IMPORTANTE: NO filtrar por confianza aquí
                            # El Triple Ensemble se encarga de validar con votación 3-way
                            # Crear registro incluso con confianza baja
                            record = CedulaRecord.from_primitives(
                                cedula=num,
                                confidence=confidence * 100  # Convertir a porcentaje
                            )
                            records.append(record)

                            # Log diferenciado para debugging
                            if confidence >= self.confidence_threshold:
                                print(f"✓ Cédula extraída: '{num}' ({len(num)} dígitos)")
                            else:
                                print(f"⚠ Cédula extraída (baja conf): '{num}' ({confidence*100:.1f}%)")
                        elif len(num) < 3:
                            print(f"✗ Descartada (muy corta): '{num}' ({len(num)} dígitos)")
                        else:
                            print(f"✗ Descartada (muy larga): '{num}' ({len(num)} dígitos)")

            # Eliminar duplicados
            unique_records = self._remove_duplicates(records)

            print(f"DEBUG AWS Textract: Total cédulas únicas: {len(unique_records)}")

            return unique_records

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'ProvisionedThroughputExceededException':
                print("ERROR AWS Textract: Rate limit excedido (demasiadas peticiones)")
                print("💡 Espera unos segundos y vuelve a intentar")
            elif error_code == 'InvalidParameterException':
                print("ERROR AWS Textract: Imagen inválida o formato no soportado")
                print("💡 Verifica que la imagen sea PNG o JPEG válido")
            else:
                print(f"ERROR AWS Textract ClientError: {error_code} - {e}")

            return []

        except Exception as e:
            print(f"ERROR AWS Textract: {e}")
            import traceback
            traceback.print_exc()
            return []

    def extract_full_form_data(
        self,
        image: Image.Image,
        expected_rows: int = 15
    ) -> List[RowData]:
        """
        Extrae datos completos del formulario (nombres + cédulas) por renglón.

        ESTRATEGIA OPTIMIZADA (UNA SOLA LLAMADA API):
        1. Enviar imagen COMPLETA a AWS Textract (1 llamada)
        2. AWS detecta TODO el texto con coordenadas
        3. Organizar texto en renglones basado en coordenada Y
        4. Separar nombres (izquierda) y cédulas (derecha) por coordenada X

        Args:
            image: Imagen PIL del formulario completo
            expected_rows: Número esperado de renglones (default: 15)

        Returns:
            Lista de RowData, uno por renglón
        """
        if self.client is None:
            print("ERROR: AWS Textract no está inicializado")
            return []

        print(f"\nDEBUG AWS Textract: Extrayendo formulario completo ({expected_rows} renglones)")
        print("DEBUG AWS Textract: Enviando imagen COMPLETA a API (1 sola llamada)")

        try:
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)

            # Convertir a bytes
            img_byte_arr = io.BytesIO()
            processed_image.save(img_byte_arr, format='PNG')
            image_bytes = img_byte_arr.getvalue()

            # Llamar a AWS Textract
            print("DEBUG AWS Textract: Llamando a detect_document_text...")
            response = self.client.detect_document_text(
                Document={'Bytes': image_bytes}
            )

            print("✓ AWS Textract: Respuesta recibida (1 llamada API)")

            # Extraer bloques con coordenadas
            all_blocks = self._extract_text_blocks_with_coords(response, processed_image.height)

            # Asignar bloques a renglones por coordenada Y
            rows_blocks = self._assign_blocks_to_rows(all_blocks, processed_image.height, expected_rows)

            # Procesar cada renglón
            all_rows_data = []

            for row_idx in range(expected_rows):
                blocks_in_row = rows_blocks.get(row_idx, [])
                row_data = self._process_row_blocks(blocks_in_row, row_idx, processed_image.width)
                all_rows_data.append(row_data)

            print(f"✓ AWS Textract: Total renglones procesados: {len(all_rows_data)}")
            print(f"✓ AWS Textract: Total llamadas API: 1 (óptimo)")

            return all_rows_data

        except Exception as e:
            print(f"ERROR AWS Textract: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_text_blocks_with_coords(
        self,
        response: Dict,
        image_height: int
    ) -> List[Dict]:
        """
        Extrae bloques de texto con coordenadas desde resultado de AWS Textract.

        AWS Textract retorna bloques con Geometry.BoundingBox que contiene:
        - Left: coordenada X normalizada (0-1)
        - Top: coordenada Y normalizada (0-1)
        - Width: ancho normalizado
        - Height: alto normalizado

        Args:
            response: Resultado de detect_document_text
            image_height: Alto de la imagen para desnormalización

        Returns:
            Lista de dicts con: text, x, y, confidence
        """
        blocks = []

        if 'Blocks' not in response:
            return blocks

        # Filtrar solo bloques de tipo LINE
        lines = [block for block in response['Blocks'] if block['BlockType'] == 'LINE']

        for line in lines:
            text = line.get('Text', '').strip()
            confidence = line.get('Confidence', 0.0) / 100.0  # Convertir 0-100 a 0-1

            # Obtener coordenadas del bounding box
            if 'Geometry' in line and 'BoundingBox' in line['Geometry']:
                bbox = line['Geometry']['BoundingBox']
                # AWS da coordenadas normalizadas (0-1), no necesitamos desnormalizar
                x = bbox.get('Left', 0.0)
                y = bbox.get('Top', 0.0)

                blocks.append({
                    'text': text,
                    'x': x,
                    'y': y,
                    'confidence': confidence
                })

        return blocks

    def _assign_blocks_to_rows(
        self,
        blocks: List[Dict],
        image_height: int,
        num_rows: int
    ) -> Dict[int, List[Dict]]:
        """
        Asigna bloques de texto a renglones basado en coordenada Y.

        AWS Textract usa coordenadas normalizadas (0-1), así que podemos
        dividir directamente.

        Args:
            blocks: Lista de bloques con coordenadas
            image_height: Alto total de la imagen (no usado, coords son normalizadas)
            num_rows: Número de renglones esperados

        Returns:
            Dict donde key=row_index, value=lista de bloques en ese renglón
        """
        rows_blocks = {}

        for block in blocks:
            # Calcular índice de renglón basado en Y normalizada (0-1)
            row_index = int(block['y'] * num_rows)

            # Asegurar que esté en rango válido
            row_index = max(0, min(row_index, num_rows - 1))

            if row_index not in rows_blocks:
                rows_blocks[row_index] = []

            rows_blocks[row_index].append(block)

        return rows_blocks

    def _process_row_blocks(
        self,
        blocks: List[Dict],
        row_index: int,
        image_width: int
    ) -> RowData:
        """
        Procesa bloques de un renglón para extraer nombres y cédula.

        Estrategia:
        - Bloques a la IZQUIERDA (< 50% width) → nombres
        - Bloques a la DERECHA (>= 50% width) → cédula

        Args:
            blocks: Lista de bloques en este renglón
            row_index: Índice del renglón
            image_width: Ancho total de la imagen (no usado, coords normalizadas)

        Returns:
            RowData con nombres y cédula extraídos
        """
        nombres_parts = []
        cedula_parts = []
        confidence_data = {'nombres': 0.0, 'cedula': 0.0}

        # AWS usa coordenadas normalizadas, 0.5 = 50%
        middle_x = 0.5

        for block in blocks:
            text = block['text'].strip()
            x = block['x']
            conf = block['confidence']

            if x < middle_x:
                # Está a la izquierda → nombres
                nombres_parts.append(text)
                confidence_data['nombres'] = max(confidence_data['nombres'], conf)
            else:
                # Está a la derecha → cédula
                cedula_parts.append(text)
                confidence_data['cedula'] = max(confidence_data['cedula'], conf)

        # Unir partes
        nombres = ' '.join(nombres_parts).strip()
        cedula_raw = ' '.join(cedula_parts).strip()

        # Limpiar cédula (solo números)
        cedula = self._clean_cedula(cedula_raw)

        # Crear texto raw para debugging
        raw_text = f"{nombres} | {cedula_raw}".strip()

        # Detectar si es renglón vacío
        min_confidence = self.config.get('ocr.aws_textract.confidence_threshold', 0.30)
        is_empty = (
            (not nombres and not cedula) or
            (confidence_data.get('nombres', 0) < min_confidence and confidence_data.get('cedula', 0) < min_confidence) or
            (len(nombres) < 2 and len(cedula) < 6)
        )

        # Usar factory method para crear RowData con Value Objects
        return RowData.from_primitives(
            row_index=row_index,
            nombres_manuscritos=nombres,
            cedula=cedula,
            is_empty=is_empty,
            confidence=confidence_data,
            raw_text=raw_text
        )

    def _extract_numbers_from_text(self, text: str) -> List[str]:
        """
        Extrae números del texto reconocido.

        ESTRATEGIA MEJORADA:
        Cuando hay letras entre dígitos (ej: "107 116C1931"), NO separar
        en múltiples números. En su lugar, eliminar TODAS las letras y
        espacios, dejando solo dígitos continuos.

        Esto evita que una cédula de 10 dígitos se divida en múltiples fragmentos.

        Args:
            text: Texto reconocido por AWS Textract (ej: "107 116C1931")

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

    def _clean_cedula(self, cedula_text: str) -> str:
        """
        Limpia texto de cédula para extraer solo números.

        Args:
            cedula_text: Texto crudo de cédula

        Returns:
            String con solo dígitos
        """
        # Remover todo lo que no sea dígito
        cedula_clean = re.sub(r'[^\d]', '', cedula_text)
        return cedula_clean

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
            # Usar .value ya que cedula es CedulaNumber (Value Object)
            cedula_key = record.cedula.value
            # Comparar confidence usando .as_percentage()
            if cedula_key not in seen or record.confidence.as_percentage() > seen[cedula_key].confidence.as_percentage():
                seen[cedula_key] = record

        return list(seen.values())

    def get_character_confidences(self, text: str) -> Dict[str, any]:
        """
        Extrae la confianza individual de cada carácter en el texto detectado.

        AWS Textract retorna confianza a nivel de palabra (WORD blocks).
        Para cada carácter, usamos la confianza de la palabra que lo contiene.

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
                'confidences': [0.96, 0.96, 0.98, 0.98, ...],
                'positions': [0, 1, 2, 3, ...],
                'average': 0.970,
                'source': 'aws_textract'
            }

        Raises:
            ValueError: Si no hay respuesta disponible (ejecuta extract_cedulas() primero)
        """
        if not self.last_raw_response:
            raise ValueError("No hay respuesta disponible. Ejecuta extract_cedulas() primero.")

        if 'Blocks' not in self.last_raw_response:
            print("ADVERTENCIA: No hay bloques en respuesta de AWS Textract")
            # Fallback: confianza uniforme
            return {
                'confidences': [0.85] * len(text),
                'positions': list(range(len(text))),
                'average': 0.85,
                'source': 'aws_textract'
            }

        # Limpiar el texto buscado (eliminar espacios, puntos, etc)
        text_clean = text.replace(' ', '').replace('.', '').replace(',', '').replace('-', '')

        # Extraer todas las palabras con sus confianzas
        all_words = []

        # Filtrar solo bloques de tipo WORD
        words = [block for block in self.last_raw_response['Blocks'] if block['BlockType'] == 'WORD']

        for word in words:
            word_text = word.get('Text', '')
            word_confidence = word.get('Confidence', 95.0) / 100.0  # Convertir 0-100 a 0-1

            all_words.append({
                'text': word_text,
                'confidence': word_confidence
            })

        # Construir string de todas las palabras (solo dígitos)
        all_text = ''.join([w['text'] for w in all_words])
        all_text_clean = ''.join([c for c in all_text if c.isdigit()])

        # Intentar encontrar el texto buscado en el texto detectado
        confidences = []
        positions = []

        if text_clean in all_text_clean:
            # Encontrado - extraer confianzas correspondientes
            start_idx = all_text_clean.index(text_clean)

            # Mapear índices a confianzas de palabras
            digit_counter = 0
            for word in all_words:
                word_text = word['text']
                word_conf = word['confidence']

                # Procesar cada carácter de la palabra
                for char in word_text:
                    if char.isdigit():
                        if digit_counter >= start_idx and digit_counter < start_idx + len(text_clean):
                            # Este dígito es parte de la cédula buscada
                            confidences.append(word_conf)
                            positions.append(digit_counter - start_idx)
                        digit_counter += 1
        else:
            # No encontrado - usar confianza uniforme basada en promedio general
            print(f"ADVERTENCIA: Texto '{text_clean}' no encontrado en respuesta de AWS Textract")
            print(f"DEBUG: Texto detectado: '{all_text_clean[:100]}...'")

            # Calcular confianza promedio de todas las palabras con dígitos
            numeric_words = [w for w in all_words if any(c.isdigit() for c in w['text'])]
            avg_conf = sum(w['confidence'] for w in numeric_words) / len(numeric_words) if numeric_words else 0.90

            confidences = [avg_conf] * len(text_clean)
            positions = list(range(len(text_clean)))

        # Calcular promedio
        average = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            'confidences': confidences,
            'positions': positions,
            'average': average,
            'source': 'aws_textract'
        }
