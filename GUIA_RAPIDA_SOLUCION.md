# 🚀 Guía Rápida - Solución Aplicada

## ✅ Cambios Realizados

### 1. **Velocidad de Digitación Mejorada 5x**
- **Archivo:** `config/settings.yaml`
- **Cambio:** `typing_interval: 0.05` → `0.01`
- **Resultado:** Las cédulas se escriben **5 veces más rápido**

### 2. **Scripts de Diagnóstico Creados**

#### `scripts/test_hotkeys.py`
Prueba que las hotkeys funcionen correctamente.

**Ejecutar:**
```bash
python scripts/test_hotkeys.py
```

**Qué hace:**
- Detecta si Ctrl+Q, F3, F4 funcionan
- Te confirma con mensajes en consola
- Presiona ESC para salir

#### `scripts/configure_search_field.py`
Configura automáticamente las coordenadas del campo de búsqueda.

**Ejecutar:**
```bash
python scripts/configure_search_field.py
```

**Qué hace:**
1. Te da 3 segundos para posicionar el mouse sobre el campo de búsqueda
2. Detecta las coordenadas X, Y
3. Las guarda automáticamente en `config/settings.yaml`

---

## 🔧 Pasos para Solucionar Problemas

### Problema 1: "Ctrl+Q escribe muy lento"
✅ **SOLUCIONADO** - El intervalo de tipeo se redujo de 50ms a 10ms

### Problema 2: "Hotkeys no funcionan (F4, Ctrl+Q, etc.)"

**Paso 1: Verificar que las hotkeys se detectan**
```bash
python scripts/test_hotkeys.py
```

Si las hotkeys NO se detectan:
- **Windows:** Ejecuta el script como administrador
- Cierra aplicaciones que puedan tener conflictos (Discord, OBS, etc.)

Si las hotkeys SÍ se detectan pero no funcionan en la app:
- Ve al Paso 2

**Paso 2: Configurar coordenadas del campo de búsqueda**
```bash
python scripts/configure_search_field.py
```

1. Abre el navegador/aplicación donde buscas cédulas
2. Ejecuta el script
3. Posiciona el mouse sobre el campo de búsqueda
4. Espera 3 segundos
5. El script guardará las coordenadas automáticamente

**Verificar que se guardaron:**
```bash
# Verificar en Windows
type config\settings.yaml | findstr "search_field" -A 2

# Verificar en Linux/Mac
grep -A 2 "search_field" config/settings.yaml
```

Deberías ver algo como:
```yaml
search_field:
  x: 1234
  y: 567
```

Si ves `x: null` o `y: null`, repite el Paso 2.

### Problema 3: "Botón 'Iniciar Procesamiento' no funciona"

**Causa probable:** No hay cédulas extraídas

**Solución:**
1. Presiona F4 para seleccionar área
2. Click en "Capturar Pantalla"
3. Click en "Extraer Cédulas" (espera 2-3 segundos)
4. Ahora sí, click en "Iniciar Procesamiento"

---

## 📋 Flujo Completo Correcto

### 1. **Primera Vez - Configuración Inicial**

```bash
# Configurar coordenadas del campo de búsqueda
python scripts/configure_search_field.py
```

### 2. **Uso Normal - Cada Vez**

1. **Ejecutar aplicación:**
   ```bash
   python main.py
   ```

2. **Seleccionar área de captura:**
   - Presiona `F4` (o click en "Seleccionar Área")
   - Arrastra para seleccionar el área con las cédulas
   - Suelta el mouse

3. **Capturar pantalla:**
   - Click en "Capturar Pantalla"
   - Espera 0.5s

4. **Extraer cédulas con OCR:**
   - Click en "Extraer Cédulas"
   - Espera 2-3 segundos (procesamiento OCR)
   - Verás las cédulas en la lista

5. **Iniciar procesamiento:**
   - Click en "Iniciar Procesamiento"

6. **Procesar cédulas:**

   **Opción A - Usando Botón "Siguiente":**
   - Click en "Siguiente"
   - El sistema hace Alt+Tab automáticamente
   - Escribe la cédula
   - Presiona Enter
   - Repite para cada cédula

   **Opción B - Usando Ctrl+Q (MÁS RÁPIDO ⚡):**
   - Enfoca manualmente la ventana del navegador/app
   - Presiona `Ctrl+Q`
   - El sistema escribe la cédula (5x más rápido ahora)
   - Presiona Enter
   - Repite para cada cédula

---

## 🎯 Diferencias: Botón vs Ctrl+Q

| Característica | Botón "Siguiente" | Ctrl+Q |
|----------------|------------------|--------|
| Alt+Tab automático | ✅ Sí | ❌ No (debes enfocar manualmente) |
| Velocidad | Normal | **5x más rápido** |
| Requiere configuración | Sí (coordenadas) | Sí (coordenadas) |
| Mejor para | Comodidad | Velocidad máxima |

**Recomendación:** Usa `Ctrl+Q` para máxima velocidad una vez configurado.

---

## 🧪 Verificación Final

### Checklist de Configuración

- [ ] **Velocidad mejorada**: `config/settings.yaml` tiene `typing_interval: 0.01`
- [ ] **Hotkeys detectadas**: `python scripts/test_hotkeys.py` funciona
- [ ] **Coordenadas configuradas**: `config/settings.yaml` tiene `search_field.x` y `search_field.y` con valores numéricos (no `null`)
- [ ] **Aplicación ejecuta**: `python main.py` abre la ventana
- [ ] **Flujo completo funciona**: F4 → Capturar → Extraer → Iniciar → Ctrl+Q

---

## 📚 Documentación Completa

Para más detalles, consulta:
- **[SOLUCION_HOTKEYS.md](SOLUCION_HOTKEYS.md)** - Explicación técnica completa
- **[README.md](README.md)** - Documentación general del proyecto

---

## 🆘 ¿Problemas?

Si después de seguir esta guía aún tienes problemas:

1. **Revisa los logs:**
   ```bash
   # Ver últimas líneas del log de hoy
   type logs\app_*.log | findstr /C:"ERROR" /C:"WARNING"
   ```

2. **Ejecuta la aplicación en modo debug:**
   ```bash
   python main.py
   ```
   Y revisa los mensajes en la consola.

3. **Verifica que las dependencias estén instaladas:**
   ```bash
   pip install -r requirements.txt
   ```

---

**¡Listo!** Con estos cambios, Ctrl+Q debería funcionar **5 veces más rápido** y las hotkeys deberían estar operativas.
