# Progreso - Implementación OCR Dual con Validación Automática

**Fecha inicio:** 2025-11-18
**Estado:** 🔄 EN DESARROLLO
**Proyecto:** Evolución a sistema de OCR dual con validación inteligente

---

## 🎯 Objetivo

Implementar sistema de OCR dual que:
1. **Google Vision** → Extrae nombres + cédulas del formulario manuscrito
2. **Tesseract** → Lee formulario web digital para validación
3. **Fuzzy Matching** → Validación automática inteligente (>85% match)
4. **Automatización completa** → Pausas ESC/F9, alertas, flujo automático

---

## ✅ Completado (Fase 1)

### 1. Entidades de Dominio Creadas

#### ✅ `src/domain/entities/row_data.py`
- Representa datos de un renglón del formulario manuscrito
- Propiedades: `row_index`, `nombres_manuscritos`, `cedula`, `is_empty`, `confidence`
- Detecta renglones vacíos automáticamente

#### ✅ `src/domain/entities/form_data.py`
- Representa datos del formulario web digital
- Campos: `primer_nombre`, `segundo_nombre`, `primer_apellido`, `segundo_apellido`
- Propiedades: `nombre_completo`, `apellidos`, `nombres`, `is_empty`
- Detecta cuando persona no existe en BD (todos campos vacíos)

#### ✅ `src/domain/entities/validation_result.py`
- Resultado de validación fuzzy
- Estados: `OK`, `WARNING`, `ERROR`
- Acciones: `AUTO_SAVE`, `REQUIRE_VALIDATION`, `ALERT_NOT_FOUND`
- Incluye detalles de comparación campo por campo

### 2. Servicios Críticos

#### ✅ `src/application/services/fuzzy_validator.py`
- Validador fuzzy para comparar manuscrito vs digital
- Algoritmo Levenshtein para similitud de strings
- Normalización de texto (tildes, acentos, mayúsculas)
- Umbral configurable (default: 85% similitud)
- Criterios de validación:
  - **Primer apellido** >85% match (OBLIGATORIO)
  - **Al menos un nombre** >85% match (OBLIGATORIO)
  - Si ambos OK → `AUTO_SAVE`
  - Si falla → `REQUIRE_VALIDATION`
  - Si persona no existe → `ALERT_NOT_FOUND`

### 3. Dependencias Agregadas

#### ✅ `requirements.txt` actualizado
- `python-Levenshtein>=0.21.0` - Fuzzy matching rápido
- `unidecode>=1.3.7` - Normalización de texto
- `pynput==1.7.6` - Ya existía, para pausas ESC/F9

---

## ✅ Completado (Fase 2)

### Adaptadores OCR y Controlador de Automatización

#### 1. ✅ GoogleVisionAdapter Actualizado
**Archivo:** `src/infrastructure/ocr/google_vision_adapter.py`

**Cambios implementados:**
- ✅ Método actual: `extract_cedulas()` → solo extrae cédulas
- ✅ Nuevo método: `extract_full_form_data()` → extrae nombres + cédulas
- ✅ Lógica de detección de renglones vacíos
- ✅ Retornar `List[RowData]` en lugar de `List[CedulaRecord]`
- ✅ Dividir imagen en ~15 regiones (renglones)
- ✅ Procesar cada región individualmente

**Estrategia de división:**
```
Imagen completa (354x473 px)
↓
Dividir en 15 regiones horizontales
↓
Región 1 (0-31 px): {nombres columna izq + cédula columna centro}
Región 2 (32-63 px): {...}
...
Región 15 (442-473 px): {...}
```

#### 2. ✅ TesseractWebScraper Creado
**Archivo:** `src/infrastructure/ocr/tesseract_web_scraper.py`

**Responsabilidades implementadas:**
- ✅ Capturar región del formulario web (campos digitales)
- ✅ Leer campos uno por uno con Tesseract
- ✅ Detectar campos vacíos
- ✅ Retornar `FormData`

**Métodos implementados:**
```python
class TesseractWebScraper:
    def capture_web_form_region() -> Image
    def extract_field_value(field_name: str) -> str
    def get_all_fields() -> FormData
    def is_person_not_found() -> bool
    def configure_field_region(field_name, x, y, width, height)
```

**Configuración Tesseract:**
- ✅ `--psm 6` - Bloque uniforme de texto
- ✅ `--oem 3` - Modo LSTM
- ✅ `-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ `

#### 3. ✅ AutomationController Creado
**Archivo:** `src/application/controllers/automation_controller.py`

**Responsabilidades implementadas:**
- ✅ Coordinar flujo automático completo
- ✅ Procesar cada renglón secuencialmente
- ✅ Manejar pausas (ESC/F9)
- ✅ Gestionar alertas
- ✅ Logging detallado
- ✅ Estadísticas de procesamiento

