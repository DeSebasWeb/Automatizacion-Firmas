"""Tests unitarios para el pipeline de preprocesamiento de imágenes."""
import pytest
import numpy as np
from PIL import Image
import cv2

from src.infrastructure.image import ImagePreprocessor, ImageEnhancer, QualityMetrics


class TestImageEnhancer:
    """Tests para la clase ImageEnhancer."""

    def test_upscale_increases_resolution(self):
        """Test que upscaling aumenta la resolución correctamente."""
        # Crear imagen de prueba 100x100
        image = np.zeros((100, 100), dtype=np.uint8)

        # Upscale 3x
        upscaled = ImageEnhancer.upscale(image, factor=3)

        # Verificar dimensiones
        assert upscaled.shape == (300, 300)

    def test_upscale_factor_2(self):
        """Test upscaling con factor 2."""
        image = np.zeros((50, 50), dtype=np.uint8)
        upscaled = ImageEnhancer.upscale(image, factor=2)
        assert upscaled.shape == (100, 100)

    def test_to_grayscale_rgb(self):
        """Test conversión a escala de grises desde RGB."""
        # Crear imagen RGB
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        # Convertir a escala de grises
        gray = ImageEnhancer.to_grayscale(image)

        # Verificar que es 2D (escala de grises)
        assert len(gray.shape) == 2
        assert gray.shape == (100, 100)

    def test_to_grayscale_already_gray(self):
        """Test conversión cuando ya es escala de grises."""
        # Crear imagen en escala de grises
        image = np.zeros((100, 100), dtype=np.uint8)

        # Convertir (no debería cambiar)
        gray = ImageEnhancer.to_grayscale(image)

        # Verificar que sigue siendo la misma
        assert np.array_equal(gray, image)

    def test_denoise(self):
        """Test reducción de ruido."""
        # Crear imagen con ruido
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        # Aplicar reducción de ruido
        denoised = ImageEnhancer.denoise(image, h=10)

        # Verificar que las dimensiones no cambian
        assert denoised.shape == image.shape

        # Verificar que se aplicó (varianza debería disminuir)
        assert np.var(denoised) <= np.var(image)

    def test_increase_contrast(self):
        """Test aumento de contraste con CLAHE."""
        # Crear imagen de bajo contraste
        image = np.full((100, 100), 128, dtype=np.uint8)

        # Aplicar CLAHE
        enhanced = ImageEnhancer.increase_contrast(image, clip_limit=2.0)

        # Verificar dimensiones
        assert enhanced.shape == image.shape

    def test_sharpen(self):
        """Test sharpening."""
        # Crear imagen
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        # Aplicar sharpening
        sharpened = ImageEnhancer.sharpen(image)

        # Verificar dimensiones
        assert sharpened.shape == image.shape

    def test_binarize_otsu(self):
        """Test binarización con método Otsu."""
        # Crear imagen en escala de grises
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        # Binarizar
        binary = ImageEnhancer.binarize(image, method='otsu')

        # Verificar que solo tiene valores 0 y 255
        unique_values = np.unique(binary)
        assert len(unique_values) <= 2
        assert all(v in [0, 255] for v in unique_values)

    def test_binarize_adaptive(self):
        """Test binarización con método adaptativo."""
        # Crear imagen
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        # Binarizar
        binary = ImageEnhancer.binarize(image, method='adaptive')

        # Verificar que solo tiene valores 0 y 255
        unique_values = np.unique(binary)
        assert all(v in [0, 255] for v in unique_values)

    def test_binarize_invalid_method(self):
        """Test que método inválido lanza excepción."""
        image = np.zeros((100, 100), dtype=np.uint8)

        with pytest.raises(ValueError):
            ImageEnhancer.binarize(image, method='invalid')

    def test_morphological_clean(self):
        """Test operaciones morfológicas."""
        # Crear imagen binaria
        image = np.random.choice([0, 255], (100, 100), p=[0.9, 0.1]).astype(np.uint8)

        # Aplicar limpieza morfológica
        cleaned = ImageEnhancer.morphological_clean(image, kernel_size=(2, 2))

        # Verificar dimensiones
        assert cleaned.shape == image.shape

    def test_pil_to_cv2_rgb(self):
        """Test conversión PIL a OpenCV (RGB)."""
        # Crear imagen PIL RGB
        pil_image = Image.new('RGB', (100, 100), color=(255, 0, 0))

        # Convertir a OpenCV
        cv_image = ImageEnhancer.pil_to_cv2(pil_image)

        # Verificar dimensiones y tipo
        assert cv_image.shape == (100, 100, 3)
        assert cv_image.dtype == np.uint8

    def test_cv2_to_pil_bgr(self):
        """Test conversión OpenCV a PIL (BGR)."""
        # Crear imagen OpenCV BGR
        cv_image = np.zeros((100, 100, 3), dtype=np.uint8)

        # Convertir a PIL
        pil_image = ImageEnhancer.cv2_to_pil(cv_image)

        # Verificar tipo
        assert isinstance(pil_image, Image.Image)
        assert pil_image.size == (100, 100)

    def test_cv2_to_pil_grayscale(self):
        """Test conversión OpenCV a PIL (escala de grises)."""
        # Crear imagen en escala de grises
        cv_image = np.zeros((100, 100), dtype=np.uint8)

        # Convertir a PIL
        pil_image = ImageEnhancer.cv2_to_pil(cv_image)

        # Verificar tipo
        assert isinstance(pil_image, Image.Image)
        assert pil_image.size == (100, 100)


