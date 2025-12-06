"""Pipeline completo de preprocesamiento de imágenes para Google Cloud Vision API."""
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Tuple, Optional
from pathlib import Path
import time

from .enhancer import ImageEnhancer
from .quality_metrics import QualityMetrics
from ...shared.logging import (
    LoggerFactory,
    log_info_message,
    log_debug_message,
    log_processing_step
)


class ImagePreprocessor:
    """
    Pipeline completo de mejoras de imagen para maximizar precisión de Google Vision OCR.

    Aplica secuencialmente:
    1. Upscaling (2x-3x) con interpolación cúbica
    2. Conversión a escala de grises
    3. Reducción de ruido (fastNlMeansDenoising)
    4. Aumento de contraste adaptativo (CLAHE)
    5. Sharpening para aumentar nitidez
    6. Binarización método Otsu
    7. Operaciones morfológicas (Close + Open)
    8. Corrección de inclinación (opcional)

    Attributes:
        config: Diccionario de configuración
        enhancer: Instancia de ImageEnhancer
        metrics: Instancia de QualityMetrics
        stats: Estadísticas del último procesamiento
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el preprocesador con configuración.

        Args:
            config: Diccionario de configuración (opcional)
        """
        self.config = config or self._get_default_config()
        self.enhancer = ImageEnhancer
        self.metrics = QualityMetrics
        self.stats = {}
        self.logger = LoggerFactory.get_image_logger()

    def _get_default_config(self) -> Dict:
        """
        Obtiene configuración por defecto del pipeline.

        OPTIMIZADO PARA GOOGLE VISION API:
        - Pipeline CONSERVADOR que NO destruye información
        - NO binarización (Google Vision prefiere escala de grises)
        - NO morfología (puede destruir trazos finos)
        - SÍ upscaling moderado (mejora resolución)
        - SÍ reducción de ruido suave
        - SÍ contraste moderado
        - SÍ sharpening suave

        Returns:
            Diccionario con configuración por defecto
        """
        return {
            'enabled': True,
            'upscale_factor': 4,  # 4x para máxima resolución sin degradar
            'normalize_illumination': {
                'enabled': False  # Desactivado - puede crear artefactos
            },
            'denoise': {
                'enabled': True,
                'h': 7,  # Moderado - preserva trazos sin adelgazar
                'template_window_size': 7,
                'search_window_size': 21
            },
            'contrast': {
                'enabled': True,
                'clip_limit': 2.5,  # Moderado - no adelgaza trazos
                'tile_grid_size': (8, 8)
            },
            'enhance_edges': {
                'enabled': False  # Desactivado - adelgaza trazos
            },
            'sharpen': {
                'enabled': True,
                'intensity': 'normal',  # Normal - no adelgaza trazos
                'use_unsharp_mask': False  # Desactivado - adelgaza trazos
            },
            'binarize': {
                'enabled': False,  # CRÍTICO: NO binarizar para Google Vision
                'method': 'otsu'
            },
            'morphology': {
                'enabled': False,  # CRÍTICO: NO morfología, destruye información
                'kernel_size': (2, 2),
                'iterations': 1
            },
            'deskew': {
                'enabled': False  # Solo si imagen está inclinada
            },
            'save_processed_images': False,
            'output_dir': 'temp/processed'
        }

    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Ejecuta el pipeline completo de preprocesamiento.

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen PIL preprocesada y optimizada
        """
        start_time = time.time()

        # Convertir PIL a OpenCV
        cv_image = self.enhancer.pil_to_cv2(image)
        original_cv = cv_image.copy()

        log_info_message(
            self.logger,
            "Iniciando pipeline de preprocesamiento",
            version="3.1",
            original_size=f"{cv_image.shape[1]}x{cv_image.shape[0]}",
            optimized_for="google_vision_api"
        )

        # Calcular métricas de imagen original
        original_stats = self.metrics.get_image_stats(original_cv)

        # Contar pasos habilitados
        enabled_steps = []

        # PASO 0: Normalización de iluminación
        if self.config.get('normalize_illumination', {}).get('enabled', True):
            enabled_steps.append("normalize_illumination")
            cv_image = self.enhancer.normalize_illumination(cv_image)

        # PASO 1: Upscaling
        if self.config.get('upscale_factor', 4) > 1:
            factor = self.config['upscale_factor']
            enabled_steps.append(f"upscale_{factor}x")
            cv_image = self.enhancer.upscale(cv_image, factor=factor)
            log_debug_message(
                self.logger,
                "Upscaling aplicado",
                factor=factor,
                new_size=f"{cv_image.shape[1]}x{cv_image.shape[0]}"
            )

        # PASO 2: Conversión a escala de grises
        enabled_steps.append("grayscale")
        cv_image = self.enhancer.to_grayscale(cv_image)

        # PASO 3: Reducción de ruido
        if self.config.get('denoise', {}).get('enabled', True):
            enabled_steps.append("denoise")
            denoise_config = self.config['denoise']
            cv_image = self.enhancer.denoise(
                cv_image,
                h=denoise_config.get('h', 12),
                template_window_size=denoise_config.get('template_window_size', 7),
                search_window_size=denoise_config.get('search_window_size', 21)
            )

        # PASO 4: Aumento de contraste (CLAHE)
        if self.config.get('contrast', {}).get('enabled', True):
            enabled_steps.append("contrast")
            contrast_config = self.config['contrast']
            cv_image = self.enhancer.increase_contrast(
                cv_image,
                clip_limit=contrast_config.get('clip_limit', 3.0),
                tile_grid_size=tuple(contrast_config.get('tile_grid_size', [8, 8]))
            )

        # PASO 5: Realzar bordes
        if self.config.get('enhance_edges', {}).get('enabled', False):
            enabled_steps.append("enhance_edges")
            cv_image = self.enhancer.enhance_edges(cv_image, strength=0.5)

        # PASO 6: Sharpening
        if self.config.get('sharpen', {}).get('enabled', True):
            sharpen_config = self.config.get('sharpen', {})
            intensity = sharpen_config.get('intensity', 'high')
            enabled_steps.append(f"sharpen_{intensity}")
            cv_image = self.enhancer.sharpen(cv_image, intensity=intensity)

            if sharpen_config.get('use_unsharp_mask', False):
                enabled_steps.append("unsharp_mask")
                cv_image = self.enhancer.unsharp_mask(cv_image, sigma=1.5, strength=1.5)

        # PASO 7: Binarización
        if self.config.get('binarize', {}).get('enabled', True):
            binarize_config = self.config['binarize']
            method = binarize_config.get('method', 'otsu')
            enabled_steps.append(f"binarize_{method}")
            cv_image = self.enhancer.binarize(cv_image, method=method)

        # PASO 8: Operaciones morfológicas
        if self.config.get('morphology', {}).get('enabled', True):
            morphology_config = self.config['morphology']
            iterations = morphology_config.get('iterations', 2)
            enabled_steps.append(f"morphology_x{iterations}")
            kernel_size = tuple(morphology_config.get('kernel_size', [2, 2]))
            cv_image = self.enhancer.morphological_clean(
                cv_image,
                kernel_size=kernel_size,
                iterations=iterations
            )

        # PASO 9: Corrección de inclinación
        if self.config.get('deskew', {}).get('enabled', False):
            enabled_steps.append("deskew")
            cv_image = self.enhancer.deskew(cv_image)

        # Calcular métricas de imagen procesada
        processed_stats = self.metrics.get_image_stats(cv_image)

        # Comparar métricas
        comparison = self.metrics.compare_images(original_cv, cv_image)

        # Guardar estadísticas
        processing_time = (time.time() - start_time) * 1000
        self.stats = {
            'original_size': (original_cv.shape[1], original_cv.shape[0]),
            'processed_size': (cv_image.shape[1], cv_image.shape[0]),
            'original_stats': original_stats,
            'processed_stats': processed_stats,
            'comparison': comparison,
            'processing_time_ms': processing_time,
            'enabled_steps': enabled_steps
        }

        # Guardar imágenes de comparación si está habilitado
        if self.config.get('save_processed_images', False):
            self._save_comparison(original_cv, cv_image)

        # Convertir de escala de grises a RGB para Google Vision
        if len(cv_image.shape) == 2:  # Si es escala de grises
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2RGB)

        # Convertir de vuelta a PIL
        processed_pil = self.enhancer.cv2_to_pil(cv_image)

        # Log resumen conciso
        log_info_message(
            self.logger,
            "Pipeline de preprocesamiento completado",
            steps_applied=len(enabled_steps),
            steps=enabled_steps,
            processing_time_ms=round(processing_time, 2),
            original_size=f"{original_cv.shape[1]}x{original_cv.shape[0]}",
            processed_size=f"{cv_image.shape[1]}x{cv_image.shape[0]}",
            sharpness_improvement=f"{comparison['improvement_percent']['sharpness']:.1f}%",
            contrast_improvement=f"{comparison['improvement_percent']['contrast']:.1f}%"
        )

        return processed_pil


    def _save_comparison(self, original: np.ndarray, processed: np.ndarray) -> None:
        """
        Guarda imágenes originales y procesadas para comparación.

        Args:
            original: Imagen original
            processed: Imagen procesada
        """
        output_dir = Path(self.config.get('output_dir', 'temp/processed'))
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime('%Y%m%d_%H%M%S')

        # Guardar original
        original_path = output_dir / f'original_{timestamp}.png'
        cv2.imwrite(str(original_path), original)

        # Guardar procesada
        processed_path = output_dir / f'processed_{timestamp}.png'
        cv2.imwrite(str(processed_path), processed)

        log_info_message(
            self.logger,
            "Imagenes de comparacion guardadas",
            output_dir=str(output_dir),
            original_file=original_path.name,
            processed_file=processed_path.name
        )

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del último procesamiento.

        Returns:
            Diccionario con métricas de mejora
        """
        return self.stats

    def update_config(self, new_config: Dict) -> None:
        """
        Actualiza la configuración del preprocesador.

        Args:
            new_config: Nueva configuración
        """
        self.config.update(new_config)
