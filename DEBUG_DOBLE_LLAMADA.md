# 🔍 Debug: Doble Llamada a handle_start_processing()

## 🐛 Problema

El usuario reportó que `handle_start_processing()` se está llamando DOS VECES automáticamente, causando el error:
```
"No se puede iniciar sesión en estado running"
```

## 📊 Evidencia del Log

```
20:01:57.429390 - "Extracción completada"
20:01:57.436799 - "Iniciando procesamiento" ← PRIMERA LLAMADA
20:01:57.437812 - "Sesión iniciada" (exitosa)
20:01:57.930783 - "Iniciando procesamiento" ← SEGUNDA LLAMADA (494ms después)
20:01:57.930783 - "Intento de iniciar sesión en estado inválido" (ERROR)
```

**Timing:** La segunda llamada ocurre **~494ms** después de la primera.

## 🔎 Posibles Fuentes de la Llamada

### Fuente 1: Flujo Automático (Línea 376)
```python
# En handle_extract():
QTimer.singleShot(100, self.handle_start_processing)  # Línea 376
```

### Fuente 2: Hotkey Alt+4 (Línea 169)
```python
# En safe_start_processing():
QTimer.singleShot(0, self.handle_start_processing)  # Línea 169
```

### Fuente 3: Botón "Iniciar Procesamiento" (Línea 83)
```python
# En __init__():
self.window.start_processing_requested.connect(self.handle_start_processing)  # Línea 83
```

## ✅ Soluciones Implementadas

### Solución 1: Guard en handle_start_processing()
Agregado check para prevenir el error si la sesión ya está corriendo:

```python
def handle_start_processing(self):
    # Verificar si la sesión ya está corriendo (evitar doble inicio)
    if session.status == SessionStatus.RUNNING:
        self.logger.info("Sesión ya está corriendo, ignorando llamada duplicada")
        return  # Salir sin error
```

**Resultado:** Previene el ERROR pero NO soluciona la causa raíz.

### Solución 2: Flag de Protección en handle_extract()
Agregado flag `_extracting` para prevenir llamadas múltiples:

```python
def handle_extract(self):
    # Prevenir llamadas múltiples simultáneas
    if hasattr(self, '_extracting') and self._extracting:
        self.logger.warning("Extracción ya en progreso, ignorando llamada duplicada")
        return

    self._extracting = True

    try:
        # ... proceso de extracción ...
        self._extracting = False  # Reset al completar
    except:
        self._extracting = False  # Reset en caso de error
```

**Resultado:** Si `handle_extract()` se llama dos veces, solo se ejecutará una vez.

### Solución 3: Debug Logging con Stack Trace
Agregado logging para identificar la fuente exacta de las llamadas:

```python
import traceback
stack_trace = ''.join(traceback.format_stack()[-4:-1])
self.logger.info(f"handle_extract() LLAMADO desde:\n{stack_trace}")
self.logger.info(f"handle_start_processing() LLAMADO desde:\n{stack_trace}")
```

**Resultado:** El log mostrará EXACTAMENTE desde dónde se llama cada método.

## 🧪 Cómo Probar

1. Ejecutar la aplicación:
   ```bash
   python main.py
   ```

2. Presionar Alt+1 y seleccionar área (sin tocar ninguna otra tecla)

3. Revisar el log para ver los stack traces:
   ```bash
   tail -50 log.txt
   ```

4. Buscar las líneas que contienen "LLAMADO desde:" para ver la fuente exacta

## 🎯 Hipótesis

Basándome en el timing (~494ms), sospecho que:

1. **Hipótesis A:** La hotkey Alt+4 se está activando accidentalmente
   - Timing: QTimer.singleShot(0) = inmediato, pero la ejecución puede tomar tiempo
   - Si se presiona Alt+4 justo después del flujo automático, explicaría el delay

2. **Hipótesis B:** El botón se está clickeando programáticamente
   - `btn_start.setEnabled(True)` en `set_cedulas_list()` podría trigger algo
   - Poco probable, pero posible con ciertos widgets

3. **Hipótesis C:** `handle_extract()` se llama DOS VECES
   - Si el flujo automático en `_perform_capture()` llama a `handle_extract()` dos veces
   - Esto causaría dos llamadas a `handle_start_processing()` con 100ms de delay cada una
   - Timing: 494ms podría ser 100ms (timer) + 394ms (procesamiento OCR) + 100ms (timer)

## 📋 Próximos Pasos

1. ✅ **Ejecutar con debug logging** para ver los stack traces
2. ⏳ **Analizar las fuentes** de las llamadas duplicadas
3. ⏳ **Eliminar la fuente duplicada** una vez identificada
4. ⏳ **Verificar** que el flujo automático funciona sin errores

## 🚨 IMPORTANTE

El usuario confirmó: **"sin que presione algo se está llamando dos veces"**

Esto significa que NO es la hotkey Alt+4 ni el botón. La causa está en el **flujo automático**.

Posible causa raíz:
- `_perform_capture()` o `handle_extract()` se están llamando dos veces
- Algún signal/slot connection está duplicado

---

**Fecha:** 2025-12-02
**Estado:** 🔍 Investigando con debug logging
