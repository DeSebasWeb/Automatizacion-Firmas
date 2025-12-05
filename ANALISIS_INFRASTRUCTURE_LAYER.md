# 🔍 Análisis de Infrastructure Layer - Problemas y Mejoras

**Fecha:** 2025-12-04
**Severidad:** 🔴 CRÍTICA - Multiple high-impact issues found
**Archivos analizados:** 22

---

## 📊 Resumen Ejecutivo

Se han identificado **34 problemas** en la capa de infraestructura:

| Severidad | Cantidad | Categoría |
|-----------|----------|-----------|
| 🔴 CRÍTICA | 8 | SOLID violations, God classes |
| 🟠 ALTA | 12 | Architecture issues, hardcoded logic |
| 🟡 MEDIA | 10 | Code smells, inefficiencies |
| 🔵 BAJA | 4 | Minor improvements |

### Problemas Principales:

1. **ImagePreprocessor es un God Class** (338 LOC, 11 responsabilidades)
2. **ImageEnhancer con 15+ métodos estáticos** (anti-pattern utility class)
3. **print() statements en producción** (debe usar logger)
4. **Hardcoded configuration** en múltiples clases
5. **Sin manejo de errores** en operaciones críticas
6. **Código duplicado** entre adaptadores OCR
7. **Falta de abstracción** en preprocesamiento
8. **Performance issues** (operaciones síncronas que podrían ser async)

---

## 🔴 Problemas CRÍTICOS (Severidad ALTA)

### 1. **ImagePreprocessor: God Class Anti-pattern**

**Archivo:** `src/infrastructure/image/preprocessor.py` (338 LOC)
**Severidad:** 🔴 CRÍTICA

**Problema:**
```python
class ImagePreprocessor:
    # 11 RESPONSABILIDADES DIFERENTES:
    # 1. Upscaling
    # 2. Normalización de iluminación
    # 3. Conversión a escala de grises
    # 4. Reducción de ruido
    # 5. Aumento de contraste
    # 6. Realce de bordes
    # 7. Sharpening
    # 8. Binarización
    # 9. Operaciones morfológicas
    # 10. Corrección de inclinación
    # 11. Generación de reportes y estadísticas
```

**Consecuencias:**
- ❌ Imposible testear componentes individuales
- ❌ Acoplamiento alto con ImageEnhancer y QualityMetrics
- ❌ Difícil agregar nuevos pasos de procesamiento
- ❌ Performance: no puede paralelizar pasos independientes
- ❌ Pipeline hardcodeado (sin composición dinámica)

**Solución:**
```python
# Pipeline modular con Strategy Pattern:

class PreprocessingStep(ABC):
    """Interface para pasos de preprocesamiento."""
    @abstractmethod
    def process(self, image: np.ndarray) -> np.ndarray:
        pass

class UpscalingStep(PreprocessingStep):
    def __init__(self, factor: int = 4):
        self.factor = factor

    def process(self, image: np.ndarray) -> np.ndarray:
        return cv2.resize(image, ..., interpolation=cv2.INTER_CUBIC)

class DenoiseStep(PreprocessingStep):
    def __init__(self, h: int = 7, template_size: int = 7):
        self.h = h
        self.template_size = template_size

    def process(self, image: np.ndarray) -> np.ndarray:
        return cv2.fastNlMeansDenoising(image, None, h=self.h, ...)

# Pipeline composable:
class ImagePipeline:
    def __init__(self, steps: List[PreprocessingStep], logger: LoggerPort):
        self.steps = steps
        self.logger = logger

    def process(self, image: np.ndarray) -> np.ndarray:
        for step in self.steps:
            image = step.process(image)
            self.logger.debug(f"Applied {step.__class__.__name__}")
        return image

# Uso:
pipeline = ImagePipeline(steps=[
    UpscalingStep(factor=4),
    DenoiseStep(h=7),
    ContrastStep(clip_limit=2.5),
    SharpenStep(intensity='normal')
], logger=logger)

processed = pipeline.process(image)
```

**Beneficios:**
- ✅ Single Responsibility: cada paso es independiente
- ✅ Open/Closed: agregar pasos sin modificar pipeline
- ✅ Testeable: cada paso se prueba aisladamente
- ✅ Flexible: componer pipelines dinámicamente
- ✅ Paralel izab le: pasos independientes pueden ejecutarse en paralelo

---

### 2. **ImageEnhancer: Utility Class Anti-pattern**

**Archivo:** `src/infrastructure/image/enhancer.py` (410 LOC)
**Severidad:** 🔴 CRÍTICA

