# Guía de Configuración de Google Cloud Vision API

Esta guía te ayudará a configurar Google Cloud Vision API para usar con el Asistente de Digitación de Cédulas.

## Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Crear Cuenta de Google Cloud](#crear-cuenta-de-google-cloud)
3. [Crear Proyecto](#crear-proyecto)
4. [Habilitar Cloud Vision API](#habilitar-cloud-vision-api)
5. [Configurar Facturación](#configurar-facturación)
6. [Instalar Google Cloud SDK](#instalar-google-cloud-sdk)
7. [Autenticación](#autenticación)
8. [Verificar Instalación](#verificar-instalación)
9. [Solución de Problemas](#solución-de-problemas)

---

## Requisitos Previos

- Cuenta de Google (Gmail)
- Tarjeta de crédito/débito para habilitar facturación (no se cobrará sin uso que exceda cuota gratuita)
- Python 3.10+ instalado
- Acceso a internet

---

## Crear Cuenta de Google Cloud

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Iniciar sesión con tu cuenta de Google
3. Aceptar los términos y condiciones
4. **Primer registro**: Google ofrece $300 USD en créditos gratis por 90 días

---

## Crear Proyecto

1. En la consola, hacer clic en el selector de proyectos (parte superior)
2. Hacer clic en **"Nuevo Proyecto"**
3. Configurar:
   - **Nombre del proyecto**: `firmas-automatizacion` (o el nombre que prefieras)
   - **Organización**: Dejar en blanco si no tienes
   - **Ubicación**: Dejar en "Sin organización"
4. Hacer clic en **"Crear"**
5. Esperar 30-60 segundos a que se cree el proyecto
6. Seleccionar el proyecto recién creado

---

## Habilitar Cloud Vision API

1. En la consola de Google Cloud, ir a **"APIs & Services"** → **"Library"**
2. Buscar: `Cloud Vision API`
3. Hacer clic en **"Cloud Vision API"**
4. Hacer clic en **"Habilitar" (Enable)**
5. Esperar 1-2 minutos a que se habilite

**Verificación:**
- Ir a **"APIs & Services"** → **"Enabled APIs & services"**
- Deberías ver "Cloud Vision API" en la lista

---

## Configurar Facturación

**IMPORTANTE:** Sin facturación habilitada, la API no funcionará (incluso en el nivel gratuito).

### Habilitar Facturación

1. Ir a **"Billing"** (Facturación) en el menú
2. Si no tienes una cuenta de facturación, hacer clic en **"Crear cuenta de facturación"**
3. Completar información:
   - País
   - Información de tarjeta de crédito/débito
4. Aceptar términos y hacer clic en **"Iniciar mi período de prueba gratuito"**
5. Vincular cuenta de facturación a tu proyecto

### Entender los Costos

**Nivel Gratuito (Free Tier):**
- **Primeras 1,000 detecciones/mes**: GRATIS
- **Después de 1,000**: $1.50 USD por cada 1,000 detecciones

**Para este proyecto:**
- **1 imagen con 15 cédulas** = 1 detección (procesamos la imagen completa)
- **1,000 imágenes gratis/mes** = 15,000 cédulas gratis/mes
- **Uso típico**: ~100-200 imágenes/mes = 1,500-3,000 cédulas/mes = **$0 USD**

**Costo estimado en pesos colombianos:**
- Si procesas 200 imágenes/mes: **$0 COP** (dentro del free tier)
- Si procesas 2,000 imágenes/mes: ~$1.50 USD = **~$6,450 COP**
- Si procesas 5,000 imágenes/mes: ~$6.00 USD = **~$25,800 COP**

### Configurar Alertas de Presupuesto

Para evitar sorpresas:

1. Ir a **"Billing"** → **"Budgets & alerts"**
2. Hacer clic en **"Create Budget"**
3. Configurar:
   - **Nombre**: "Alerta Cloud Vision"
   - **Monto**: $10 USD
   - **Umbrales de alerta**: 50%, 75%, 90%, 100%
4. Agregar tu email para recibir notificaciones
5. Hacer clic en **"Finish"**

---

## Instalar Google Cloud SDK

### Windows

1. Descargar instalador: [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Ejecutar instalador `GoogleCloudSDKInstaller.exe`
3. Seguir el asistente de instalación
4. Marcar:
   - ✓ Instalar componentes de Python
   - ✓ Agregar gcloud al PATH
5. Finalizar instalación
6. Abrir nueva terminal (CMD o PowerShell)
7. Verificar instalación:
   ```bash
   gcloud --version
   ```

### Linux

```bash
# Ubuntu/Debian
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-sdk
```

### macOS

```bash
# Homebrew
brew install --cask google-cloud-sdk
```

---

## Autenticación

### Método 1: Application Default Credentials (Recomendado)

Este es el método más simple y seguro:

```bash
gcloud auth application-default login
```

**Esto hará:**
1. Abrir tu navegador web
2. Pedirte que inicies sesión con tu cuenta de Google
3. Pedirte que autorices el acceso
4. Guardar credenciales localmente en:
   - Windows: `%APPDATA%\gcloud\application_default_credentials.json`
   - Linux/macOS: `~/.config/gcloud/application_default_credentials.json`

### Método 2: Service Account Key (Opcional, para servidores)

Solo si necesitas ejecutar en un servidor o ambiente de producción:

1. Ir a **"IAM & Admin"** → **"Service Accounts"**
2. Hacer clic en **"Create Service Account"**
3. Configurar:
   - **Nombre**: `vision-service-account`
   - **Rol**: "Cloud Vision API User"
4. Hacer clic en **"Create Key"** → **"JSON"**
5. Guardar archivo JSON en lugar seguro
6. Configurar variable de entorno:
   ```bash
   # Windows
   set GOOGLE_APPLICATION_CREDENTIALS=C:\ruta\al\archivo\credentials.json

   # Linux/macOS
   export GOOGLE_APPLICATION_CREDENTIALS=/ruta/al/archivo/credentials.json
   ```

**IMPORTANTE:** NO subas este archivo JSON a GitHub o repositorios públicos.

---

## Verificar Instalación

### 1. Verificar gcloud

```bash
gcloud --version
```

Deberías ver algo como:
```
Google Cloud SDK 450.0.0
```

### 2. Verificar Proyecto Activo

```bash
gcloud config get-value project
```

Debería mostrar: `firmas-automatizacion` (o el nombre de tu proyecto)

Si no:
```bash
gcloud config set project firmas-automatizacion
```

### 3. Verificar Autenticación

```bash
gcloud auth application-default print-access-token
```

Debería imprimir un token largo (no compartir).

### 4. Probar Cloud Vision API

Crear archivo de prueba `test_vision.py`:

```python
from google.cloud import vision

try:
    client = vision.ImageAnnotatorClient()
    print("✓ Google Cloud Vision inicializado correctamente")
    print("✓ Autenticación exitosa")
except Exception as e:
    print(f"✗ Error: {e}")
```

Ejecutar:
```bash
python test_vision.py
```

Debería imprimir:
```
✓ Google Cloud Vision inicializado correctamente
✓ Autenticación exitosa
```

---

## Solución de Problemas

### Error: "API has not been used in project"

**Causa:** Cloud Vision API no está habilitada

**Solución:**
1. Ir a [API Library](https://console.cloud.google.com/apis/library)
2. Buscar "Cloud Vision API"
3. Hacer clic en "Enable"

### Error: "PERMISSION_DENIED"

**Causa:** Facturación no habilitada o proyecto incorrecto

**Solución:**
1. Verificar que facturación está habilitada
2. Verificar proyecto activo:
   ```bash
   gcloud config get-value project
   ```
3. Si es incorrecto, configurar proyecto correcto:
   ```bash
   gcloud config set project firmas-automatizacion
   ```

### Error: "DefaultCredentialsError"

**Causa:** No se encontraron credenciales

**Solución:**
```bash
gcloud auth application-default login
```

### Error: "Quota exceeded"

**Causa:** Excediste el límite gratuito de 1,000 detecciones/mes

**Solución:**
1. Verificar uso en [Cloud Console](https://console.cloud.google.com/)
2. Ir a **"APIs & Services"** → **"Quotas"**
3. Ver uso de "Cloud Vision API"
4. Esperar al próximo mes o aceptar cargos adicionales

### gcloud no reconocido

**Causa:** gcloud no está en el PATH

**Solución Windows:**
1. Buscar "Variables de entorno" en el menú inicio
2. Editar "Path" en variables del sistema
3. Agregar: `C:\Users\TuUsuario\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin`
4. Reiniciar terminal

**Solución Linux/macOS:**
Agregar al `~/.bashrc` o `~/.zshrc`:
```bash
export PATH=$PATH:$HOME/google-cloud-sdk/bin
```

---

## Próximos Pasos

Una vez completada la configuración:

1. ✓ Volver a [README.md](../README.md) para continuar con la instalación del proyecto
2. ✓ Revisar [IMAGE_PREPROCESSING.md](IMAGE_PREPROCESSING.md) para entender el pipeline de mejoras
3. ✓ Revisar [ACCURACY_TIPS.md](ACCURACY_TIPS.md) para maximizar precisión
4. ✓ Revisar [COST_ANALYSIS.md](COST_ANALYSIS.md) para optimizar costos

---

## Referencias

- [Documentación oficial de Cloud Vision](https://cloud.google.com/vision/docs)
- [Precios de Cloud Vision](https://cloud.google.com/vision/pricing)
- [Guía de autenticación](https://cloud.google.com/docs/authentication/getting-started)
- [Instalación de gcloud SDK](https://cloud.google.com/sdk/docs/install)

---

**Última actualización:** 2025-11-18
