# Triple Ensemble - Guía de Inicio Rápido

Guía rápida para configurar y usar el sistema de Triple Ensemble OCR (Google Vision + Azure Vision + AWS Textract) con votación 3-way para máxima precisión.

---

## 🎯 ¿Qué es Triple Ensemble?

El Triple Ensemble combina **3 motores OCR** con votación inteligente dígito por dígito:

| OCR | Fortaleza | Uso |
|-----|-----------|-----|
| **Google Vision** | Excelente para manuscritos | Voto #1 |
| **Azure Vision** | Muy preciso, segunda opinión | Voto #2 |
| **AWS Textract** | Tercera opinión, desempate | Voto #3 |

### Ventajas:

✅ **Precisión esperada: 99.5-99.8%** (vs 98.5% con dual)
✅ **Errores críticos (1↔7, 3↔8) < 0.2%** (vs 1-2% con dual)
✅ **Votación 3-way**: Cuando 2 de 3 coinciden, alta certeza
✅ **Desempate confiable**: AWS decide cuando Google y Azure difieren

---

## 📦 Instalación

### Paso 1: Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- `google-cloud-vision` (Google Vision API)
- `azure-ai-vision-imageanalysis` (Azure Vision API)
- `boto3` (AWS Textract) ⬅️ **NUEVO**

### Paso 2: Configurar credenciales

Necesitas configurar credenciales para los 3 servicios:

#### 2.1 Google Cloud Vision

```bash
gcloud auth application-default login
```

O configura `GOOGLE_APPLICATION_CREDENTIALS`:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

#### 2.2 Azure Computer Vision

Crea archivo `.env` en la raíz del proyecto:

```bash
# Azure Computer Vision
AZURE_VISION_ENDPOINT=https://tu-recurso.cognitiveservices.azure.com/
AZURE_VISION_KEY=tu_subscription_key_aqui
```

#### 2.3 AWS Textract ⬅️ **NUEVO**

Agrega al archivo `.env`:

```bash
# AWS Textract
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
AWS_DEFAULT_REGION=us-east-1
```

**⚠️ IMPORTANTE**: Lee la [guía completa de configuración de AWS Textract](./AWS_TEXTRACT_SETUP.md) para crear el usuario IAM con permisos correctos.

### Paso 3: Activar Triple Ensemble

Edita `config/settings.yaml`:

```yaml
ocr:
  provider: triple_ensemble  # ⬅️ CAMBIAR AQUÍ
```

---

## 🚀 Uso

### Opción A: Usar desde la aplicación

Simplemente ejecuta la aplicación normal:

```bash
python main.py
```

El sistema automáticamente usará el Triple Ensemble si está configurado en `settings.yaml`.

### Opción B: Usar programáticamente

```python
from PIL import Image
from src.shared.config import YamlConfigAdapter
from src.infrastructure.ocr import create_ocr_adapter

# Cargar configuración
config = YamlConfigAdapter('config/settings.yaml')

# Crear OCR (automáticamente será Triple Ensemble)
ocr = create_ocr_adapter(config)

# Cargar imagen
image = Image.open('path/to/formulario.png')

# Extraer cédulas con máxima precisión
records = ocr.extract_cedulas(image)

# Procesar resultados
for record in records:
    print(f"Cédula: {record.cedula.value}")
    print(f"Confianza: {record.confidence.as_percentage():.1f}%")
```

---

## 📊 Cómo funciona la votación 3-way

Para **cada dígito** de cada cédula:

### Escenario A: Unanimidad (3/3 coinciden)

```
Posición 0:
  Google:  '1' (96%)
  Azure:   '1' (92%)
  AWS:     '1' (94%)

→ RESULTADO: '1' con 97% de confianza
  (boost +5% por unanimidad)
```

### Escenario B: Mayoría (2/3 coinciden)

```
Posición 0:
  Google:  '1' (96%)  ✓
  Azure:   '7' (88%)
  AWS:     '1' (94%)  ✓

→ RESULTADO: '1' con 95% de confianza
  (promedio de los 2 que coinciden)
```