**Problema:**
```python
class ImageEnhancer:
    """15+ métodos estáticos sin estado."""

    @staticmethod
    def upscale(...): pass

    @staticmethod
    def to_grayscale(...): pass

    @staticmethod
    def denoise(...): pass

    @staticmethod
    def increase_contrast(...): pass

    @staticmethod
    def sharpen(...): pass

    @staticmethod
    def unsharp_mask(...): pass

    @staticmethod
    def binarize(...): pass

    @staticmethod
    def morphological_clean(...): pass

    @staticmethod
    def enhance_edges(...): pass

    @staticmethod
    def normalize_illumination(...): pass

    @staticmethod
    def deskew(...): pass

    @staticmethod
    def pil_to_cv2(...): pass

    @staticmethod
    def cv2_to_pil(...): pass
```

**Consecuencias:**
- ❌ Violación de OOP: no usa objetos, solo funciones
- ❌ No se puede mockear para tests
- ❌ No se puede extender (no hay herencia)
- ❌ No tiene estado (no puede cachear resultados)
- ❌ Namespace pollution: todo en una sola clase

**Problema Real:**
```python
# En ImagePreprocessor:
self.enhancer = ImageEnhancer  # ❌ Asigna CLASE, no instancia
cv_image = self.enhancer.upscale(image)  # Llama método estático
```

Esto NO es inyección de dependencias real - es simplemente llamar funciones estáticas.

**Solución:**
```python
# Separar en clases especializadas con estado:

class ImageScaler:
    """Responsable de escalado."""
    def __init__(self, default_factor: int = 4, interpolation=cv2.INTER_CUBIC):
        self.default_factor = default_factor
        self.interpolation = interpolation

    def upscale(self, image: np.ndarray, factor: Optional[int] = None) -> np.ndarray:
        factor = factor or self.default_factor
        h, w = image.shape[:2]
        return cv2.resize(image, (w*factor, h*factor), interpolation=self.interpolation)

class ImageDenoiser:
    """Responsable de reducción de ruido."""
    def __init__(self, h: int = 7, template_size: int = 7, search_size: int = 21):
        self.h = h
        self.template_size = template_size
        self.search_size = search_size

    def denoise(self, image: np.ndarray) -> np.ndarray:
        return cv2.fastNlMeansDenoising(
            image, None,
            h=self.h,
            templateWindowSize=self.template_size,
            searchWindowSize=self.search_size
        )

class ContrastEnhancer:
    """Responsable de aumento de contraste."""
    def __init__(self, clip_limit: float = 2.5, tile_size: Tuple[int, int] = (8, 8)):
        self.clip_limit = clip_limit
        self.tile_size = tile_size
        self._clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)

    def enhance(self, image: np.ndarray) -> np.ndarray:
        return self._clahe.apply(image)

# Inyección de dependencias REAL:
class ImagePipeline:
    def __init__(
        self,
        scaler: ImageScaler,
        denoiser: ImageDenoiser,
        contrast_enhancer: ContrastEnhancer,
        logger: LoggerPort
    ):
        self.scaler = scaler
        self.denoiser = denoiser
        self.contrast_enhancer = contrast_enhancer
        self.logger = logger
```

**Beneficios:**
- ✅ Inyección de dependencias REAL
- ✅ Testeable: mock cada componente
- ✅ Configurable: parámetros en __init__
- ✅ Cacheable: puede guardar estado (ej: CLAHE instance)
- ✅ Extensible: herencia y composición

---

### 3. **print() en Lugar de Logger**

**Archivos:** Múltiples (22 archivos)
**Severidad:** 🔴 CRÍTICA

**Problema:**
```python
# preprocessor.py:
print("\n" + "="*70)
print("PIPELINE DE PREPROCESAMIENTO - BALANCEADO v3.1")
print("="*70)
print(f"✓ Imagen original: {cv_image.shape[1]}x{cv_image.shape[0]} px")

# google_vision_adapter.py:
print("DEBUG Google Vision: Inicializando cliente...")
print("✓ Google Cloud Vision inicializado correctamente")
print(f"ERROR Google Vision API: {response.error.message}")

# digit_level_ensemble_ocr.py:
print("\n" + "="*70)
print("DIGIT-LEVEL ENSEMBLE OCR INICIALIZADO")
print("="*70)

# ocr_factory.py:
print("\n⚠️ No se pudo inicializar '{provider}', intentando fallback...")
print(f"→ Intentando {fallback_provider}...")
```

**Consecuencias:**
- ❌ No se puede controlar logging level (debug, info, error)
- ❌ No se puede redirigir a archivo o syslog
- ❌ No se puede filtrar por módulo
- ❌ No hay contexto estructurado (timestamps, thread IDs)
- ❌ Logs mezclados en stdout (horrible para producción)
- ❌ Imposible de testear (output va a stdout)
- ❌ Imposible de desactivar (siempre imprime)

