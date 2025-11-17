"""Implementación de OCR usando Tesseract."""
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import List

from ...domain.entities import CedulaRecord
from ...domain.ports import OCRPort, ConfigPort


class TesseractOCR(OCRPort):
    """
    Implementación de OCR usando Tesseract con pre-procesamiento de imágenes.

    Attributes:
        config: Servicio de configuración
    """

    def __init__(self, config: ConfigPort):
        """
        Inicializa el servicio de OCR.

        Args:
            config: Servicio de configuración
        """
        self.config = config

        # Configurar ruta de Tesseract si es necesario (Windows)
        tesseract_path = self.config.get('ocr.tesseract_path')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocesa una imagen para mejorar el OCR, optimizado para escritura manual.

        Aplica las siguientes técnicas:
        - Conversión a escala de grises
        - Redimensionamiento grande
        - Mejora de contraste
        - Binarización adaptativa
        - Morfología para limpiar

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada
        """
        # Convertir PIL a formato OpenCV
        img_array = np.array(image)

        print(f"DEBUG Preprocess: Imagen original: {img_array.shape}")

        # Convertir a escala de grises
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Redimensionar MUCHO para escritura manual
        scale_factor = 4.0  # Escritura manual necesita más resolución
        width = int(gray.shape[1] * scale_factor)
        height = int(gray.shape[0] * scale_factor)
        resized = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)

        print(f"DEBUG Preprocess: Imagen redimensionada: {resized.shape}")

        # Mejorar contraste primero
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(resized)

        # Reducción de ruido ligero
        denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # Binarización adaptativa (mejor para escritura manual)
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15,  # Tamaño de bloque más grande
            10   # Constante C más grande
        )

        # Invertir si el fondo es oscuro
        if np.mean(binary) < 127:
            binary = cv2.bitwise_not(binary)

        # Operaciones morfológicas para limpiar ruido
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        print(f"DEBUG Preprocess: Preprocesamiento completado")

        # Convertir de vuelta a PIL
        processed_image = Image.fromarray(binary)

        return processed_image

    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        """
        Extrae números de cédula de una imagen.

        Args:
            image: Imagen PIL a procesar

        Returns:
            Lista de registros de cédulas extraídas
        """
        # Obtener configuración de OCR
        language = self.config.get('ocr.language', 'spa')
        min_confidence = self.config.get('ocr.min_confidence', 50.0)

        records = []

        # Intentar con múltiples configuraciones de PSM para mejor detección
        # PSM 6 = bloque uniforme de texto
        # PSM 4 = columna de texto
        # PSM 11 = texto disperso
        # PSM 13 = línea de texto sin restricciones
        psm_modes = [4, 6, 11, 13]

        for psm in psm_modes:
            # Configurar Tesseract - solo números, sin diccionario
            # Para escritura manual es mejor ser más permisivo
            custom_config = (
                f'--oem 3 --psm {psm} '
                f'-c tessedit_char_whitelist=0123456789 '
                f'-c classify_bln_numeric_mode=1 '
                f'-c tessedit_pageseg_mode={psm}'
            )

            try:
                # Ejecutar OCR con datos detallados
                ocr_data = pytesseract.image_to_data(
                    image,
                    lang=language,
                    config=custom_config,
                    output_type=pytesseract.Output.DICT
                )

                # Procesar cada elemento detectado
                for i, text in enumerate(ocr_data['text']):
                    # Limpiar texto - eliminar espacios y caracteres extraños
                    text = text.strip().replace(' ', '').replace('.', '').replace(',', '')

                    # Verificar si es un número
                    if text and text.isdigit():
                        confidence = float(ocr_data['conf'][i])

                        # Para escritura manual, aceptar confianza más baja
                        if confidence >= 0:  # Aceptar todos para debug
                            # Validar longitud razonable (5 a 15 dígitos para cédulas)
                            if 5 <= len(text) <= 15:
                                record = CedulaRecord(
                                    cedula=text,
                                    confidence=max(confidence, 30.0)  # Mínimo 30% de confianza
                                )
                                records.append(record)

                                print(f"DEBUG OCR PSM{psm}: Encontrado '{text}' (len={len(text)}) con confianza {confidence:.1f}%")

            except Exception as e:
                print(f"DEBUG OCR: Error en PSM {psm}: {e}")
                continue

        # Si no se encontró nada, intentar extracción de texto completo
        if not records:
            print("DEBUG OCR: Intentando extracción de texto completo...")
            try:
                full_text = pytesseract.image_to_string(image, lang=language)
                print(f"DEBUG OCR: Texto completo extraído:\n{full_text}")

                # Buscar números en el texto
                numbers = re.findall(r'\d+', full_text)
                for num in numbers:
                    if 4 <= len(num) <= 20:
                        record = CedulaRecord(
                            cedula=num,
                            confidence=60.0  # Confianza media
                        )
                        records.append(record)
                        print(f"DEBUG OCR: Número extraído del texto: {num}")

            except Exception as e:
                print(f"DEBUG OCR: Error en extracción de texto completo: {e}")

        # Eliminar duplicados manteniendo el de mayor confianza
        unique_records = self._remove_duplicates(records)

        print(f"DEBUG OCR: Total registros únicos: {len(unique_records)}")

        return unique_records

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
