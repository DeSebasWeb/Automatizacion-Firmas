# Preprocesamiento para Google Vision API

**Fecha:** 2025-11-18
**Estrategia:** Pipeline CONSERVADOR que NO destruye información

---

## 🎯 Principio Fundamental

**Google Vision API es INTELIGENTE y necesita MENOS preprocesamiento que Tesseract.**

### ❌ ERROR COMÚN: Preprocesamiento Agresivo

Aplicar técnicas agresivas como:
- Binarización (blanco y negro puro)
- Operaciones morfológicas (close/open)
- Normalización agresiva de iluminación
- Sharpening ultra fuerte

**DESTRUYE información** en lugar de mejorarla para Google Vision.

### ✅ ESTRATEGIA CORRECTA: Preprocesamiento Conservador

1. **Aumentar resolución** (upscaling)
2. **Reducir ruido suavemente**
3. **Mejorar contraste moderadamente**
4. **Mantener escala de grises/color**
5. **NO binarizar**
6. **NO morfología**

---

## 📊 Comparación: Tesseract vs Google Vision

| Técnica | Tesseract (OCR local) | Google Vision (Cloud) |
|---------|----------------------|----------------------|
| **Binarización** | ✅ Necesaria | ❌ Perjudicial |
| **Morfología** | ✅ Ayuda | ❌ Destruye información |
| **Upscaling** | ✅ Crítico | ✅ Ayuda moderadamente |
| **Denoise** | ⚠️ Moderado | ✅ Suave |
| **Contraste** | ✅ Fuerte (CLAHE 3-4) | ✅ Moderado (CLAHE 2-2.5) |
| **Sharpening** | ✅ Agresivo | ⚠️ Suave |
| **Escala grises** | ✅ Requerido | ✅ Preferido (o RGB) |
| **Color** | ❌ No funciona | ✅ Funciona bien |

---

## ✅ Pipeline Óptimo para Google Vision

### Configuración Recomendada

```yaml
image_preprocessing:
  enabled: true
  upscale_factor: 3  # 3x es suficiente

  # Reducción de ruido SUAVE
  denoise:
    enabled: true
    h: 8  # No más de 10

  # Contraste MODERADO
  contrast:
    enabled: true
    clip_limit: 2.5  # No más de 3.0

  # Sharpening SUAVE
  sharpen:
    enabled: true
    intensity: normal  # NO usar 'high' o 'ultra'
    use_unsharp_mask: false

  # CRÍTICO: Estas deben estar DESACTIVADAS
  binarize:
    enabled: false  # ⚠️ NUNCA activar

  morphology:
    enabled: false  # ⚠️ NUNCA activar

  normalize_illumination:
    enabled: false  # ⚠️ Puede crear artefactos

  enhance_edges:
    enabled: false  # Google Vision ya detecta bordes
```

---

## 🔬 ¿Por qué NO Binarizar?

### Binarización (Blanco y Negro Puro)

**Ejemplo:**
```
Original (escala de grises):    Binarizado:
  180  185  190  195              255  255  255  255
  175  180  185  190     →        255  255  255  255
  170  175  180  185              0    0    255  255
  165  170  175  180              0    0    0    255
```

**Problema:**
- ❌ Pierde sutilezas de trazos (grosor, intensidad)
- ❌ Puede cerrar el "3" haciéndolo parecer "8"
- ❌ Puede abrir el "8" haciéndolo parecer "3"
- ❌ Elimina información de presión del trazo
- ❌ Google Vision usa IA que aprovecha matices de gris

**Google Vision prefiere:**
- ✅ Escala de grises con 256 niveles
- ✅ Información de intensidad de píxeles
- ✅ Gradientes suaves entre trazos y fondo

---

## 🔬 ¿Por qué NO Morfología?

### Operaciones Morfológicas (Close/Open)

**Cierre (Close):**
```
Antes:              Después:
  ┌──┐               ┌──┐
  └──┤  ← Hueco      └──┘  ← Hueco cerrado
```