**Solución:**
```python
# ANTES:
print("DEBUG Google Vision: Inicializando cliente...")
print(f"✓ Google Cloud Vision inicializado correctamente")
print(f"ERROR Google Vision API: {response.error.message}")

# DESPUÉS:
class GoogleVisionAdapter(OCRPort):
    def __init__(self, config: ConfigPort, logger: LoggerPort):
        self.config = config
        self.logger = logger.bind(component="GoogleVisionAdapter")

    def _initialize_ocr(self):
        self.logger.debug("Initializing Google Vision client")

        try:
            self.client = vision.ImageAnnotatorClient()
            self.logger.info(
                "Google Vision initialized successfully",
                auth_method="ADC",
                optimized_for="handwriting"
            )
        except Exception as e:
            self.logger.error(
                "Failed to initialize Google Vision",
                error=str(e),
                solutions=[
                    "gcloud auth application-default login",
                    "Set GOOGLE_APPLICATION_CREDENTIALS",
                    "Enable Cloud Vision API"
                ]
            )
            raise
```

**Beneficios:**
- ✅ Control granular de logging level
- ✅ Logs estructurados (JSON)
- ✅ Contexto automático (timestamps, component, thread)
- ✅ Testeable (mock logger)
- ✅ Configurable (log file, syslog, etc.)
- ✅ Filtrable por módulo

---

### 4. **Hardcoded Configuration en Clases**

**Archivo:** Múltiples
**Severidad:** 🔴 CRÍTICA

**Problema:**
```python
# pyautogui_automation.py:
class PyAutoGUIAutomation(AutomationPort):
    def __init__(self):
        pyautogui.FAILSAFE = True  # ❌ Hardcoded
        pyautogui.PAUSE = 0.05     # ❌ Hardcoded

        self.key_mapping = {        # ❌ Hardcoded
            'enter': 'enter',
            'tab': 'tab',
            # ...
        }

# pyautogui_capture.py:
class PyAutoGUICapture(ScreenCapturePort):
    def __init__(self):
        pyautogui.FAILSAFE = True  # ❌ Hardcoded (duplicado!)
        pyautogui.PAUSE = 0.1      # ❌ Hardcoded (diferente valor!)

# preprocessor.py:
def _get_default_config(self) -> Dict:
    return {
        'upscale_factor': 4,       # ❌ Hardcoded
        'denoise': {
            'h': 7,                # ❌ Hardcoded
            'template_window_size': 7,
            'search_window_size': 21
        },
        'contrast': {
            'clip_limit': 2.5,     # ❌ Hardcoded
            'tile_grid_size': (8, 8)
        }
        # ... 50+ líneas más de config hardcodeada
    }
```

**Consecuencias:**
- ❌ Imposible cambiar sin modificar código
- ❌ Valores duplicados entre clases
- ❌ Sin validación de configuración
- ❌ Difícil mantener consistencia
- ❌ Tests deben usar valores hardcodeados

**Solución:**
```python
# config/settings.yaml:
automation:
  failsafe: true
  pause: 0.05
  key_mapping:
    enter: "enter"
    tab: "tab"

capture:
  failsafe: true
  pause: 0.1

image_preprocessing:
  upscale_factor: 4
  denoise:
    h: 7
    template_window_size: 7
    search_window_size: 21
  contrast:
    clip_limit: 2.5
    tile_grid_size: [8, 8]

# Clases:
class PyAutoGUIAutomation(AutomationPort):
    def __init__(self, config: ConfigPort, logger: LoggerPort):
        self.config = config
        self.logger = logger.bind(component="PyAutoGUIAutomation")

        # Leer de config
        pyautogui.FAILSAFE = config.get('automation.failsafe', True)
        pyautogui.PAUSE = config.get('automation.pause', 0.05)

        self.key_mapping = config.get('automation.key_mapping', {
            'enter': 'enter',
            'tab': 'tab'
        })

        self.logger.info(
            "PyAutoGUI initialized",
            failsafe=pyautogui.FAILSAFE,
            pause=pyautogui.PAUSE
        )
```

**Beneficios:**
- ✅ Configuración centralizada
- ✅ Fácil de cambiar sin recompilar
- ✅ Validación de configuración
- ✅ Documentación clara de opciones
- ✅ Tests pueden override config

---

### 5. **Sin Manejo de Errores en Operaciones Críticas**

**Archivos:** Múltiples
**Severidad:** 🔴 CRÍTICA

