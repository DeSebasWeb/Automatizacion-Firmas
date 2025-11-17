"""Utilidades para procesamiento de imágenes."""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple


class ImageUtils:
    """Utilidades estáticas para procesamiento de imágenes."""

    @staticmethod
    def pil_to_cv2(image: Image.Image) -> np.ndarray:
        """
        Convierte imagen PIL a formato OpenCV.

        Args:
            image: Imagen PIL

        Returns:
            Array numpy en formato BGR
        """
        # Convertir a RGB si no lo está
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convertir a numpy array
        img_array = np.array(image)

        # Convertir RGB a BGR (OpenCV usa BGR)
        bgr_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        return bgr_image

    @staticmethod
    def cv2_to_pil(image: np.ndarray) -> Image.Image:
        """
        Convierte imagen OpenCV a formato PIL.

        Args:
            image: Array numpy en formato BGR

        Returns:
            Imagen PIL
        """
        # Convertir BGR a RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convertir a PIL
        pil_image = Image.fromarray(rgb_image)

        return pil_image

    @staticmethod
    def resize_image(image: Image.Image, max_width: int = 800, max_height: int = 600) -> Image.Image:
        """
        Redimensiona una imagen manteniendo aspect ratio.

        Args:
            image: Imagen a redimensionar
            max_width: Ancho máximo
            max_height: Alto máximo

        Returns:
            Imagen redimensionada
        """
        # Calcular ratio
        width_ratio = max_width / image.width
        height_ratio = max_height / image.height
        ratio = min(width_ratio, height_ratio, 1.0)  # No agrandar

        # Calcular nuevas dimensiones
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)

        # Redimensionar
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return resized

    @staticmethod
    def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
        """
        Mejora el contraste de una imagen.

        Args:
            image: Imagen a procesar
            factor: Factor de mejora (1.0 = sin cambios)

        Returns:
            Imagen con contraste mejorado
        """
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Contrast(image)
        enhanced = enhancer.enhance(factor)

        return enhanced

    @staticmethod
    def to_grayscale(image: Image.Image) -> Image.Image:
        """
        Convierte imagen a escala de grises.

        Args:
            image: Imagen a convertir

        Returns:
            Imagen en escala de grises
        """
        return image.convert('L')

    @staticmethod
    def crop_area(image: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
        """
        Recorta un área específica de la imagen.

        Args:
            image: Imagen a recortar
            x: Coordenada X
            y: Coordenada Y
            width: Ancho del área
            height: Alto del área

        Returns:
            Imagen recortada
        """
        box = (x, y, x + width, y + height)
        cropped = image.crop(box)

        return cropped

    @staticmethod
    def save_with_quality(image: Image.Image, path: str, quality: int = 95) -> None:
        """
        Guarda imagen con calidad específica.

        Args:
            image: Imagen a guardar
            path: Ruta donde guardar
            quality: Calidad (1-100)
        """
        image.save(path, quality=quality, optimize=True)
