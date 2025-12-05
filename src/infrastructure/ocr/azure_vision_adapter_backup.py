"""Implementación de OCR usando Azure Computer Vision Read API v4.0 - Para comparación con Google Vision."""
import re
import os
import time
from PIL import Image
from typing import List, Dict
import io

try:
    from azure.ai.vision.imageanalysis import ImageAnalysisClient
    from azure.ai.vision.imageanalysis.models import VisualFeatures
    from azure.core.credentials import AzureKeyCredential
    AZURE_VISION_AVAILABLE = True
except ImportError:
    AZURE_VISION_AVAILABLE = False
    print("ADVERTENCIA: Azure Computer Vision no está instalado. Instalar con: pip install azure-ai-vision-imageanalysis")

from ...domain.entities import CedulaRecord, RowData
from ...domain.ports import OCRPort, ConfigPort
from ..image import ImagePreprocessor


class AzureVisionAdapter(OCRPort):
    """
    Implementación de OCR usando Azure Computer Vision Read API v4.0.

    Azure Computer Vision es:
    - Especializado en lectura de texto (Read API)
    - Alta precisión con números manuscritos
    - 5,000 transacciones gratis al mes (free tier)
    - Después: $1 USD por cada 1,000 transacciones

    Para 15 cédulas por imagen:
    - 5,000 imágenes gratis = 75,000 cédulas gratis/mes

    PREPROCESAMIENTO:
    - Reutiliza el mismo pipeline que Google Vision para comparación justa
    - Upscaling 3x, denoising, CLAHE, sharpening, etc.

    Attributes:
        config: Servicio de configuración
        client: Cliente de Azure Computer Vision
        preprocessor: Pipeline de preprocesamiento de imágenes
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

        self.config = config
        self.client = None
        self.last_raw_response = None  # Para guardar respuesta completa y extraer confianza por dígito

        # Inicializar preprocesador con la MISMA configuración que Google Vision
        preprocessing_config = self.config.get('image_preprocessing', {})
        self.preprocessor = ImagePreprocessor(preprocessing_config)

        # Configuración de Azure
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
        print("DEBUG Azure Vision: Inicializando cliente...")

        # 1. Intentar desde variables de entorno
        endpoint = os.getenv('AZURE_VISION_ENDPOINT')
        subscription_key = os.getenv('AZURE_VISION_KEY')

        # 2. Si no están en env, intentar desde config
        if not endpoint:
            endpoint = self.config.get('ocr.azure_vision.endpoint')
            # Expandir variables de entorno si están en formato ${VAR}
            if endpoint and endpoint.startswith('${') and endpoint.endswith('}'):
                var_name = endpoint[2:-1]  # Extraer nombre de variable
                endpoint = os.getenv(var_name)

        if not subscription_key:
            subscription_key = self.config.get('ocr.azure_vision.subscription_key')
            # Expandir variables de entorno si están en formato ${VAR}
            if subscription_key and subscription_key.startswith('${') and subscription_key.endswith('}'):
                var_name = subscription_key[2:-1]  # Extraer nombre de variable
                subscription_key = os.getenv(var_name)

        # Validar que tenemos las credenciales
        if not endpoint or not subscription_key:
            error_msg = (
                "ERROR Azure Vision: Faltan credenciales.\n\n"
                "💡 Configura las variables de entorno:\n"
                "   AZURE_VISION_ENDPOINT=https://tu-recurso.cognitiveservices.azure.com/\n"
                "   AZURE_VISION_KEY=tu_subscription_key\n\n"
                "O agrega en config/settings.yaml:\n"
                "   ocr:\n"
                "     azure_vision:\n"
                "       endpoint: https://tu-recurso.cognitiveservices.azure.com/\n"
                "       subscription_key: tu_key\n"
            )
            print(error_msg)
            raise ValueError("Credenciales de Azure Vision no configuradas")

        try:
            # Crear cliente con credenciales
            self.client = ImageAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(subscription_key)
            )
            self.endpoint = endpoint

            print("✓ Azure Computer Vision inicializado correctamente")
            print(f"✓ Endpoint: {endpoint}")
            print("✓ Read API v4.0 - Optimizado para texto manuscrito")

        except Exception as e:
            print(f"ERROR Azure Vision: No se pudo inicializar: {e}")
            print("\n💡 Soluciones:")
            print("   1. Verifica que el endpoint sea correcto")
            print("   2. Verifica que la subscription key sea válida")
            print("   3. Asegúrate de tener Computer Vision API habilitado en Azure")
            raise

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen para Azure Vision usando el MISMO pipeline que Google Vision.

        Esto es CRÍTICO para comparación justa entre ambos proveedores.

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
        print(f"\nDEBUG Azure Vision: Imagen original {image.width}x{image.height}")

        # Verificar si el preprocesamiento está habilitado
        if not self.config.get('image_preprocessing.enabled', True):
            print("DEBUG Azure Vision: Preprocesamiento deshabilitado, usando imagen original")
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image

        # Aplicar el MISMO pipeline que Google Vision
        processed_image = self.preprocessor.preprocess(image)

        # Azure Vision acepta RGB, PNG, JPEG
        if processed_image.mode != 'RGB':
            processed_image = processed_image.convert('RGB')

        print(f"DEBUG Azure Vision: Imagen procesada {processed_image.width}x{processed_image.height}")

        return processed_image

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
            print("ERROR: Azure Computer Vision no está inicializado")
            return []

        print("DEBUG Azure Vision: Iniciando extracción de cédulas...")
        print("DEBUG Azure Vision: Enviando imagen a Read API v4.0")

        try:
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)

            # Convertir imagen PIL a bytes
            img_byte_arr = io.BytesIO()
            processed_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Llamar a Azure Read API v4.0
            print("DEBUG Azure Vision: Llamando a analyze() con feature READ...")
            result = self.client.analyze(
                image_data=img_byte_arr,
                visual_features=[VisualFeatures.READ]
            )

            # Guardar respuesta completa para análisis de confianza por dígito
            self.last_raw_response = result

            print("✓ Azure Vision: Respuesta recibida")

            # Procesar resultados
            records = []

            if result.read and result.read.blocks:
                print(f"DEBUG Azure Vision: {len(result.read.blocks)} bloques detectados")

                for block in result.read.blocks:
                    for line in block.lines:
                        text = line.text
                        confidence = line.confidence if hasattr(line, 'confidence') else 0.95

                        print(f"DEBUG Azure Vision: Línea detectada: '{text}' (confidence: {confidence:.2f})")

                        # Extraer números del texto
                        numbers = self._extract_numbers_from_text(text)

                        for num in numbers:
                            # Validar longitud de cédula colombiana (6-10 dígitos)
                            if 3 <= len(num) <= 11:
                                # Usar factory method para crear con Value Objects
                                record = CedulaRecord.from_primitives(
                                    cedula=num,
                                    confidence=confidence * 100  # Convertir a porcentaje
                                )
                                records.append(record)
                                print(f"✓ Cédula extraída: '{num}' ({len(num)} dígitos)")
                            elif len(num) < 3:
                                print(f"✗ Descartada (muy corta): '{num}' ({len(num)} dígitos)")
                            else:
                                print(f"✗ Descartada (muy larga): '{num}' ({len(num)} dígitos)")

            # Eliminar duplicados
            unique_records = self._remove_duplicates(records)

            print(f"DEBUG Azure Vision: Total cédulas únicas: {len(unique_records)}")

            return unique_records

        except Exception as e:
            print(f"ERROR Azure Vision: {e}")
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
            print("ERROR: Azure Computer Vision no está inicializado")
            return []

        print(f"\nDEBUG Azure Vision: Extrayendo formulario completo ({expected_rows} renglones)")
        print("DEBUG Azure Vision: Enviando imagen COMPLETA a API (1 sola llamada)")

        try:
            # Preprocesar imagen
            processed_image = self.preprocess_image(image)

            # Convertir a bytes
            img_byte_arr = io.BytesIO()
            processed_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Llamar a Azure Read API
            print("DEBUG Azure Vision: Llamando a analyze() con feature READ...")
            result = self.client.analyze(
                image_data=img_byte_arr,
                visual_features=[VisualFeatures.READ]
            )

            print("✓ Azure Vision: Respuesta recibida (1 llamada API)")

            # Extraer bloques con coordenadas
            all_blocks = self._extract_text_blocks_with_coords(result, processed_image.height)

            # Asignar bloques a renglones por coordenada Y
            rows_blocks = self._assign_blocks_to_rows(all_blocks, processed_image.height, expected_rows)

            # Procesar cada renglón
            all_rows_data = []

            for row_idx in range(expected_rows):
                blocks_in_row = rows_blocks.get(row_idx, [])
                row_data = self._process_row_blocks(blocks_in_row, row_idx, processed_image.width)
                all_rows_data.append(row_data)

            print(f"✓ Azure Vision: Total renglones procesados: {len(all_rows_data)}")
            print(f"✓ Azure Vision: Total llamadas API: 1 (óptimo)")

            return all_rows_data

        except Exception as e:
            print(f"ERROR Azure Vision: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_text_blocks_with_coords(
        self,
        result,
        image_height: int
    ) -> List[Dict]:
        """
        Extrae bloques de texto con coordenadas desde resultado de Azure.

        Args:
            result: Resultado de Azure analyze()
            image_height: Alto de la imagen para normalización

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

    def _assign_blocks_to_rows(
        self,
        blocks: List[Dict],
        image_height: int,
        num_rows: int
    ) -> Dict[int, List[Dict]]:
        """
        Asigna bloques de texto a renglones basado en coordenada Y.

        Similar a la lógica de GoogleVisionAdapter.

        Args:
            blocks: Lista de bloques con coordenadas
            image_height: Alto total de la imagen
            num_rows: Número de renglones esperados

        Returns:
            Dict donde key=row_index, value=lista de bloques en ese renglón
        """
        row_height = image_height / num_rows
        rows_blocks = {}

        for block in blocks:
            # Calcular índice de renglón basado en Y
            row_index = int(block['y'] / row_height)

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
            image_width: Ancho total de la imagen

        Returns:
            RowData con nombres y cédula extraídos
        """
        nombres_parts = []
        cedula_parts = []
        confidence_data = {'nombres': 0.0, 'cedula': 0.0}

        middle_x = image_width / 2

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
        min_confidence = self.config.get('ocr.azure_vision.confidence_threshold', 0.30)
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
            text: Texto reconocido por Azure (ej: "107 116C1931")

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

        Azure Read API v4.0 retorna confianza a nivel de palabra en:
        - result.read.blocks[].lines[].words[]

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
                'confidences': [0.97, 0.94, 0.98, 0.95, ...],
                'positions': [0, 1, 2, 3, ...],
                'average': 0.962,
                'source': 'azure_vision'
            }

        Raises:
            ValueError: Si no hay respuesta disponible (ejecuta extract_cedulas() primero)
        """
        if not self.last_raw_response:
            raise ValueError("No hay respuesta disponible. Ejecuta extract_cedulas() primero.")

        if not self.last_raw_response.read or not self.last_raw_response.read.blocks:
            print("ADVERTENCIA: No hay datos de lectura en respuesta de Azure Vision")
            # Fallback: confianza uniforme
            return {
                'confidences': [0.85] * len(text),
                'positions': list(range(len(text))),
                'average': 0.85,
                'source': 'azure_vision'
            }

        # Limpiar el texto buscado (eliminar espacios, puntos, etc)
        text_clean = text.replace(' ', '').replace('.', '').replace(',', '').replace('-', '')

        # Extraer todas las palabras con sus confianzas
        all_words = []

        # Iterar sobre la estructura de Azure Vision Read API
        for block in self.last_raw_response.read.blocks:
            for line in block.lines:
                # Azure Read API da words con confianza
                if hasattr(line, 'words') and line.words:
                    for word in line.words:
                        word_text = word.text
                        word_confidence = word.confidence if hasattr(word, 'confidence') else 0.95

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
            print(f"ADVERTENCIA: Texto '{text_clean}' no encontrado en respuesta de Azure Vision")
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
            'source': 'azure_vision'
        }

    def _extract_text_blocks_with_positions(self, result) -> List[Dict]:
        """
        Extrae palabras individuales con coordenadas (NO líneas completas).

        CAMBIO IMPORTANTE: Ahora extrae a nivel de PALABRA en lugar de LÍNEA.
        Esto permite que filter_nombres() agrupe correctamente nombres que están
        separados espacialmente, igual que en Google Vision.

        Args:
            result: Resultado de Azure Read API

        Returns:
            Lista de palabras con {text, x, y, width, height, confidence}
        """
        word_blocks = []

        if not result.read or not result.read.blocks:
            return word_blocks

        for block in result.read.blocks:
            for line in block.lines:
                # Extraer cada palabra individual de la línea
                if not hasattr(line, 'words') or not line.words:
                    continue

                for word in line.words:
                    # Azure retorna polygon con 8 puntos [x1,y1, x2,y2, x3,y3, x4,y4]
                    if not hasattr(word, 'polygon') or not word.polygon:
                        continue

                    polygon = word.polygon
                    if len(polygon) < 8:
                        continue

                    # Extraer coordenadas x, y
                    x_coords = [polygon[i] for i in range(0, len(polygon), 2)]
                    y_coords = [polygon[i] for i in range(1, len(polygon), 2)]

                    min_x = min(x_coords)
                    max_x = max(x_coords)
                    min_y = min(y_coords)
                    max_y = max(y_coords)

                    # Confianza de la palabra
                    word_confidence = word.confidence if hasattr(word, 'confidence') else 0.95

                    if word.text.strip():
                        word_blocks.append({
                            'text': word.text.strip(),
                            'x': min_x,
                            'y': min_y,
                            'width': max_x - min_x,
                            'height': max_y - min_y,
                            'confidence': word_confidence
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
        print("AZURE VISION: Extracción de pares nombre-cédula")
        print("="*80)

        # 1. Preprocesar imagen
        processed_image = self.preprocess_image(image)

        # 2. Extraer TODO el texto con coordenadas
        print("[1/4] Extrayendo texto con coordenadas...")

        # Convertir imagen a bytes
        img_byte_arr = io.BytesIO()
        if processed_image.mode != 'RGB':
            processed_image = processed_image.convert('RGB')
        processed_image.save(img_byte_arr, format='PNG')
        image_data = img_byte_arr.getvalue()

        # Llamar a Azure Read API
        result = self.client.analyze(
            image_data=image_data,
            visual_features=[VisualFeatures.READ]
        )

        self.last_raw_response = result

        # Extraer bloques con posiciones
        all_blocks = self._extract_text_blocks_with_positions(result)
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