**Problema:**
```python
# preprocessor.py:
def preprocess(self, image: Image.Image) -> Image.Image:
    # ❌ Sin try/except - puede crashear en cualquier paso
    cv_image = self.enhancer.pil_to_cv2(image)
    cv_image = self.enhancer.upscale(cv_image, factor=factor)
    cv_image = self.enhancer.denoise(cv_image, h=h)
    cv_image = self.enhancer.increase_contrast(cv_image)
    # ... 10 pasos más sin error handling

# pyautogui_automation.py:
def click(self, x: int, y: int) -> None:
    pyautogui.click(x, y)  # ❌ Puede fallar si coordenadas inválidas

def type_text(self, text: str, interval: float = 0.05) -> None:
    pyautogui.write(text, interval=interval)  # ❌ Puede fallar si window inactiva

# google_vision_adapter.py:
def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
    # ❌ Un solo try/except para todo
    try:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')  # ❌ Puede fallar
        # ...
        response = self.client.document_text_detection(...)  # ❌ Puede fallar (red, quota)
        # ... procesamiento complejo sin error handling individual
    except Exception as e:
        print(f"ERROR: {e}")  # ❌ Solo print, no reraise
        return []  # ❌ Retorna lista vacía sin indicar error
```

**Consecuencias:**
- ❌ Crasheos silenciosos
- ❌ Pérdida de datos sin aviso
- ❌ Difícil debugging (sin contexto de error)
- ❌ No se pueden recuperar de errores parciales
- ❌ Usuario no sabe qué salió mal

**Solución:**
```python
class ImagePipeline:
    def __init__(self, steps: List[PreprocessingStep], logger: LoggerPort):
        self.steps = steps
        self.logger = logger

    def process(self, image: np.ndarray) -> np.ndarray:
        for i, step in enumerate(self.steps):
            try:
                image = step.process(image)
                self.logger.debug(
                    "Step completed successfully",
                    step=step.__class__.__name__,
                    step_index=i
                )
            except cv2.error as e:
                self.logger.error(
                    "OpenCV error in preprocessing step",
                    step=step.__class__.__name__,
                    step_index=i,
                    error=str(e)
                )
                raise PreprocessingError(
                    f"Failed at step {i} ({step.__class__.__name__}): {e}"
                ) from e
            except Exception as e:
                self.logger.error(
                    "Unexpected error in preprocessing step",
                    step=step.__class__.__name__,
                    step_index=i,
                    error=str(e)
                )
                raise

        return image

class GoogleVisionAdapter(OCRPort):
    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        try:
            img_bytes = self._convert_to_bytes(image)
        except Exception as e:
            self.logger.error("Failed to convert image to bytes", error=str(e))
            raise OCRError("Image conversion failed") from e

        try:
            response = self._call_api(img_bytes)
        except GoogleAPIError as e:
            if "QUOTA_EXCEEDED" in str(e):
                self.logger.error("Google Vision quota exceeded")
                raise QuotaExceededError("Google Vision API quota exceeded") from e
            elif "PERMISSION_DENIED" in str(e):
                self.logger.error("Google Vision permission denied")
                raise PermissionError("Check Google Cloud credentials") from e
            else:
                self.logger.error("Google Vision API error", error=str(e))
                raise OCRError(f"API call failed: {e}") from e

        try:
            records = self._parse_response(response)
        except Exception as e:
            self.logger.error("Failed to parse API response", error=str(e))
            raise OCRError("Response parsing failed") from e

        return records
```

**Beneficios:**
- ✅ Errores específicos con contexto
- ✅ Recovery parcial posible
- ✅ Debugging más fácil
- ✅ Usuario informado del problema
- ✅ Logging estructurado de errores

---

### 6. **ImagePreprocessor: Inicialización Incorrecta de Dependencies**

**Archivo:** `src/infrastructure/image/preprocessor.py:42-43`
**Severidad:** 🔴 CRÍTICA

**Problema:**
```python
class ImagePreprocessor:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.enhancer = ImageEnhancer  # ❌ CRÍTICO: Asigna CLASE, no instancia
        self.metrics = QualityMetrics  # ❌ CRÍTICO: Asigna CLASE, no instancia
        self.stats = {}
```

**¿Por qué es CRÍTICO?**

1. **NO es dependency injection** - solo referencias a clases
2. **Coupling directo** - no se pueden mockear en tests
3. **Sin configuración** - ImageEnhancer y QualityMetrics no reciben config
4. **Sin logger** - no pueden loguear sus operaciones

**Impacto Real:**
```python
# Uso actual:
cv_image = self.enhancer.pil_to_cv2(image)  # Llama método estático
cv_image = self.enhancer.upscale(cv_image)  # Llama método estático

# NO se puede hacer:
mock_enhancer = Mock()
preprocessor = ImagePreprocessor(enhancer=mock_enhancer)  # ❌ No acepta enhancer
```

