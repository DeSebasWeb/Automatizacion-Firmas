"""Métodos individuales de mejora de imágenes para optimizar OCR."""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional


class ImageEnhancer:
    """
    Métodos estáticos de mejora individual de imágenes.

    Cada método realiza una transformación específica para mejorar la calidad
    de la imagen antes de enviarla a Google Cloud Vision API.
    """

    @staticmethod
    def upscale(image: np.ndarray, factor: int = 3) -> np.ndarray:
        """
        Aumenta la resolución de la imagen con interpolación cúbica.

        CRÍTICO para distinguir 1 vs 7 en escritura manual.

        Args:
            image: Imagen en formato OpenCV (numpy array)
            factor: Factor de escalado (2 o 3 recomendado)

        Returns:
            Imagen escalada con mayor resolución
        """
        height, width = image.shape[:2]
        new_width = width * factor
        new_height = height * factor

        # Interpolación cúbica para mejor calidad
        upscaled = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_CUBIC
        )

        return upscaled

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        Convierte imagen a escala de grises.

        Elimina información de color innecesaria y reduce tamaño.

        Args:
            image: Imagen en formato OpenCV (BGR o RGB)

        Returns:
            Imagen en escala de grises
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        return gray

    @staticmethod
    def denoise(
        image: np.ndarray,
        h: int = 10,
        template_window_size: int = 7,
        search_window_size: int = 21
    ) -> np.ndarray:
        """
        Reduce ruido de la imagen usando fastNlMeansDenoising.

        Elimina artefactos de escaneo o fotografía.

        Args:
            image: Imagen en escala de grises
            h: Parámetro de filtrado (10 recomendado)
            template_window_size: Tamaño de ventana de template (7 recomendado)
            search_window_size: Tamaño de ventana de búsqueda (21 recomendado)

        Returns:
            Imagen sin ruido
        """
        denoised = cv2.fastNlMeansDenoising(
            image,
            None,
            h=h,
            templateWindowSize=template_window_size,
            searchWindowSize=search_window_size
        )

        return denoised

    @staticmethod
    def increase_contrast(
        image: np.ndarray,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8)
    ) -> np.ndarray:
        """
        Aumenta contraste adaptativo usando CLAHE.

        Mejora contraste local sin sobreexponer.

        Args:
            image: Imagen en escala de grises
            clip_limit: Límite de recorte (2.0 recomendado)
            tile_grid_size: Tamaño de la cuadrícula de tiles

        Returns:
            Imagen con contraste mejorado
        """
        clahe = cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=tile_grid_size
        )

        enhanced = clahe.apply(image)

        return enhanced

    @staticmethod
    def sharpen(image: np.ndarray, intensity: str = 'high') -> np.ndarray:
        """
        Aumenta la nitidez de la imagen.

        Hace bordes de números más definidos. CRÍTICO para distinguir 3 vs 8.

        Args:
            image: Imagen en escala de grises
            intensity: Intensidad del sharpening ('normal', 'high', 'ultra')

        Returns:
            Imagen más nítida
        """
        if intensity == 'ultra':
            # Kernel ultra agresivo para escritura manual difícil
            kernel = np.array([
                [-1, -2, -1],
                [-2, 17, -2],
                [-1, -2, -1]
            ], dtype=np.float32)
        elif intensity == 'high':
            # Kernel agresivo (mejor para distinguir 3 vs 8)
            kernel = np.array([
                [0, -1, 0],
                [-1, 9, -1],
                [0, -1, 0]
            ], dtype=np.float32)
        else:  # normal
            # Kernel estándar
            kernel = np.array([
                [0, -1, 0],
                [-1, 5, -1],
                [0, -1, 0]
            ], dtype=np.float32)

        sharpened = cv2.filter2D(image, -1, kernel)

        return sharpened

    @staticmethod
    def unsharp_mask(image: np.ndarray, sigma: float = 1.5, strength: float = 1.5) -> np.ndarray:
        """
        Aplica unsharp masking para realzar bordes (alternativa a sharpening).

        Método más sofisticado que el sharpening básico.

        Args:
            image: Imagen en escala de grises
            sigma: Radio del Gaussian blur (1.0-2.0 recomendado)
            strength: Intensidad del realce (1.5-2.5 recomendado)

        Returns:
            Imagen con bordes realzados
        """
        # Crear versión borrosa
        blurred = cv2.GaussianBlur(image, (0, 0), sigma)

        # Unsharp mask = Original + strength * (Original - Blurred)
        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)

        return sharpened

    @staticmethod
    def binarize(image: np.ndarray, method: str = 'otsu') -> np.ndarray:
        """
        Convierte imagen a blanco y negro puro usando binarización.

        Args:
            image: Imagen en escala de grises
            method: Método de binarización ('otsu' o 'adaptive')

        Returns:
            Imagen binarizada
        """
        if method == 'otsu':
            # Método Otsu - auto-calcula mejor umbral
            _, binary = cv2.threshold(
                image,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        elif method == 'adaptive':
            # Binarización adaptativa
            binary = cv2.adaptiveThreshold(
                image,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
        else:
            raise ValueError(f"Método de binarización '{method}' no soportado")

        return binary

    @staticmethod
    def morphological_clean(
        image: np.ndarray,
        kernel_size: Tuple[int, int] = (2, 2),
        iterations: int = 1
    ) -> np.ndarray:
        """
        Aplica operaciones morfológicas para limpiar la imagen.

        - Close: Rellena pequeños huecos en números
        - Open: Elimina ruido pequeño

        Args:
            image: Imagen binarizada
            kernel_size: Tamaño del kernel morfológico
            iterations: Número de iteraciones de cada operación

        Returns:
            Imagen limpia
        """
        kernel = np.ones(kernel_size, np.uint8)

        # Close: Rellena huecos pequeños
        closed = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=iterations)

        # Open: Elimina ruido pequeño
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=iterations)

        return opened

    @staticmethod
    def enhance_edges(image: np.ndarray) -> np.ndarray:
        """
        Realza los bordes de la imagen sin hacer sharpening completo.

        Útil para mejorar la distinción entre caracteres similares (3 vs 8).

        Args:
            image: Imagen en escala de grises

        Returns:
            Imagen con bordes realzados
        """
        # Detectar bordes con Sobel
        sobelx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)

        # Magnitud del gradiente
        edges = np.sqrt(sobelx**2 + sobely**2)
        edges = np.uint8(np.clip(edges, 0, 255))

        # Combinar con imagen original
        enhanced = cv2.addWeighted(image, 0.7, edges, 0.3, 0)

        return enhanced

    @staticmethod
    def normalize_illumination(image: np.ndarray) -> np.ndarray:
        """
        Normaliza la iluminación para corregir sombras o iluminación desigual.

        Funciona tanto con imágenes en color como en escala de grises.

        Args:
            image: Imagen en cualquier formato (BGR, RGB, o escala de grises)

        Returns:
            Imagen con iluminación normalizada (mismo formato que entrada)
        """
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            # Es imagen en color
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            # Ya es escala de grises
            gray = image

        # Crear imagen de fondo estimada (muy borrosa)
        background = cv2.GaussianBlur(gray, (51, 51), 0)

        # Restar fondo para normalizar
        normalized = cv2.subtract(gray, background)
        normalized = cv2.add(normalized, 127)  # Ajustar brillo

        # Si la entrada era color, devolver en color (aunque ahora será gris)
        if len(image.shape) == 3:
            normalized = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)

        return normalized

    @staticmethod
    def deskew(image: np.ndarray) -> np.ndarray:
        """
        Corrige la inclinación de la imagen.

        Usa minAreaRect para detectar ángulo y rotar.
        Solo aplicar si la imagen está visiblemente inclinada.

        Args:
            image: Imagen binarizada

        Returns:
            Imagen corregida
        """
        # Encontrar coordenadas de píxeles no cero
        coords = np.column_stack(np.where(image > 0))

        if len(coords) < 10:
            # No hay suficientes píxeles para calcular ángulo
            return image

        # Calcular ángulo de rotación
        angle = cv2.minAreaRect(coords)[-1]

        # Ajustar ángulo
        if angle < -45:
            angle = 90 + angle

        # Solo corregir si el ángulo es significativo (>1 grado)
        if abs(angle) < 1.0:
            return image

        # Rotar imagen
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return rotated

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
            image: Array numpy (puede ser BGR, RGB o escala de grises)

        Returns:
            Imagen PIL
        """
        # Si es escala de grises, convertir directamente
        if len(image.shape) == 2:
            return Image.fromarray(image)

        # Si es BGR, convertir a RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        return pil_image
