# Solución a Problemas con Hotkeys y Velocidad de Digitación

## Problemas Identificados

### 1. ⚡ Velocidad de Digitación Lenta
**Síntoma:** Al presionar Ctrl+Q, la cédula se escribe muy lento
**Causa:** El intervalo entre teclas estaba configurado en `0.05` segundos (50ms)
**Solución:** Reducido a `0.01` segundos (10ms) → **5x más rápido**

**Archivo modificado:** [config/settings.yaml](config/settings.yaml#L4)
```yaml
automation:
  typing_interval: 0.01  # Antes: 0.05
```

**Impacto:**
- Cédula de 10 dígitos:
  - **Antes:** 500ms (0.5 segundos)
  - **Ahora:** 100ms (0.1 segundos)
  - **Mejora:** 80% más rápido

---

### 2. 🎯 Campo de Búsqueda No Configurado
**Síntoma:** Las hotkeys no funcionan o el sistema no hace click en el campo
**Causa:** Las coordenadas del campo de búsqueda están en `null`
**Ubicación:** [config/settings.yaml](config/settings.yaml#L99-L100)

```yaml
search_field:
  x: null  # ← PROBLEMA: No configurado
  y: null  # ← PROBLEMA: No configurado
```

**Solución:**
1. Ejecuta la aplicación: `python main.py`
2. En el formulario web donde quieres buscar cédulas:
   - Posiciona el mouse EXACTAMENTE sobre el campo de búsqueda de cédulas
   - Anota las coordenadas X, Y
3. Edita `config/settings.yaml` y coloca las coordenadas:
   ```yaml
   search_field:
     x: 1234  # Reemplaza con tu coordenada X
     y: 567   # Reemplaza con tu coordenada Y
   ```

**Importante:** Sin estas coordenadas, el sistema NO puede hacer click automático en el campo.

---

### 3. ✅ Hotkeys Están Correctamente Configuradas
Las hotkeys están bien registradas en el código:
- **Ctrl+Q** → Procesar siguiente cédula (sin Alt+Tab)
- **F4** → Seleccionar área de captura
- **F3** → Pausar/Reanudar procesamiento

**Ubicación del código:** [src/presentation/controllers/main_controller.py](src/presentation/controllers/main_controller.py#L134-L136)

---

## 🧪 Cómo Probar que las Hotkeys Funcionan

### Opción 1: Script de Prueba Rápida
```bash
python scripts/test_hotkeys.py
```

Presiona las teclas y verifica que aparezcan mensajes:
- `Ctrl+Q` → "✅ Ctrl+Q detectado correctamente!"
- `F3` → "✅ F3 detectado correctamente!"
- `F4` → "✅ F4 detectado correctamente!"
- `ESC` → Sale del script

**Si las hotkeys NO funcionan en el script de prueba:**
- Windows: Ejecuta como administrador
- Verifica que no haya conflictos con otras aplicaciones (Discord, OBS, etc.)

---

### Opción 2: Aplicación Completa
```bash
python main.py
```

**Flujo de trabajo correcto:**

1. **Seleccionar Área (F4 o botón)**
   - Presiona F4
   - Arrastra para seleccionar el área con las cédulas
   - Suelta el mouse

2. **Capturar Pantalla (botón)**
   - Click en "Capturar Pantalla"
   - Espera 0.5s para que la ventana se oculte

3. **Extraer Cédulas (botón)**
   - Click en "Extraer Cédulas"
   - Espera a que el OCR procese la imagen

4. **Iniciar Procesamiento (botón)**
   - Click en "Iniciar Procesamiento"
   - **IMPORTANTE:** Enfoca manualmente la ventana del navegador/aplicación donde vas a escribir

5. **Procesar Cédulas**
   - **Opción A - Botón "Siguiente":** Hace Alt+Tab + escribe cédula
   - **Opción B - Ctrl+Q:** Solo escribe cédula (debes enfocar manualmente la ventana objetivo)

---

## 🔧 Configuración Completa Recomendada

### Configurar Coordenadas del Campo de Búsqueda

#### Método 1: Usar el Script de Detección de Coordenadas
```python
import pyautogui
import time

print("Posiciona el mouse sobre el campo de búsqueda de cédulas...")
print("Detectando en 3 segundos...")
time.sleep(3)

x, y = pyautogui.position()
print(f"\nCoordenadas detectadas:")
print(f"  x: {x}")
print(f"  y: {y}")
print(f"\nCopia estas coordenadas a config/settings.yaml en 'search_field'")
```

#### Método 2: Manual
1. Abre el navegador/aplicación donde buscas cédulas
2. Usa la extensión "Page Ruler" o herramientas del navegador (F12 → Elements)
3. Encuentra las coordenadas X, Y del campo de búsqueda
4. Añádelas a `config/settings.yaml`

---

## 📊 Comparación Antes vs Después

| Aspecto | Antes | Después | Mejora |
|---------|-------|---------|--------|
| **Velocidad de tipeo** | 50ms/tecla | 10ms/tecla | 5x más rápido |
| **Tiempo por cédula (10 dígitos)** | 0.5s | 0.1s | 80% más rápido |
| **Hotkeys funcionan** | Sí | Sí | - |
| **Click automático campo** | ❌ No configurado | ⚠️ Requiere configuración | - |

---

## 🚨 Solución de Problemas

### Problema: "Ctrl+Q no hace nada"
**Causas posibles:**
1. ✅ La sesión no está en estado `RUNNING`
   - **Solución:** Click en "Iniciar Procesamiento" primero

2. ✅ Throttling activo (presionaste Ctrl+Q muy rápido)
   - **Solución:** Espera 0.5 segundos entre pulsaciones

3. ✅ No hay cédulas extraídas
   - **Solución:** Click en "Extraer Cédulas" primero

### Problema: "F4 no abre el selector de área"
**Solución:**
- Windows: Ejecuta como administrador
- Verifica que no haya conflictos con otras apps

### Problema: "El sistema escribe en el lugar equivocado"
**Causa:** Coordenadas `search_field` mal configuradas o no configuradas
**Solución:**
1. Configura las coordenadas correctas (ver sección "Configurar Coordenadas")
2. O usa el botón "Siguiente" que hace Alt+Tab automático

### Problema: "El sistema no escribe nada"
**Causas posibles:**
1. La ventana objetivo no está enfocada
   - **Solución con Botón:** Usa el botón "Siguiente" (hace Alt+Tab)
   - **Solución con Ctrl+Q:** Enfoca manualmente la ventana objetivo antes de presionar

2. PyAutoGUI está bloqueado por antivirus
   - **Solución:** Añade excepción en el antivirus

---

## 📝 Resumen de Cambios Realizados

### Archivos Modificados
1. ✅ [config/settings.yaml](config/settings.yaml#L4)
   - `typing_interval: 0.05` → `0.01`

### Archivos Creados
1. ✅ [scripts/test_hotkeys.py](scripts/test_hotkeys.py) - Script de prueba de hotkeys
2. ✅ [SOLUCION_HOTKEYS.md](SOLUCION_HOTKEYS.md) - Este documento

### Archivos Que Requieren Configuración Manual
1. ⚠️ [config/settings.yaml](config/settings.yaml#L99-L100)
   - `search_field.x` y `search_field.y` → Debes configurar con las coordenadas de tu pantalla

---

## 🎯 Próximos Pasos

1. **Probar las hotkeys:**
   ```bash
   python scripts/test_hotkeys.py
   ```

2. **Configurar coordenadas del campo:**
   - Usa el método descrito arriba
   - Edita `config/settings.yaml`

3. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

4. **Probar el flujo completo:**
   - F4 → Seleccionar área
   - Capturar → Click botón
   - Extraer → Click botón
   - Iniciar → Click botón
   - Ctrl+Q → Procesar siguiente (repite)

---

## ℹ️ Información Adicional

### Diferencia entre Botón "Siguiente" y Ctrl+Q

| Característica | Botón "Siguiente" | Ctrl+Q |
|----------------|------------------|--------|
| **Alt+Tab automático** | ✅ Sí | ❌ No |
| **Click en campo** | ✅ Sí (si configurado) | ✅ Sí (si configurado) |
| **Escribe cédula** | ✅ Sí | ✅ Sí |
| **Presiona Enter** | ✅ Sí | ✅ Sí |
| **Requiere enfocar ventana** | ❌ No | ✅ Sí (manual) |
| **Velocidad** | Normal | **5x más rápido** (ahora) |

**Recomendación:**
- Usa **Ctrl+Q** para máxima velocidad (después de configurar coordenadas)
- Usa **Botón** si prefieres que el sistema cambie de ventana automáticamente

---

**¿Preguntas o problemas?** Revisa la sección "Solución de Problemas" arriba o contacta al equipo de desarrollo.