**Solución:**
```python
class ImagePreprocessor:
    def __init__(
        self,
        pipeline: ImagePipeline,
        metrics: QualityMetrics,
        config: ConfigPort,
        logger: LoggerPort
    ):
        self.pipeline = pipeline
        self.metrics = metrics
        self.config = config
        self.logger = logger.bind(component="ImagePreprocessor")
        self.stats = {}

    def preprocess(self, image: Image.Image) -> Image.Image:
        self.logger.info("Starting preprocessing", image_size=image.size)

        # Convertir PIL a OpenCV
        cv_image = ImageConverter.pil_to_cv2(image)

        # Calcular métricas originales
        original_stats = self.metrics.get_image_stats(cv_image)

        # Aplicar pipeline
        try:
            processed = self.pipeline.process(cv_image)
        except PreprocessingError as e:
            self.logger.error("Preprocessing failed", error=str(e))
            raise

        # Calcular métricas procesadas
        processed_stats = self.metrics.get_image_stats(processed)

        # Guardar estadísticas
        self.stats = {
            'original': original_stats,
            'processed': processed_stats,
            'improvement': self.metrics.compare(original_stats, processed_stats)
        }

        # Convertir de vuelta a PIL
        result = ImageConverter.cv2_to_pil(processed)

        self.logger.info(
            "Preprocessing completed",
            original_size=image.size,
            processed_size=result.size,
            improvement=self.stats['improvement']
        )

        return result
```

---

### 7. **Código Duplicado Entre Adaptadores OCR**

**Archivos:** `google_vision_adapter.py`, `azure_vision_adapter.py`, `digit_level_ensemble_ocr.py`
**Severidad:** 🟠 ALTA

**Problema:**
```python
# Código IDÉNTICO o muy similar en 3+ archivos:

# google_vision_adapter.py:92-129:
def preprocess_image(self, image: Image.Image) -> Image.Image:
    print(f"\nDEBUG Google Vision: Imagen original {image.width}x{image.height}")

    if not self.config.get('image_preprocessing.enabled', True):
        print("DEBUG Google Vision: Preprocesamiento deshabilitado")
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return image

    processed_image = self.preprocessor.preprocess(image)

    if processed_image.mode != 'RGB':
        processed_image = processed_image.convert('RGB')

    print(f"DEBUG Google Vision: Imagen procesada {processed_image.width}x{processed_image.height}")

    return processed_image

# azure_vision_adapter.py:XX-XX:
def preprocess_image(self, image: Image.Image) -> Image.Image:
    print(f"\nDEBUG Azure Vision: Imagen original {image.width}x{image.height}")  # Casi idéntico

    if not self.config.get('image_preprocessing.enabled', True):
        print("DEBUG Azure Vision: Preprocesamiento deshabilitado")  # Casi idéntico
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return image

    processed_image = self.preprocessor.preprocess(image)  # Idéntico

    if processed_image.mode != 'RGB':
        processed_image = processed_image.convert('RGB')

    print(f"DEBUG Azure Vision: Imagen procesada {processed_image.width}x{processed_image.height}")

    return processed_image
```

**Consecuencias:**
- ❌ Cambios deben hacerse en 3+ lugares
- ❌ Alto riesgo de inconsistencias
- ❌ Más líneas de código que mantener
- ❌ Bug fixes deben replicarse

**Solución:**
```python
# Base class con lógica común:
class BaseOCRAdapter(OCRPort, ABC):
    """Base class para adaptadores OCR con preprocesamiento."""

    def __init__(
        self,
        config: ConfigPort,
        preprocessor: ImagePreprocessor,
        logger: LoggerPort
    ):
        self.config = config
        self.preprocessor = preprocessor
        self.logger = logger.bind(component=self.__class__.__name__)

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocesa imagen según configuración."""
        self.logger.debug("Preprocessing image", original_size=image.size)

        # Check if preprocessing is enabled
        if not self.config.get('image_preprocessing.enabled', True):
            self.logger.debug("Preprocessing disabled, using original image")
            return self._ensure_rgb(image)

        # Apply preprocessing
        processed = self.preprocessor.preprocess(image)
        processed = self._ensure_rgb(processed)

        self.logger.debug("Preprocessing completed", processed_size=processed.size)

        return processed

    def _ensure_rgb(self, image: Image.Image) -> Image.Image:
        """Ensures image is in RGB mode."""
        if image.mode != 'RGB':
            return image.convert('RGB')
        return image

    @abstractmethod
    def _call_api(self, image: Image.Image) -> Any:
        """Calls the specific OCR API. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def _parse_response(self, response: Any) -> List[CedulaRecord]:
        """Parses API response. Must be implemented by subclasses."""
        pass

# Implementaciones específicas:
class GoogleVisionAdapter(BaseOCRAdapter):
    def __init__(self, config: ConfigPort, preprocessor: ImagePreprocessor, logger: LoggerPort):
        super().__init__(config, preprocessor, logger)
        self.client = vision.ImageAnnotatorClient()

    def _call_api(self, image: Image.Image) -> vision.AnnotateImageResponse:
        img_bytes = self._image_to_bytes(image)
        vision_image = vision.Image(content=img_bytes)
        return self.client.document_text_detection(image=vision_image)

    def _parse_response(self, response) -> List[CedulaRecord]:
        # Google-specific parsing logic
        pass

class AzureVisionAdapter(BaseOCRAdapter):
    def __init__(self, config: ConfigPort, preprocessor: ImagePreprocessor, logger: LoggerPort):
        super().__init__(config, preprocessor, logger)
        self.client = ImageAnalysisClient(...)

    def _call_api(self, image: Image.Image) -> ImageAnalysisResult:
        img_bytes = self._image_to_bytes(image)
        return self.client.analyze(image_data=img_bytes)

    def _parse_response(self, response) -> List[CedulaRecord]:
        # Azure-specific parsing logic
        pass
```