**Problema con el "3":**
- ❌ Puede cerrar las aperturas del "3"
- ❌ El "3" se convierte en "8"
- ❌ Pierde la característica distintiva (abierto vs cerrado)

**Apertura (Open):**
```
Antes:              Después:
  ┌──┐               ┌  ┐
  │  │  ← Cerrado    │  │  ← Se abre
```

**Problema con el "8":**
- ❌ Puede abrir los bucles del "8"
- ❌ El "8" se convierte en "3" o "B"
- ❌ Elimina trazos finos

---

## 📈 Casos de Uso por Nivel de Dificultad

### 1. Escritura Manual Clara y Legible

**Configuración MÍNIMA:**
```yaml
image_preprocessing:
  enabled: true
  upscale_factor: 2  # 2x suficiente

  denoise:
    enabled: false  # No necesario

  contrast:
    enabled: true
    clip_limit: 2.0

  sharpen:
    enabled: false  # No necesario

  # Todo lo demás: false
```

**Resultado esperado:** 98-99% precisión

---

### 2. Escritura Manual Estándar (Caso General)

**Configuración MODERADA (RECOMENDADA):**
```yaml
image_preprocessing:
  enabled: true
  upscale_factor: 3  # 3x para mejor resolución

  denoise:
    enabled: true
    h: 8  # Suave

  contrast:
    enabled: true
    clip_limit: 2.5  # Moderado

  sharpen:
    enabled: true
    intensity: normal

  # binarize, morphology, enhance_edges: false
```

**Resultado esperado:** 96-98% precisión

---

### 3. Escritura Manual Descuidada o con Ruido

**Configuración MEJORADA:**
```yaml
image_preprocessing:
  enabled: true
  upscale_factor: 3  # No más de 4x

  denoise:
    enabled: true
    h: 10  # Más agresivo

  contrast:
    enabled: true
    clip_limit: 3.0  # Más fuerte

  sharpen:
    enabled: true
    intensity: normal  # Mantener normal

  # binarize, morphology: SIEMPRE false
```

**Resultado esperado:** 94-96% precisión

---

## 🚨 Configuraciones PROHIBIDAS

### ❌ NO hacer esto:

```yaml
# ESTO DESTRUYE INFORMACIÓN
binarize:
  enabled: true  # ❌ NUNCA

morphology:
  enabled: true  # ❌ NUNCA

enhance_edges:
  enabled: true  # ❌ No necesario para Google Vision

sharpen:
  intensity: ultra  # ❌ Demasiado agresivo

denoise:
  h: 15  # ❌ Elimina detalles importantes

upscale_factor: 5  # ❌ Degradación por sobreescalado
```

---

## 🧪 Cómo Validar el Preprocesamiento

### 1. Activar guardado de imágenes

```yaml
image_preprocessing:
  save_processed_images: true
  output_dir: temp/processed
```

### 2. Procesar una imagen

Ejecutar la aplicación y capturar una imagen.

### 3. Comparar original vs procesada

Revisar `temp/processed/`:
- `original_YYYYMMDD_HHMMSS.png`
- `processed_YYYYMMDD_HHMMSS.png`

### 4. Verificar que NO se pierde información

**Buscar en imagen procesada:**

✅ **Debe tener:**
- Números claramente visibles
- Trazos del "3" ABIERTOS a un lado
- Trazos del "8" CERRADOS en ambos lados
- Detalles finos preservados
- Sin bloques sólidos negros donde antes había texto

❌ **NO debe tener:**
- Números desaparecidos o ilegibles
- Todo blanco y negro puro (debe tener grises)
- Trazos destruidos o unidos incorrectamente
- Artefactos extraños
- Pérdida de información visible

---

## 📊 Mejora Esperada con Pipeline Conservador

| Métrica | Sin Preprocesamiento | Con Pipeline Conservador |
|---------|---------------------|-------------------------|
| **Precisión general** | 93-95% | 96-98% |
| **Confusión 3 vs 8** | 8-12% | 2-4% |
| **Confusión 1 vs 7** | 5-8% | 1-3% |
| **Cédulas extraídas** | 13-14 de 15 | 14-15 de 15 |
| **Tiempo procesamiento** | ~50 ms | ~400 ms |

