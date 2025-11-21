"""Implementación de OCR usando EasyOCR (mejor para escritura manual)."""
import re
import numpy as np
from PIL import Image
from typing import List
import easyocr

from ...domain.entities import CedulaRecord
from ...domain.ports import OCRPort, ConfigPort


class EasyOCRAdapter(OCRPort):
    """
    Implementación de OCR usando EasyOCR con deep learning.

    EasyOCR es superior a Tesseract para:
    - Escritura manual
    - Texto en múltiples idiomas
    - Texto con diferentes ángulos
    - Texto con calidad variable

    Attributes:
        config: Servicio de configuración
        reader: Lector de EasyOCR
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el servicio de OCR con EasyOCR.

        Args:
            config: Servicio de configuración
        """
        self.config = config
        self.reader = None
        self._initialize_reader()

    def _initialize_reader(self) -> None:
        """Inicializa el lector de EasyOCR."""
        # Obtener configuración
        languages = self.config.get('ocr.languages', ['es', 'en'])
        gpu = self.config.get('ocr.gpu', False)

        print(f"DEBUG EasyOCR: Inicializando con idiomas {languages}, GPU={gpu}")

        try:
            # Crear lector de EasyOCR
            # gpu=False para usar CPU (más lento pero más compatible)
            # gpu=True si tienes NVIDIA GPU (más rápido)
            self.reader = easyocr.Reader(languages, gpu=gpu, verbose=False)
            print("DEBUG EasyOCR: Lector inicializado correctamente")
        except Exception as e:
            print(f"ERROR EasyOCR: No se pudo inicializar: {e}")
            raise

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen para mejorar el OCR.

        Para EasyOCR, el preprocesamiento puede ser más simple ya que
        el modelo de deep learning es más robusto.

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada
        """
        # EasyOCR funciona bien con la imagen original
        # Solo aseguramos que esté en RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')

        print(f"DEBUG EasyOCR Preprocess: Imagen {image.width}x{image.height}")

        return image

    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen usando EasyOCR.

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista de registros de cédulas extraídas
        """
        if self.reader is None:
            print("ERROR: EasyOCR reader no está inicializado")
            return []

        print("DEBUG EasyOCR: Iniciando extracción...")

        # Convertir PIL a numpy array
        img_array = np.array(image)

        try:
            # Ejecutar OCR
            # allowlist: solo números
            # paragraph: False para detectar líneas individuales
            results = self.reader.readtext(
                img_array,
                detail=1,  # Retornar detalles (coordenadas, texto, confianza)
                paragraph=False,
                allowlist='0123456789',  # Solo dígitos
                batch_size=4
            )

            print(f"DEBUG EasyOCR: Detectados {len(results)} elementos")

            records = []
            min_confidence = self.config.get('ocr.min_confidence', 50.0) / 100.0  # EasyOCR usa 0-1

            for bbox, text, confidence in results:
                # Limpiar texto
                text = text.strip().replace(' ', '').replace('.', '').replace(',', '')

                print(f"DEBUG EasyOCR: '{text}' con confianza {confidence*100:.1f}%")

                # Verificar que sea solo dígitos
                if text and text.isdigit():
                    # Validar longitud de cédula (3-11 dígitos)
                    if 3 <= len(text) <= 11:
                        # EasyOCR tiende a dar mejor confianza
                        if confidence >= 0.3:  # Umbral bajo inicial (30%)
                            # Usar factory method para crear con Value Objects
                            record = CedulaRecord.from_primitives(
                                cedula=text,
                                confidence=confidence * 100  # Convertir a porcentaje
                            )
                            records.append(record)

                            print(f"✓ Cédula aceptada: '{text}' ({confidence*100:.1f}%)")

            # Si no se encontró nada con allowlist, intentar sin restricciones
            if not records:
                print("DEBUG EasyOCR: Intentando sin allowlist...")
                results = self.reader.readtext(
                    img_array,
                    detail=1,
                    paragraph=False,
                    batch_size=4
                )

                for bbox, text, confidence in results:
                    # Extraer solo números del texto
                    numbers = re.findall(r'\d+', text)

                    for num in numbers:
                        if 3 <= len(num) <= 11:
                            # Usar factory method para crear con Value Objects
                            record = CedulaRecord.from_primitives(
                                cedula=num,
                                confidence=confidence * 100 * 0.8  # Penalizar un poco
                            )
                            records.append(record)
                            print(f"✓ Número extraído del texto '{text}': {num}")

            # Eliminar duplicados manteniendo el de mayor confianza
            unique_records = self._remove_duplicates(records)

            print(f"DEBUG EasyOCR: Total registros únicos: {len(unique_records)}")

            return unique_records

        except Exception as e:
            print(f"ERROR EasyOCR: {e}")
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