**Beneficios:**
- ✅ DRY: lógica común en un solo lugar
- ✅ Consistencia garantizada
- ✅ Fácil mantener
- ✅ Template Method pattern aplicado

---

### 8. **RowBasedExtraction: Coordenadas Hardcodeadas**

**Archivo:** `src/infrastructure/ocr/row_based_extraction.py:23-82`
**Severidad:** 🟠 ALTA

**Problema:**
```python
def detect_rows(image: Image.Image, min_height: int = 25) -> List[Tuple[int, int]]:
    """
    Detecta las filas del formulario usando COORDENADAS FIJAS PROPORCIONALES.

    ESTRATEGIA FINAL - MAPEADO MANUAL PROPORCIONAL:
    Basado en análisis visual de image.png (1010x544):  # ❌ Hardcoded para UN tamaño
    """
    width, height = image.size

    header_end = 15  # ❌ Hardcoded
    total_data_height = height - header_end
    num_rows = 15  # ❌ Hardcoded
    row_height = total_data_height / num_rows
```

**Consecuencias:**
- ❌ Solo funciona para formularios de UN tamaño específico
- ❌ Falla con formularios escaneados a diferente resolución
- ❌ No detecta realmente las filas (asume distribución uniforme)
- ❌ Sin validación de que las coordenadas contengan datos

**Solución:**
```python
class AdaptiveRowDetector:
    """Detecta filas dinámicamente basado en contenido."""

    def __init__(self, config: ConfigPort, logger: LoggerPort):
        self.config = config
        self.logger = logger
        self.min_row_height = config.get('row_detection.min_height', 25)
        self.header_ratio = config.get('row_detection.header_ratio', 0.03)

    def detect_rows(self, image: Image.Image) -> List[RowRegion]:
        """Detecta filas basándose en proyección horizontal."""
        # Convertir a OpenCV
        cv_image = np.array(image.convert('L'))

        # Calcular proyección horizontal (suma de píxeles por fila)
        h_projection = np.sum(cv_image < 128, axis=1)  # Contar píxeles oscuros

        # Detectar header (primeras filas con poco texto)
        header_end = self._detect_header_end(h_projection)

        # Detectar separadores de filas (valles en proyección)
        row_separators = self._find_row_separators(h_projection[header_end:])

        # Crear regiones
        rows = []
        for i in range(len(row_separators) - 1):
            y_start = row_separators[i] + header_end
            y_end = row_separators[i + 1] + header_end

            if y_end - y_start >= self.min_row_height:
                rows.append(RowRegion(
                    y_start=y_start,
                    y_end=y_end,
                    confidence=self._calculate_confidence(h_projection[y_start:y_end])
                ))

        self.logger.info(f"Detected {len(rows)} rows", header_end=header_end)

        return rows

    def _detect_header_end(self, projection: np.ndarray) -> int:
        """Detecta dónde termina el header basándose en densidad de texto."""
        # Header típicamente tiene poco texto
        threshold = np.mean(projection) * 0.5

        for i, value in enumerate(projection):
            if value > threshold:
                # Primera fila con suficiente texto
                return max(0, i - 5)  # 5px de padding

        # Default si no se detecta
        return int(len(projection) * self.header_ratio)

    def _find_row_separators(self, projection: np.ndarray) -> List[int]:
        """Encuentra posiciones de separadores entre filas."""
        # Suavizar proyección
        from scipy.ndimage import gaussian_filter1d
        smoothed = gaussian_filter1d(projection, sigma=2)

        # Encontrar mínimos locales (valles)
        from scipy.signal import find_peaks
        valleys, _ = find_peaks(-smoothed, distance=self.min_row_height)

        return [0] + valleys.tolist() + [len(projection)]
```

**Beneficios:**
- ✅ Funciona con cualquier tamaño de formulario
- ✅ Detecta realmente las filas (no asume)
- ✅ Robusto a variaciones de escaneo
- ✅ Proporciona confianza por fila

---

## 🟠 Problemas de ALTA Severidad

### 9. **Sin Abstracción para Conversión PIL ↔ OpenCV**

**Archivos:** Multiple (código duplicado en 5+ lugares)
**Severidad:** 🟠 ALTA

