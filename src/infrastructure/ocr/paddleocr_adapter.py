"""Implementación de OCR usando PaddleOCR (alternativa ligera a EasyOCR)."""
import re
import numpy as npz
from PIL import Image
from typing import List

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("ADVERTENCIA: PaddleOCR no está instalado. Instalar con: pip install paddleocr")

from ...domain.entities import CedulaRecord
from ...domain.ports import OCRPort, ConfigPort


class PaddleOCRAdapter(OCRPort):
    """
    Implementación de OCR usando PaddleOCR.

    PaddleOCR es:
    - Más ligero que EasyOCR
    - Excelente para escritura manual
    - Rápido en CPU
    - Soporta múltiples idiomas

    Attributes:
        config: Servicio de configuración
        ocr: Motor de PaddleOCR
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el servicio de OCR con PaddleOCR.

        Args:
            config: Servicio de configuración
        """
        if not PADDLEOCR_AVAILABLE:
            raise ImportError("PaddleOCR no está instalado. Instalar con: pip install paddleocr")

        self.config = config
        self.ocr = None
        self._initialize_ocr()

    def _initialize_ocr(self) -> None:
        """Inicializa PaddleOCR."""
        # Obtener configuración
        lang = self.config.get('ocr.paddle_lang', 'es')  # es, en, ch, etc.

        print(f"DEBUG PaddleOCR: Inicializando con idioma '{lang}'")

        try:
            # Crear motor de PaddleOCR con parámetros mínimos
            # use_angle_cls=True: detecta texto rotado
            # lang='es': español (cambia según necesidad)
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang
            )
            print("DEBUG PaddleOCR: Inicializado correctamente")
        except Exception as e:
            print(f"ERROR PaddleOCR: No se pudo inicializar: {e}")
            raise

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen para mejorar el OCR.

        PaddleOCR es robusto, no necesita mucho preprocesamiento.

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada
        """
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')

        print(f"DEBUG PaddleOCR Preprocess: Imagen {image.width}x{image.height}")

        return image

    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen usando PaddleOCR.

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista de registros de cédulas extraídas
        """
        if self.ocr is None:
            print("ERROR: PaddleOCR no está inicializado")
            return []

        print("DEBUG PaddleOCR: Iniciando extracción...")

        # Convertir PIL a numpy array
        img_array = np.array(image)

        try:
            # Ejecutar OCR
            # Retorna: [[[bbox], (text, confidence)], ...]
            results = self.ocr.ocr(img_array, cls=True)

            if not results or results[0] is None:
                print("DEBUG PaddleOCR: No se detectó texto")
                return []

            print(f"DEBUG PaddleOCR: Detectados {len(results[0])} elementos")

            records = []

            for line in results[0]:
                bbox, (text, confidence) = line

                # Limpiar texto - extraer solo números
                text_clean = text.strip().replace(' ', '').replace('.', '').replace(',', '')

                print(f"DEBUG PaddleOCR: '{text}' -> '{text_clean}' con confianza {confidence*100:.1f}%")

                # Extraer números del texto
                numbers = re.findall(r'\d+', text_clean)

                for num in numbers:
                    # Validar longitud de cédula (3-11 dígitos)
                    if 3 <= len(num) <= 11:
                        # PaddleOCR da buena confianza, umbral bajo
                        if confidence >= 0.3:  # 30% mínimo
                            # Usar factory method para crear con Value Objects
                            record = CedulaRecord.from_primitives(
                                cedula=num,
                                confidence=confidence * 100  # Convertir a porcentaje
                            )
                            records.append(record)

                            print(f"✓ Cédula aceptada: '{num}' ({confidence*100:.1f}%)")

            # Eliminar duplicados manteniendo el de mayor confianza
            unique_records = self._remove_duplicates(records)

            print(f"DEBUG PaddleOCR: Total registros únicos: {len(unique_records)}")

            return unique_records

        except Exception as e:
            print(f"ERROR PaddleOCR: {e}")
            import traceback
            traceback.print_exc()
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
