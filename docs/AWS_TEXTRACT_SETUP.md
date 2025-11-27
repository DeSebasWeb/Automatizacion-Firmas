# AWS Textract - Guía de Configuración

Esta guía te ayudará a configurar AWS Textract como el tercer motor OCR para el sistema de Triple Ensemble.

## 📋 Tabla de Contenidos

1. [¿Por qué AWS Textract?](#por-qué-aws-textract)
2. [Crear cuenta de AWS](#1-crear-cuenta-de-aws)
3. [Configurar credenciales](#2-configurar-credenciales)
4. [Verificar instalación](#3-verificar-instalación)
5. [Precios y límites](#4-precios-y-límites)
6. [Troubleshooting](#5-troubleshooting)

---

## ¿Por qué AWS Textract?

AWS Textract es el **tercer motor OCR** del sistema de Triple Ensemble, que combina:
- **Google Vision** (excelente para manuscritos)
- **Azure Vision** (segunda opinión, muy preciso)
- **AWS Textract** (tercera opinión, desempate)

### Ventajas del Triple Ensemble:

✅ **Votación 3-way**: Cuando 2 de 3 OCR coinciden, tenemos certeza matemática
✅ **Eliminación de errores**: Los errores críticos (1↔7, 3↔8) bajan a < 0.2%
✅ **Precisión objetivo**: 99.5-99.8% (vs 98.5% con dual ensemble)
✅ **Desempate confiable**: Cuando Google y Azure difieren, AWS decide

---

## 1. Crear cuenta de AWS

### Paso 1.1: Registrarse en AWS

1. Ve a [aws.amazon.com/free](https://aws.amazon.com/free)
2. Haz clic en "Create a Free Account"
3. Completa el formulario de registro:
   - Email
   - Contraseña
   - Nombre de la cuenta AWS
4. Ingresa información de contacto
5. **IMPORTANTE**: Necesitarás una tarjeta de crédito/débito (no se cobrará durante el free tier)
6. Verifica tu identidad (llamada telefónica o SMS)
7. Selecciona el plan "Basic Support - Free"

### Paso 1.2: Free Tier de AWS Textract

✅ **1,000 páginas gratis al mes** durante los **primeros 3 meses**
✅ Para 15 cédulas por imagen = **15,000 cédulas gratis/mes**
✅ Perfecto para validación inicial del triple ensemble

⚠️ **Después del free tier:**
- $1.50 USD por 1,000 páginas (~6,450 COP)
- Para 5,000 imágenes/mes = ~$32,250 COP/mes
- Sigue siendo muy económico vs. trabajo manual

---

## 2. Configurar credenciales

Hay **3 opciones** para configurar credenciales. Elige la que prefieras.

### Opción A: Variables de entorno (Recomendado para desarrollo)

1. **Crear usuario IAM:**
   - Ve a [IAM Console](https://console.aws.amazon.com/iam/)
   - Haz clic en "Users" → "Add user"
   - Nombre de usuario: `textract-ocr-user`
   - Access type: ✅ **"Programmatic access"**
   - Click "Next: Permissions"

2. **Asignar permisos:**
   - Click "Attach existing policies directly"
   - Buscar y seleccionar: **`AmazonTextractFullAccess`**
   - Click "Next: Tags" → "Next: Review" → "Create user"

3. **Guardar credenciales:**
   - ⚠️ **MUY IMPORTANTE**: Copia el **Access Key ID** y **Secret Access Key**
   - **Solo se muestran UNA VEZ**. Guárdalas en un lugar seguro.
   - Ejemplo:
     ```
     Access Key ID:     AKIAIOSFODNN7EXAMPLE
     Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
     ```

4. **Configurar en el proyecto:**

   **Opción 4a: Archivo `.env` (RECOMENDADO)**

   Crea o edita el archivo `.env` en la raíz del proyecto:

   ```bash
   # AWS Textract
   AWS_ACCESS_KEY_ID=tu_access_key_aqui
   AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
   AWS_DEFAULT_REGION=us-east-1
   ```

   ⚠️ **IMPORTANTE**: Asegúrate de que `.env` esté en `.gitignore` (nunca subir credenciales a git)

   **Opción 4b: Variables de entorno del sistema**

   En Windows (PowerShell):
   ```powershell
   $env:AWS_ACCESS_KEY_ID="tu_access_key_aqui"
   $env:AWS_SECRET_ACCESS_KEY="tu_secret_key_aqui"
   $env:AWS_DEFAULT_REGION="us-east-1"
   ```

   En Linux/Mac:
   ```bash
   export AWS_ACCESS_KEY_ID="tu_access_key_aqui"
   export AWS_SECRET_ACCESS_KEY="tu_secret_key_aqui"
   export AWS_DEFAULT_REGION="us-east-1"
   ```

### Opción B: AWS CLI (Recomendado para producción)

1. **Instalar AWS CLI:**
   - Windows: Descarga el [instalador MSI](https://awscli.amazonaws.com/AWSCLIV2.msi)
   - Mac: `brew install awscli`
   - Linux: `pip install awscli`

2. **Configurar credenciales:**
   ```bash
   aws configure
   ```

   Te pedirá:
   ```
   AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
   AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   Default region name [None]: us-east-1
   Default output format [None]: json
   ```

3. **Verificar configuración:**
   ```bash
   cat ~/.aws/credentials
   ```

   Debería mostrar:
   ```ini
   [default]
   aws_access_key_id = AKIAIOSFODNN7EXAMPLE
   aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   ```

### Opción C: Configuración en settings.yaml (NO RECOMENDADO - menos seguro)

Edita `config/settings.yaml`:

```yaml
ocr:
  aws_textract:
    region: us-east-1
    access_key: AKIAIOSFODNN7EXAMPLE
    secret_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    confidence_threshold: 0.85
    max_retries: 3
```

⚠️ **ADVERTENCIA**: Esta opción NO es recomendada porque las credenciales quedan en texto plano. Usa variables de entorno o AWS CLI en su lugar.

---

## 3. Verificar instalación

### Paso 3.1: Instalar dependencias

```bash
pip install boto3
```

O si usas el `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Paso 3.2: Script de verificación

Crea un archivo `test_aws_textract.py`:

```python
import boto3
from PIL import Image
import io

def test_aws_textract():
    """Verifica que AWS Textract está configurado correctamente."""

    print("="*60)
    print("TEST AWS TEXTRACT - Verificación de configuración")
    print("="*60)

    try:
        # Crear cliente
        print("\n1. Creando cliente de Textract...")
        client = boto3.client('textract', region_name='us-east-1')
        print("✓ Cliente creado exitosamente")

        # Crear imagen de prueba simple
        print("\n2. Creando imagen de prueba...")
        img = Image.new('RGB', (200, 50), color='white')

        # Convertir a bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()
        print("✓ Imagen de prueba creada")

        # Llamar a la API
        print("\n3. Llamando a detect_document_text...")
        response = client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        print("✓ Llamada exitosa a AWS Textract")

        # Verificar respuesta
        print("\n4. Verificando respuesta...")
        if 'Blocks' in response:
            print(f"✓ Respuesta válida: {len(response['Blocks'])} bloques detectados")
        else:
            print("⚠️ Respuesta sin bloques (normal para imagen vacía)")

        print("\n" + "="*60)
        print("✅ AWS TEXTRACT CONFIGURADO CORRECTAMENTE")
        print("="*60)
        print("\n💡 Ahora puedes usar triple_ensemble en config/settings.yaml")
        print("   Cambia: provider: triple_ensemble")

        return True

    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR AL CONFIGURAR AWS TEXTRACT")
        print("="*60)
        print(f"\nError: {e}")
        print("\n💡 Soluciones:")
        print("   1. Verifica las credenciales en .env o AWS CLI")
        print("   2. Verifica que el usuario IAM tenga AmazonTextractFullAccess")
        print("   3. Verifica la región (debe ser us-east-1)")
        return False

if __name__ == "__main__":
    test_aws_textract()
```

Ejecuta el script:

```bash
python test_aws_textract.py
```

**Resultado esperado:**

```
============================================================
TEST AWS TEXTRACT - Verificación de configuración
============================================================

1. Creando cliente de Textract...
✓ Cliente creado exitosamente

2. Creando imagen de prueba...
✓ Imagen de prueba creada

3. Llamando a detect_document_text...
✓ Llamada exitosa a AWS Textract

4. Verificando respuesta...
✓ Respuesta válida: 0 bloques detectados

============================================================
✅ AWS TEXTRACT CONFIGURADO CORRECTAMENTE
============================================================

💡 Ahora puedes usar triple_ensemble en config/settings.yaml
   Cambia: provider: triple_ensemble
```

---

## 4. Precios y límites

### Free Tier (Primeros 3 meses)

| Recurso | Límite |
|---------|--------|
| Páginas procesadas | 1,000/mes |
| Cédulas (15 por página) | 15,000/mes |
| Costo | **$0 USD** |

### Después del Free Tier

| Volumen | Precio por 1,000 páginas | Costo mensual (5K imgs) |
|---------|--------------------------|-------------------------|
| Primeras 1M páginas | $1.50 USD | $7.50 USD (~$32,250 COP) |
| 1M - 10M páginas | $0.60 USD | - |
| Más de 10M páginas | $0.30 USD | - |

### Rate Limits

- **5 peticiones/segundo** por defecto
- Puedes solicitar aumento si necesitas más

### Monitorear uso

1. Ve a [AWS Console](https://console.aws.amazon.com/)
2. Busca "Billing Dashboard"
3. Ve a "Bills" → "AWS Textract"
4. Ahí verás el uso actual del mes

**Recomendación:** Configura una alerta de facturación:
- Ve a "Billing Preferences"
- Activa "Receive Billing Alerts"
- Crea una alerta en CloudWatch cuando el costo supere $5 USD

---

## 5. Troubleshooting

### Error: "Unable to locate credentials"

**Causa**: No se encontraron las credenciales de AWS.

**Solución**:
1. Verifica que el archivo `.env` existe y tiene las credenciales
2. O ejecuta `aws configure` para configurar credenciales
3. O verifica que las variables de entorno están configuradas:
   ```bash
   echo $AWS_ACCESS_KEY_ID
   echo $AWS_SECRET_ACCESS_KEY
   ```

### Error: "An error occurred (InvalidSignatureException)"

**Causa**: Las credenciales son incorrectas.

**Solución**:
1. Verifica que copiaste correctamente el Access Key ID y Secret Access Key
2. Asegúrate de que no hay espacios al inicio/final
3. Regenera las credenciales en IAM Console si es necesario

### Error: "An error occurred (AccessDeniedException)"

**Causa**: El usuario IAM no tiene permisos para Textract.

**Solución**:
1. Ve a [IAM Console](https://console.aws.amazon.com/iam/)
2. Selecciona el usuario
3. Ve a "Permissions"
4. Agrega la política `AmazonTextractFullAccess`

### Error: "ProvisionedThroughputExceededException"

**Causa**: Excediste el rate limit (5 peticiones/segundo).

**Solución**:
1. Espera unos segundos antes de reintentar
2. Reduce la frecuencia de llamadas
3. Solicita aumento de límite en AWS Support (si procesas muchas imágenes)

### Error: "InvalidParameterException"

**Causa**: La imagen tiene un formato no soportado.

**Solución**:
1. Asegúrate de que la imagen es PNG o JPEG
2. Verifica que el tamaño de la imagen < 5MB
3. Verifica que la resolución es adecuada (mínimo 150 DPI recomendado)

### Error: "ServiceQuotaExceededException"

**Causa**: Excediste el límite de 1,000 páginas del free tier.

**Solución**:
1. Verifica tu uso en Billing Dashboard
2. Espera al siguiente mes si aún estás en free tier
3. O acepta el costo de ~$1.50 USD por cada 1,000 páginas adicionales

---

## 6. Usar Triple Ensemble

Una vez configurado AWS Textract, activa el Triple Ensemble:

### Paso 6.1: Editar configuración

Edita `config/settings.yaml`:

```yaml
ocr:
  provider: triple_ensemble  # ⬅️ CAMBIAR AQUÍ
```

### Paso 6.2: Ejecutar el sistema

```bash
python main.py
```

**Salida esperada:**

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
```

### Paso 6.3: Monitorear resultados

El sistema mostrará:
- Votos de cada OCR por dígito
- Consenso alcanzado (unanimidad, mayoría, conflicto)
- Estadísticas de precisión
- Cédulas procesadas con alta confianza

**Ejemplo de salida:**

```
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
    Mayoría (2/3):       10/10 dígitos  ⬅️ Google + AWS coinciden
    Conflicto (0/3):      0/10 dígitos
    Acuerdo total:       100%
```

---

## 7. Siguiente paso: ¡Demostrar 99.5% de precisión!

Con el Triple Ensemble configurado, estás listo para:

✅ Procesar 100-200 formularios reales
✅ Medir la mejora de precisión (esperado: 99.5-99.8%)
✅ Reducir errores críticos a < 0.2%
✅ **Demostrar viabilidad para inversión de 50M COP**
✅ **Vender el sistema como servicio SaaS**

---

## 8. Recursos adicionales

- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS Free Tier Details](https://aws.amazon.com/free/)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

## ¿Problemas?

Si tienes problemas configurando AWS Textract, verifica:

1. ✅ Usuario IAM creado con permisos `AmazonTextractFullAccess`
2. ✅ Credenciales guardadas en `.env` o configuradas con `aws configure`
3. ✅ Región configurada como `us-east-1`
4. ✅ boto3 instalado (`pip install boto3`)
5. ✅ Script de verificación ejecutado exitosamente

Si todo está configurado pero no funciona, revisa la sección de [Troubleshooting](#5-troubleshooting).

---

**¡Listo! 🚀 Ahora tienes el Triple Ensemble con máxima precisión para lograr tu meta de 50M COP.**
