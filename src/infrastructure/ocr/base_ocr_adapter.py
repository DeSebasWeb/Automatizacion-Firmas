"""Clase base abstracta para adaptadores OCR - Elimina duplicación de código."""
import re
from abc import ABC, abstractmethod
from typing import List, Dict
from PIL import Image

from ...domain.entities import CedulaRecord, RowData
from ...domain.ports import OCRPort, ConfigPort
from ..image import ImagePreprocessor


class BaseOCRAdapter(OCRPort, ABC):
    """
    Clase base abstracta para adaptadores OCR.

    Proporciona implementación común para:
    - Preprocesamiento de imágenes
    - Extracción de números del texto
    - Limpieza y corrección de cédulas
    - Eliminación de duplicados
    - Asignación de bloques a renglones
    - Procesamiento de bloques por renglón

    Las clases hijas (GoogleVisionAdapter, AzureVisionAdapter) solo necesitan
    implementar la lógica específica de llamadas a la API.

    Attributes:
        config: Servicio de configuración
        preprocessor: Pipeline de preprocesamiento de imágenes
        last_raw_response: Última respuesta raw de la API (para análisis de confianza)
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el adaptador OCR base.

        Args:
            config: Servicio de configuración
        """
        self.config = config
        self.last_raw_response = None

        # Inicializar preprocesador con configuración
        preprocessing_config = self.config.get('image_preprocessing', {})
        self.preprocessor = ImagePreprocessor(preprocessing_config)

    @abstractmethod
    def _initialize_ocr(self) -> None:
        """
        Inicializa el cliente OCR específico (Google, Azure, etc).

        Debe ser implementado por cada adaptador concreto.
        """
        pass

    @abstractmethod
    def _call_ocr_api(self, image_bytes: bytes) -> any:
        """
        Realiza la llamada a la API OCR específica.

        Args:
            image_bytes: Imagen en bytes (PNG format)

        Returns:
            Respuesta raw de la API (formato específico de cada proveedor)

        Raises:
            Exception: Si hay error en la llamada API
        """
        pass

    @abstractmethod
    def _extract_text_blocks_with_coords(self, response: any) -> List[Dict]:
        """
        Extrae bloques de texto con coordenadas desde respuesta de API.

        Args:
            response: Respuesta raw de la API

        Returns:
            Lista de dicts con: text, x, y, confidence
        """
        pass

    # ========== MÉTODOS COMUNES (NO DUPLICADOS) ==========

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen usando pipeline robusto.

        Aplica preprocesamiento intensivo para maximizar precisión:
        1. Upscaling (3x-4x) - CRÍTICO para distinguir 1 vs 7
        2. Conversión a escala de grises
        3. Reducción de ruido (fastNlMeansDenoising)
        4. Aumento de contraste adaptativo (CLAHE)
        5. Sharpening para nitidez
        6. Binarización método Otsu (opcional)
        7. Operaciones morfológicas (opcional)

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada y optimizada en RGB
        """
        print(f"\nDEBUG OCR: Imagen original {image.width}x{image.height}")

        # Verificar si el preprocesamiento está habilitado
        if not self.config.get('image_preprocessing.enabled', True):
            print("DEBUG OCR: Preprocesamiento deshabilitado, usando imagen original")
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image

        # Aplicar pipeline completo de preprocesamiento
        processed_image = self.preprocessor.preprocess(image)

        # Convertir a RGB si es necesario (ambos proveedores lo requieren)
        if processed_image.mode != 'RGB':
            processed_image = processed_image.convert('RGB')

        print(f"DEBUG OCR: Imagen procesada {processed_image.width}x{processed_image.height}")

        return processed_image

    def _extract_numbers_from_text(self, text: str) -> List[str]:
        """
        Extrae números del texto reconocido.

        ESTRATEGIA MEJORADA:
        Cuando hay letras entre dígitos (ej: "107 116C1931"), NO separar
        en múltiples números. En su lugar, eliminar TODAS las letras y
        espacios, dejando solo dígitos continuos.

        Esto evita que una cédula de 10 dígitos se divida en múltiples fragmentos.

        Args:
            text: Texto reconocido por OCR (ej: "107 116C1931")

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

    def _corregir_errores_ocr_cedula(self, cedula: str) -> str:
        """
        Corrige errores comunes de OCR en cédulas manuscritas.

        OPTIMIZACIÓN CRÍTICA:
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
        image_width: int,
        column_boundary_ratio: float = 0.6
    ) -> RowData:
        """
        Procesa bloques de un renglón separando nombres y cédula.

        Separa los bloques en dos columnas basándose en coordenada X:
        - Columna izquierda (0-boundary% del ancho): NOMBRES
        - Columna derecha (boundary%-100% del ancho): CÉDULA

        Args:
            blocks: Bloques de texto del renglón
            row_index: Índice del renglón
            image_width: Ancho de la imagen
            column_boundary_ratio: Ratio para separar columnas (default: 0.6 = 60%)

        Returns:
            RowData con nombres, cédula y confianza
        """
        # Límite de columnas
        column_boundary = image_width * column_boundary_ratio

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
        min_confidence = self.config.get('ocr.confidence_threshold', 0.30)
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
