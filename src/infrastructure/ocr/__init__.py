from .tesseract_ocr import TesseractOCR
from .manual_ocr import ManualOCR

try:
    from .google_vision_adapter import GoogleVisionAdapter
    GOOGLE_VISION_AVAILABLE = True
except Exception:
    GOOGLE_VISION_AVAILABLE = False

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

__all__ = ['TesseractOCR', 'ManualOCR']

if GOOGLE_VISION_AVAILABLE:
    __all__.append('GoogleVisionAdapter')

if EASYOCR_AVAILABLE:
    __all__.append('EasyOCRAdapter')

if PADDLEOCR_AVAILABLE:
    __all__.append('PaddleOCRAdapter')