**Estados del sistema implementados:**
- ✅ `IDLE` - Sistema inactivo
- ✅ `RUNNING` - Procesando automáticamente
- ✅ `PAUSED_ESC` - Usuario presionó ESC
- ✅ `PAUSED_ALERT` - Esperando validación
- ✅ `PAUSED_ERROR` - Error requiere intervención
- ✅ `COMPLETED` - Todos los renglones procesados

**Características implementadas:**
- ✅ Listener de teclado para ESC (pausar) y F9 (reanudar)
- ✅ Callbacks para alertas y progreso
- ✅ Manejo automático de renglones vacíos
- ✅ Validación fuzzy automática
- ✅ Click automático en botón guardar
- ✅ Resumen de estadísticas al finalizar

---

## 📋 Flujo Completo Planificado

```
1. Usuario captura formulario manuscrito (F4)
   ↓
2. Google Vision extrae TODOS los renglones
   → List[RowData] con 15 renglones
   ↓
3. Para CADA renglón:

   A) Si renglón está VACÍO:
      → Click automático en "Renglón En Blanco"
      → Log: "Renglón X: Vacío"
      → Continuar con siguiente

   B) Si renglón tiene datos:
      → Digitar cédula en campo de búsqueda
      → Presionar Enter
      → Esperar carga (max 5 seg)
      → Tesseract lee formulario web → FormData

      → FuzzyValidator compara manuscrito vs digital:

      C.1) Si persona NO ENCONTRADA (FormData.is_empty):
           ⚠️ ALERTA: "Cédula no existe"
           → PAUSAR proceso
           → Opciones: [Continuar] [Marcar novedad] [Pausar]

      C.2) Si persona ENCONTRADA:
           → Validación fuzzy:

           Si ValidationResult.action == AUTO_SAVE:
             ✓ Click automático en "Guardar"
             → Log: "Renglón X: Guardado (confianza: 92%)"
             → Siguiente renglón

           Si ValidationResult.action == REQUIRE_VALIDATION:
             ⚠️ ALERTA: "Validación requerida"
             → Mostrar comparación manuscrito vs digital
             → PAUSAR proceso
             → Opciones: [Guardar] [Saltar] [Corregir]

4. Presionar ESC en CUALQUIER momento:
   → Pausar inmediatamente
   → Guardar estado
   → Mostrar: "PAUSADO - F9 para continuar"

5. Completar todos los renglones:
   → Mostrar resumen:
     - Validados automáticamente: X
     - Requerida intervención: Y
     - Renglones vacíos: Z
     - No encontrados: W
```

---

## 📊 Arquitectura OCR Dual

```
┌─────────────────────────────────────────────────┐
│         FORMULARIO MANUSCRITO (PAPEL)           │
│  [Google Cloud Vision API - Escritura manual]  │
│                                                 │
│  Columna Izquierda    │  Columna Centro        │
│  ==================   │  ================       │
│  MARIA DE JESUS       │  20014807              │
│  OMAR                 │  79828861              │
│  [VACÍO]              │  [VACÍO]               │
│  ...                  │  ...                   │
└─────────────────────────────────────────────────┘
          ↓ extract_full_form_data()
┌─────────────────────────────────────────────────┐
│              List[RowData]                      │
│  - row_index: 0                                 │
│  - nombres_manuscritos: "MARIA DE JESUS"        │
│  - cedula: "20014807"                           │
│  - is_empty: False                              │
└─────────────────────────────────────────────────┘
          ↓ Para cada renglón
┌─────────────────────────────────────────────────┐
│    AUTOMATIZACIÓN: Digitar cédula + Enter      │
│         → Esperar carga de página              │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│         FORMULARIO WEB (DIGITAL/IMPRESO)        │
│     [Tesseract OCR - Texto digital/impreso]    │
│                                                 │
│  1er Nombre:   OMAR                             │
│  2do Nombre:   [VACÍO]                          │
│  1er Apellido: MAYORGA                          │
│  2do Apellido: ROBLES                           │
└─────────────────────────────────────────────────┘
          ↓ get_all_fields()
┌─────────────────────────────────────────────────┐
│               FormData                          │
│  - primer_nombre: "OMAR"                        │
│  - segundo_nombre: ""                           │
│  - primer_apellido: "MAYORGA"                   │
│  - segundo_apellido: "ROBLES"                   │
│  - is_empty: False                              │
└─────────────────────────────────────────────────┘
          ↓ validate_person()
┌─────────────────────────────────────────────────┐
│          FuzzyValidator                         │
│                                                 │
│  Manuscrito: "MARIA DE JESUS"                   │
│  Digital:    "OMAR MAYORGA"                     │
│                                                 │
│  Primer apellido: "JESUS" vs "MAYORGA" → 12% ❌  │
│  Nombres: "MARIA" vs "OMAR" → 20% ❌             │
│                                                 │
│  Result: REQUIRE_VALIDATION                     │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│    ALERTA: Usuario debe validar manualmente    │
└─────────────────────────────────────────────────┘
```

---

## 🔧 Configuración Planificada

**Nuevo archivo:** `config/settings.yaml` (sección nueva)

