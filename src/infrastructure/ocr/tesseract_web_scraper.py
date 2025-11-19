"""Scraper OCR para leer campos del formulario web digital usando Tesseract."""
import pytesseract
from PIL import Image, ImageGrab
from typing import Dict, Tuple, Optional
import re

from ...domain.entities import FormData


class TesseractWebScraper:
    """
    Scraper OCR para extraer datos del formulario web digital.

    Usa Tesseract OCR optimizado para texto digital/impreso.
    Lee campos del formulario web DESPUÉS de buscar la cédula.

    Estrategia:
    - Captura región específica del formulario web
    - Lee cada campo individualmente con Tesseract
    - Detecta campos vacíos (persona no encontrada en BD)
    - Retorna FormData estructurado

    Configuración Tesseract para texto digital:
    - --psm 6: Bloque uniforme de texto
    - --oem 3: Modo LSTM
    - Whitelist: Solo letras (nombres no tienen números)
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el scraper.

        Args:
            config: Configuración opcional de Tesseract
        """
        self.config = config or self._get_default_config()

        # Configuración de Tesseract
        self.tesseract_config = self.config.get('tesseract', {}).get('config', '--psm 6 --oem 3')
        self.char_whitelist = self.config.get('tesseract', {}).get('char_whitelist', 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ ')

        # Regiones de captura para cada campo (se configuran dinámicamente)
        self.field_regions = self.config.get('field_regions', {})

    def _get_default_config(self) -> Dict:
        """
        Configuración por defecto.

        Returns:
            Diccionario de configuración
        """
        return {
            'tesseract': {
                'enabled': True,
                'config': '--psm 6 --oem 3',
                'char_whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ '
            },
            'field_regions': {
                # Coordenadas (x, y, width, height) para cada campo
                # Estos valores deben ajustarse según la aplicación web real
                'primer_nombre': (100, 150, 300, 40),
                'segundo_nombre': (100, 200, 300, 40),
                'primer_apellido': (100, 250, 300, 40),
                'segundo_apellido': (100, 300, 300, 40)
            }
        }

    def capture_web_form_region(
        self,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Image.Image:
        """
        Captura una región de la pantalla (formulario web).

        Args:
            region: Tupla (x, y, width, height) de la región a capturar.
                   Si None, captura toda la pantalla.

        Returns:
            Imagen PIL de la región capturada
        """
        if region is None:
            # Capturar toda la pantalla
            screenshot = ImageGrab.grab()
        else:
            # Capturar región específica
            x, y, width, height = region
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox=bbox)

        return screenshot

    def extract_field_value(
        self,
        field_name: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        image: Optional[Image.Image] = None
    ) -> str:
        """
        Extrae el valor de un campo específico usando Tesseract.

        Args:
            field_name: Nombre del campo ('primer_nombre', 'segundo_nombre', etc.)
            region: Región del campo (x, y, width, height). Si None, usa field_regions config
            image: Imagen ya capturada. Si None, captura nueva región

        Returns:
            Texto extraído del campo (vacío si no se detecta texto)
        """
        # Determinar región a usar
        if region is None:
            region = self.field_regions.get(field_name)
            if region is None:
                print(f"ADVERTENCIA: No hay región configurada para campo '{field_name}'")
                return ""

        # Capturar o usar imagen proporcionada
        if image is None:
            field_image = self.capture_web_form_region(region)
        else:
            # Recortar imagen si se proporcionó una completa
            x, y, width, height = region
            field_image = image.crop((x, y, x + width, y + height))

        # Configurar Tesseract con whitelist de caracteres
        custom_config = f"{self.tesseract_config} -c tessedit_char_whitelist='{self.char_whitelist}'"

        try:
            # Extraer texto con Tesseract
            text = pytesseract.image_to_string(
                field_image,
                lang='spa',  # Español
                config=custom_config
            )

            # Limpiar texto
            text = self._clean_extracted_text(text)

            return text

        except Exception as e:
            print(f"ERROR extrayendo campo '{field_name}': {e}")
            return ""

    def get_all_fields(
        self,
        cedula_consultada: Optional[str] = None,
        full_form_image: Optional[Image.Image] = None
    ) -> FormData:
        """
        Extrae todos los campos del formulario web.

        Args:
            cedula_consultada: Cédula que se consultó (para referencia)
            full_form_image: Imagen completa del formulario (opcional).
                            Si None, captura cada campo individualmente.

        Returns:
            FormData con todos los campos extraídos
        """
        print(f"\n{'='*70}")
        print("TESSERACT - Extrayendo campos del formulario web")
        print(f"{'='*70}")

        # Extraer cada campo
        primer_nombre = self.extract_field_value('primer_nombre', image=full_form_image)
        segundo_nombre = self.extract_field_value('segundo_nombre', image=full_form_image)
        primer_apellido = self.extract_field_value('primer_apellido', image=full_form_image)
        segundo_apellido = self.extract_field_value('segundo_apellido', image=full_form_image)

        # Log resultados
        print(f"1er Nombre:   '{primer_nombre}'")
        print(f"2do Nombre:   '{segundo_nombre}'")
        print(f"1er Apellido: '{primer_apellido}'")
        print(f"2do Apellido: '{segundo_apellido}'")

        # Determinar si todos los campos están vacíos (persona no encontrada)
        is_empty = not primer_nombre and not primer_apellido

        if is_empty:
            print(f"⚠️ TODOS LOS CAMPOS VACÍOS - Persona no encontrada en BD")
        else:
            print(f"✓ Datos extraídos correctamente")

        print(f"{'='*70}\n")

        # Crear FormData
        form_data = FormData(
            primer_nombre=primer_nombre,
            segundo_nombre=segundo_nombre,
            primer_apellido=primer_apellido,
            segundo_apellido=segundo_apellido,
            is_empty=is_empty,
            cedula_consultada=cedula_consultada
        )

        return form_data

    def is_person_not_found(self, form_data: FormData) -> bool:
        """
        Determina si la persona NO fue encontrada en la base de datos.

        Una persona no encontrada tiene TODOS los campos principales vacíos.

        Args:
            form_data: Datos del formulario extraídos

        Returns:
            True si persona no fue encontrada
        """
        return form_data.is_empty

    def _clean_extracted_text(self, text: str) -> str:
        """
        Limpia el texto extraído por Tesseract.

        Elimina:
        - Caracteres especiales no deseados
        - Espacios extra
        - Saltos de línea

        Preserva:
        - Letras (incluidas tildes)
        - Espacios simples entre palabras

        Args:
            text: Texto crudo de Tesseract

        Returns:
            Texto limpio
        """
        if not text:
            return ""

        # Eliminar saltos de línea
        text = text.replace('\n', ' ').replace('\r', ' ')

        # Eliminar caracteres especiales (solo letras, tildes, y espacios)
        # Preservar letras con tildes
        text = re.sub(r'[^A-ZÁÉÍÓÚÑa-záéíóúñ\s]', '', text)

        # Convertir a mayúsculas
        text = text.upper()

        # Eliminar espacios extra
        text = ' '.join(text.split())

        return text.strip()

    def configure_field_region(
        self,
        field_name: str,
        x: int,
        y: int,
        width: int,
        height: int
    ):
        """
        Configura la región de captura para un campo específico.

        Permite ajustar dinámicamente las coordenadas según la aplicación web.

        Args:
            field_name: Nombre del campo
            x: Coordenada X (píxeles desde la izquierda)
            y: Coordenada Y (píxeles desde arriba)
            width: Ancho de la región
            height: Alto de la región
        """
        self.field_regions[field_name] = (x, y, width, height)
        print(f"✓ Región configurada para '{field_name}': ({x}, {y}, {width}, {height})")

    def get_configured_regions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """
        Obtiene todas las regiones configuradas.

        Returns:
            Diccionario de {field_name: (x, y, width, height)}
        """
        return self.field_regions.copy()