**Problema:**
```python
# Código DUPLICADO en multiple lugares:

# enhancer.py:368-388:
@staticmethod
def pil_to_cv2(image: Image.Image) -> np.ndarray:
    if image.mode != 'RGB':
        image = image.convert('RGB')
    img_array = np.array(image)
    bgr_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    return bgr_image

@staticmethod
def cv2_to_pil(image: np.ndarray) -> Image.Image:
    if len(image.shape) == 2:
        return Image.fromarray(image)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_image)
    return pil_image

# preprocessor.py usa ImageEnhancer.pil_to_cv2()
# google_vision_adapter.py convierte manualmente
# azure_vision_adapter.py convierte manualmente
# digit_level_ensemble_ocr.py puede necesitar conversiones
```

**Solución:**
```python
class ImageConverter:
    """Utility class para conversiones entre formatos de imagen."""

    @staticmethod
    def pil_to_cv2(image: Image.Image) -> np.ndarray:
        """Converts PIL Image to OpenCV format (BGR)."""
        if image.mode != 'RGB':
            image = image.convert('RGB')

        img_array = np.array(image)
        bgr_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        return bgr_image

    @staticmethod
    def cv2_to_pil(image: np.ndarray) -> Image.Image:
        """Converts OpenCV image (BGR or grayscale) to PIL Image."""
        if len(image.shape) == 2:
            # Grayscale
            return Image.fromarray(image)

        # BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_image)

    @staticmethod
    def pil_to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
        """Converts PIL Image to bytes."""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()

    @staticmethod
    def bytes_to_pil(data: bytes) -> Image.Image:
        """Converts bytes to PIL Image."""
        return Image.open(io.BytesIO(data))

    @staticmethod
    def cv2_to_bytes(image: np.ndarray, format: str = 'PNG') -> bytes:
        """Converts OpenCV image to bytes."""
        pil_image = ImageConverter.cv2_to_pil(image)
        return ImageConverter.pil_to_bytes(pil_image, format)

# Usar en todos los lugares:
from ...infrastructure.image import ImageConverter

# En adapters:
cv_image = ImageConverter.pil_to_cv2(pil_image)
img_bytes = ImageConverter.pil_to_bytes(pil_image)
```

---

### 10. **QualityMetrics: Clase Estática Sin Dependencies**

**Archivo:** `src/infrastructure/image/quality_metrics.py`
**Severidad:** 🟠 ALTA

**Problema:**
Similar a ImageEnhancer - solo métodos estáticos sin estado.

**Solución:**
```python
class QualityMetrics:
    """Calcula métricas de calidad de imagen."""

    def __init__(self, logger: Optional[LoggerPort] = None):
        self.logger = logger or NullLogger()
        self._metrics_cache: Dict[str, ImageStats] = {}

    def get_image_stats(self, image: np.ndarray, cache_key: Optional[str] = None) -> ImageStats:
        """Calcula estadísticas de calidad de una imagen."""
        # Check cache
        if cache_key and cache_key in self._metrics_cache:
            return self._metrics_cache[cache_key]

        stats = ImageStats(
            mean_intensity=float(np.mean(image)),
            std_intensity=float(np.std(image)),
            min_intensity=int(np.min(image)),
            max_intensity=int(np.max(image)),
            sharpness=self._calculate_sharpness(image),
            contrast=self._calculate_contrast(image)
        )

        # Cache result
        if cache_key:
            self._metrics_cache[cache_key] = stats

        self.logger.debug("Image stats calculated", stats=stats.to_dict())

        return stats

    def compare_images(
        self,
        original: np.ndarray,
        processed: np.ndarray
    ) -> ComparisonResult:
        """Compara métricas entre imagen original y procesada."""
        original_stats = self.get_image_stats(original, cache_key="original")
        processed_stats = self.get_image_stats(processed, cache_key="processed")

        improvement = {
            'sharpness': self._calculate_improvement(
                original_stats.sharpness,
                processed_stats.sharpness
            ),
            'contrast': self._calculate_improvement(
                original_stats.contrast,
                processed_stats.contrast
            )
        }

        return ComparisonResult(
            original=original_stats,
            processed=processed_stats,
            improvement=improvement
        )
```

---

### 11-20. **Otros Problemas de Alta Severidad**

Por brevedad, listo los restantes problemas:

11. **Sin retry logic en llamadas a APIs** (Google Vision, Azure Vision)
12. **Sin timeout en operaciones de red**
13. **Sin validación de inputs** (imágenes vacías, tamaños inválidos)
14. **Sin rate limiting** para APIs externas
15. **Operaciones síncronas** que podrían ser async
16. **Sin caching de resultados** OCR repetidos
17. **Credentials hardcodeadas** o en variables de entorno sin validación
18. **Sin metrics/telemetry** para monitorear performance
19. **Pipeline no es transaccional** (falla parcial deja estado inconsistente)
20. **Sin circuit breaker** para llamadas a APIs

---

## 🟡 Problemas de MEDIA Severidad