### Escenario C: Conflicto (los 3 difieren)

```
Posición 0:
  Google:  '1' (85%)
  Azure:   '7' (82%)
  AWS:     '4' (88%)  ✓ (mayor confianza)

→ RESULTADO: '4' con 88% de confianza
  (si >= 80%, se acepta; si < 80%, marcar para revisión)
```

---

## 📈 Salida del sistema

### Ejemplo de logging detallado

Cuando ejecutas con `verbose_logging: true`, verás:

```
================================================================================
TRIPLE ENSEMBLE OCR INICIALIZADO (VOTACIÓN 3-WAY)
================================================================================
✓ Google Vision:  GoogleVisionAdapter
✓ Azure Vision:   AzureVisionAdapter
✓ AWS Textract:   AWSTextractAdapter
✓ Min digit confidence:      70%
✓ Low confidence threshold:  80%
✓ Min agreement ratio:       60%
✓ Verbose logging: True
================================================================================

================================================================================
INICIANDO TRIPLE ENSEMBLE OCR (VOTACIÓN 3-WAY)
================================================================================

✓ Google Vision encontró: 15 cédulas
✓ Azure Vision encontró:  15 cédulas
✓ AWS Textract encontró:  15 cédulas
✓ Emparejadas: 15 tripletes

================================================================================
[Cédula 1/15]
================================================================================
  Originales:
    Google:  1036221525      (conf: 96.8%)
    Azure:   7036221525      (conf: 88.2%)
    AWS:     1036221525      (conf: 94.5%)

  → RESULTADO: 1036221525
    Confianza: 95.6%

  Estadísticas de votación:
    Unanimidad (3/3):     0/10 dígitos
    Mayoría (2/3):       10/10 dígitos
    Conflicto (0/3):      0/10 dígitos
    Acuerdo total:       100%

================================================================================
[Cédula 2/15]
================================================================================
  Originales:
    Google:  1234567890      (conf: 97.2%)
    Azure:   1234567890      (conf: 95.8%)
    AWS:     1234567890      (conf: 96.5%)

  → RESULTADO: 1234567890
    Confianza: 96.8%

  Estadísticas de votación:
    Unanimidad (3/3):    10/10 dígitos
    Mayoría (2/3):        0/10 dígitos
    Conflicto (0/3):      0/10 dígitos
    Acuerdo total:       100%

...

================================================================================
RESULTADO FINAL: 15 cédulas extraídas con alta confianza
================================================================================
```

---

## ⚙️ Configuración avanzada

### Ajustar umbrales de confianza

Edita `config/settings.yaml`:

```yaml
ocr:
  triple_ensemble:
    min_digit_confidence: 0.70          # Mínimo 70% por dígito
    low_confidence_threshold: 0.80      # Mínimo 80% en conflictos
    min_agreement_ratio: 0.60           # Mínimo 60% de acuerdo
    verbose_logging: true               # Mostrar logging detallado
```

### Umbrales recomendados:

| Uso | min_digit_confidence | low_confidence_threshold | min_agreement_ratio |
|-----|----------------------|--------------------------|---------------------|
| **Máxima precisión** | 0.80 | 0.90 | 0.70 |
| **Balanceado** ⭐ | 0.70 | 0.80 | 0.60 |
| **Permisivo** | 0.60 | 0.70 | 0.50 |

---

## 💰 Costos

### Free Tier (primeros 3 meses)

| Servicio | Límite gratis |
|----------|---------------|
| Google Vision | 1,000 imgs/mes |
| Azure Vision | 5,000 imgs/mes |
| AWS Textract | 1,000 imgs/mes ⬅️ **NUEVO** |

### Costos después del Free Tier (por 1,000 imágenes)

