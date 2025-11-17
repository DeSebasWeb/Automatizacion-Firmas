"""Implementación de OCR usando Google Cloud Vision API - Óptimo para escritura manual."""
import re
import os
from PIL import Image
from typing import List
import io

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("ADVERTENCIA: Google Cloud Vision no está instalado. Instalar con: pip install google-cloud-vision")

from ...domain.entities import CedulaRecord
from ...domain.ports import OCRPort, ConfigPort


class GoogleVisionAdapter(OCRPort):
    """
    Implementación de OCR usando Google Cloud Vision API.

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
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el servicio de OCR con Google Cloud Vision.

        Args:
            config: Servicio de configuración
        """
        if not GOOGLE_VISION_AVAILABLE:
            raise ImportError("Google Cloud Vision no está instalado. Instalar con: pip install google-cloud-vision")

        self.config = config
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

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen para Google Vision.

        Google Vision funciona muy bien sin preprocesamiento,
        pero podemos mejorar la calidad si es necesario.

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada
        """
        # Google Vision prefiere imágenes en RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')

        print(f"DEBUG Google Vision: Imagen {image.width}x{image.height}")

        return image

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
            # Convertir imagen PIL a bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Crear objeto Image de Google Vision
            vision_image = vision.Image(content=img_byte_arr)

            # Llamar a la API - DOCUMENT_TEXT_DETECTION detecta texto línea por línea
            # Esta es la ÚNICA llamada API que hacemos
            print("DEBUG Google Vision: Llamando a DOCUMENT_TEXT_DETECTION...")
            response = self.client.document_text_detection(image=vision_image)

            if response.error.message:
                print(f"ERROR Google Vision API: {response.error.message}")
                return []

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

                    # Extraer números del texto
                    numbers = self._extract_numbers_from_text(line)

                    for num in numbers:
                        # Validar longitud de cédula colombiana (6-10 dígitos típicamente)
                        if 6 <= len(num) <= 10:
                            record = CedulaRecord(
                                cedula=num,
                                confidence=95.0  # Google Vision es muy confiable
                            )
                            records.append(record)
                            print(f"✓ Cédula extraída: '{num}' ({len(num)} dígitos)")
                        elif len(num) < 6:
                            print(f"✗ Descartada (muy corta): '{num}' ({len(num)} dígitos)")
                        else:
                            print(f"✗ Descartada (muy larga): '{num}' ({len(num)} dígitos)")

            print(f"✓ Google Vision: Total llamadas API: 1 (óptimo)")

            # Eliminar duplicados
            unique_records = self._remove_duplicates(records)

            print(f"DEBUG Google Vision: Total cédulas únicas: {len(unique_records)}")

            return unique_records

        except Exception as e:
            print(f"ERROR Google Vision: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _split_image_into_lines(self, image: Image.Image) -> List[Image.Image]:
        """
        Divide la imagen en líneas individuales (una por cédula).

        Usa división uniforme: imagen de 490px / 15 líneas = ~32px por línea

        Args:
            image: Imagen completa

        Returns:
            Lista de sub-imágenes (una por línea)
        """
        height = image.height
        width = image.width

        # Dividir en 15 líneas uniformes
        expected_lines = 15
        line_height = height // expected_lines

        print(f"DEBUG Google Vision: Dividiendo imagen en {expected_lines} líneas de {line_height}px cada una")

        regions = []

        for i in range(expected_lines):
            y1 = i * line_height
            y2 = min((i + 1) * line_height, height)

            if y2 - y1 > 10:  # Altura mínima
                region = image.crop((0, y1, width, y2))
                regions.append(region)

        return regions

    def _extract_numbers_from_text(self, text: str) -> List[str]:
        """
        Extrae números del texto reconocido.

        Args:
            text: Texto reconocido por Google Vision

        Returns:
            Lista de strings numéricos
        """
        # Limpiar texto
        text_clean = text.replace(' ', '').replace('.', '').replace(',', '').replace('-', '').replace('\n', '')

        # Extraer solo números
        numbers = re.findall(r'\d+', text_clean)

        return numbers

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
            if record.cedula not in seen or record.confidence > seen[record.cedula].confidence:
                seen[record.cedula] = record

        return list(seen.values())