class TestQualityMetrics:
    """Tests para la clase QualityMetrics."""

    def test_calculate_sharpness(self):
        """Test cálculo de nitidez."""
        # Imagen nítida (bordes definidos)
        sharp_image = np.zeros((100, 100), dtype=np.uint8)
        sharp_image[40:60, 40:60] = 255

        # Calcular nitidez
        sharpness = QualityMetrics.calculate_sharpness(sharp_image)

        # Verificar que es un número positivo
        assert isinstance(sharpness, float)
        assert sharpness >= 0

    def test_calculate_contrast(self):
        """Test cálculo de contraste."""
        # Imagen con contraste (blanco y negro)
        high_contrast = np.zeros((100, 100), dtype=np.uint8)
        high_contrast[:50, :] = 255

        # Imagen sin contraste (gris uniforme)
        low_contrast = np.full((100, 100), 128, dtype=np.uint8)

        contrast_high = QualityMetrics.calculate_contrast(high_contrast)
        contrast_low = QualityMetrics.calculate_contrast(low_contrast)

        # Alto contraste debe ser mayor
        assert contrast_high > contrast_low

    def test_calculate_brightness(self):
        """Test cálculo de brillo."""
        # Imagen oscura
        dark = np.full((100, 100), 50, dtype=np.uint8)

        # Imagen clara
        bright = np.full((100, 100), 200, dtype=np.uint8)

        brightness_dark = QualityMetrics.calculate_brightness(dark)
        brightness_bright = QualityMetrics.calculate_brightness(bright)

        # Verificar que imagen clara tiene más brillo
        assert brightness_bright > brightness_dark

    def test_calculate_noise_level(self):
        """Test estimación de nivel de ruido."""
        # Imagen sin ruido (uniforme)
        clean = np.full((100, 100), 128, dtype=np.uint8)

        # Imagen con ruido
        noisy = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        noise_clean = QualityMetrics.calculate_noise_level(clean)
        noise_noisy = QualityMetrics.calculate_noise_level(noisy)

        # Imagen ruidosa debe tener mayor nivel de ruido
        assert noise_noisy > noise_clean

    def test_get_image_stats(self):
        """Test obtención de estadísticas completas."""
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        stats = QualityMetrics.get_image_stats(image)

        # Verificar que tiene todas las métricas esperadas
        expected_keys = ['sharpness', 'contrast', 'brightness', 'noise_level',
                         'width', 'height', 'total_pixels', 'edge_density']
        for key in expected_keys:
            assert key in stats
            assert isinstance(stats[key], float)

    def test_compare_images(self):
        """Test comparación entre dos imágenes."""
        # Crear dos imágenes diferentes
        original = np.full((100, 100), 100, dtype=np.uint8)
        processed = np.full((100, 100), 150, dtype=np.uint8)

        comparison = QualityMetrics.compare_images(original, processed)

        # Verificar estructura del resultado
        assert 'original' in comparison
        assert 'processed' in comparison
        assert 'improvement_percent' in comparison

        # Verificar que tiene métricas
        assert 'sharpness' in comparison['original']
        assert 'contrast' in comparison['processed']


