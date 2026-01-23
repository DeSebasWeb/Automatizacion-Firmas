# AWS Textract Integration

Sistema de procesamiento de formularios E-14 usando AWS Textract OCR.

## Arquitectura

```
src/infrastructure/ocr/textract/
├── textract_adapter.py        # Adaptador AWS Textract (OCR)
├── e14_textract_parser.py     # Parser E-14 especializado
└── __init__.py
```

## Componentes

### TextractAdapter
Adaptador para AWS Textract que:
- Extrae texto de imágenes usando `detect_document_text`
- Ordena bloques por posición (izquierda→derecha, arriba→abajo)
- Maneja errores de AWS (throttling, auth, etc.)
- Soporta múltiples métodos de autenticación

### E14TextractParser
Parser especializado que:
- Extrae DIVIPOL (zona, puesto, mesa, códigos)
- Identifica partidos políticos y tipo de voto
- Parsea candidatos y votos
- Detecta datos sospechosos (símbolos no numéricos)
- Marca campos con `necesita_auditoria: true`

## Configuración

### 1. Credenciales AWS

Opción A: **Variables de entorno** (recomendado para desarrollo)

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

Opción B: **AWS CLI** (recomendado para producción)

```bash
# Instalar AWS CLI
pip install awscli

# Configurar credenciales
aws configure
```

Opción C: **IAM Role** (recomendado para EC2/Lambda)

No requiere configuración manual, usa el rol asignado a la instancia.

### 2. Configuración en settings.yaml

Agregar sección AWS:

```yaml
aws:
  region: us-east-1
  # Opcional - si no se proporciona, usa cadena de credenciales por defecto
  access_key_id: ${AWS_ACCESS_KEY_ID}
  secret_access_key: ${AWS_SECRET_ACCESS_KEY}
```

### 3. Permisos IAM Requeridos

El usuario/rol de AWS debe tener permisos de Textract:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText"
      ],
      "Resource": "*"
    }
  ]
}
```

## Uso

### Endpoint FastAPI

```bash
POST /api/v1/documents/e14/textract
Content-Type: multipart/form-data
Authorization: Bearer <your_jwt_token>

Body:
  file: <E-14 image file (JPEG, PNG, TIFF)>
```

### Ejemplo con curl

```bash
curl -X POST http://localhost:8000/api/v1/documents/e14/textract \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@e14_sample.jpg"
```

### Ejemplo con Python

```python
from src.infrastructure.ocr.textract import TextractAdapter, E14TextractParser
from src.shared.config.yaml_config import YAMLConfig
from PIL import Image

# Inicializar adaptador
config = YAMLConfig("config/settings.yaml")
adapter = TextractAdapter(config)

# Extraer texto
image = Image.open("e14_form.jpg")
raw_text = adapter.extract_text_from_image(image)

# Parsear E-14
parser = E14TextractParser()
result = parser.parse(raw_text)

# Resultado estructurado
print(result["e14"]["pagina"])  # "01 de 09"
print(result["e14"]["Partido"])  # Lista de partidos
```

## Respuesta del Endpoint

```json
{
  "success": true,
  "structured_data": {
    "e14": {
      "pagina": "01 de 09",
      "divipol": {
        "CodDep": "16",
        "CodMun": "001",
        "zona": "01",
        "Puesto": "01",
        "Mesa": "001"
      },
      "TotalSufragantesE14": "134",
      "TotalVotosEnUrna": "131",
      "TotalIncinerados": "***",
      "Partido": [
        {
          "numPartido": "0261",
          "nombrePartido": "COALICION CENTRO ESPERANZA",
          "tipoDeVoto": "ListaConVotoPreferente",
          "id": "0",
          "votosSoloPorLaAgrupacionPolitica": "1",
          "candidatos": [
            {
              "idcandidato": "101",
              "votos": "2",
              "necesita_auditoria": false
            }
          ],
          "TotalVotosAgrupacion+VotosCandidatos": "4",
          "necesita_auditoria": false
        }
      ]
    }
  },
  "raw_ocr_text": "FORMATO E-14\nPAGINA 01 de 09\n...",
  "warnings": [],
  "processing_time_ms": 1234
}
```

## Auditoría

Campos con símbolos no numéricos (*, /, ⚡, etc.) se marcan con:
- `necesita_auditoria: true` a nivel de candidato
- `necesita_auditoria: true` a nivel de partido

Ejemplo:

```json
{
  "idcandidato": "101",
  "votos": "***",
  "necesita_auditoria": true
}
```

## Resultados Guardados

Cada procesamiento genera 3 archivos en `data/results/`:

1. **{timestamp}_e14_structured.json** - Datos estructurados
2. **{timestamp}_e14_raw_ocr.txt** - Texto OCR completo
3. **{timestamp}_e14_warnings.txt** - Advertencias y campos para auditoría

## Limitaciones

- **Max file size**: 10MB
- **Formatos soportados**: JPEG, PNG, TIFF
- **Resolución recomendada**: 300 DPI
- **Throttling**: AWS Textract limita 1-5 RPS según región

## Costos AWS

- **DetectDocumentText**: $0.0015 USD por página
- **Free Tier**: 1,000 páginas/mes primeros 12 meses

Ejemplo: 10,000 formularios E-14 = $15 USD/mes (después de free tier)

## Troubleshooting

### Error: "textract_client_not_initialized"

**Causa**: Credenciales AWS no configuradas

**Solución**:
1. Verificar variables de entorno: `echo $AWS_ACCESS_KEY_ID`
2. Verificar AWS CLI: `aws configure list`
3. Verificar permisos IAM

### Error: "ClientError: AccessDeniedException"

**Causa**: Usuario/rol sin permisos de Textract

**Solución**:
1. Agregar política `AmazonTextractFullAccess` al usuario
2. O crear política custom con `textract:DetectDocumentText`

### Error: "ThrottlingException"

**Causa**: Demasiadas requests por segundo

**Solución**:
1. Implementar retry con backoff exponencial
2. Solicitar aumento de límite a AWS Support
3. Procesar en batches más pequeños

## Escalabilidad

### Soporte Multi-Página (Futuro)

```python
# Para PDFs multi-página, usar:
response = client.start_document_text_detection(
    DocumentLocation={'S3Object': {'Bucket': 'my-bucket', 'Name': 'e14.pdf'}}
)

# Procesamiento asíncrono
job_id = response['JobId']
# ... polling hasta completion
```

### Procesamiento en Paralelo

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(use_case.execute, image)
        for image in images
    ]
```

## Referencias

- [AWS Textract Docs](https://docs.aws.amazon.com/textract/)
- [Boto3 Textract Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract.html)
- [Arquitectura Clean Architecture](../../../CLAUDE.md)
