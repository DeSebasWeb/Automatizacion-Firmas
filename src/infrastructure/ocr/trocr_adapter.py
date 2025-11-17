"""Implementación de OCR usando TrOCR (Microsoft) - Estado del arte para escritura manual."""
import re
from PIL import Image
from typing import List
import warnings
warnings.filterwarnings('ignore')

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    import torch
    TROCR_AVAILABLE = True
except ImportError:
    TROCR_AVAILABLE = False
    print("ADVERTENCIA: TrOCR no está instalado. Instalar con: pip install transformers torch")

from ...domain.entities import CedulaRecord
from ...domain.ports import OCRPort, ConfigPort


class TrOCRAdapter(OCRPort):
    """
    Implementación de OCR usando TrOCR de Microsoft.

    TrOCR es:
    - Estado del arte (state-of-the-art) para escritura manual
    - Basado en transformers (Vision Transformer + GPT)
    - Entrenado específicamente en texto manuscrito
    - Excelente precisión con números escritos a mano
    - 100% gratuito y funciona localmente

    Attributes:
        config: Servicio de configuración
        processor: Procesador de TrOCR
        model: Modelo de TrOCR
        device: Dispositivo (CPU o CUDA)
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el servicio de OCR con TrOCR.

        Args:
            config: Servicio de configuración
        """
        if not TROCR_AVAILABLE:
            raise ImportError("TrOCR no está instalado. Instalar con: pip install transformers torch")

        self.config = config
        self.processor = None
        self.model = None
        self.device = None
        self._initialize_ocr()

    def _initialize_ocr(self) -> None:
        """Inicializa TrOCR."""
        print("DEBUG TrOCR: Inicializando modelo...")
        print("DEBUG TrOCR: Esto puede tardar la primera vez (descarga modelo ~1GB)")

        try:
            # Detectar si hay GPU disponible
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"DEBUG TrOCR: Usando dispositivo: {self.device}")

            # Cargar modelo preentrenado para manuscritos
            # microsoft/trocr-base-handwritten: Modelo base entrenado en IAM Handwriting
            # microsoft/trocr-large-handwritten: Modelo grande (más preciso pero más lento)
            model_name = "microsoft/trocr-base-handwritten"

            print(f"DEBUG TrOCR: Cargando modelo '{model_name}'...")

            self.processor = TrOCRProcessor.from_pretrained(model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()  # Modo evaluación

            print("DEBUG TrOCR: ✓ Modelo cargado correctamente")
            print("DEBUG TrOCR: ✓ Listo para reconocer escritura manual")

        except Exception as e:
            print(f"ERROR TrOCR: No se pudo inicializar: {e}")
            raise

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen para TrOCR.

        TrOCR funciona mejor con:
        - Imágenes en RGB o escala de grises
        - Buena resolución
        - Texto en una sola línea por imagen

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada
        """
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')

        print(f"DEBUG TrOCR Preprocess: Imagen {image.width}x{image.height}")

        return image

    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen usando TrOCR.

        TrOCR procesa imágenes de texto línea por línea.
        Para extraer múltiples cédulas, dividimos la imagen en regiones.

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista de registros de cédulas extraídas
        """
        if self.model is None or self.processor is None:
            print("ERROR: TrOCR no está inicializado")
            return []

        print("DEBUG TrOCR: Iniciando extracción...")

        try:
            # Dividir imagen en líneas/regiones horizontales
            # Asumiendo que las cédulas están una debajo de otra
            regions = self._split_image_into_lines(image)

            print(f"DEBUG TrOCR: Detectadas {len(regions)} regiones de texto")

            records = []

            for idx, region in enumerate(regions):
                # Procesar cada región con TrOCR
                text = self._recognize_text(region)

                if not text:
                    continue

                print(f"DEBUG TrOCR: Región {idx+1}: '{text}'")

                # Extraer números del texto
                numbers = self._extract_numbers_from_text(text)

                for num in numbers:
                    # Validar longitud de cédula colombiana (6-10 dígitos típicamente)
                    if 6 <= len(num) <= 10:
                        # TrOCR es muy confiable, usar confianza alta
                        record = CedulaRecord(
                            cedula=num,
                            confidence=95.0  # Alta confianza para TrOCR
                        )
                        records.append(record)
                        print(f"✓ Cédula extraída: '{num}' ({len(num)} dígitos)")
                    elif len(num) < 6:
                        print(f"✗ Descartada (muy corta): '{num}' ({len(num)} dígitos)")
                    else:
                        print(f"✗ Descartada (muy larga): '{num}' ({len(num)} dígitos)")

            # Eliminar duplicados
            unique_records = self._remove_duplicates(records)

            print(f"DEBUG TrOCR: Total cédulas únicas: {len(unique_records)}")

            return unique_records

        except Exception as e:
            print(f"ERROR TrOCR: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _split_image_into_lines(self, image: Image.Image) -> List[Image.Image]:
        """
        Divide la imagen en regiones de líneas de texto usando proyección horizontal.

        Estrategia: Dividir la imagen en franjas uniformes basándose en la altura esperada
        de cada línea (aprox. 30-35 píxeles por línea para 15 cédulas en ~490 píxeles).

        Args:
            image: Imagen completa

        Returns:
            Lista de sub-imágenes (una por línea)
        """
        import numpy as np
        import cv2

        height = image.height
        width = image.width

        # Calcular altura promedio por línea
        # Si hay ~15 líneas en 490 píxeles: 490/15 ≈ 32 píxeles por línea
        expected_lines = 15
        line_height = height // expected_lines

        print(f"DEBUG Segmentación: Altura imagen={height}px, líneas esperadas={expected_lines}, altura por línea≈{line_height}px")

        # Convertir PIL a OpenCV para análisis
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Binarización simple para detectar texto
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Proyección horizontal
        horizontal_projection = np.sum(binary, axis=1)

        # Encontrar "valles" (áreas con poco texto) que separan líneas
        # Suavizar la proyección para encontrar valles más claros
        from scipy.ndimage import gaussian_filter1d
        smoothed = gaussian_filter1d(horizontal_projection, sigma=2)

        # Normalizar
        if smoothed.max() > 0:
            smoothed = smoothed / smoothed.max()

        # Buscar mínimos locales (valles) como separadores de líneas
        valleys = []
        for y in range(3, height - 3):
            # Es un valle si es menor que sus vecinos
            if (smoothed[y] < smoothed[y-1] and smoothed[y] < smoothed[y+1] and
                smoothed[y] < smoothed[y-2] and smoothed[y] < smoothed[y+2] and
                smoothed[y] < 0.3):  # Umbral: valles profundos (poco texto)
                valleys.append(y)

        # Filtrar valles muy cercanos (mantener solo uno cada ~line_height píxeles)
        filtered_valleys = []
        last_valley = -100
        for v in valleys:
            if v - last_valley > line_height * 0.6:  # Al menos 60% de la altura esperada
                filtered_valleys.append(v)
                last_valley = v

        print(f"DEBUG Segmentación: Detectados {len(filtered_valleys)} valles (separadores)")

        # Crear regiones basándose en los valles
        regions = []

        if len(filtered_valleys) == 0:
            # No se encontraron valles, usar división uniforme
            print("DEBUG Segmentación: No se encontraron valles, usando división uniforme")
            for i in range(expected_lines):
                y1 = i * line_height
                y2 = min((i + 1) * line_height, height)
                if y2 - y1 > 15:  # Altura mínima
                    region = image.crop((0, y1, width, y2))
                    region = self._preprocess_line(region)
                    regions.append(region)
        else:
            # Usar valles como separadores
            # Primera región: desde el inicio hasta el primer valle
            if filtered_valleys[0] > 15:
                region = image.crop((0, 0, width, filtered_valleys[0]))
                region = self._preprocess_line(region)
                regions.append(region)

            # Regiones intermedias: entre valles
            for i in range(len(filtered_valleys) - 1):
                y1 = filtered_valleys[i]
                y2 = filtered_valleys[i + 1]
                if y2 - y1 > 15:
                    region = image.crop((0, y1, width, y2))
                    region = self._preprocess_line(region)
                    regions.append(region)

            # Última región: desde el último valle hasta el final
            if height - filtered_valleys[-1] > 15:
                region = image.crop((0, filtered_valleys[-1], width, height))
                region = self._preprocess_line(region)
                regions.append(region)

        print(f"DEBUG TrOCR: Segmentación detectó {len(regions)} líneas de texto")

        if len(regions) < 10 or len(regions) > 20:
            print(f"⚠️  ADVERTENCIA: Se esperaban ~15 líneas, se detectaron {len(regions)}")

        return regions

    def _preprocess_line(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una línea individual para mejorar el reconocimiento OCR.

        Aplica:
        - Mejora de contraste
        - Binarización adaptativa
        - Eliminación de ruido
        - Normalización

        Args:
            image: Línea de imagen con una cédula

        Returns:
            Imagen preprocesada optimizada para TrOCR
        """
        import numpy as np
        import cv2

        # Convertir a numpy array
        img_array = np.array(image)

        # Convertir a escala de grises
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Mejora de contraste usando CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Binarización adaptativa (mejor para manuscritos con iluminación irregular)
        binary = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Tamaño de vecindad
            2    # Constante restada de la media
        )

        # Eliminar ruido pequeño (morfología)
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)

        # Convertir de vuelta a PIL en RGB (TrOCR requiere RGB)
        cleaned_rgb = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(cleaned_rgb)

    def _has_content(self, image: Image.Image) -> bool:
        """
        Verifica si una región de imagen tiene contenido (no está vacía/blanca).

        Args:
            image: Región de imagen

        Returns:
            True si tiene contenido, False si está vacía
        """
        # Convertir a escala de grises
        gray = image.convert('L')

        # Calcular varianza de píxeles
        # Imagen vacía/blanca tendrá varianza muy baja
        import numpy as np
        pixels = np.array(gray)
        variance = pixels.var()

        # Umbral: si varianza > 100, hay contenido
        return variance > 100

    def _recognize_text(self, image: Image.Image) -> str:
        """
        Reconoce texto en una región de imagen usando TrOCR.

        Args:
            image: Región de imagen

        Returns:
            Texto reconocido
        """
        # Preprocesar imagen
        pixel_values = self.processor(
            images=image,
            return_tensors="pt"
        ).pixel_values.to(self.device)

        # Generar texto
        with torch.no_grad():
            generated_ids = self.model.generate(pixel_values)

        # Decodificar texto
        generated_text = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        return generated_text.strip()

    def _extract_numbers_from_text(self, text: str) -> List[str]:
        """
        Extrae números del texto reconocido.

        Args:
            text: Texto reconocido

        Returns:
            Lista de strings numéricos
        """
        # Limpiar texto
        text_clean = text.replace(' ', '').replace('.', '').replace(',', '').replace('-', '')

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
