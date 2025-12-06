from .tesseract_ocr import TesseractOCR
from .manual_ocr import ManualOCR

# Base classes and utilities
from .base_ocr_adapter import BaseOCRAdapter
from .image_converter import ImageConverter

# OCR Factory (siempre disponible)
from .ocr_factory import create_ocr_adapter, get_available_providers, get_provider_comparison

try:
    from .google_vision_adapter import GoogleVisionAdapter
    GOOGLE_VISION_AVAILABLE = True
except Exception:
    GOOGLE_VISION_AVAILABLE = False

try:
    from .azure_vision_adapter import AzureVisionAdapter
    AZURE_VISION_AVAILABLE = True
except Exception:
    AZURE_VISION_AVAILABLE = False

try:
    from .ensemble_ocr import EnsembleOCR
    ENSEMBLE_AVAILABLE = True
except Exception:
    ENSEMBLE_AVAILABLE = False

try:
    from .digit_level_ensemble_ocr import DigitLevelEnsembleOCR
    DIGIT_ENSEMBLE_AVAILABLE = True
except Exception:
    DIGIT_ENSEMBLE_AVAILABLE = False

try:
    from .easyocr_adapter import EasyOCRAdapter
    EASYOCR_AVAILABLE = True
except Exception:
    EASYOCR_AVAILABLE = False

try:
    from .paddleocr_adapter import PaddleOCRAdapter
    PADDLEOCR_AVAILABLE = True
except Exception:
    PADDLEOCR_AVAILABLE = False

__all__ = [
    'TesseractOCR',
    'ManualOCR',
    'BaseOCRAdapter',
    'ImageConverter',
    'create_ocr_adapter',
    'get_available_providers',
    'get_provider_comparison',
]

if GOOGLE_VISION_AVAILABLE:
    __all__.append('GoogleVisionAdapter')

if AZURE_VISION_AVAILABLE:
    __all__.append('AzureVisionAdapter')

if ENSEMBLE_AVAILABLE:
    __all__.append('EnsembleOCR')

if DIGIT_ENSEMBLE_AVAILABLE:
    __all__.append('DigitLevelEnsembleOCR')

if EASYOCR_AVAILABLE:
    __all__.append('EasyOCRAdapter')

if PADDLEOCR_AVAILABLE:
    __all__.append('PaddleOCRAdapter')
