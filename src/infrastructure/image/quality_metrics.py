"""Métricas de calidad de imágenes para evaluar mejoras de preprocesamiento."""
import cv2
import numpy as np
from typing import Dict, Tuple
from PIL import Image


class QualityMetrics:
    """
    Calcula métricas de calidad de imágenes.

    Permite evaluar mejoras antes/después del preprocesamiento.
    """

    @staticmethod
    def calculate_sharpness(image: np.ndarray) -> float:
        """
        Calcula la nitidez de una imagen usando varianza de Laplaciano.

        Mayor valor = imagen más nítida.

        Args:
            image: Imagen en escala de grises

        Returns:
            Valor de nitidez (0-infinito, típicamente 0-1000)
        """
        # Aplicar operador Laplaciano
        laplacian = cv2.Laplacian(image, cv2.CV_64F)

        # Calcular varianza (mayor varianza = más nítida)
        sharpness = laplacian.var()

        return float(sharpness)

    @staticmethod
    def calculate_contrast(image: np.ndarray) -> float:
        """
        Calcula el contraste de una imagen usando desviación estándar.

        Mayor valor = mayor contraste.

        Args:
            image: Imagen en escala de grises

        Returns:
            Valor de contraste (0-255)
        """
        # Desviación estándar de los valores de píxeles
        contrast = np.std(image)

        return float(contrast)

    @staticmethod
    def calculate_brightness(image: np.ndarray) -> float:
        """
        Calcula el brillo promedio de una imagen.

        Args:
            image: Imagen en escala de grises

        Returns:
            Valor de brillo promedio (0-255)
        """
        brightness = np.mean(image)

        return float(brightness)

    @staticmethod
    def calculate_noise_level(image: np.ndarray) -> float:
        """
        Estima el nivel de ruido de una imagen.

        Usa el método de varianza local.

        Args:
            image: Imagen en escala de grises

        Returns:
            Estimación de nivel de ruido (0-100, menor es mejor)
        """
        # Calcular imagen suavizada
        blurred = cv2.GaussianBlur(image, (5, 5), 0)

        # Diferencia entre original y suavizada
        noise = cv2.absdiff(image, blurred)

        # Promedio de la diferencia
        noise_level = np.mean(noise)

        return float(noise_level)

    @staticmethod
    def calculate_resolution_quality(image: np.ndarray) -> Dict[str, float]:
        """
        Calcula métricas relacionadas con la resolución.

        Args:
            image: Imagen en escala de grises

        Returns:
            Diccionario con métricas de resolución
        """
        height, width = image.shape[:2]
        total_pixels = height * width

        # Calcular densidad de bordes (más bordes = mejor resolución)
        edges = cv2.Canny(image, 50, 150)
        edge_density = np.count_nonzero(edges) / total_pixels

        return {
            'width': float(width),
            'height': float(height),
            'total_pixels': float(total_pixels),
            'edge_density': float(edge_density)
        }

    @staticmethod
    def compare_images(
        original: np.ndarray,
        processed: np.ndarray
    ) -> Dict[str, Dict[str, float]]:
        """
        Compara métricas entre imagen original y procesada.

        Args:
            original: Imagen original
            processed: Imagen procesada

        Returns:
            Diccionario con métricas comparativas
        """
        # Convertir a escala de grises si es necesario
        if len(original.shape) == 3:
            original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        else:
            original_gray = original

        if len(processed.shape) == 3:
            processed_gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        else:
            processed_gray = processed

        # Calcular métricas para ambas imágenes
        original_metrics = {
            'sharpness': QualityMetrics.calculate_sharpness(original_gray),
            'contrast': QualityMetrics.calculate_contrast(original_gray),
            'brightness': QualityMetrics.calculate_brightness(original_gray),
            'noise_level': QualityMetrics.calculate_noise_level(original_gray),
        }

        processed_metrics = {
            'sharpness': QualityMetrics.calculate_sharpness(processed_gray),
            'contrast': QualityMetrics.calculate_contrast(processed_gray),
            'brightness': QualityMetrics.calculate_brightness(processed_gray),
            'noise_level': QualityMetrics.calculate_noise_level(processed_gray),
        }

        # Calcular mejoras
        improvements = {}
        for key in original_metrics:
            original_val = original_metrics[key]
            processed_val = processed_metrics[key]

            if original_val > 0:
                # Para noise_level, menor es mejor
                if key == 'noise_level':
                    improvement = ((original_val - processed_val) / original_val) * 100
                else:
                    improvement = ((processed_val - original_val) / original_val) * 100
            else:
                improvement = 0.0

            improvements[key] = improvement

        return {
            'original': original_metrics,
            'processed': processed_metrics,
            'improvement_percent': improvements
        }

    @staticmethod
    def get_image_stats(image: np.ndarray) -> Dict[str, float]:
        """
        Obtiene estadísticas completas de una imagen.

        Args:
            image: Imagen en cualquier formato

        Returns:
            Diccionario con todas las métricas disponibles
        """
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        stats = {
            'sharpness': QualityMetrics.calculate_sharpness(gray),
            'contrast': QualityMetrics.calculate_contrast(gray),
            'brightness': QualityMetrics.calculate_brightness(gray),
            'noise_level': QualityMetrics.calculate_noise_level(gray),
            'width': float(image.shape[1]),
            'height': float(image.shape[0]),
            'total_pixels': float(image.shape[0] * image.shape[1]),
        }

        # Agregar métricas de resolución
        resolution_metrics = QualityMetrics.calculate_resolution_quality(gray)
        stats.update(resolution_metrics)

        return stats

    @staticmethod
    def print_comparison(comparison: Dict[str, Dict[str, float]]) -> None:
        """
        Imprime una comparación legible de métricas.

        Args:
            comparison: Resultado de compare_images()
        """
        print("\n" + "="*60)
        print("COMPARACIÓN DE CALIDAD DE IMAGEN")
        print("="*60)

        print("\nMÉTRICAS ORIGINALES:")
        for key, value in comparison['original'].items():
            print(f"  {key:15s}: {value:8.2f}")

        print("\nMÉTRICAS PROCESADAS:")
        for key, value in comparison['processed'].items():
            print(f"  {key:15s}: {value:8.2f}")

        print("\nMEJORAS (%):")
        for key, value in comparison['improvement_percent'].items():
            sign = "↑" if value > 0 else "↓" if value < 0 else "="
            print(f"  {key:15s}: {sign} {abs(value):6.1f}%")

        print("="*60 + "\n")