class TestImagePreprocessor:
    """Tests para la clase ImagePreprocessor."""

    def test_initialization_default_config(self):
        """Test inicialización con configuración por defecto."""
        preprocessor = ImagePreprocessor()

        assert preprocessor.config is not None
        assert preprocessor.config['enabled'] == True
        assert preprocessor.config['upscale_factor'] == 3

    def test_initialization_custom_config(self):
        """Test inicialización con configuración personalizada."""
        custom_config = {
            'enabled': True,
            'upscale_factor': 4,
            'denoise': {'enabled': False}
        }

        preprocessor = ImagePreprocessor(custom_config)

        assert preprocessor.config['upscale_factor'] == 4
        assert preprocessor.config['denoise']['enabled'] == False

    def test_preprocess_returns_pil_image(self):
        """Test que preprocess retorna una imagen PIL."""
        # Crear imagen PIL de prueba
        image = Image.new('RGB', (100, 100), color=(255, 255, 255))

        # Configuración mínima para testing rápido
        config = {
            'enabled': True,
            'upscale_factor': 2,
            'denoise': {'enabled': False},
            'contrast': {'enabled': False},
            'sharpen': {'enabled': False},
            'binarize': {'enabled': False},
            'morphology': {'enabled': False},
            'deskew': {'enabled': False},
            'save_processed_images': False
        }

        preprocessor = ImagePreprocessor(config)
        processed = preprocessor.preprocess(image)

        # Verificar que retorna imagen PIL
        assert isinstance(processed, Image.Image)

    def test_preprocess_increases_size(self):
        """Test que preprocess aumenta el tamaño de la imagen."""
        # Crear imagen pequeña
        image = Image.new('RGB', (100, 100))

        config = {
            'enabled': True,
            'upscale_factor': 3,
            'denoise': {'enabled': False},
            'contrast': {'enabled': False},
            'sharpen': {'enabled': False},
            'binarize': {'enabled': False},
            'morphology': {'enabled': False},
            'deskew': {'enabled': False}
        }

        preprocessor = ImagePreprocessor(config)
        processed = preprocessor.preprocess(image)

        # Verificar que aumentó de tamaño
        assert processed.size[0] > image.size[0]
        assert processed.size[1] > image.size[1]

    def test_get_stats_after_preprocessing(self):
        """Test que get_stats retorna estadísticas después de procesar."""
        image = Image.new('RGB', (50, 50))

        config = {
            'enabled': True,
            'upscale_factor': 2,
            'denoise': {'enabled': False},
            'contrast': {'enabled': False},
            'sharpen': {'enabled': False},
            'binarize': {'enabled': False},
            'morphology': {'enabled': False},
            'deskew': {'enabled': False}
        }

        preprocessor = ImagePreprocessor(config)
        preprocessor.preprocess(image)

        stats = preprocessor.get_stats()

        # Verificar que tiene estadísticas
        assert 'original_size' in stats
        assert 'processed_size' in stats
        assert 'processing_time_ms' in stats

    def test_update_config(self):
        """Test actualización de configuración."""
        preprocessor = ImagePreprocessor()

        # Configuración inicial
        assert preprocessor.config['upscale_factor'] == 3

        # Actualizar configuración
        preprocessor.update_config({'upscale_factor': 4})

        # Verificar que se actualizó
        assert preprocessor.config['upscale_factor'] == 4


# Tests de integración
class TestIntegration:
    """Tests de integración del pipeline completo."""

    def test_full_pipeline_execution(self):
        """Test ejecución completa del pipeline."""
        # Crear imagen de prueba realista
        image = Image.new('L', (200, 300), color=200)

        config = {
            'enabled': True,
            'upscale_factor': 2,
            'denoise': {'enabled': True, 'h': 10},
            'contrast': {'enabled': True, 'clip_limit': 2.0},
            'sharpen': {'enabled': True},
            'binarize': {'enabled': True, 'method': 'otsu'},
            'morphology': {'enabled': True, 'kernel_size': (2, 2)},
            'deskew': {'enabled': False},
            'save_processed_images': False
        }

        preprocessor = ImagePreprocessor(config)
        processed = preprocessor.preprocess(image)

        # Verificar que se ejecutó correctamente
        assert isinstance(processed, Image.Image)
        assert processed.size[0] > image.size[0]

        # Verificar estadísticas
        stats = preprocessor.get_stats()
        assert stats['processing_time_ms'] > 0
