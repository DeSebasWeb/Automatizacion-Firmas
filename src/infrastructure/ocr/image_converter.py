"""Utilidad para conversiones de formatos de imagen."""
import io
from PIL import Image
from typing import Tuple


class ImageConverter:
    """
    Utilidad para convertir imágenes entre diferentes formatos.

    Proporciona métodos estáticos para conversiones comunes:
    - PIL Image a bytes (PNG/JPEG)
    - bytes a PIL Image
    - Conversiones de modo de color (RGB, RGBA, L, etc)
    - Validación de formato

    Esta clase centraliza la lógica de conversión que estaba duplicada
    en GoogleVisionAdapter y AzureVisionAdapter.
    """

    @staticmethod
    def pil_to_bytes(
        image: Image.Image,
        format: str = 'PNG',
        quality: int = 95
    ) -> bytes:
        """
        Convierte imagen PIL a bytes.

        Args:
            image: Imagen PIL a convertir
            format: Formato de salida ('PNG', 'JPEG', 'WEBP', etc)
            quality: Calidad de compresión para JPEG/WEBP (1-100)

        Returns:
            Imagen en bytes

        Example:
            >>> img = Image.open('photo.jpg')
            >>> img_bytes = ImageConverter.pil_to_bytes(img, format='PNG')
            >>> len(img_bytes)
            245680
        """
        img_byte_arr = io.BytesIO()

        # Asegurar compatibilidad de formato
        if format.upper() in ('JPEG', 'JPG') and image.mode in ('RGBA', 'P'):
            # JPEG no soporta transparencia
            image = image.convert('RGB')

        # Guardar en buffer
        if format.upper() in ('JPEG', 'JPG', 'WEBP'):
            image.save(img_byte_arr, format=format.upper(), quality=quality)
        else:
            image.save(img_byte_arr, format=format.upper())

        return img_byte_arr.getvalue()

    @staticmethod
    def bytes_to_pil(image_bytes: bytes) -> Image.Image:
        """
        Convierte bytes a imagen PIL.

        Args:
            image_bytes: Bytes de la imagen

        Returns:
            Imagen PIL

        Raises:
            ValueError: Si los bytes no son una imagen válida

        Example:
            >>> with open('photo.jpg', 'rb') as f:
            ...     img_bytes = f.read()
            >>> img = ImageConverter.bytes_to_pil(img_bytes)
            >>> img.size
            (800, 600)
        """
        try:
            img_buffer = io.BytesIO(image_bytes)
            image = Image.open(img_buffer)
            return image
        except Exception as e:
            raise ValueError(f"No se pudo convertir bytes a imagen PIL: {e}")

    @staticmethod
    def ensure_rgb(image: Image.Image) -> Image.Image:
        """
        Asegura que la imagen esté en modo RGB.

        Si la imagen está en otro modo (RGBA, L, P, etc), la convierte a RGB.

        Args:
            image: Imagen PIL

        Returns:
            Imagen en modo RGB

        Example:
            >>> img = Image.open('transparent.png')  # RGBA
            >>> img.mode
            'RGBA'
            >>> img_rgb = ImageConverter.ensure_rgb(img)
            >>> img_rgb.mode
            'RGB'
        """
        if image.mode != 'RGB':
            return image.convert('RGB')
        return image

    @staticmethod
    def ensure_grayscale(image: Image.Image) -> Image.Image:
        """
        Asegura que la imagen esté en escala de grises (modo L).

        Args:
            image: Imagen PIL

        Returns:
            Imagen en modo L (grayscale)

        Example:
            >>> img = Image.open('color.jpg')  # RGB
            >>> img.mode
            'RGB'
            >>> img_gray = ImageConverter.ensure_grayscale(img)
            >>> img_gray.mode
            'L'
        """
        if image.mode != 'L':
            return image.convert('L')
        return image

    @staticmethod
    def get_image_info(image: Image.Image) -> dict:
        """
        Obtiene información sobre la imagen.

        Args:
            image: Imagen PIL

        Returns:
            Dict con información: width, height, mode, format, size_bytes

        Example:
            >>> img = Image.open('photo.jpg')
            >>> info = ImageConverter.get_image_info(img)
            >>> info
            {
                'width': 800,
                'height': 600,
                'mode': 'RGB',
                'format': 'JPEG',
                'size_bytes': 245680
            }
        """
        # Calcular tamaño en bytes si es posible
        size_bytes = None
        try:
            img_bytes = ImageConverter.pil_to_bytes(image, format='PNG')
            size_bytes = len(img_bytes)
        except:
            pass

        return {
            'width': image.width,
            'height': image.height,
            'mode': image.mode,
            'format': image.format or 'Unknown',
            'size_bytes': size_bytes
        }

    @staticmethod
    def validate_image_size(
        image: Image.Image,
        min_width: int = 100,
        min_height: int = 100,
        max_width: int = 10000,
        max_height: int = 10000
    ) -> Tuple[bool, str]:
        """
        Valida que el tamaño de la imagen esté dentro de los límites.

        Args:
            image: Imagen PIL a validar
            min_width: Ancho mínimo permitido
            min_height: Alto mínimo permitido
            max_width: Ancho máximo permitido
            max_height: Alto máximo permitido

        Returns:
            Tupla (es_válida, mensaje_error)

        Example:
            >>> img = Image.open('tiny.jpg')  # 50x50
            >>> is_valid, error = ImageConverter.validate_image_size(img, min_width=100)
            >>> is_valid
            False
            >>> error
            'Imagen muy pequeña: 50x50 (mínimo: 100x100)'
        """
        width, height = image.size

        if width < min_width or height < min_height:
            return False, f"Imagen muy pequeña: {width}x{height} (mínimo: {min_width}x{min_height})"

        if width > max_width or height > max_height:
            return False, f"Imagen muy grande: {width}x{height} (máximo: {max_width}x{max_height})"

        return True, ""

    @staticmethod
    def resize_if_needed(
        image: Image.Image,
        max_width: int = 4000,
        max_height: int = 4000,
        maintain_aspect_ratio: bool = True
    ) -> Image.Image:
        """
        Redimensiona la imagen si excede los límites máximos.

        Args:
            image: Imagen PIL
            max_width: Ancho máximo
            max_height: Alto máximo
            maintain_aspect_ratio: Si mantener aspect ratio

        Returns:
            Imagen redimensionada (o la original si no excede límites)

        Example:
            >>> img = Image.open('huge.jpg')  # 8000x6000
            >>> img_resized = ImageConverter.resize_if_needed(img, max_width=4000)
            >>> img_resized.size
            (4000, 3000)
        """
        width, height = image.size

        # Si no excede límites, retornar original
        if width <= max_width and height <= max_height:
            return image

        if maintain_aspect_ratio:
            # Calcular nuevo tamaño manteniendo aspect ratio
            ratio = min(max_width / width, max_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
        else:
            new_width = min(width, max_width)
            new_height = min(height, max_height)

        return image.resize((new_width, new_height), Image.LANCZOS)