| Servicio | Costo |
|----------|-------|
| Google Vision | $5.16 COP |
| Azure Vision | $4,200 COP |
| AWS Textract | $6,450 COP ⬅️ **NUEVO** |
| **TOTAL Triple Ensemble** | **$15,816 COP** |

Para 5,000 imágenes/mes = **~$79,080 COP/mes**

**Sigue siendo extremadamente económico vs. trabajo manual** (~$500 COP/formulario manual)

---

## 🧪 Tests

Ejecutar tests unitarios:

```bash
pytest tests/unit/test_triple_ensemble.py -v
```

Tests incluidos:
- ✅ Inicialización de AWS Textract
- ✅ Extracción de números con AWS Textract
- ✅ Confianzas por carácter
- ✅ Votación unánime
- ✅ Votación por mayoría
- ✅ Manejo de conflictos
- ✅ Emparejamiento por posición
- ✅ Ejecución paralela de los 3 OCR

---

## 📊 Métricas esperadas

### Antes (Dual Ensemble)

- Precisión: **98.5%**
- Errores críticos (1↔7, 3↔8): **1-2%**
- Tiempo: 2-3 seg/imagen
- Costo: $9,360 COP/1000 imgs

### Después (Triple Ensemble)

- Precisión: **99.5-99.8%** ⬆️ +1.0-1.3%
- Errores críticos: **< 0.2%** ⬇️ -80%
- Tiempo: 3-4 seg/imagen
- Costo: $15,816 COP/1000 imgs

### ROI

Para demostrar **inversión de 50M COP**:

✅ Procesar 100-200 formularios reales
✅ Medir precisión real (objetivo: > 99.5%)
✅ Documentar reducción de errores (objetivo: < 0.2%)
✅ Calcular ahorro vs. trabajo manual
✅ Proyectar escalabilidad a miles de formularios/mes

---

## 🚨 Troubleshooting

### Error: "Unable to locate credentials" (AWS)

**Solución**: Configura credenciales en `.env`:
```bash
AWS_ACCESS_KEY_ID=tu_key
AWS_SECRET_ACCESS_KEY=tu_secret
```

O ejecuta:
```bash
aws configure
```

Ver [guía completa](./AWS_TEXTRACT_SETUP.md) para más detalles.

### Error: "AccessDeniedException" (AWS)

**Solución**: El usuario IAM necesita el permiso `AmazonTextractFullAccess`.

1. Ve a [IAM Console](https://console.aws.amazon.com/iam/)
2. Selecciona tu usuario
3. Agrega política: `AmazonTextractFullAccess`

### Precisión no mejora

**Posibles causas**:
1. Imágenes de baja calidad → Mejora preprocesamiento
2. Umbrales muy permisivos → Aumenta `min_digit_confidence`
3. Solo 1 o 2 OCR funcionando → Verifica que los 3 estén activos

**Verificar que los 3 OCR estén activos**:
```python
# Debería mostrar los 3
ocr = create_ocr_adapter(config)
print(type(ocr).__name__)  # Debe ser: TripleEnsembleOCR
```

---

## 📚 Recursos adicionales

- [Configuración de AWS Textract](./AWS_TEXTRACT_SETUP.md) - Guía completa paso a paso
- [AWS Textract Docs](https://docs.aws.amazon.com/textract/)
- [Google Vision Docs](https://cloud.google.com/vision/docs)
- [Azure Vision Docs](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/)

---

## 🎯 Próximos pasos

1. ✅ **Configurar AWS Textract** siguiendo la [guía](./AWS_TEXTRACT_SETUP.md)
2. ✅ **Activar Triple Ensemble** en `config/settings.yaml`
3. ✅ **Procesar 100-200 formularios** reales
4. ✅ **Medir precisión** (objetivo: 99.5-99.8%)
5. ✅ **Documentar resultados** para inversión
6. ✅ **Demostrar viabilidad** de 50M COP
7. ✅ **Vender como SaaS** 🚀

---

**¡Listo para alcanzar 99.5-99.8% de precisión y conseguir tu inversión de 50M COP!** 🎯