---

## 🔧 Ajuste Fino por Problema

### Problema: Confunde 3 con 8

**Solución:**
```yaml
upscale_factor: 4  # Aumentar resolución
contrast:
  clip_limit: 3.0  # Más contraste
sharpen:
  enabled: true
  intensity: normal  # Mantener normal, NO high
```

**NO hacer:**
- ❌ Activar binarización
- ❌ Activar morfología
- ❌ Usar sharpening ultra

---

### Problema: Confunde 1 con 7

**Solución:**
```yaml
upscale_factor: 4  # Crítico para ver la serifa del 7
denoise:
  h: 6  # Reducir para preservar detalles finos
sharpen:
  enabled: true
```

---

### Problema: No detecta algunos números

**Solución:**
```yaml
# REDUCIR preprocesamiento
upscale_factor: 2
denoise:
  enabled: false  # Desactivar
sharpen:
  enabled: false  # Desactivar

# Verificar que estén desactivados:
binarize:
  enabled: false
morphology:
  enabled: false
```

**Posible causa:**
- Preprocesamiento está eliminando números
- Reducir pasos de preprocesamiento

---

## 💡 Consejos Avanzados

### 1. Calidad de Captura Original

El preprocesamiento NO puede arreglar:
- ❌ Imagen extremadamente borrosa
- ❌ Desenfoque por movimiento
- ❌ Resolución original muy baja (< 150x150 px)
- ❌ Iluminación pésima (muy oscuro/claro)

**Mejor estrategia:** Mejorar la captura original

---

### 2. Upscaling Óptimo

```
Resolución original: 332x480 px
Upscaling 3x:        996x1440 px  ✅ ÓPTIMO

Upscaling 4x:        1328x1920 px ⚠️ OK, pero más lento
Upscaling 5x:        1660x2400 px ❌ Degradación por interpolación
```

**Regla:** No exceder 4x upscaling

---

### 3. Contraste Adaptativo (CLAHE)

```yaml
# Clip Limit: Cuánto puede aumentar el contraste
clip_limit: 2.0   # ✅ Conservador (recomendado)
clip_limit: 2.5   # ✅ Moderado (bueno)
clip_limit: 3.0   # ⚠️ Fuerte (solo casos difíciles)
clip_limit: 4.0   # ❌ Demasiado, crea artefactos
```

---

## 📝 Resumen Ejecutivo

### ✅ HACER:
1. Upscaling moderado (2-3x)
2. Reducción de ruido suave (h=6-8)
3. Contraste moderado (clip_limit=2.0-2.5)
4. Sharpening normal (opcional)
5. Mantener escala de grises o RGB
6. Probar con save_processed_images=true

### ❌ NO HACER:
1. **NUNCA** binarizar
2. **NUNCA** morfología
3. **NUNCA** normalización agresiva de iluminación
4. **NUNCA** sharpening ultra
5. **NUNCA** upscaling > 4x
6. **NUNCA** denoise h > 12

---

## 🚀 Configuración Final Recomendada

```yaml
image_preprocessing:
  enabled: true
  upscale_factor: 3

  denoise:
    enabled: true
    h: 8

  contrast:
    enabled: true
    clip_limit: 2.5

  sharpen:
    enabled: true
    intensity: normal
    use_unsharp_mask: false

  # CRÍTICO: Todo lo demás DESACTIVADO
  normalize_illumination:
    enabled: false
  enhance_edges:
    enabled: false
  binarize:
    enabled: false
  morphology:
    enabled: false
  deskew:
    enabled: false
```

**Resultado esperado:**
- ✅ 96-98% precisión general
- ✅ Confusión 3 vs 8: < 3%
- ✅ Confusión 1 vs 7: < 2%
- ✅ Extrae 14-15 de 15 cédulas
- ✅ Tiempo: ~400 ms (aceptable)

---

**Última actualización:** 2025-11-18
**Autor:** Juan Sebastian Lopez Hernandez
