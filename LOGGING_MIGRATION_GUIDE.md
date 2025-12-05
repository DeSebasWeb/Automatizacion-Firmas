# GUIA DE MIGRACION: Print() → Logging Estructurado

**Fecha:** 2025-12-05
**Objetivo:** Migrar de `print()` a logging estructurado compatible con API REST

---

## 📋 TABLA DE CONTENIDOS

1. [Por qué migrar](#por-qué-migrar)
2. [Componentes del sistema](#componentes-del-sistema)
3. [Guía de migración paso a paso](#guía-de-migración-paso-a-paso)
4. [Ejemplos de migración](#ejemplos-de-migración)
5. [Uso para API REST futuro](#uso-para-api-rest-futuro)
6. [Mejores prácticas](#mejores-prácticas)

---

## 🎯 POR QUÉ MIGRAR

### Problemas con `print()`

❌ **No estructurado** - Dificil parsear en producción
❌ **Sin niveles** - No puedes filtrar DEBUG vs ERROR
❌ **Sin contexto** - No incluye metadata (timestamps, request IDs, etc.)
❌ **No escalable** - Inutil para API REST con multiples requests concurrentes
❌ **No rastreable** - Imposible correlacionar logs entre componentes

### Beneficios del nuevo sistema

✅ **Logging estructurado JSON** - Fácil parsear con ELK, Splunk, etc.
✅ **Niveles apropiados** - DEBUG, INFO, WARNING, ERROR
✅ **Contexto automático** - Timestamps, operation IDs, request IDs
✅ **API REST ready** - Request tracking, correlation IDs
✅ **Rastreabilidad** - Seguir flujo completo de una operación

---

## 🔧 COMPONENTES DEL SISTEMA

### 1. StructuredLogger (Core)
Logger base con formato JSON estructurado.

### 2. LoggerFactory
Factory para crear loggers con configuración consistente.

### 3. OperationLogger (Context Manager)
Track automático de inicio/fin de operaciones con duración y métricas.

### 4. APIOperationLogger (Context Manager)
Especializado para operaciones API REST con request IDs.

### 5. Log Helpers
Funciones helpers para migración fácil de `print()`.

---

## 📚 GUÍA DE MIGRACIÓN PASO A PASO

### Paso 1: Importar el logger en tu módulo

**ANTES:**
```python
# Sin imports
```

**DESPUÉS:**
```python
from shared.logging import LoggerFactory, log_operation
from shared.logging import (
    log_info_message,
    log_warning_message,
    log_error_message,
    log_api_call,
    log_api_response
)
```

### Paso 2: Crear logger en `__init__`

**ANTES:**
```python
class GoogleVisionAdapter:
    def __init__(self, config):
        self.config = config
        self.client = None
```

**DESPUÉS:**
```python
class GoogleVisionAdapter:
    def __init__(self, config):
        self.config = config
        self.client = None
        self.logger = LoggerFactory.get_ocr_logger("google_vision")
```

### Paso 3: Reemplazar prints por logging

Ver sección [Ejemplos de Migración](#ejemplos-de-migración)

---

## 💡 EJEMPLOS DE MIGRACIÓN

### Ejemplo 1: Mensaje DEBUG

**ANTES:**
```python
print(f"DEBUG Google Vision: Texto completo detectado:\\n{full_text}")
```

**DESPUÉS:**
```python
self.logger.debug("Texto completo detectado", full_text=full_text)
```

**Output JSON:**
```json
{
  "event": "Texto completo detectado",
  "full_text": "1234567\\n7654321",
  "level": "debug",
  "timestamp": "2025-12-05T10:30:00.123Z",
  "component": "ocr",
  "provider": "google_vision"
}
```

---

### Ejemplo 2: Mensaje INFO

**ANTES:**
```python
print("✓ Google Vision: Respuesta recibida (1 llamada API)")
```

**DESPUÉS:**
```python
log_api_response(self.logger, "google_vision", True, api_calls=1)
```

**Output JSON:**
```json
{
  "event": "Respuesta API: google_vision",
  "api_provider": "google_vision",
  "status": "success",
  "api_calls": 1,
  "level": "info",
  "timestamp": "2025-12-05T10:30:01.456Z"
}
```

---

### Ejemplo 3: Mensaje WARNING

**ANTES:**
```python
print(f"ADVERTENCIA: Texto '{text_clean}' no encontrado en respuesta")
```

**DESPUÉS:**
```python
log_warning_message(
    self.logger,
    "Texto no encontrado en respuesta",
    text=text_clean
)
```

**Output JSON:**
```json
{
  "event": "Texto no encontrado en respuesta",
  "text": "1234567",
  "level": "warning",
  "timestamp": "2025-12-05T10:30:02.789Z"
}
```

---

### Ejemplo 4: Mensaje ERROR

**ANTES:**
```python
print(f"ERROR Google Vision: {e}")
import traceback
traceback.print_exc()
```

**DESPUÉS:**
```python
log_error_message(
    self.logger,
    "Error en Google Vision API",
    error=e
)
```

**Output JSON:**
```json
{
  "event": "Error en Google Vision API",
  "error_type": "APIException",
  "error_message": "Invalid credentials",
  "level": "error",
  "timestamp": "2025-12-05T10:30:03.012Z"
}
```

---

### Ejemplo 5: Tracking de operaciones completas

**ANTES:**
```python
def extract_cedulas(self, image):
    print("DEBUG: Iniciando extracción...")

    # Procesamiento
    cedulas = []
    for line in lines:
        cedulas.append(process_line(line))

    print(f"✓ Total cédulas: {len(cedulas)}")
    return cedulas
```

**DESPUÉS:**
```python
def extract_cedulas(self, image):
    with log_operation(self.logger, "extract_cedulas", image_id=image.id) as op:
        # Procesamiento
        cedulas = []
        for line in lines:
            cedulas.append(process_line(line))

        # Agregar métricas
        op.add_metric("cedulas_extraidas", len(cedulas))

        return cedulas
```

**Output JSON (inicio):**
```json
{
  "event": "Iniciando operacion: extract_cedulas",
  "operation": "extract_cedulas",
  "operation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "image_id": 123,
  "level": "info",
  "timestamp": "2025-12-05T10:30:00.000Z"
}
```

**Output JSON (fin):**
```json
{
  "event": "Operacion completada: extract_cedulas",
  "operation": "extract_cedulas",
  "operation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "image_id": 123,
  "duration_seconds": 1.234,
  "status": "success",
  "cedulas_extraidas": 15,
  "level": "info",
  "timestamp": "2025-12-05T10:30:01.234Z"
}
```

---

### Ejemplo 6: Llamadas a APIs externas

**ANTES:**
```python
print("DEBUG: Llamando a Google Vision API...")
response = self.client.document_text_detection(image)
print("✓ Respuesta recibida")
```

**DESPUÉS:**
```python
log_api_call(self.logger, "google_vision", "document_text_detection", language="es")
response = self.client.document_text_detection(image)
log_api_response(self.logger, "google_vision", True)
```

---

## 🚀 USO PARA API REST FUTURO

Cuando migres a API REST, el sistema ya está preparado:

### Ejemplo: Endpoint de procesamiento de imágenes

```python
from fastapi import FastAPI, Request
from shared.logging import LoggerFactory, APIOperationLogger

app = FastAPI()
logger = LoggerFactory.get_api_logger()

@app.post("/api/v1/images/process")
async def process_image(request: Request, image_data: bytes):
    # Context manager con tracking de request
    with APIOperationLogger(
        logger,
        "process_image_upload",
        request_id=request.state.request_id,  # Auto-generado por middleware
        endpoint="/api/v1/images/process",
        method="POST",
        user_id=request.state.user.id,
        client_ip=request.client.host
    ) as op:
        # Procesar imagen
        result = ocr_service.extract_cedulas(image_data)

        # Agregar métricas
        op.add_metric("cedulas_found", len(result.cedulas))
        op.add_metric("confidence_avg", result.average_confidence)

        return {"cedulas": result.cedulas}
```

**Output JSON:**
```json
{
  "event": "Operacion completada: process_image_upload",
  "operation": "process_image_upload",
  "operation_id": "xyz789...",
  "request_id": "req-abc123...",
  "endpoint": "/api/v1/images/process",
  "method": "POST",
  "user_id": 42,
  "client_ip": "192.168.1.100",
  "duration_seconds": 2.456,
  "status": "success",
  "cedulas_found": 15,
  "confidence_avg": 0.95,
  "level": "info",
  "timestamp": "2025-12-05T10:30:00.000Z"
}
```

---

## ✅ MEJORES PRÁCTICAS

### 1. **Usar niveles apropiados**

| Nivel | Cuándo usar | Ejemplo |
|-------|-------------|---------|
| **DEBUG** | Información detallada para debugging | Valores de variables, flujo interno |
| **INFO** | Flujo normal de la aplicación | "Request recibido", "Operación exitosa" |
| **WARNING** | Situaciones anómalas pero no errores | "Texto no encontrado", "Fallback usado" |
| **ERROR** | Errores y excepciones | "API falló", "Credenciales inválidas" |

### 2. **Usar contexto estructurado**

❌ **MAL:**
```python
logger.info(f"Procesando imagen {image_id} del usuario {user_id}")
```

✅ **BIEN:**
```python
logger.info("Procesando imagen", image_id=image_id, user_id=user_id)
```

### 3. **Usar operation loggers para flujos completos**

❌ **MAL:**
```python
logger.info("Iniciando procesamiento")
# ... código ...
logger.info("Procesamiento completado")
```

✅ **BIEN:**
```python
with log_operation(logger, "procesamiento", image_id=123) as op:
    # ... código ...
    op.add_metric("items_processed", count)
```

### 4. **Nombrar operaciones consistentemente**

✅ **Convención:** `verbo_sustantivo`
- `extract_cedulas`
- `process_image`
- `validate_form`
- `save_results`

### 5. **Incluir métricas relevantes**

Para OCR:
```python
op.add_metric("cedulas_extraidas", count)
op.add_metric("confidence_promedio", avg_conf)
op.add_metric("api_calls", 1)
```

Para API:
```python
op.add_metric("items_returned", len(results))
op.add_metric("processing_time_ms", duration)
op.add_metric("cache_hit", True/False)
```

### 6. **Configurar contexto global**

En el inicio de la aplicación:

```python
from shared.logging import LoggerFactory

# Configurar contexto global
LoggerFactory.set_global_context(
    environment="production",  # o "development"
    app_version="1.0.0",
    instance_id="server-01"
)
```

Esto agregará estos campos a **todos** los logs automáticamente.

---

## 📊 TABLA DE CONVERSIÓN RÁPIDA

| Print actual | Reemplazo | Helper |
|-------------|-----------|---------|
| `print("DEBUG: ...")` | `logger.debug(...)` | `log_debug_message()` |
| `print("✓ ...")` | `logger.info(...)` | `log_info_message()` |
| `print("ADVERTENCIA: ...")` | `logger.warning(...)` | `log_warning_message()` |
| `print("ERROR: ...")` | `logger.error(...)` | `log_error_message()` |
| `print(f"✓ Extraído: {x}")` | `log_success("extracted", value=x)` | `log_success()` |
| `print(f"✗ Descartado: {x}")` | `log_failure("discarded", reason=r)` | `log_failure()` |
| Llamada API | `log_api_call()` + `log_api_response()` | Helpers API |
| Operación completa | `with log_operation(...):` | Context manager |

---

## 🎯 PRIORIDADES DE MIGRACIÓN

### Prioridad ALTA (migrar primero)
1. ✅ **Errores y excepciones** - `print("ERROR: ...")` → `log_error_message()`
2. ✅ **Llamadas a APIs externas** - Agregar `log_api_call()` y `log_api_response()`
3. ✅ **Operaciones principales** - Wrap con `log_operation()`

### Prioridad MEDIA
4. ✅ **Advertencias** - `print("ADVERTENCIA: ...")` → `log_warning_message()`
5. ✅ **Mensajes informativos** - `print("✓ ...")` → `log_info_message()`

### Prioridad BAJA (opcional)
6. ⚠️ **Debug verbose** - `print("DEBUG: ...")` → `logger.debug()`

---

## 📝 EJEMPLO COMPLETO: ANTES vs DESPUÉS

### ANTES (GoogleVisionAdapter.extract_cedulas)

```python
def extract_cedulas(self, image):
    print("DEBUG Google Vision: Iniciando extracción...")
    print("DEBUG Google Vision: Enviando imagen completa a API (1 sola llamada)")

    try:
        processed_image = self.preprocess_image(image)
        img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

        print("DEBUG Google Vision: Llamando a DOCUMENT_TEXT_DETECTION (es)...")
        response = self._call_ocr_api(img_bytes)

        print("✓ Google Vision: Respuesta recibida (1 llamada API)")

        records = []
        if response.full_text_annotation:
            full_text = response.full_text_annotation.text
            print(f"DEBUG Google Vision: Texto completo detectado:\\n{full_text}")

            for num in numbers:
                if 3 <= len(num) <= 11:
                    record = CedulaRecord.from_primitives(cedula=num, confidence=95.0)
                    records.append(record)
                    print(f"✓ Cédula extraída: '{num}' ({len(num)} dígitos)")
                else:
                    print(f"✗ Descartada (muy corta): '{num}'")

        print(f"DEBUG Google Vision: Total cédulas únicas: {len(records)}")
        return records

    except Exception as e:
        print(f"ERROR Google Vision: {e}")
        import traceback
        traceback.print_exc()
        return []
```

### DESPUÉS (GoogleVisionAdapter.extract_cedulas)

```python
def extract_cedulas(self, image):
    with log_operation(self.logger, "extract_cedulas", image_size=f"{image.width}x{image.height}") as op:
        try:
            # Preprocesar
            processed_image = self.preprocess_image(image)
            img_bytes = ImageConverter.pil_to_bytes(processed_image, format='PNG')

            # Llamar API
            log_api_call(self.logger, "google_vision", "document_text_detection", language="es")
            response = self._call_ocr_api(img_bytes)
            log_api_response(self.logger, "google_vision", True, api_calls=1)

            # Procesar respuesta
            records = []
            if response.full_text_annotation:
                full_text = response.full_text_annotation.text
                self.logger.debug("Texto completo detectado", full_text=full_text)

                for num in numbers:
                    if 3 <= len(num) <= 11:
                        record = CedulaRecord.from_primitives(cedula=num, confidence=95.0)
                        records.append(record)
                        log_success(self.logger, "cedula_extraida", cedula=num, digits=len(num))
                    else:
                        log_failure(self.logger, "cedula_descartada", reason="too_short", cedula=num)

            # Agregar métricas
            op.add_metric("cedulas_extraidas", len(records))

            return records

        except Exception as e:
            log_error_message(self.logger, "Error en extracción OCR", error=e)
            return []
```

**Beneficios:**
- ✅ Logs estructurados en JSON
- ✅ Tracking automático de duración
- ✅ Operation ID para correlación
- ✅ Métricas agregadas
- ✅ Compatible con API REST futuro

---

## 🔍 CÓMO CONSULTAR LOGS

### En desarrollo (consola)
Los logs se imprimen en consola y se guardan en `logs/app_YYYYMMDD.log`

### En producción (JSON parsing)

**Ejemplo con `jq`:**
```bash
# Ver solo errores
cat logs/app_20251205.log | jq 'select(.level=="error")'

# Ver operación específica
cat logs/app_20251205.log | jq 'select(.operation_id=="a1b2c3d4...")'

# Ver métricas de extracción
cat logs/app_20251205.log | jq 'select(.operation=="extract_cedulas") | {duration, cedulas_extraidas}'
```

**Con ELK Stack / Splunk:**
```
level:error AND component:ocr
operation:extract_cedulas AND cedulas_extraidas:>10
request_id:"req-abc123" | stats avg(duration_seconds)
```

---

## ❓ FAQ

**P: ¿Debo migrar todos los prints de una vez?**
R: No. Migra gradualmente empezando por los más críticos (errores, APIs).

**P: ¿Puedo mezclar prints y logging?**
R: Sí, pero no es recomendable. Migra módulo por módulo.

**P: ¿Qué pasa con los prints en imports fallidos?**
R: Déjalos por ahora. Esos son mensajes de inicialización que no afectan logging operacional.

**P: ¿El logging afecta el performance?**
R: Mínimamente. El overhead de structlog es <1ms por log.

**P: ¿Cómo testeo código con logging?**
R: Usa `LoggerFactory` con un logger mock o captura logs en tests.

---

**Autor:** Tu usuario
**Fecha:** 2025-12-05
**Status:** ✅ SISTEMA LISTO PARA USAR
