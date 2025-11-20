# 🧪 Guía de Pruebas y Uso - Sistema OCR Dual

**Proyecto:** Automatización de Firmas con OCR Dual
**Fecha:** 2025-11-18
**Versión:** 1.0

---

## 📋 Índice

1. [Estado Actual del Proyecto](#estado-actual-del-proyecto)
2. [Cómo Probar la Aplicación](#cómo-probar-la-aplicación)
3. [Componentes Implementados](#componentes-implementados)
4. [Cómo Sugerir Cambios](#cómo-sugerir-cambios)
5. [Áreas Que Requieren Configuración](#áreas-que-requieren-configuración)
6. [Preguntas Frecuentes](#preguntas-frecuentes)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Estado Actual del Proyecto

### ✅ **COMPLETADO - Fase 1 y Fase 2**

El sistema OCR dual está **implementado al 85%**. Los componentes core están completos:

#### Componentes Core Terminados:
- ✅ **GoogleVisionAdapter** - Extrae nombres + cédulas del formulario manuscrito
- ✅ **TesseractWebScraper** - Lee campos digitales del formulario web
- ✅ **FuzzyValidator** - Validación inteligente con 85% de umbral
- ✅ **AutomationController** - Orquestación completa del flujo
- ✅ **Sistema de pausas ESC/F9** - Control en tiempo real
- ✅ **Diálogos de validación** - Alertas visuales para el usuario
- ✅ **Panel de progreso** - Estadísticas en tiempo real
- ✅ **Herramienta de configuración** - Para calibrar regiones Tesseract

#### Pendiente:
- 🔄 **Integración final con UI principal** - Conectar todos los componentes
- 🔄 **Calibración de regiones Tesseract** - Definir coordenadas de campos web
- 🔄 **Tests de integración end-to-end** - Probar flujo completo

---

## 🚀 Cómo Probar la Aplicación

### Paso 1: Verificar Dependencias

Asegúrate de tener todas las dependencias instaladas:

```bash
pip install -r requirements.txt
```

**Dependencias críticas nuevas:**
- `python-Levenshtein>=0.21.0` - Fuzzy matching
- `unidecode>=1.3.7` - Normalización de texto
- `pynput==1.7.6` - Pausas ESC/F9 (ya estaba instalado)

### Paso 2: Probar Componentes Individuales

#### 2.1. Probar FuzzyValidator

Crea un archivo de prueba `test_fuzzy.py`:

```python
from src.application.services.fuzzy_validator import FuzzyValidator
from src.domain.entities import RowData, FormData

# Crear validador
validator = FuzzyValidator(min_similarity=0.85)

# Datos manuscritos (simulados)
row_data = RowData(
    row_index=0,
    nombres_manuscritos="MARIA DE JESUS BEJARANO JIMENEZ",
    cedula="20014807",
    is_empty=False,
    confidence={'nombres': 0.95, 'cedula': 0.98}
)

# Datos digitales (simulados)
form_data = FormData(
    primer_nombre="MARIA",
    segundo_nombre="DE JESUS",
    primer_apellido="BEJARANO",
    segundo_apellido="JIMENEZ",
    is_empty=False,
    cedula_consultada="20014807"
)

# Validar
result = validator.validate_person(row_data, form_data)

print(f"Status: {result.status}")
print(f"Action: {result.action}")
print(f"Confidence: {result.confidence:.0%}")
print(f"Details: {result.details}")
print(f"\nComparación:")
print(f"  Manuscrito: {result.manuscrito_nombres}")
print(f"  Digital: {result.digital_nombres}")
```

Ejecutar:
```bash
python test_fuzzy.py
```

**Resultado esperado:**
```
Status: ValidationStatus.OK
Action: ValidationAction.AUTO_SAVE
Confidence: 100%
Details: Primer apellido y nombre coinciden (confianza: 100%)

Comparación:
  Manuscrito: MARIA DE JESUS BEJARANO JIMENEZ
  Digital: MARIA DE JESUS BEJARANO JIMENEZ
```

#### 2.2. Probar TesseractWebScraper (Simulado)

Crea `test_tesseract.py`:

```python
from src.infrastructure.ocr.tesseract_web_scraper import TesseractWebScraper

# Crear scraper
scraper = TesseractWebScraper()

# Configurar regiones (ejemplo)
scraper.configure_field_region('primer_nombre', 100, 150, 300, 40)
scraper.configure_field_region('segundo_nombre', 100, 200, 300, 40)
scraper.configure_field_region('primer_apellido', 100, 250, 300, 40)
scraper.configure_field_region('segundo_apellido', 100, 300, 300, 40)

# Ver regiones configuradas
regions = scraper.get_configured_regions()
print("Regiones configuradas:")
for field, coords in regions.items():
    print(f"  {field}: {coords}")

# Nota: Para probar extracción real, necesitas:
# 1. Una captura del formulario web
# 2. Coordenadas calibradas correctamente
```

#### 2.3. Probar Panel de Progreso

Crea `test_progress_panel.py`:

```python
from PyQt6.QtWidgets import QApplication
from src.presentation.ui import ProgressPanel
import sys

app = QApplication(sys.argv)

# Crear panel
panel = ProgressPanel()
panel.show()

# Simular progreso
panel.update_progress(5, 15, "Procesando renglón 5/15...")
panel.update_stats(
    total=15,
    processed=5,
    auto_saved=3,
    required_validation=1,
    empty_rows=1,
    not_found=0,
    errors=0
)

panel.set_processing_state()

sys.exit(app.exec())
```

#### 2.4. Probar Diálogos de Validación

Crea `test_dialogs.py`:

```python
from PyQt6.QtWidgets import QApplication
from src.presentation.ui import ValidationAlertDialog, PersonNotFoundDialog
from src.domain.entities import ValidationResult, ValidationStatus, ValidationAction, FieldMatch
import sys

app = QApplication(sys.argv)

# Test 1: Diálogo de validación
validation_result = ValidationResult(
    status=ValidationStatus.WARNING,
    action=ValidationAction.REQUIRE_VALIDATION,
    confidence=0.75,
    matches={
        'primer_apellido': FieldMatch(
            match=False,
            similarity=0.75,
            compared="BEJARANO vs MAYORGA",
            field_name="primer_apellido"
        ),
        'primer_nombre': FieldMatch(
            match=True,
            similarity=0.92,
            compared="MARIA vs MARIA",
            field_name="primer_nombre"
        )
    },
    details="Primer apellido no coincide (75%)",
    manuscrito_nombres="MARIA BEJARANO",
    digital_nombres="MARIA MAYORGA"
)

dialog = ValidationAlertDialog(validation_result, row_number=5)
result = dialog.exec()

if result:
    print(f"Usuario seleccionó: {dialog.get_user_action()}")

# Test 2: Diálogo de persona no encontrada
dialog2 = PersonNotFoundDialog(
    cedula="12345678",
    nombres_manuscritos="JUAN PEREZ",
    row_number=8
)
result2 = dialog2.exec()

if result2:
    print(f"Usuario seleccionó: {dialog2.get_user_action()}")

sys.exit(app.exec())
```

#### 2.5. Probar Herramienta de Configuración Tesseract

Crea `test_config_tool.py`:

```python
from PyQt6.QtWidgets import QApplication
from src.presentation.ui import TesseractConfigTool
import sys

app = QApplication(sys.argv)

tool = TesseractConfigTool()
tool.exec()

# Al cerrar, puedes obtener las regiones configuradas
regions = tool.get_field_regions()
print("\nRegiones configuradas:")
for field, coords in regions.items():
    print(f"  {field}: {coords}")

sys.exit(app.exec())
```

---

## 🔍 Componentes Implementados

### 1. **Entidades de Dominio**

Ubicación: `src/domain/entities/`

#### `RowData` (row_data.py)
Representa un renglón del formulario manuscrito.

**Propiedades:**
- `row_index`: Índice del renglón (0-14)
- `nombres_manuscritos`: Nombres completos manuscritos
- `cedula`: Cédula extraída
- `is_empty`: Si el renglón está vacío
- `confidence`: Diccionario de confianza por campo

#### `FormData` (form_data.py)
Representa datos del formulario web digital.

**Propiedades:**
- `primer_nombre`, `segundo_nombre`
- `primer_apellido`, `segundo_apellido`
- `is_empty`: Si persona no existe en BD
- `nombre_completo`: Propiedad calculada

#### `ValidationResult` (validation_result.py)
Resultado de validación fuzzy.

**Propiedades:**
- `status`: OK, WARNING, ERROR
- `action`: AUTO_SAVE, REQUIRE_VALIDATION, ALERT_NOT_FOUND
- `confidence`: Confianza 0.0-1.0
- `matches`: Diccionario de FieldMatch por campo

### 2. **Servicios**

#### `FuzzyValidator` (src/application/services/fuzzy_validator.py)

**Responsabilidad:** Comparar datos manuscritos vs digitales.

**Método principal:**
```python
def validate_person(
    manuscrito_data: RowData,
    digital_data: FormData
) -> ValidationResult
```

**Lógica:**
- Si `FormData.is_empty` → `ALERT_NOT_FOUND`
- Si primer apellido >85% match Y al menos un nombre >85% → `AUTO_SAVE`
- Caso contrario → `REQUIRE_VALIDATION`

**Normalización:**
- Elimina tildes con `unidecode`
- Convierte a mayúsculas
- Elimina caracteres especiales
- Normaliza espacios

### 3. **Adaptadores OCR**

#### `GoogleVisionAdapter` (src/infrastructure/ocr/google_vision_adapter.py)

**Nuevo método:**
```python
def extract_full_form_data(
    image: Image.Image,
    expected_rows: int = 15
) -> List[RowData]
```

**Estrategia:**
1. Divide imagen en 15 regiones horizontales
2. Procesa cada región con Google Vision
3. Separa texto por posición (60% boundary)
   - Izquierda: nombres
   - Derecha: cédula
4. Detecta renglones vacíos
5. Retorna `List[RowData]`

#### `TesseractWebScraper` (src/infrastructure/ocr/tesseract_web_scraper.py)

**Métodos principales:**
```python
def capture_web_form_region(region: Tuple) -> Image.Image
def extract_field_value(field_name: str) -> str
def get_all_fields(cedula_consultada: str) -> FormData
def configure_field_region(field_name, x, y, width, height)
```

**Configuración Tesseract:**
- `--psm 6` - Bloque uniforme de texto
- `--oem 3` - Modo LSTM
- Character whitelist: Solo letras y espacios

### 4. **Controlador de Automatización**

#### `AutomationController` (src/application/controllers/automation_controller.py)

**Método principal:**
```python
def process_all_rows(form_image) -> ProcessingStats
```

**Flujo:**
1. Extrae renglones con `GoogleVisionAdapter`
2. Para cada renglón:
   - Si vacío → click "Renglón En Blanco"
   - Si tiene datos:
     - Digita cédula
     - Lee formulario web con `TesseractWebScraper`
     - Valida con `FuzzyValidator`
     - Ejecuta acción según resultado
3. Maneja pausas ESC/F9
4. Retorna estadísticas

**Estados:**
- `IDLE`, `RUNNING`, `PAUSED_ESC`, `PAUSED_ALERT`, `PAUSED_ERROR`, `COMPLETED`

**Sistema de pausas:**
- ESC: Pausa después del renglón actual
- F9: Reanuda procesamiento
- Listener de teclado con `pynput`

### 5. **Interfaz de Usuario**

#### Diálogos (`src/presentation/ui/validation_dialogs.py`)

**ValidationAlertDialog:**
- Muestra comparación manuscrito vs digital
- Campos campo por campo con porcentajes
- Botones: Guardar, Saltar, Corregir, Pausar

**PersonNotFoundDialog:**
- Alerta de persona no encontrada
- Botones: Continuar, Marcar Novedad, Pausar

#### Panel de Progreso (`src/presentation/ui/progress_panel.py`)

**ProgressPanel:**
- Barra de progreso visual
- Estadísticas en tiempo real:
  - Total / Procesados
  - Guardados automáticamente
  - Requirieron validación
  - Renglones vacíos
  - No encontrados
  - Errores

#### Herramienta de Configuración (`src/presentation/ui/tesseract_config_tool.py`)

**TesseractConfigTool:**
- Interfaz visual para configurar regiones
- Spinboxes para X, Y, Width, Height
- Vista previa de configuración
- Exporta a YAML

---

## 💡 Cómo Sugerir Cambios

### Formato de Sugerencias

Cuando quieras sugerir cambios, usa este formato:

```
📝 SUGERENCIA: [Tipo]

COMPONENTE: [Nombre del archivo o componente]
UBICACIÓN: [Ruta del archivo]

PROBLEMA ACTUAL:
[Describe qué no funciona o qué se puede mejorar]

CAMBIO PROPUESTO:
[Describe exactamente qué quieres cambiar]

RAZÓN:
[Por qué es necesario este cambio]

PRIORIDAD: [Alta / Media / Baja]
```

### Tipos de Sugerencias

#### 1. **Bug / Error**
```
📝 SUGERENCIA: BUG

COMPONENTE: FuzzyValidator
UBICACIÓN: src/application/services/fuzzy_validator.py

PROBLEMA ACTUAL:
El validador no reconoce correctamente nombres compuestos como "MARIA DE JESUS".
Compara "DE" como un nombre independiente.

CAMBIO PROPUESTO:
Filtrar conectores ("DE", "LA", "DEL") antes de comparar, o darles menor peso.

RAZÓN:
Muchos nombres colombianos tienen conectores que causan falsos negativos.

PRIORIDAD: Alta
```

#### 2. **Mejora de UX**
```
📝 SUGERENCIA: UX

COMPONENTE: ValidationAlertDialog
UBICACIÓN: src/presentation/ui/validation_dialogs.py

PROBLEMA ACTUAL:
El diálogo no muestra la cédula que se está validando.

CAMBIO PROPUESTO:
Agregar un label que muestre "Cédula: 12345678" en la parte superior del diálogo.

RAZÓN:
El usuario necesita contexto visual para saber qué registro está validando.

PRIORIDAD: Media
```

#### 3. **Configuración**
```
📝 SUGERENCIA: CONFIGURACIÓN

COMPONENTE: TesseractWebScraper
UBICACIÓN: src/infrastructure/ocr/tesseract_web_scraper.py

PROBLEMA ACTUAL:
Las coordenadas de los campos no coinciden con mi formulario web.

CAMBIO PROPUESTO:
Necesito usar estas coordenadas:
- primer_nombre: (250, 180, 350, 45)
- segundo_nombre: (250, 235, 350, 45)
- primer_apellido: (250, 290, 350, 45)
- segundo_apellido: (250, 345, 350, 45)

RAZÓN:
Mi formulario web tiene un diseño diferente.

PRIORIDAD: Alta
```

#### 4. **Nueva Funcionalidad**
```
📝 SUGERENCIA: FEATURE

COMPONENTE: AutomationController
UBICACIÓN: src/application/controllers/automation_controller.py

PROBLEMA ACTUAL:
No puedo saltar directamente a un renglón específico.

CAMBIO PROPUESTO:
Agregar un método `jump_to_row(row_index)` que permita saltar a un renglón específico.

RAZÓN:
A veces necesito reanudar desde un renglón específico después de una interrupción.

PRIORIDAD: Baja
```

#### 5. **Optimización**
```
📝 SUGERENCIA: OPTIMIZACIÓN

COMPONENTE: GoogleVisionAdapter
UBICACIÓN: src/infrastructure/ocr/google_vision_adapter.py

PROBLEMA ACTUAL:
Procesar 15 renglones toma mucho tiempo (>30 segundos).

CAMBIO PROPUESTO:
Procesar regiones en paralelo usando ThreadPoolExecutor.

RAZÓN:
Reducir tiempo de espera inicial.

PRIORIDAD: Media
```

---

## ⚙️ Áreas Que Requieren Configuración

### 1. **Regiones de Tesseract (CRÍTICO)**

**Ubicación:** `config/settings.yaml`

**Qué configurar:**
Las coordenadas de los campos del formulario web digital.

**Cómo configurar:**

**Opción A - Usando la herramienta gráfica:**
```python
python test_config_tool.py
```

1. Captura el formulario web
2. Selecciona cada campo
3. Ajusta X, Y, Width, Height
4. Exporta a YAML
5. Copia la configuración a `config/settings.yaml`

**Opción B - Manualmente:**

1. Captura screenshot del formulario web
2. Usa una herramienta como Paint/GIMP para medir píxeles
3. Anota las coordenadas de cada campo
4. Edita `config/settings.yaml`:

```yaml
ocr:
  tesseract:
    enabled: true
    field_regions:
      primer_nombre:
        x: 250      # Píxeles desde la izquierda
        y: 180      # Píxeles desde arriba
        width: 350  # Ancho del campo
        height: 45  # Alto del campo

      segundo_nombre:
        x: 250
        y: 235
        width: 350
        height: 45

      primer_apellido:
        x: 250
        y: 290
        width: 350
        height: 45

      segundo_apellido:
        x: 250
        y: 345
        width: 350
        height: 45
```

**IMPORTANTE:** Las coordenadas dependen de:
- Resolución de tu pantalla
- Zoom del navegador web
- Posición de la ventana del navegador

### 2. **Umbral de Similitud Fuzzy**

**Ubicación:** `config/settings.yaml`

**Valor actual:** 85% (0.85)

```yaml
validation:
  enabled: true
  fuzzy_matching: true
  min_similarity: 0.85  # Ajustar según necesidad
```

**Cómo ajustar:**
- **Más estricto** (90% - 0.90): Menos guardados automáticos, más validaciones manuales
- **Más permisivo** (80% - 0.80): Más guardados automáticos, riesgo de errores

**Recomendación:** Empezar con 0.85 y ajustar según resultados.

### 3. **Timeouts y Delays**

**Ubicación:** `config/settings.yaml`

```yaml
automation:
  typing_delay_ms: 50        # Delay entre teclas al digitar
  click_delay_ms: 300        # Delay después de clicks
  page_load_timeout: 5       # Segundos para esperar carga de página
```

**Ajustar si:**
- Formulario web carga muy lento → Aumentar `page_load_timeout`
- Errores de digitación → Aumentar `typing_delay_ms`
- Clicks no se registran → Aumentar `click_delay_ms`

---

## ❓ Preguntas Frecuentes

### 1. **¿Cómo ejecuto el sistema completo?**

**Respuesta:** Aún NO implementado completamente. Los componentes core están listos pero falta la integración final en la UI principal.

**Para probar componentes individuales:** Ver sección "Cómo Probar la Aplicación".

### 2. **¿Qué pasa si Google Vision no detecta bien los nombres manuscritos?**

**Soluciones:**
1. Ajustar preprocesamiento de imagen (v3.1 balanceado ya está optimizado)
2. Reducir threshold de confianza en `config/settings.yaml`:
   ```yaml
   ocr:
     google_vision:
       confidence_threshold: 0.25  # Reducir de 0.30
   ```
3. Verificar calidad de captura (iluminación, contraste)

### 3. **¿Qué pasa si Tesseract no lee bien los campos digitales?**

**Soluciones:**
1. Verificar que las regiones estén bien configuradas
2. Aumentar zoom del navegador (100% recomendado)
3. Ajustar configuración de Tesseract en `settings.yaml`:
   ```yaml
   ocr:
     tesseract:
       config: "--psm 7 --oem 3"  # Cambiar PSM a 7 (línea única)
   ```

### 4. **¿Cómo sé si la validación fuzzy está funcionando bien?**

**Indicadores:**
- **85%+ match** → Guardado automático (verde ✓)
- **70-84% match** → Requiere validación (amarillo ⚠️)
- **<70% match** → Probablemente error (rojo ✗)

**Prueba manual:**
```python
# Ver test_fuzzy.py en sección de pruebas
```

### 5. **¿Puedo pausar el proceso en cualquier momento?**

**Sí.** Presiona **ESC** en cualquier momento.

- El proceso terminará el renglón actual
- Mostrará "PAUSADO"
- Presiona **F9** para reanudar
- Las estadísticas se conservan

### 6. **¿Qué hago si encuentro un bug?**

1. Anota exactamente qué estabas haciendo
2. Copia el error completo (si hay)
3. Usa el formato de sugerencias (ver sección "Cómo Sugerir Cambios")
4. Compártelo conmigo con prioridad ALTA

---

## 🔧 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'Levenshtein'"

**Solución:**
```bash
pip install python-Levenshtein
```

### Problema: "ModuleNotFoundError: No module named 'unidecode'"

**Solución:**
```bash
pip install unidecode
```

### Problema: Tesseract no detecta texto

**Causas posibles:**
1. Tesseract no instalado en el sistema
2. Regiones mal configuradas
3. Texto demasiado pequeño

**Soluciones:**
1. Instalar Tesseract:
   - Windows: Descargar de https://github.com/UB-Mannheim/tesseract/wiki
   - Agregar a PATH
2. Verificar regiones con `test_config_tool.py`
3. Aumentar zoom del navegador

### Problema: Pausas ESC/F9 no funcionan

**Solución:**
Verificar que `pynput` está instalado:
```bash
pip install pynput==1.7.6
```

### Problema: Diálogos de validación no se muestran

**Causa:** Probablemente callbacks no están conectados.

**Verificar:**
```python
# En OCRDualController
self.automation_controller.on_alert = self._handle_alert
```

---

## 📊 Resumen de Archivos Clave

### Configuración
- `config/settings.yaml` - Configuración general
- `requirements.txt` - Dependencias

### Core Components
- `src/domain/entities/` - Entidades (RowData, FormData, ValidationResult)
- `src/application/services/fuzzy_validator.py` - Validador fuzzy
- `src/application/controllers/automation_controller.py` - Orquestador principal
- `src/infrastructure/ocr/google_vision_adapter.py` - OCR manuscrito
- `src/infrastructure/ocr/tesseract_web_scraper.py` - OCR digital

### UI Components
- `src/presentation/ui/validation_dialogs.py` - Diálogos de alerta
- `src/presentation/ui/progress_panel.py` - Panel de progreso
- `src/presentation/ui/tesseract_config_tool.py` - Herramienta de configuración
- `src/presentation/controllers/ocr_dual_controller.py` - Controlador UI

### Documentación
- `PROGRESO_OCR_DUAL.md` - Progreso del proyecto
- `GUIA_PRUEBAS_Y_USO.md` - Esta guía

---

## 🎯 Próximos Pasos Recomendados

### Para Empezar a Probar:

1. **Día 1 - Pruebas Básicas:**
   - Ejecutar `test_fuzzy.py`
   - Ejecutar `test_dialogs.py`
   - Ejecutar `test_progress_panel.py`
   - Familiarizarte con los diálogos

2. **Día 2 - Configuración:**
   - Ejecutar `test_config_tool.py`
   - Calibrar regiones de Tesseract
   - Actualizar `config/settings.yaml`
   - Probar extracción de campos web (simulado)

3. **Día 3 - Pruebas Integradas:**
   - Sugerir cambios de configuración
   - Reportar cualquier bug encontrado
   - Proponer mejoras de UX
   - Validar flujo de trabajo

### Para Sugerir Cambios:

**Prioriza en este orden:**
1. **Bugs críticos** - Cualquier cosa que rompa el flujo
2. **Configuración** - Coordenadas, umbrales, timeouts
3. **UX** - Mejoras de usabilidad
4. **Features** - Nuevas funcionalidades
5. **Optimizaciones** - Rendimiento

---

**¿Tienes dudas o sugerencias?** ¡Usa el formato de sugerencias y compártelas! 🚀
