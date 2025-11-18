"""Pipeline completo de preprocesamiento de imágenes para Google Cloud Vision API."""
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Tuple, Optional
from pathlib import Path
import time

from .enhancer import ImageEnhancer
from .quality_metrics import QualityMetrics


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
            'upscale_factor': 3,  # 3x es suficiente sin degradar
            'normalize_illumination': {
                'enabled': False  # Desactivado - puede crear artefactos
            },
            'denoise': {
                'enabled': True,
                'h': 8,  # Suave - no destruye detalles
                'template_window_size': 7,
                'search_window_size': 21
            },
            'contrast': {
                'enabled': True,
                'clip_limit': 2.5,  # Moderado
                'tile_grid_size': (8, 8)
            },
            'enhance_edges': {
                'enabled': False  # Desactivado - Google Vision ya detecta bien bordes
            },
            'sharpen': {
                'enabled': True,
                'intensity': 'normal',  # Normal, no agresivo
                'use_unsharp_mask': False  # Desactivado
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

        print("\n" + "="*70)
        print("PIPELINE DE PREPROCESAMIENTO - GOOGLE VISION API")
        print("Pipeline CONSERVADOR: preserva información sin destruirla")
        print("="*70)

        # Convertir PIL a OpenCV
        cv_image = self.enhancer.pil_to_cv2(image)
        original_cv = cv_image.copy()

        print(f"✓ Imagen original: {cv_image.shape[1]}x{cv_image.shape[0]} px")

        # Calcular métricas de imagen original
        original_stats = self.metrics.get_image_stats(original_cv)

        # PASO 0: Normalización de iluminación (NUEVO)
        if self.config.get('normalize_illumination', {}).get('enabled', True):
            print(f"\n[0/11] Normalizando iluminación...")
            cv_image = self.enhancer.normalize_illumination(cv_image)
            print(f"      ✓ Iluminación normalizada")

        # PASO 1: Upscaling (CRÍTICO para distinguir 1 vs 7 y 3 vs 8)
        if self.config.get('upscale_factor', 4) > 1:
            factor = self.config['upscale_factor']
            print(f"\n[1/11] Upscaling {factor}x con interpolación cúbica...")
            cv_image = self.enhancer.upscale(cv_image, factor=factor)
            print(f"      ✓ Nueva resolución: {cv_image.shape[1]}x{cv_image.shape[0]} px")
        else:
            print("\n[1/11] Upscaling deshabilitado")

        # PASO 2: Conversión a escala de grises
        print("\n[2/11] Convirtiendo a escala de grises...")
        cv_image = self.enhancer.to_grayscale(cv_image)
        print(f"      ✓ Conversión completada")

        # PASO 3: Reducción de ruido
        if self.config.get('denoise', {}).get('enabled', True):
            print("\n[3/11] Reduciendo ruido con fastNlMeansDenoising...")
            denoise_config = self.config['denoise']
            cv_image = self.enhancer.denoise(
                cv_image,
                h=denoise_config.get('h', 12),
                template_window_size=denoise_config.get('template_window_size', 7),
                search_window_size=denoise_config.get('search_window_size', 21)
            )
            print(f"      ✓ Ruido reducido")
        else:
            print("\n[3/11] Reducción de ruido deshabilitada")

        # PASO 4: Aumento de contraste (CLAHE)
        if self.config.get('contrast', {}).get('enabled', True):
            print("\n[4/11] Aumentando contraste adaptativo (CLAHE)...")
            contrast_config = self.config['contrast']
            cv_image = self.enhancer.increase_contrast(
                cv_image,
                clip_limit=contrast_config.get('clip_limit', 3.0),
                tile_grid_size=tuple(contrast_config.get('tile_grid_size', [8, 8]))
            )
            print(f"      ✓ Contraste mejorado")
        else:
            print("\n[4/11] Aumento de contraste deshabilitado")

        # PASO 5: Realzar bordes (NUEVO - antes de sharpening)
        if self.config.get('enhance_edges', {}).get('enabled', True):
            print("\n[5/11] Realzando bordes (Sobel)...")
            cv_image = self.enhancer.enhance_edges(cv_image)
            print(f"      ✓ Bordes realzados")
        else:
            print("\n[5/11] Realce de bordes deshabilitado")

        # PASO 6: Sharpening agresivo
        if self.config.get('sharpen', {}).get('enabled', True):
            sharpen_config = self.config.get('sharpen', {})
            intensity = sharpen_config.get('intensity', 'high')
            print(f"\n[6/11] Aumentando nitidez (sharpening {intensity})...")
            cv_image = self.enhancer.sharpen(cv_image, intensity=intensity)
            print(f"      ✓ Nitidez aumentada (kernel {intensity})")

            # PASO 6b: Unsharp masking adicional (NUEVO)
            if sharpen_config.get('use_unsharp_mask', True):
                print(f"      [6b] Aplicando unsharp masking adicional...")
                cv_image = self.enhancer.unsharp_mask(cv_image, sigma=1.5, strength=2.0)
                print(f"      ✓ Unsharp masking aplicado")
        else:
            print("\n[6/11] Sharpening deshabilitado")

        # PASO 7: Binarización
        if self.config.get('binarize', {}).get('enabled', True):
            print("\n[7/11] Aplicando binarización método Otsu...")
            binarize_config = self.config['binarize']
            method = binarize_config.get('method', 'otsu')
            cv_image = self.enhancer.binarize(cv_image, method=method)
            print(f"      ✓ Binarización completada ({method})")
        else:
            print("\n[7/11] Binarización deshabilitada")

        # PASO 8: Operaciones morfológicas con iteraciones
        if self.config.get('morphology', {}).get('enabled', True):
            print("\n[8/11] Aplicando operaciones morfológicas (Close + Open)...")
            morphology_config = self.config['morphology']
            kernel_size = tuple(morphology_config.get('kernel_size', [2, 2]))
            iterations = morphology_config.get('iterations', 2)
            cv_image = self.enhancer.morphological_clean(
                cv_image,
                kernel_size=kernel_size,
                iterations=iterations
            )
            print(f"      ✓ Limpieza morfológica completada ({iterations} iteraciones)")
        else:
            print("\n[8/11] Operaciones morfológicas deshabilitadas")

        # PASO 9: Corrección de inclinación (opcional)
        if self.config.get('deskew', {}).get('enabled', False):
            print("\n[9/11] Corrigiendo inclinación...")
            cv_image = self.enhancer.deskew(cv_image)
            print(f"      ✓ Inclinación corregida")
        else:
            print("\n[9/11] Corrección de inclinación deshabilitada")

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
            'processing_time_ms': processing_time
        }

        # Imprimir resumen
        self._print_summary()

        # Guardar imágenes de comparación si está habilitado
        if self.config.get('save_processed_images', False):
            self._save_comparison(original_cv, cv_image)

        # Convertir de escala de grises a RGB para Google Vision
        # Google Vision funciona MEJOR con imágenes en color/escala de grises RGB
        if len(cv_image.shape) == 2:  # Si es escala de grises
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2RGB)
            print("✓ Imagen convertida a RGB para Google Vision")

        # Convertir de vuelta a PIL
        processed_pil = self.enhancer.cv2_to_pil(cv_image)

        print("="*70)
        print("PIPELINE COMPLETADO EXITOSAMENTE")
        print("="*70 + "\n")

        return processed_pil

    def _print_summary(self) -> None:
        """Imprime resumen de las mejoras aplicadas."""
        print("\n" + "-"*70)
        print("RESUMEN DE MEJORAS")
        print("-"*70)

        comparison = self.stats['comparison']

        print(f"\nResolución:")
        print(f"  Original:  {self.stats['original_size'][0]}x{self.stats['original_size'][1]} px")
        print(f"  Procesada: {self.stats['processed_size'][0]}x{self.stats['processed_size'][1]} px")

        print(f"\nMejoras de calidad:")
        improvements = comparison['improvement_percent']
        for metric, value in improvements.items():
            sign = "↑" if value > 0 else "↓" if value < 0 else "="
            color = "+" if value > 0 else "-" if value < 0 else " "
            print(f"  {metric:15s}: {sign} {color}{abs(value):6.1f}%")

        print(f"\nTiempo de procesamiento: {self.stats['processing_time_ms']:.0f} ms")
        print("-"*70)

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

        print(f"\n✓ Imágenes guardadas en: {output_dir}")
        print(f"  - {original_path.name}")
        print(f"  - {processed_path.name}")

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
