# 🚀 Integración Rápida - Sistema OCR Dual

**Tiempo estimado:** 10-15 minutos
**Dificultad:** Media

---

## 📋 PASOS RÁPIDOS PARA INTEGRAR

### **Opción A: Integración Completa (Recomendada)**

Sigue las instrucciones en `CONTEXTO_CONTINUACION.md` sección #1.

### **Opción B: Integración Rápida (Más Simple)**

Agrega un **botón nuevo** en la UI que active el sistema OCR dual sin tocar el código existente.

---

## ✅ OPCIÓN B - PASOS RÁPIDOS

### **1. Agregar botón en main_window.py**

Busca la sección `_create_control_section()` y agrega:

```python
def _create_control_section(self) -> QGroupBox:
    """Crea la sección de control de procesamiento."""
    group = QGroupBox("2. Control de Procesamiento")
    layout = QVBoxLayout()

    # ... código existente de botones ...

    # NUEVO: Botón OCR Dual
    self.btn_ocr_dual = QPushButton("🚀 Procesamiento OCR Dual (NUEVO)")
    self.btn_ocr_dual.clicked.connect(self._start_ocr_dual_processing)
    self.btn_ocr_dual.setEnabled(False)
    self.btn_ocr_dual.setStyleSheet(
        "QPushButton { background-color: #9c27b0; color: white; font-weight: bold; padding: 10px; }"
        "QPushButton:hover { background-color: #7b1fa2; }"
        "QPushButton:disabled { background-color: #ccc; }"
    )

    btn_layout.addWidget(self.btn_ocr_dual)  # Agregar después de otros botones

    # ... resto del código ...
```

### **2. Agregar señal en main_window.py**

Arriba de la clase, agrega:

```python
class MainWindow(QMainWindow):
    # ... señales existentes ...

    ocr_dual_processing_requested = pyqtSignal()  # NUEVA
```

### **3. Conectar señal:**

```python
def _start_ocr_dual_processing(self):
    """Inicia procesamiento OCR dual."""
    self.ocr_dual_processing_requested.emit()
```

### **4. Agregar método en main_controller.py**

Al final de `_connect_signals()`:

```python
def _connect_signals(self):
    # ... código existente ...

    # NUEVO: OCR Dual
    self.window.ocr_dual_processing_requested.connect(self.handle_ocr_dual_processing)
```

### **5. Implementar handler en main_controller.py**

Al final del archivo, después de todos los métodos:

```python
def handle_ocr_dual_processing(self):
    """Maneja procesamiento OCR dual automático."""
    if not self.current_image:
        self.window.add_log("Primero capture una imagen", "WARNING")
        return

    try:
        # Cargar configuración
        from ...shared.config import load_config
        config = load_config()

        # Crear componentes si no existen
        if not hasattr(self, 'automation_controller'):
            from ...application.controllers import AutomationController
            from ...infrastructure.ocr.google_vision_adapter import GoogleVisionAdapter
            from ...infrastructure.ocr.tesseract_web_scraper import TesseractWebScraper
            from ..ui import ProgressPanel
            from .ocr_dual_controller import OCRDualController

            self.logger.info("Inicializando componentes OCR dual")
            self.window.add_log("🔧 Inicializando sistema OCR dual...", "INFO")

            # Crear adaptadores
            self.google_vision_dual = GoogleVisionAdapter(
                config=config.get('ocr', {}).get('google_vision')
            )
            self.tesseract = TesseractWebScraper(
                config=config.get('ocr', {}).get('tesseract')
            )

            # Crear AutomationController
            self.automation_controller = AutomationController(
                config=config,
                on_alert=None,
                on_progress=None
            )

            # Crear ProgressPanel
            self.progress_panel = ProgressPanel()

            # Agregar ProgressPanel a la ventana si no existe
            if not hasattr(self.window, 'progress_panel'):
                # Buscar layout principal
                central_widget = self.window.centralWidget()
                main_layout = central_widget.layout()
                # Insertar antes de logs
                main_layout.insertWidget(main_layout.count() - 1, self.progress_panel)
                self.window.progress_panel = self.progress_panel

            # Crear OCRDualController
            self.ocr_dual_controller = OCRDualController(
                automation_controller=self.automation_controller,
                progress_panel=self.progress_panel,
                logger=self.logger
            )

            self.window.add_log("✓ Sistema OCR dual inicializado", "INFO")

        # Iniciar procesamiento
        self.logger.info("Iniciando procesamiento OCR dual")
        self.window.add_log("🚀 Iniciando procesamiento OCR dual automático...", "INFO")
        self.window.add_log("⚠️ Presiona ESC para pausar en cualquier momento", "INFO")

        # Deshabilitar botón mientras procesa
        self.window.btn_ocr_dual.setEnabled(False)

        # Iniciar procesamiento
        self.ocr_dual_controller.start_processing(self.current_image)

        # Rehabilitar botón
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self.window.btn_ocr_dual.setEnabled(True))

    except Exception as e:
        self.logger.error("Error en procesamiento OCR dual", error=str(e))
        self.window.add_log(f"❌ Error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
```

### **6. Habilitar botón después de captura**

En `_perform_capture()`, después de `self.window.set_preview_image(...)`:

```python
# Habilitar botón OCR dual
self.window.btn_ocr_dual.setEnabled(True)
```

---

## 🎯 RESULTADO

Ahora tendrás:

1. ✅ Botón morado "🚀 Procesamiento OCR Dual (NUEVO)"
2. ✅ Se habilita después de capturar imagen
3. ✅ Al hacer click:
   - Inicializa componentes OCR dual
   - Muestra ProgressPanel
   - Inicia procesamiento automático
4. ✅ Usuario puede pausar con ESC
5. ✅ Al finalizar, muestra estadísticas

---

## ⚙️ ANTES DE USAR

**CRÍTICO:** Configura las regiones de Tesseract:

```bash
python test_tesseract_selector.py
```

1. Captura tu formulario web
2. Selecciona cada campo visualmente
3. Copia el YAML generado a `config/settings.yaml`

**Sin esto, Tesseract no podrá leer los campos correctamente.**

---

## 🧪 PROBAR

1. Ejecutar aplicación:
```bash
./run.bat
```

2. Capturar formulario manuscrito (F4)

3. Click en "🚀 Procesamiento OCR Dual (NUEVO)"

4. Observar:
   - Panel de progreso aparece
   - Sistema procesa renglones automáticamente
   - Muestra diálogos de validación cuando sea necesario
   - Presionar ESC para pausar
   - Presionar F9 para reanudar

---

## 🐛 TROUBLESHOOTING

### **Error: No module named 'src.shared.config'**

Cambiar:
```python
from ...shared.config import load_config
config = load_config()
```

Por:
```python
import yaml
with open('config/settings.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
```

### **Error: Panel no aparece**

Verificar que `self.progress_panel` se agregó correctamente al layout.

### **Tesseract no lee nada**

Verificar que configuraste las regiones en `settings.yaml`.

---

## 📝 RESUMEN

**Ventajas de Opción B:**
- ✅ No toca código existente
- ✅ Fácil de implementar
- ✅ Fácil de revertir si falla
- ✅ Usuario puede elegir modo antiguo o nuevo

**Desventajas:**
- ❌ Botón extra en la UI
- ❌ No reemplaza extracción antigua

**Recomendación:** Usar Opción B primero para probar, luego migrar a Opción A cuando funcione.

---

**Tiempo total:** 10-15 minutos
**Archivos a modificar:** 2 (main_window.py, main_controller.py)
**Líneas de código:** ~100