```yaml
ocr:
  google_vision:
    enabled: true
    extract_nombres: true  # NUEVO
    extract_cedulas: true
    detect_empty_rows: true  # NUEVO
    confidence_threshold: 0.30

  tesseract:
    enabled: true  # NUEVO
    target: "web_form_fields"
    config: "--psm 6 --oem 3"
    char_whitelist: "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ "

validation:
  enabled: true  # NUEVO
  fuzzy_matching: true
  min_similarity: 0.85  # 85% umbral
  required_matches:
    - "primer_apellido"
    - "any_nombre"
  alert_on_not_found: true
  alert_on_mismatch: true

automation:
  enabled: true
  typing_delay_ms: 50
  click_delay_ms: 300
  page_load_timeout: 5
  pause_key: "esc"  # NUEVO
  resume_key: "f9"  # NUEVO
  auto_click_save: true
  auto_handle_empty_rows: true

empty_row_handling:
  auto_click_button: true  # NUEVO
  button_name: "Renglón En Blanco"
  log_empty_rows: true
```

---

## 📈 Métricas de Éxito Objetivo

- ✅ **85%+** de renglones validados automáticamente
- ✅ **0%** de guardados incorrectos (falsos positivos)
- ✅ **< 5 segundos** por renglón en promedio
- ✅ **100%** de renglones vacíos detectados correctamente
- ✅ **100%** de personas no encontradas detectadas

---

## 🚀 Próximos Pasos Inmediatos

### ✅ Fase 2 - Adaptadores OCR (COMPLETADA)

1. ✅ **GoogleVisionAdapter Actualizado**
   - ✅ Implementar `extract_full_form_data()`
   - ✅ Dividir imagen en regiones
   - ✅ Detectar renglones vacíos
   - ✅ Retornar `List[RowData]`

2. ✅ **TesseractWebScraper Creado**
   - ✅ Capturar formulario web
   - ✅ Leer campos digitales
   - ✅ Detectar persona no encontrada
   - ✅ Retornar `FormData`

3. ✅ **AutomationController Creado**
   - ✅ Orquestar flujo completo
   - ✅ Manejar pausas ESC/F9
   - ✅ Gestionar alertas
   - ✅ Logging detallado

### 🔄 Fase 3 - UI y Experiencia de Usuario (PRÓXIMA)

4. **Integración con UI Principal** ← PRÓXIMO
   - Integrar AutomationController en la aplicación PyQt6
   - Conectar callbacks de alertas y progreso
   - Panel de progreso visual
   - Alertas visuales para validación
   - Estadísticas en tiempo real

5. **Configuración de Regiones Tesseract**
   - Herramienta para configurar regiones de campos web
   - Calibración de coordenadas (x, y, width, height)
   - Guardar configuración en settings.yaml

### Fase 4 - Testing y Documentación

6. **Tests unitarios e integración**
   - Test fuzzy validation
   - Test extracción completa
   - Test flujo end-to-end

7. **Documentación**
   - Guía de usuario
   - Arquitectura técnica
   - Troubleshooting

---

## 📝 Notas de Implementación

### Decisiones de Diseño

1. **Google Vision para manuscrito:**
   - Mejor para escritura manual
   - Procesa imagen completa en una llamada
   - Extrae nombres Y cédulas simultáneamente

2. **Tesseract para digital:**
   - Gratuito (sin límites de API)
   - Óptimo para texto digital/impreso
   - Solo lee formulario web después de búsqueda

3. **Fuzzy Matching:**
   - Tolerante a errores de OCR
   - Umbral 85% balanceado
   - Normalización robusta (tildes, acentos)

4. **Arquitectura Hexagonal:**
   - Mantenida en todos los componentes
   - Fácil testeo
   - Desacoplamiento

---

## ⚠️ Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Google Vision no detecta nombres | Ajustar confianza + preprocesamiento |
| Tesseract no lee campos digitales | Configuración PSM/OEM optimizada |
| Fuzzy matching genera falsos positivos | Umbral 85% + validación manual |
| Usuario pierde control | Sistema de pausas ESC en todo momento |
| Errores de red/timeout | Reintentos automáticos + alertas |

---

**Estado actual:** ✅ Fase 1 completada | ✅ Fase 2 completada (OCR Dual + AutomationController)
**Próximo hito:** 🔄 Fase 3 - Integración con UI PyQt6
**Estimación:** ~1 día adicional para integración con UI

**Componentes Core Implementados:**
- ✅ GoogleVisionAdapter.extract_full_form_data() - Extrae nombres + cédulas
- ✅ TesseractWebScraper - Lee formulario web digital
- ✅ FuzzyValidator - Validación inteligente 85% umbral
- ✅ AutomationController - Orquestación completa con pausas ESC/F9
- ✅ Entidades de dominio (RowData, FormData, ValidationResult)

**Última actualización:** 2025-11-18
**Desarrollador:** Juan Sebastian Lopez Hernandez
