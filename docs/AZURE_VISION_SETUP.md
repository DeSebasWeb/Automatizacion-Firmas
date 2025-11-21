# 🔵 Azure Computer Vision API - Guía de Configuración

**Versión:** Read API v4.0
**SDK:** azure-ai-vision-imageanalysis
**Última actualización:** 2025-11-20

---

## 📖 Índice

1. [¿Qué es Azure Computer Vision?](#qué-es-azure-computer-vision)
2. [Requisitos Previos](#requisitos-previos)
3. [Paso 1: Crear Cuenta Azure](#paso-1-crear-cuenta-azure)
4. [Paso 2: Crear Recurso Computer Vision](#paso-2-crear-recurso-computer-vision)
5. [Paso 3: Obtener Credenciales](#paso-3-obtener-credenciales)
6. [Paso 4: Configurar Variables de Entorno](#paso-4-configurar-variables-de-entorno)
7. [Paso 5: Instalar SDK](#paso-5-instalar-sdk)
8. [Paso 6: Verificar Instalación](#paso-6-verificar-instalación)
9. [Paso 7: Configurar en el Proyecto](#paso-7-configurar-en-el-proyecto)
10. [Troubleshooting](#troubleshooting)
11. [Costos y Límites](#costos-y-límites)
12. [Comparación con Google Vision](#comparación-con-google-vision)

---

## ¿Qué es Azure Computer Vision?

Azure Computer Vision es el servicio OCR de Microsoft, especializado en:

✅ **Read API v4.0** - Última versión optimizada para texto manuscrito
✅ **Alta precisión** - Comparable con Google Vision
✅ **Free Tier generoso** - 5,000 transacciones gratis/mes
✅ **Rápido** - Respuestas en 1-2 segundos
✅ **Confiable** - Infraestructura global de Microsoft Azure

### ¿Por qué Azure Vision?

1. **Alternativa a Google Vision** - Para comparar precisión
2. **Mejor precio** - Free tier más generoso (5,000 vs 1,000)
3. **Modo Ensemble** - Combinar ambos para máxima precisión (>99%)

---

## Requisitos Previos

Antes de comenzar, asegúrate de tener:

- [ ] **Cuenta Microsoft** (Hotmail, Outlook, o crear nueva)
- [ ] **Tarjeta de crédito/débito** (solo para verificación, no se cobra en free tier)
- [ ] **Python 3.10+** instalado
- [ ] **pip** actualizado (`python -m pip install --upgrade pip`)

---

## Paso 1: Crear Cuenta Azure

### 1.1 Crear Cuenta Gratuita

1. Ve a: https://azure.microsoft.com/es-mx/free/
2. Click en **"Empieza gratis"** o **"Start free"**
3. Inicia sesión con tu cuenta Microsoft (o crea una nueva)

### 1.2 Completar Registro

Te pedirá:

- **Información personal** (nombre, país, teléfono)
- **Verificación de identidad** (SMS o llamada)
- **Tarjeta de crédito** (SOLO para verificación, no se cobra)
- **Aceptar términos** de servicios

💡 **IMPORTANTE:** No te cobrarán mientras uses el free tier (5,000 transacciones/mes)

### 1.3 Acceder al Portal

Después del registro:

1. Ir a: https://portal.azure.com
2. Deberías ver el **Dashboard de Azure**

---

## Paso 2: Crear Recurso Computer Vision

### 2.1 Buscar Computer Vision

1. En el portal Azure, click en **"Crear un recurso"** (botón azul arriba a la izquierda)
2. En la barra de búsqueda, escribe: **"Computer Vision"**
3. Click en **"Computer Vision"** (de Microsoft)
4. Click en **"Crear"**

### 2.2 Configurar Recurso

Llena el formulario:

| Campo | Valor Recomendado |
|-------|-------------------|
| **Suscripción** | Azure subscription 1 (la que tienes) |
| **Grupo de recursos** | Crear nuevo: `firmas-automatizacion` |
| **Región** | `East US` o `West Europe` (más cercano) |
| **Nombre** | `firmas-ocr-vision` (debe ser único globalmente) |
| **Plan de tarifa** | **Free F0** (5,000 transacciones/mes gratis) |

**💰 CRÍTICO:** Asegúrate de seleccionar **"Free F0"** en el plan de tarifa.

### 2.3 Revisar y Crear

1. Click en **"Revisar y crear"**
2. Verificar que dice **"Free F0"** en el plan
3. Click en **"Crear"**
4. Espera 1-2 minutos (verás "Implementación en curso")
5. Cuando termine, click en **"Ir al recurso"**

---

## Paso 3: Obtener Credenciales

Una vez en el recurso:

### 3.1 Obtener Endpoint

1. En el menú izquierdo, click en **"Información general"** (Overview)
2. Busca **"Punto de conexión"** o **"Endpoint"**
3. Copia la URL completa, ejemplo:
   ```
   https://firmas-ocr-vision.cognitiveservices.azure.com/
   ```

### 3.2 Obtener Subscription Key

1. En el menú izquierdo, click en **"Claves y puntos de conexión"** (Keys and Endpoint)
2. Verás **dos claves** (KEY 1 y KEY 2)
3. Copia **KEY 1** (puedes usar cualquiera de las dos)
4. Ejemplo:
   ```
   a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```

⚠️ **IMPORTANTE:** Nunca compartas estas claves públicamente (son como contraseñas)

---

## Paso 4: Configurar Variables de Entorno

### 4.1 Crear archivo `.env`

En la raíz del proyecto, crea un archivo llamado `.env`:

```bash
# Azure Computer Vision API
AZURE_VISION_ENDPOINT=https://tu-recurso.cognitiveservices.azure.com/
AZURE_VISION_KEY=tu_subscription_key_aqui

# Google Cloud Vision (si lo usas)
GOOGLE_APPLICATION_CREDENTIALS=path/to/google_credentials.json
```

Reemplaza:
- `tu-recurso` con el nombre de tu recurso
- `tu_subscription_key_aqui` con tu KEY 1

### 4.2 Verificar que `.env` está en `.gitignore`

**⚠️ CRÍTICO:** Asegúrate que el archivo `.env` NO se suba a Git.

Verifica que `.gitignore` contenga:
```
.env
*.env
```

---

## Paso 5: Instalar SDK

### 5.1 Instalar con pip

```bash
pip install azure-ai-vision-imageanalysis
```

### 5.2 Verificar Instalación

```bash
python -c "from azure.ai.vision.imageanalysis import ImageAnalysisClient; print('✓ Azure Vision instalado')"
```

Deberías ver:
```
✓ Azure Vision instalado
```

---

## Paso 6: Verificar Instalación

### 6.1 Script de Prueba

Crea un archivo `test_azure.py`:

```python
import os
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from PIL import Image
import io

# Leer credenciales
endpoint = os.getenv('AZURE_VISION_ENDPOINT')
key = os.getenv('AZURE_VISION_KEY')

if not endpoint or not key:
    print("❌ Faltan variables de entorno")
    print("Configura AZURE_VISION_ENDPOINT y AZURE_VISION_KEY")
    exit(1)

print(f"✓ Endpoint: {endpoint}")
print(f"✓ Key: {key[:8]}...")

# Crear cliente
client = ImageAnalysisClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

print("✓ Cliente creado exitosamente")

# Crear imagen de prueba con texto
from PIL import ImageDraw, ImageFont
img = Image.new('RGB', (400, 100), color='white')
d = ImageDraw.Draw(img)
try:
    # Intentar usar fuente TrueType
    font = ImageFont.truetype("arial.ttf", 40)
except:
    # Fallback a fuente por defecto
    font = ImageFont.load_default()

d.text((10, 30), "1234567890", fill='black', font=font)

# Convertir a bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes = img_bytes.getvalue()

print("✓ Imagen de prueba creada")

# Llamar a Azure
print("→ Enviando a Azure Computer Vision...")

result = client.analyze(
    image_data=img_bytes,
    visual_features=[VisualFeatures.READ]
)

print("✓ Respuesta recibida")

# Procesar resultado
if result.read and result.read.blocks:
    print("\n📝 Texto detectado:")
    for block in result.read.blocks:
        for line in block.lines:
            print(f"   {line.text} (confidence: {line.confidence:.2f})")
    print("\n✅ Azure Computer Vision funciona correctamente!")
else:
    print("⚠️ No se detectó texto")

print("\n🎉 Instalación verificada exitosamente")
```

### 6.2 Ejecutar Prueba

```bash
python test_azure.py
```

Deberías ver:
```
✓ Endpoint: https://...
✓ Key: a1b2c3d4...
✓ Cliente creado exitosamente
✓ Imagen de prueba creada
→ Enviando a Azure Computer Vision...
✓ Respuesta recibida

📝 Texto detectado:
   1234567890 (confidence: 0.98)

✅ Azure Computer Vision funciona correctamente!

🎉 Instalación verificada exitosamente
```

---

## Paso 7: Configurar en el Proyecto

### 7.1 Elegir Proveedor OCR

Edita `config/settings.yaml`:

```yaml
ocr:
  # Opciones: "google_vision", "azure_vision", "ensemble"
  provider: azure_vision

  azure_vision:
    endpoint: ${AZURE_VISION_ENDPOINT}
    subscription_key: ${AZURE_VISION_KEY}
    confidence_threshold: 0.85
    max_retries: 3
    timeout: 30
```

### 7.2 Ejecutar Aplicación

```bash
python main.py
```

La aplicación detectará automáticamente Azure Vision y lo usará.

---

## Troubleshooting

### Error: "Faltan credenciales"

**Síntoma:**
```
ERROR Azure Vision: Faltan credenciales
```

**Solución:**
1. Verifica que `.env` existe en la raíz del proyecto
2. Verifica que las variables están bien escritas (sin espacios):
   ```bash
   AZURE_VISION_ENDPOINT=https://...
   AZURE_VISION_KEY=tu_key
   ```
3. Reinicia la aplicación

---

### Error: "401 Unauthorized"

**Síntoma:**
```
401 Unauthorized: Access denied due to invalid subscription key
```

**Soluciones:**
1. **Clave incorrecta** - Copia de nuevo desde Azure Portal
2. **Clave expirada** - Verifica en Portal que el recurso sigue activo
3. **Región incorrecta** - Endpoint debe coincidir con región del recurso

---

### Error: "404 Resource not found"

**Síntoma:**
```
404: The specified resource does not exist
```

**Soluciones:**
1. **Endpoint incorrecto** - Verifica que termina en `.cognitiveservices.azure.com/`
2. **Recurso eliminado** - Verifica en Portal que el recurso existe
3. **Nombre mal escrito** - Copia exactamente desde Portal

---

### Error: "429 Rate limit exceeded"

**Síntoma:**
```
429: Too many requests
```

**Causa:** Superaste el límite de free tier (5,000 transacciones/mes)

**Soluciones:**
1. **Esperar** - El límite se reinicia cada mes
2. **Upgradearlo a S1** - $1 USD por 1,000 transacciones adicionales
3. **Usar Google Vision** - Cambiar provider temporalmente

---

### Error: "Timeout waiting for response"

**Síntoma:**
```
Timeout waiting for Azure response
```

**Soluciones:**
1. **Red lenta** - Aumentar timeout en settings.yaml:
   ```yaml
   azure_vision:
     timeout: 60  # Aumentar a 60 segundos
   ```
2. **Azure caído** - Verificar status: https://status.azure.com
3. **Firewall** - Verificar que no bloquea cognitiveservices.azure.com

---

## Costos y Límites

### Free Tier (F0)

| Métrica | Límite |
|---------|--------|
| **Transacciones/mes** | 5,000 gratis |
| **Transacciones/segundo** | 20 |
| **Expiración** | Nunca (gratis siempre) |

Para este proyecto:
- 15 cédulas por imagen
- **5,000 imágenes gratis/mes** = **75,000 cédulas gratis/mes**

### Paid Tier (S1)

Si necesitas más:

| Métrica | Costo |
|---------|-------|
| **0-1M transacciones** | $1 USD por 1,000 |
| **1-10M transacciones** | $0.65 USD por 1,000 |
| **10M+ transacciones** | $0.40 USD por 1,000 |

**Ejemplo de costo:**
- 10,000 imágenes/mes = 10,000 transacciones
- Costo: (10,000 - 5,000) × $1 / 1,000 = **$5 USD/mes**

Comparar con Google Vision:
- 10,000 imágenes/mes
- Costo: (10,000 - 1,000) × $1.50 / 1,000 = **$13.50 USD/mes**

💡 **Azure es 63% más barato que Google Vision**

---

## Comparación con Google Vision

### Tabla Comparativa

| Característica | Azure Vision | Google Vision | Ganador |
|----------------|--------------|---------------|---------|
| **Free tier** | 5,000/mes | 1,000/mes | 🏆 Azure (5x más) |
| **Costo S1** | $1/1000 | $1.50/1000 | 🏆 Azure (33% más barato) |
| **Precisión manuscritos** | 95-98% | 95-98% | 🤝 Empate |
| **Velocidad** | 1-2 seg | 1-2 seg | 🤝 Empate |
| **Setup inicial** | Más complejo | Más simple | 🏆 Google |
| **Documentación** | Buena | Excelente | 🏆 Google |
| **Estabilidad** | Muy buena | Excelente | 🏆 Google |

### Recomendaciones

#### Usar **Google Vision** si:
- ✅ Primera vez configurando OCR
- ✅ Prefieres setup más simple (gcloud auth)
- ✅ Necesitas la mejor documentación

#### Usar **Azure Vision** si:
- ✅ Necesitas más transacciones gratis (5,000 vs 1,000)
- ✅ Quieres menor costo en producción
- ✅ Ya tienes infraestructura Azure

#### Usar **Ensemble** (ambos) si:
- ✅ Necesitas >99% de precisión
- ✅ El costo no es limitante
- ✅ Datos extremadamente críticos

### ¿Cuál es mejor para este proyecto?

**Para producción:**
1. **Probar ambos** con 100 imágenes reales
2. **Comparar precisión** (usar metrics del sistema)
3. **Elegir el de mejor precisión**
4. Si empatan → elegir **Azure** (más barato)

**Para desarrollo:**
- Usa el que ya tengas configurado
- O el que te resulte más fácil de configurar

---

## Próximos Pasos

Una vez configurado Azure Vision:

1. ✅ **Probar extracción** - Ejecuta `python main.py` y prueba con imágenes reales
2. ✅ **Comparar con Google** - Cambia `provider` en settings.yaml y compara resultados
3. ✅ **Probar Ensemble** - Configura `provider: ensemble` para máxima precisión
4. ✅ **Medir métricas** - Usa el logging para analizar precisión vs costo

---

## Recursos Adicionales

### Documentación Oficial
- **Azure Computer Vision:** https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/
- **Read API v4.0:** https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/overview-ocr
- **Python SDK:** https://learn.microsoft.com/en-us/python/api/overview/azure/ai-vision-imageanalysis-readme
- **Pricing:** https://azure.microsoft.com/en-us/pricing/details/cognitive-services/computer-vision/

### Tutoriales
- **Quickstart Python:** https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/quickstarts-sdk/image-analysis-client-library-40
- **Best Practices:** https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/how-to/call-read-api

### Soporte
- **Azure Status:** https://status.azure.com
- **Foro Stack Overflow:** https://stackoverflow.com/questions/tagged/azure-computer-vision
- **GitHub Issues:** https://github.com/Azure/azure-sdk-for-python/issues

---

## Changelog

### v1.0.0 (2025-11-20)
- ✅ Implementación inicial Azure Computer Vision Read API v4.0
- ✅ Integración con pipeline de preprocesamiento existente
- ✅ Factory pattern para selección de proveedor
- ✅ Modo Ensemble (Google + Azure)
- ✅ Documentación completa

---

**¿Necesitas ayuda?** Abre un issue en el repositorio del proyecto.

**¿Encontraste un error en esta guía?** Pull requests son bienvenidos.

---

**Última actualización:** 2025-11-20
**Autor:** Juan Sebastian Lopez Hernandez
**Proyecto:** Sistema de Automatización de Firmas
