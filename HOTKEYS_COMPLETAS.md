# 🎮 Guía Completa de Hotkeys

## ✅ Todas las Hotkeys Disponibles (ACTUALIZADO)

### Hotkeys Implementadas

| Tecla | Acción | Estado |
|-------|--------|--------|
| **F4** | Seleccionar área de captura | ✅ Implementado |
| **F5** | Capturar pantalla | ✅ **NUEVO** |
| **F6** | Extraer cédulas con OCR | ✅ **NUEVO** |
| **F7** | Iniciar procesamiento | ✅ **NUEVO** |
| **Ctrl+Q** | Procesar siguiente cédula | ✅ Implementado |
| **F3** | Pausar/Reanudar | ✅ Implementado |

---

## 🚀 Flujo de Trabajo Completo con Hotkeys

### Antes (con mouse)
1. Click en "Seleccionar Área"
2. Click en "Capturar Pantalla"
3. Click en "Extraer Cédulas"
4. Click en "Iniciar Procesamiento"
5. Click en "Siguiente" × N veces

### Ahora (solo teclado) ⚡
1. **F4** → Seleccionar área
2. **F5** → Capturar pantalla
3. **F6** → Extraer cédulas
4. **F7** → Iniciar procesamiento
5. **Ctrl+Q** × N veces → Procesar todas las cédulas

**¡Todo sin tocar el mouse!** 🎯

---

## 🔧 Configuración

### Archivo: `config/settings.yaml`

```yaml
hotkeys:
  capture_area: f4           # Seleccionar área
  capture_screen: f5         # Capturar pantalla (NUEVO)
  extract_cedulas: f6        # Extraer cédulas (NUEVO)
  start_processing: f7       # Iniciar procesamiento (NUEVO)
  next_record: ctrl+q        # Procesar siguiente
  pause: f3                  # Pausar/Reanudar
```

**Nota:** Puedes cambiar las teclas editando este archivo y reiniciando la aplicación.

---

## 🧪 Cómo Probar las Hotkeys

### Script de Prueba Mejorado

```bash
python scripts/test_hotkeys.py
```

**Qué hace:**
- Detecta todas las hotkeys (F4, F5, F6, F7, Ctrl+Q, F3)
- Muestra contador de detecciones
- Resumen final al presionar ESC

**Ejemplo de salida:**
```
✅ F4 detectado correctamente! (#1)
✅ F5 detectado correctamente! (#1)
✅ F6 detectado correctamente! (#1)
✅ F7 detectado correctamente! (#1)
✅ Ctrl+Q detectado correctamente! (#3)
✅ F3 detectado correctamente! (#2)

RESUMEN DE DETECCIONES:
  ✅ F4: 1 detección(es)
  ✅ F5: 1 detección(es)
  ✅ F6: 1 detección(es)
  ✅ F7: 1 detección(es)
  ✅ CTRL+Q: 3 detección(es)
  ✅ F3: 2 detección(es)
```

---

## 🐛 Solución de Problemas

### Problema: "F4 no funciona"

**Causas posibles:**

1. **Otra aplicación usa F4**
   - Discord, OBS, Bandicam, etc.
   - **Solución:** Cierra esas aplicaciones o cambia sus hotkeys

2. **Falta permisos de administrador (Windows)**
   - **Solución:** Ejecuta la aplicación como administrador
   ```bash
   # Click derecho en run.bat → Ejecutar como administrador
   ```

3. **Conflicto con teclas del sistema**
   - En algunos laptops, F4 requiere presionar Fn
   - **Solución:** Cambia la hotkey en `config/settings.yaml`
   ```yaml
   hotkeys:
     capture_area: f9  # En lugar de f4
   ```

### Problema: "Ninguna hotkey funciona"

**Diagnóstico:**

1. **Ejecuta el script de prueba:**
   ```bash
   python scripts/test_hotkeys.py
   ```

2. **Si el script NO detecta las teclas:**
   - Ejecuta como administrador
   - Verifica que pynput esté instalado:
     ```bash
     pip install pynput
     ```

3. **Si el script SÍ detecta pero la app NO:**
   - Revisa los logs en `logs/app_*.log`
   - Busca errores en el registro de hotkeys
   - Reporta el problema con los logs

### Problema: "F5/F6/F7 no funcionan"

**Estas son hotkeys nuevas. Si no funcionan:**

1. **Verifica que la configuración esté actualizada:**
   ```bash
   # Windows
   type config\settings.yaml | findstr "hotkeys" -A 6

   # Linux/Mac
   grep -A 6 "hotkeys" config/settings.yaml
   ```

   Debe mostrar:
   ```yaml
   hotkeys:
     capture_area: f4
     capture_screen: f5
     extract_cedulas: f6
     start_processing: f7
     next_record: ctrl+q
     pause: f3
   ```

2. **Reinicia la aplicación:**
   - Cierra completamente la app
   - Ejecuta de nuevo: `python main.py`

3. **Revisa la consola al iniciar:**
   Deberías ver:
   ```
   Registrando hotkeys...
     ✓ Ctrl+Q registrado
     ✓ F3 registrado
     ✓ F4 registrado
     ✓ F5 registrado
     ✓ F6 registrado
     ✓ F7 registrado
   ✅ Todas las hotkeys registradas correctamente
   ```

---

## 📊 Comparación: Antes vs Ahora