21. **print() statements mezclados con lógica de negocio**
22. **Comentarios en español e inglés mezclados**
23. **Magic numbers sin nombres** (ej: `header_end = 15`)
24. **Nombres de variables poco claros** (ej: `h`, `img_byte_arr`)
25. **Métodos muy largos** (>100 LOC)
26. **Sin docstrings en algunos métodos**
27. **Falta de type hints completos**
28. **Sin validación de que config keys existan**
29. **Acoplamiento temporal** entre pasos de pipeline
30. **Tests faltantes** para componentes críticos

---

## 🔵 Problemas de BAJA Severidad

31. **Convenciones de naming inconsistentes** (snake_case vs camelCase en algunos lugares)
32. **Imports desordenados** (stdlib, third-party, local mezclados)
33. **Líneas muy largas** (>120 caracteres)
34. **Falta de blank lines** entre secciones lógicas

---

## 📊 Resumen de Refactorings Recomendados

### 🔴 Prioridad CRÍTICA (Hacer YA)

1. **Refactorizar ImagePreprocessor** → Pipeline modular
2. **Eliminar ImageEnhancer estático** → Clases con estado
3. **Reemplazar print()** → Logger estructurado
4. **Externalizar configuración** → ConfigPort
5. **Agregar error handling** → Try/except con contexto
6. **Crear BaseOCRAdapter** → DRY entre adaptadores
7. **Inyectar dependencies correctamente** → No asignar clases

### 🟠 Prioridad ALTA (Próxima iteración)

8. **Crear ImageConverter utility**
9. **Refactorizar QualityMetrics** → Instancia con logger
10. **Adaptive row detection** → Reemplazar coordenadas hardcodeadas
11. **Agregar retry logic** → APIs externas
12. **Agregar timeout** → Operaciones de red
13. **Validar inputs** → Imágenes y configuración

### 🟡 Prioridad MEDIA (Mejoras continuas)

14. **Agregar rate limiting**
15. **Convertir a async** donde sea posible
16. **Implementar caching** de resultados
17. **Circuit breaker** para APIs
18. **Metrics/telemetry**
19. **Transactional pipeline**
20. **Mejorar naming** y documentación

---

## 🎯 Plan de Acción

### Fase 1: Refactoring Crítico (Semana 1-2)

1. ✅ **Crear ImagePipeline modular**
   - PreprocessingStep interface
   - Implementar 10+ steps
   - Pipeline composable
   - Inyección de dependencies

2. ✅ **Refactorizar ImageEnhancer**
   - Separar en clases especializadas
   - ImageScaler, ImageDenoiser, ContrastEnhancer, etc.
   - Estado y configuración en __init__

3. ✅ **Logging completo**
   - Reemplazar TODOS los print()
   - Logger inyectado en constructores
   - Logs estructurados

4. ✅ **BaseOCRAdapter**
   - Extraer lógica común
   - Template Method pattern
   - DRY entre Google y Azure

### Fase 2: Error Handling y Validación (Semana 3)

5. ✅ **Error handling robusto**
   - Try/except con contexto
   - Custom exceptions
   - Recovery parcial

6. ✅ **Input validation**
   - Validar imágenes
   - Validar configuración
   - Schemas con pydantic

7. ✅ **Retry logic y timeout**
   - Decorators para retry
   - Timeout en APIs
   - Exponential backoff

### Fase 3: Performance y Observability (Semana 4)

8. ✅ **Caching**
   - Cache de OCR results
   - Cache de preprocessing
   - TTL configurables

9. ✅ **Metrics**
   - Prometheus metrics
   - Latency tracking
   - Error rates

10. ✅ **Tests unitarios**
    - Cobertura >80%
    - Mocks de APIs
    - Property-based testing

---

## 🎓 Conclusión

La capa de infraestructura tiene **34 problemas** identificados, de los cuales **8 son CRÍTICOS** y requieren atención inmediata.

Los problemas principales son:
- **God classes** (ImagePreprocessor)
- **Utility classes estáticas** (ImageEnhancer, QualityMetrics)
- **print() en producción**
- **Configuración hardcodeada**
- **Sin error handling**
- **Código duplicado**

La refactorización propuesta seguirá los mismos principios SOLID aplicados en la capa de aplicación, resultando en:
- ✅ **Código más mantenible** (clases pequeñas, Single Responsibility)
- ✅ **100% testeable** (dependency injection real)
- ✅ **Extensible** (Open/Closed, fácil agregar nuevos pasos)
- ✅ **Robusto** (error handling completo, validación)
- ✅ **Profesional** (logging estructurado, metrics, observability)

**Prioridad:** Comenzar con los 7 issues críticos antes de continuar con features nuevas.

---

**Próximo paso:** ¿Quieres que empiece con la refactorización del ImagePreprocessor o prefieres otro componente crítico?
