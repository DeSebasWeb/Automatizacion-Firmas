# Consejos para Maximizar Precisión del OCR

Guía práctica para obtener la máxima precisión en la detección de cédulas con Google Cloud Vision API.

## Tabla de Contenidos

1. [Factores que Afectan la Precisión](#factores-que-afectan-la-precisión)
2. [Configuración Óptima](#configuración-óptima)
3. [Mejores Prácticas de Captura](#mejores-prácticas-de-captura)
4. [Solución de Problemas Comunes](#solución-de-problemas-comunes)
5. [Casos Especiales](#casos-especiales)
6. [Depuración y Diagnóstico](#depuración-y-diagnóstico)

---

## Factores que Afectan la Precisión

### 1. Calidad de la Imagen Original

| Factor | Impacto | Recomendación |
|--------|---------|---------------|
| **Resolución** | ALTO | Capturar a resolución nativa, evitar zoom |
| **Iluminación** | ALTO | Pantalla con brillo alto, sin reflejos |
| **Contraste** | MEDIO | Fondo claro, texto oscuro (o viceversa) |
| **Nitidez** | MEDIO | Sin motion blur, enfoque correcto |
| **Ruido** | BAJO | Pantalla limpia, sin artefactos |

### 2. Configuración del Preprocesamiento

| Parámetro | Impacto | Valor Óptimo |
|-----------|---------|--------------|
| `upscale_factor` | **CRÍTICO** | **3** (mínimo 2) |
| `denoise.enabled` | ALTO | **true** |
| `contrast.enabled` | ALTO | **true** |
| `sharpen.enabled` | MEDIO | **true** |
| `binarize.enabled` | MEDIO | **true** |
| `morphology.enabled` | BAJO | true |

### 3. Tipo de Escritura

| Tipo | Precisión Base | Mejoras Necesarias |
|------|----------------|-------------------|
| Impresa | 98-99% | Mínimas |
| Manuscrita clara | 90-95% | Upscaling 3x |
| Manuscrita descuidada | 70-85% | Upscaling 4x + ajustes |
| Mixta | 85-95% | Pipeline completo |

---

## Configuración Óptima

### Para Escritura Manual Clara

```yaml
image_preprocessing:
  enabled: true
  upscale_factor: 3

  denoise:
    enabled: true
    h: 10

  contrast:
    enabled: true
    clip_limit: 2.0

  sharpen:
    enabled: true

  binarize:
    enabled: true
    method: otsu

  morphology:
    enabled: true
    kernel_size: [2, 2]

  deskew:
    enabled: false
```

**Precisión esperada:** 95-98%

### Para Escritura Manual Descuidada

```yaml
image_preprocessing:
  enabled: true
  upscale_factor: 4  # Aumentar a 4x

  denoise:
    enabled: true
    h: 15  # Más agresivo

  contrast:
    enabled: true
    clip_limit: 3.0  # Mayor contraste

  sharpen:
    enabled: true

  binarize:
    enabled: true
    method: adaptive  # Cambiar a adaptive

  morphology:
    enabled: true
    kernel_size: [3, 3]  # Kernel más grande

  deskew:
    enabled: true  # Activar si está inclinada
```

**Precisión esperada:** 85-92%

### Para Texto Impreso

```yaml
image_preprocessing:
  enabled: true
  upscale_factor: 2  # Suficiente con 2x

  denoise:
    enabled: false  # No necesario

  contrast:
    enabled: true
    clip_limit: 1.5

  sharpen:
    enabled: false  # Ya está nítido

  binarize:
    enabled: true
    method: otsu

  morphology:
    enabled: false  # No necesario

  deskew:
    enabled: false
```

**Precisión esperada:** 98-99%

---

## Mejores Prácticas de Captura

### 1. Configuración de Pantalla

**✓ Hacer:**
- Aumentar brillo de pantalla al máximo
- Usar modo de alto contraste si está disponible
- Desactivar modo nocturno/filtro azul
- Maximizar ventana del navegador
- Zoom al 100% (evitar zoom digital)

**✗ Evitar:**
- Brillo bajo
- Modo nocturno activo
- Pantalla sucia o rayada
- Reflejos de luces externas

### 2. Selección del Área

**✓ Hacer:**
- Capturar SOLO la columna de cédulas
- Incluir un pequeño margen (5-10 px)
- Asegurar que números están centrados
- Capturar área rectangular uniforme

**✗ Evitar:**
- Incluir bordes de ventana
- Incluir columnas innecesarias
- Área muy pequeña (< 200 px)
- Área muy grande (> 2000 px)

### 3. Condiciones Ambientales

**Óptimas:**
- Luz natural indirecta o luz artificial uniforme
- Sin reflejos en la pantalla
- Pantalla perpendicular a la vista
- Sin movimiento durante la captura

---

## Solución de Problemas Comunes

### Problema 1: Confunde 1 con 7

**Síntomas:**
- Cédulas con "1" se detectan como "7"
- O viceversa

**Diagnóstico:**
```yaml
# Verificar configuración actual
image_preprocessing:
  upscale_factor: ?  # ¿Cuál es el valor?
```

**Soluciones en orden de prioridad:**

1. **Aumentar upscaling** (CRÍTICO):
   ```yaml
   upscale_factor: 4  # Probar con 4x
   ```

2. **Activar guardado de imágenes**:
   ```yaml
   save_processed_images: true
   ```
   - Revisar `temp/processed/processed_*.png`
   - Verificar que "1" y "7" se distinguen visualmente

3. **Aumentar sharpening** (agregar configuración custom):
   ```python
   # En enhancer.py, aumentar kernel de sharpening
   kernel = np.array([[0, -2, 0], [-2, 9, -2], [0, -2, 0]])
   ```

4. **Capturar área más grande**:
   - Seleccionar área con más píxeles por número
   - Mínimo 20-30 px de altura por línea

### Problema 2: No Detecta Algunos Números

**Síntomas:**
- Algunas cédulas no aparecen en la lista
- Lista incompleta

**Diagnóstico:**
1. Verificar imagen procesada
2. Revisar logs de Google Vision

**Soluciones:**

1. **Aumentar contraste**:
   ```yaml
   contrast:
     clip_limit: 3.0  # Aumentar de 2.0 a 3.0
   ```

2. **Cambiar método de binarización**:
   ```yaml
   binarize:
     method: adaptive  # Cambiar de otsu a adaptive
   ```

3. **Reducir ruido más agresivamente**:
   ```yaml
   denoise:
     h: 15  # Aumentar de 10 a 15
   ```

### Problema 3: Detecta Números Incorrectos

**Síntomas:**
- Detecta números que no existen
- Detecta bordes o artefactos como números

**Soluciones:**

1. **Activar operaciones morfológicas**:
   ```yaml
   morphology:
     enabled: true
     kernel_size: [3, 3]  # Kernel más grande
   ```

2. **Reducir el área de captura**:
   - Capturar SOLO la columna de cédulas
   - Evitar incluir bordes de tabla

3. **Ajustar reducción de ruido**:
   ```yaml
   denoise:
     enabled: true
     h: 12  # Aumentar ligeramente
   ```

### Problema 4: Números Borrosos en Imagen Procesada

**Síntomas:**
- Al revisar `processed_*.png`, números se ven borrosos
- Menos legible que original

**Soluciones:**

1. **Reducir reducción de ruido**:
   ```yaml
   denoise:
     h: 7  # Reducir de 10 a 7
   ```

2. **Desactivar binarización temporalmente**:
   ```yaml
   binarize:
     enabled: false  # Probar sin binarización
   ```

3. **Verificar que imagen original es buena**:
   - Revisar `original_*.png`
   - Si original ya está borrosa, mejorar captura

---

## Casos Especiales

### Números Muy Pequeños (< 15 px de altura)

**Configuración especial:**
```yaml
image_preprocessing:
  upscale_factor: 5  # Aumentar a 5x
  denoise:
    enabled: false  # Desactivar para no perder detalle
  sharpen:
    enabled: true
```

### Imágenes con Fondo Oscuro

**Configuración especial:**
```yaml
image_preprocessing:
  enabled: true
  upscale_factor: 3
  contrast:
    enabled: true
    clip_limit: 4.0  # Mayor contraste
  binarize:
    enabled: true
    method: adaptive  # Mejor para fondos irregulares
```

### Escritura Inclinada

**Configuración especial:**
```yaml
image_preprocessing:
  enabled: true
  deskew:
    enabled: true  # Activar corrección de inclinación
  upscale_factor: 3
```

### Múltiples Fuentes de Escritura en la Misma Imagen

**Estrategia:**
- Usar configuración balanceada
- No optimizar para un solo tipo

```yaml
image_preprocessing:
  upscale_factor: 3
  denoise:
    enabled: true
    h: 10
  contrast:
    enabled: true
    clip_limit: 2.5
  binarize:
    method: otsu  # Otsu es más general
```

---

## Depuración y Diagnóstico

### 1. Activar Guardado de Imágenes

```yaml
image_preprocessing:
  save_processed_images: true
  output_dir: temp/processed
```

**Ubicación de imágenes:**
- Original: `temp/processed/original_YYYYMMDD_HHMMSS.png`
- Procesada: `temp/processed/processed_YYYYMMDD_HHMMSS.png`

### 2. Analizar Métricas de Calidad

Revisar la salida del preprocesador:

```
RESUMEN DE MEJORAS
------------------------------------------------------------------
Mejoras de calidad:
  sharpness      : ↑ +130.5%  # Debe aumentar
  contrast       : ↑ +45.2%   # Debe aumentar
  brightness     : ↓ -12.3%   # Puede variar
  noise_level    : ↓ -65.8%   # Debe disminuir
```

**Métricas ideales:**
- Sharpness: +100% a +200%
- Contrast: +30% a +60%
- Noise Level: -50% a -80%

### 3. Revisar Logs de Google Vision

```python
# En google_vision_adapter.py, revisar:
print(f"DEBUG Google Vision: Texto completo detectado:\n{full_text}")
```

**Verificar:**
- ¿Google Vision detecta el texto?
- ¿El texto es correcto pero no se parsea bien?
- ¿Hay caracteres extraños?

### 4. Probar con Diferentes Configuraciones

**Matriz de pruebas:**

| Prueba | Upscaling | Denoise | Binarize | Resultado |
|--------|-----------|---------|----------|-----------|
| 1 | 2x | Sí | otsu | Baseline |
| 2 | 3x | Sí | otsu | +15% |
| 3 | 4x | Sí | otsu | +20% |
| 4 | 3x | No | otsu | +10% |
| 5 | 3x | Sí | adaptive | +12% |

---

## Checklist de Optimización

### Antes de Capturar

- [ ] Brillo de pantalla al máximo
- [ ] Modo nocturno desactivado
- [ ] Pantalla limpia
- [ ] Sin reflejos
- [ ] Zoom al 100%

### Durante la Captura

- [ ] Área seleccionada solo incluye cédulas
- [ ] Área rectangular uniforme
- [ ] Margen pequeño (5-10 px)
- [ ] Sin movimiento del mouse

### Después de Capturar

- [ ] Revisar imagen capturada
- [ ] Verificar que números son legibles
- [ ] Si no, reconfigurar área y repetir

### Configuración del Preprocesamiento

- [ ] `upscale_factor` ≥ 3
- [ ] `denoise.enabled` = true
- [ ] `contrast.enabled` = true
- [ ] `sharpen.enabled` = true
- [ ] `binarize.enabled` = true

### Si la Precisión es < 90%

- [ ] Activar `save_processed_images`
- [ ] Revisar imágenes guardadas
- [ ] Comparar original vs procesada
- [ ] Ajustar parámetros según análisis
- [ ] Probar con `upscale_factor: 4`

---

## Recursos Adicionales

- [IMAGE_PREPROCESSING.md](IMAGE_PREPROCESSING.md) - Detalles técnicos del pipeline
- [GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md) - Configuración de Google Cloud
- [COST_ANALYSIS.md](COST_ANALYSIS.md) - Análisis de costos

---

**Última actualización:** 2025-11-18