| Aspecto | Antes | Ahora | Mejora |
|---------|-------|-------|--------|
| **Hotkeys disponibles** | 3 (F3, F4, Ctrl+Q) | **6** (F3, F4, F5, F6, F7, Ctrl+Q) | +100% |
| **Flujo sin mouse** | ❌ No posible | ✅ Completamente posible | 🎯 |
| **Velocidad de digitación** | 50ms/tecla | 10ms/tecla | 5x más rápido |
| **Captura con teclado** | ❌ No | ✅ F5 | ✅ |
| **Extracción con teclado** | ❌ No | ✅ F6 | ✅ |
| **Inicio con teclado** | ❌ No | ✅ F7 | ✅ |

---

## 💡 Consejos de Uso

### Para Máxima Velocidad

1. **Primera vez:**
   - Configura coordenadas del campo de búsqueda:
     ```bash
     python scripts/configure_search_field.py
     ```

2. **Uso normal:**
   ```
   F4 → Seleccionar área (una vez)
   F5 → Capturar
   F6 → Extraer (espera 2-3 seg)
   F7 → Iniciar
   Ctrl+Q → Procesar (repite hasta terminar)
   ```

3. **Enfoca manualmente la ventana objetivo antes del primer Ctrl+Q**

### Para Multitasking

- Usa **F3** para pausar si necesitas hacer otra cosa
- Presiona **F3** de nuevo para reanudar
- El estado se guarda automáticamente

### Para Debugging

- Revisa la consola para ver mensajes de debug:
  ```
  DEBUG: F4 presionado - seleccionando área
  DEBUG: F5 presionado - capturando pantalla
  DEBUG: F6 presionado - extrayendo cédulas
  DEBUG: F7 presionado - iniciando procesamiento
  DEBUG: Ctrl+Q presionado - iniciando procesamiento SIN Alt+Tab
  ```

---

## 🔄 Personalizar Hotkeys

Puedes cambiar las teclas editando `config/settings.yaml`:

### Ejemplo 1: Cambiar F4 a F9
```yaml
hotkeys:
  capture_area: f9  # En lugar de f4
```

### Ejemplo 2: Usar Ctrl+Shift+tecla
```yaml
hotkeys:
  capture_screen: ctrl+shift+c
  extract_cedulas: ctrl+shift+e
```

### Ejemplo 3: Usar teclas numéricas
```yaml
hotkeys:
  capture_area: f1
  capture_screen: f2
  extract_cedulas: f3
  start_processing: f4
  next_record: ctrl+space
  pause: f12
```

**Importante:** Después de editar, reinicia la aplicación.

---

## 📝 Resumen de Cambios Implementados

### Archivos Modificados

1. **[config/settings.yaml](config/settings.yaml#L10-L16)**
   - Agregadas 3 hotkeys nuevas: F5, F6, F7

2. **[src/presentation/controllers/main_controller.py](src/presentation/controllers/main_controller.py#L91-L199)**
   - Registradas 3 hotkeys nuevas
   - Agregados mensajes de debug
   - Mensajes de confirmación en consola

3. **[scripts/test_hotkeys.py](scripts/test_hotkeys.py)**
   - Script mejorado con contador
   - Resumen de detecciones
   - Mensajes de ayuda

### Nuevas Características

- ✅ **F5** → Captura pantalla sin mouse
- ✅ **F6** → Extrae cédulas sin mouse
- ✅ **F7** → Inicia procesamiento sin mouse
- ✅ Mensajes de debug en consola
- ✅ Script de prueba mejorado
- ✅ Flujo 100% con teclado

---

## 🎯 Próximos Pasos

### 1. Probar las Hotkeys
```bash
python scripts/test_hotkeys.py
```

### 2. Configurar Coordenadas (si no lo has hecho)
```bash
python scripts/configure_search_field.py
```

### 3. Ejecutar la Aplicación
```bash
python main.py
```

### 4. Probar el Flujo Completo con Teclado
```
F4 → F5 → F6 → F7 → Ctrl+Q (repetir)
```

---

## ❓ Preguntas Frecuentes

### ¿Por qué F4 no funciona pero las demás sí?

**Posibles causas:**
- F4 está asignada a otra aplicación (Discord, OBS, etc.)
- F4 en algunos laptops requiere presionar Fn+F4
- Permisos insuficientes (Windows)

**Soluciones:**
1. Cierra otras aplicaciones
2. Cambia la hotkey a otra tecla (F8, F9, etc.)
3. Ejecuta como administrador

### ¿Puedo usar Alt+Tecla en lugar de F-keys?

Sí, edita `config/settings.yaml`:
```yaml
hotkeys:
  capture_area: alt+a
  capture_screen: alt+c
  extract_cedulas: alt+e
  start_processing: alt+s
  next_record: ctrl+q
  pause: alt+p
```

### ¿Las hotkeys funcionan en segundo plano?

Sí, son **hotkeys globales**. Funcionan incluso si la ventana de la app está minimizada.

**Precaución:** Asegúrate de pausar (F3) si no quieres que Ctrl+Q procese accidentalmente.

---

## 🆘 Soporte

### Si las hotkeys siguen sin funcionar:

1. **Ejecuta el diagnóstico:**
   ```bash
   python scripts/test_hotkeys.py
   ```

2. **Revisa los logs:**
   ```bash
   type logs\app_*.log | findstr "hotkey"
   ```

3. **Ejecuta la app con mensajes de debug:**
   ```bash
   python main.py
   ```
   Busca en la consola:
   ```
   Registrando hotkeys...
     ✓ Ctrl+Q registrado
     ✓ F3 registrado
     ✓ F4 registrado
     ✓ F5 registrado
     ✓ F6 registrado
     ✓ F7 registrado
   ✅ Todas las hotkeys registradas correctamente
   ```

4. **Si ves errores:** Copia el mensaje de error completo y repórtalo.

---

**¡Disfruta del flujo de trabajo 100% con teclado!** ⚡
