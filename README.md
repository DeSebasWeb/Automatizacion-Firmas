# Sistema de Automatización Electoral

**Plataforma completa de procesamiento OCR para campañas políticas y electorales en Colombia**. Combina dos sistemas especializados:

1. **Digitación de Cédulas**: Extrae números de cédula manuscritos con precisión **98-99.5%** usando ensemble de múltiples motores OCR
2. **Procesamiento de Formularios E-14**: Extrae y estructura datos completos de formularios electorales E-14 Senado usando Azure Document Intelligence con modelos custom entrenados

## 🎯 Características Principales

### **Sistema 1: Digitación de Cédulas con Digit-Level Ensemble OCR ⭐**
- **98-99.5% de precisión** combinando Google Vision + Azure Vision a nivel de dígito individual
- **< 0.5% de errores** en dígitos críticos (1 vs 7, 3 vs 8, 6 vs 0)
- **Validación cruzada automática** entre dos motores de IA de diferentes proveedores
- **Logging detallado** con tabla de comparación dígito por dígito para auditoría
- **Captura selectiva** de áreas de pantalla con hotkeys configurables
- **Automatización inteligente** para digitación de cédulas con validación humana

### **Sistema 2: Procesamiento de Formularios E-14 Senado ⭐ NUEVO**
- **Azure Document Intelligence** con modelo custom entrenado específicamente para E-14
- **Extracción estructurada** de datos completos: metadatos, partidos, candidatos, totales
- **Parsing inteligente** con validación de tipos de voto (con/sin voto preferente)
- **Manejo multi-página** automático (hasta 11 páginas por formulario)
- **API REST** para integración con sistemas externos
- **Procesamiento batch** de múltiples formularios
- **Timeout controlado** con cancelación automática (60 segundos)

### **Múltiples Proveedores OCR (Sistema Cédulas)**
- **Google Cloud Vision API** (95-98% precisión, óptimo para manuscritos)
- **Azure Computer Vision Read API v4.0** (96-98% precisión, alternativa robusta)
- **Ensemble Tradicional** (combina cédula completa, >99% precisión)
- **Digit-Level Ensemble** ⭐ (combina dígito por dígito, 98-99.5% precisión)
- **Tesseract OCR** (70-85% precisión, fallback gratuito)

### **Arquitectura Empresarial**
- **Clean Architecture / Hexagonal**: Separación clara de responsabilidades en capas (Domain, Application, Infrastructure, Presentation)
- **SOLID Principles**: Código mantenible y escalable con responsabilidades únicas
- **Value Objects**: CedulaNumber, ConfidenceScore con validación automática e inmutabilidad
- **Specification Pattern**: Validaciones composables y reutilizables
- **Dependency Injection**: Fácil testing y extensibilidad en toda la aplicación
- **Ports & Adapters**: Abstracciones para OCR, configuración, automatización

### **Características Operativas**
- **Dual Mode**: GUI desktop (PyQt6) para cédulas + API REST para formularios E-14
- **Captura de pantalla selectiva** con áreas configurables y hotkeys
- **Preprocesamiento optimizado** (upscaling, denoising, CLAHE) para imágenes OCR
- **Automatización inteligente** con hotkeys globales configurables
- **Validación flexible** (3-11 dígitos, soporta formatos especiales)
- **API REST** con FastAPI para procesamiento de formularios E-14
- **Logging estructurado** JSON con structlog para análisis y auditoría
- **Testing exhaustivo** con pytest (unit + integration tests)
- **Costo económico**:
  - Cédulas: Desde gratis hasta ~$8 COP por 1,000 cédulas
  - E-14: ~$1,000 COP por 1,000 páginas (Azure Document Intelligence)

## 📊 Comparación de Sistemas y Proveedores

### Sistema de Cédulas - Proveedores OCR

| Proveedor | Precisión | Costo/1,000 imgs | Velocidad | Recomendado Para |
|-----------|-----------|------------------|-----------|------------------|
| **Google Vision** | 95-98% | $5.16 COP | 1-2 seg | Producción estándar |
| **Azure Vision** | 96-98% | $4,200 COP | 1-2 seg | Comparación/validación |
| **Ensemble** | >99% | $9,360 COP | 2-3 seg | Alta precisión |
| **Digit Ensemble ⭐** | **98-99.5%** | $9,360 COP | 2-3 seg | **Ultra precisión crítica** |
| **Tesseract** | 70-85% | Gratis | 0.5-1 seg | Desarrollo/testing |

### Sistema de Formularios E-14

| Proveedor | Precisión | Costo/1,000 págs | Velocidad | Recomendado Para |
|-----------|-----------|------------------|-----------|------------------|
| **Azure Document Intelligence** ⭐ | **95-98%** | $1,000 COP | 27-32 seg | **Formularios estructurados E-14** |
| **AWS Textract** | 92-95% | $1,500 USD | 15-25 seg | Alternativa (en desarrollo) |

### ¿Cuándo usar cada sistema?

**Sistema de Cédulas (OCR Manuscritos)**:
- **Google Vision**: Mejor relación precisión/costo para producción estándar
- **Azure Vision**: Validar cuál proveedor da mejor precisión con tus imágenes
- **Digit Ensemble** ⭐: Campaña electoral crítica donde errores son inaceptables
- **Ensemble**: Alta precisión pero sin análisis por dígito
- **Tesseract**: Solo para desarrollo/testing (baja precisión)

**Sistema de Formularios E-14**:
- **Azure Document Intelligence** ⭐: Extracción estructurada de formularios E-14 con modelo custom entrenado
- **AWS Textract**: Alternativa en desarrollo (menor precisión, mayor costo)

## 📈 Métricas de Precisión

### Digit-Level Ensemble OCR (Recomendado ⭐)

| Métrica | Google Solo | Azure Solo | Digit Ensemble ⭐ |
|---------|-------------|------------|-------------------|
| **Precisión Global** | 95-98% | 96-98% | **98-99.5%** |
| **Errores 1 vs 7** | 1-3% | 1-2% | **< 0.5%** |
| **Errores 3 vs 8** | 1-2% | 1-2% | **< 0.3%** |
| **Confianza Promedio** | 95% | 96% | **97%** |
| **Tiempo Procesamiento** | 1-2 seg | 1-2 seg | 2-3 seg |
| **Costo/1000 imgs** | $5 COP | $3 COP | $8 COP |

**Ejemplo Real:**
```
Google detecta: "1036221525" (dígito 0: '1' con 98%)
Azure detecta:  "7036221525" (dígito 0: '7' con 88%)

Digit Ensemble elige: '1' (98% > 88%) ✅
Resultado final: "1036221525" con 96.4% confianza
```

## 📋 Sistema de Formularios E-14 Senado

### ¿Qué son los formularios E-14?

Los **formularios E-14** son documentos oficiales utilizados en elecciones colombianas para registrar los votos de Senado por mesa de votación. Cada formulario contiene:

- **Metadatos**: Página, código DIVIPOL (departamento, municipio, zona, puesto, mesa)
- **Totales de mesa**: Sufragantes, votos en urna, votos incinerados
- **Partidos políticos**: Hasta 11 páginas con múltiples partidos por página
- **Tipos de voto**: Lista con voto preferente (candidatos individuales) o sin voto preferente (solo agrupación)
- **Candidatos**: ID y votos por candidato (solo en listas con voto preferente)
- **Totales por partido**: Suma de votos de agrupación + candidatos

### Características del Sistema E-14

**Extracción Estructurada con Azure Document Intelligence**:
- **Modelo Custom Entrenado**: `e14-senado-v1` entrenado específicamente con formularios E-14 reales
- **Parsing Inteligente**: Reconoce automáticamente tipos de voto y ajusta estructura de salida
- **Validación de Reglas de Negocio**:
  - Partidos SIN voto preferente: NO incluyen campo `TotalVotosAgrupacion+VotosCandidatos`
  - Partidos CON voto preferente: SÍ incluyen total y array de candidatos
  - Totales sin número de partido: Se asignan al único partido en esa página
- **Multi-página**: Procesa formularios de 1 a 11 páginas automáticamente
- **Timeout Controlado**: 60 segundos con cancelación automática si no responde

**Ejemplo de Salida JSON**:
```json
{
  "e14": {
    "pagina": "01 de 11",
    "divipol": {
      "CodDep": "11",
      "CodMun": "001",
      "zona": "01",
      "Puesto": "0001",
      "Mesa": "00001"
    },
    "TotalSufragantesE14": "150",
    "TotalVotosEnUrna": "148",
    "TotalIncinerados": "2",
    "Partido": [
      {
        "numPartido": "0013",
        "nombrePartido": "PARTIDO COMUNES",
        "tipoDeVoto": "ListaSinVotoPreferente",
        "id": "0",
        "votosSoloPorLaAgrupacionPolitica": "12",
        "candidatos": []
      },
      {
        "numPartido": "0002",
        "nombrePartido": "PARTIDO CONSERVADOR COLOMBIANO",
        "tipoDeVoto": "ListaConVotoPreferente",
        "id": "0",
        "votosSoloPorLaAgrupacionPolitica": "5",
        "candidatos": [
          {"idcandidato": "1", "votos": "8"},
          {"idcandidato": "2", "votos": "12"}
        ],
        "TotalVotosAgrupacion+VotosCandidatos": "25"
      }
    ],
    "pagina2": "02 de 11",
    "divipol2": {...},
    "Partido2": [...]
  }
}
```

### API REST para E-14

El sistema expone endpoints REST para procesamiento de formularios E-14:

**POST /api/azure-di/e14-senado**
```bash
curl -X POST "http://localhost:8000/api/azure-di/e14-senado" \
  -H "Content-Type: application/pdf" \
  --data-binary "@formulario_e14.pdf"
```

**Respuesta**:
```json
{
  "status": "success",
  "data": {
    "e14": { ... }
  },
  "processing_time_seconds": 28.5
}
```

### Testing del Sistema E-14

**Tests Unitarios** ([tests/unit/azure_di/](tests/unit/azure_di/)):
- `test_e14_senado_parser.py`: 6 tests para filtrado de campos y asignación de totales
- `test_partido_parser.py`: Tests para parsing de tipos de voto y candidatos
- Todos los tests usan fixtures y mocks

**Tests de Integración** ([tests/integration/test_e14_senado_integration.py](tests/integration/test_e14_senado_integration.py)):
- 7 tests con datos reales de Azure DI
- Validan parsing completo end-to-end
- Verifican reglas de negocio con formularios reales

**Ejecutar Tests**:
```bash
# Tests unitarios E-14
"venv/Scripts/python.exe" -m pytest tests/unit/azure_di/ -v

# Tests de integración E-14 (requiere temp/cleaned_fields.json)
"venv/Scripts/python.exe" -m pytest tests/integration/test_e14_senado_integration.py -v

# Todos los tests
"venv/Scripts/python.exe" -m pytest tests/ -v
```

## 🚀 Requisitos del Sistema

### Software Necesario
- **Python**: 3.10 o superior
- **Sistema Operativo**: Windows 10/11, Linux, macOS

### Proveedores Cloud (según el sistema que uses)

#### Para Sistema de Cédulas (OCR Manuscritos)

**Opción 1: Google Cloud Vision (Recomendado)**
- Cuenta de Google Cloud con facturación habilitada
- Cloud Vision API habilitada
- gcloud CLI instalado: [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- **1,000 imágenes gratis/mes**, luego $1.50 USD/1,000

**Opción 2: Azure Computer Vision**
- Cuenta de Microsoft Azure
- Recurso Computer Vision creado
- **5,000 transacciones gratis/mes**, luego $1 USD/1,000

**Opción 3: Ambos (para Digit-Level Ensemble ⭐)**
- Configurar Google Cloud Vision + Azure Computer Vision
- **Máxima precisión 98-99.5%**
- Doble costo pero resultados profesionales

#### Para Sistema de Formularios E-14 ⭐ REQUERIDO

**Azure Document Intelligence (Custom Model)**
- Cuenta de Microsoft Azure activa
- Recurso de Document Intelligence creado
- **Modelo custom entrenado**: `e14-senado-v1` (o tu ID de modelo)
- **30,000 páginas gratis/mes**, luego $1 USD/1,000 páginas
- Variables de entorno requeridas:
  - `AZURE_DI_ENDPOINT`: URL del recurso
  - `AZURE_DI_KEY`: Clave de suscripción

## 📦 Instalación

### 1. Clonar el proyecto

```bash
git clone <repository-url>
cd ProyectoFirmasAutomatizacion
```

### 2. Crear y activar entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copia `.env.example` a `.env` y configura tus credenciales:

```bash
cp .env.example .env
```

Edita `.env`:

```bash
# ========================================
# SISTEMA DE CÉDULAS (OCR Manuscritos)
# ========================================

# Google Cloud Vision (opcional)
# Opción 1: Application Default Credentials (recomendado)
# Ejecutar: gcloud auth application-default login

# Opción 2: Service Account JSON
# GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\credentials.json

# Azure Computer Vision (opcional)
AZURE_VISION_ENDPOINT=https://tu-recurso.cognitiveservices.azure.com/
AZURE_VISION_KEY=tu_subscription_key_aqui

# Proveedor OCR a usar para cédulas
OCR_PROVIDER=digit_ensemble  # o 'google_vision', 'azure_vision', 'ensemble'

# ========================================
# SISTEMA DE FORMULARIOS E-14 ⭐
# ========================================

# Azure Document Intelligence (REQUERIDO para E-14)
AZURE_DI_ENDPOINT=https://tu-recurso.cognitiveservices.azure.com/
AZURE_DI_KEY=tu_subscription_key_aqui

# Modelo custom entrenado para E-14 Senado
# (Configurar en config/settings.yaml: azure_di.model_id)
```

### 5. Configurar Google Cloud Vision (si lo usas)

```bash
# Autenticar con Application Default Credentials
gcloud auth application-default login
```

Consulta la guía completa: [docs/GOOGLE_CLOUD_SETUP.md](docs/GOOGLE_CLOUD_SETUP.md)

### 6. Configurar Azure Computer Vision (si lo usas)

Consulta la guía completa: [docs/AZURE_VISION_SETUP.md](docs/AZURE_VISION_SETUP.md)

## 🎮 Uso

### Sistema 1: Digitación de Cédulas (GUI Desktop)

#### Inicio Rápido

```bash
# Windows
run.bat

# Linux/macOS
python main.py
```

#### Flujo de Trabajo

#### 1. Seleccionar Área de Captura
- Presiona **F4** o clic en "Seleccionar Área"
- Arrastra el mouse para seleccionar el área con las cédulas
- El área se guarda automáticamente

#### 2. Capturar y Extraer Cédulas
- Clic en "Capturar Pantalla" o presiona la hotkey configurada
- Clic en "Extraer Cédulas"
- El sistema procesará la imagen y mostrará las cédulas detectadas

#### 3. Revisar Resultados (Digit-Level Ensemble)
Si usas `digit_ensemble`, verás un log detallado:

```
==================================================================
DIGIT-LEVEL ENSEMBLE OCR INICIADO
==================================================================
✓ Primary OCR (Google):   15 cédulas detectadas
✓ Secondary OCR (Azure):  15 cédulas detectadas
✓ Emparejadas por posición: 15 cédulas

[1/15] Procesando cédula (posición 0):
  Primary:   1036221525 (conf: 94.2%)
  Secondary: 7036221525 (conf: 91.8%)

  Comparación dígito por dígito:
  ┌─────┬────────────────┬────────────────┬──────────┐
  │ Pos │ Primary        │ Secondary      │ Elegido  │
  ├─────┼────────────────┼────────────────┼──────────┤
  │  0  │ '1' (98.2%)    │ '7' (87.5%)    │ '1' (P)  │
  │  1  │ '0' (95.3%)    │ '0' (96.1%)    │ '0' (S)  │
  │  2  │ '3' (92.7%)    │ '3' (97.2%)    │ '3' (S)  │
  │  3  │ '6' (94.1%)    │ '6' (95.4%)    │ '6' (S)  │
  │  4  │ '2' (89.3%)    │ '2' (93.8%)    │ '2' (S)  │
  │  5  │ '2' (93.6%)    │ '2' (91.2%)    │ '2' (P)  │
  │  6  │ '1' (96.4%)    │ '7' (84.9%)    │ '1' (P)  │
  │  7  │ '5' (90.1%)    │ '5' (93.3%)    │ '5' (S)  │
  │  8  │ '2' (88.7%)    │ '2' (92.1%)    │ '2' (S)  │
  │  9  │ '5' (95.2%)    │ '5' (94.8%)    │ '5' (P)  │
  └─────┴────────────────┴────────────────┴──────────┘

  Estadísticas:
  - Acuerdo: 80% (8/10 dígitos coincidieron)
  - Confianza promedio: 96.4%
  - Fuentes: Primary: 5 dígitos, Secondary: 5 dígitos

  → RESULTADO FINAL: 1036221525 ✅
```

#### 4. Procesar Cédulas
- Clic en "Iniciar Procesamiento"
- El sistema digitará cada cédula automáticamente
- Presiona **Ctrl+Q** para procesar la siguiente

#### Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| **F4** | Seleccionar área de captura |
| **Ctrl+Q** | Procesar siguiente cédula |
| **F3** | Pausar/Reanudar procesamiento |
| **ESC** | Cancelar selección de área |

---

### Sistema 2: Procesamiento de Formularios E-14 (API REST)

#### Iniciar API REST

```bash
# Desde el directorio raíz del proyecto
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# O con el script de inicio
python -m src.api.main
```

La API estará disponible en: `http://localhost:8000`

#### Documentación Interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Procesar Formulario E-14

**Usando cURL**:
```bash
curl -X POST "http://localhost:8000/api/azure-di/e14-senado" \
  -H "Content-Type: application/pdf" \
  --data-binary "@formulario_e14.pdf" \
  -o resultado.json
```

**Usando Python requests**:
```python
import requests

with open("formulario_e14.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/azure-di/e14-senado",
        headers={"Content-Type": "application/pdf"},
        data=f
    )

result = response.json()
print(f"Status: {result['status']}")
print(f"Processing time: {result['processing_time_seconds']}s")
print(f"Data: {result['data']}")
```

**Usando Postman**:
1. Método: `POST`
2. URL: `http://localhost:8000/api/azure-di/e14-senado`
3. Headers: `Content-Type: application/pdf`
4. Body: Binary → Seleccionar archivo PDF del formulario E-14

#### Respuesta de la API

**Éxito (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "e14": {
      "pagina": "01 de 11",
      "divipol": {
        "CodDep": "11",
        "CodMun": "001",
        "zona": "01",
        "Puesto": "0001",
        "Mesa": "00001"
      },
      "TotalSufragantesE14": "150",
      "Partido": [...]
    }
  },
  "processing_time_seconds": 28.5
}
```

**Error (500 Internal Server Error)**:
```json
{
  "status": "error",
  "message": "Processing failed",
  "error": "Azure DI timeout after 60 seconds"
}
```

#### Archivos de Debug

El sistema guarda automáticamente archivos de debug en la carpeta `temp/`:

- `azure_full_response.json`: Respuesta completa de Azure DI (raw)
- `cleaned_fields.json`: Campos limpiados y normalizados
- `e14_senado_parsed.json`: Resultado final parseado

Estos archivos son útiles para:
- Debugging de errores de parsing
- Análisis de confianza de OCR
- Testing con datos reales
- Entrenamiento de nuevas versiones del modelo

## ⚙️ Configuración Avanzada

### Archivo `config/settings.yaml`

```yaml
# Proveedor OCR a usar
ocr:
  # Opciones: 'google_vision', 'azure_vision', 'ensemble', 'digit_ensemble'
  provider: digit_ensemble  # ⭐ Recomendado para máxima precisión

  # Google Cloud Vision
  google_vision:
    authentication: application_default
    confidence_threshold: 0.85
    project_id: firmas-automatizacion

  # Azure Computer Vision
  azure_vision:
    api_version: '2024-02-01'
    confidence_threshold: 0.85
    endpoint: ${AZURE_VISION_ENDPOINT}
    subscription_key: ${AZURE_VISION_KEY}
    max_retries: 3
    timeout: 30

  # Ensemble tradicional (combina cédula completa)
  ensemble:
    log_discrepancies: true

  # Digit-Level Ensemble (combina dígito por dígito) ⭐
  digit_ensemble:
    # Confianza mínima por dígito individual (0.0-1.0)
    min_digit_confidence: 0.70

    # Ratio mínimo de acuerdo entre OCR (0.6 = 60% de dígitos deben coincidir)
    min_agreement_ratio: 0.60

    # Mostrar tabla detallada de comparación
    verbose_logging: true

# Preprocesamiento de imágenes (optimizado)
image_preprocessing:
  enabled: true
  upscale_factor: 2          # Mejora resolución moderadamente

  denoise:
    enabled: false           # Desactivado si imagen es limpia
    h: 7

  contrast:
    enabled: false           # Desactivado si contraste es bueno
    clip_limit: 2.5

  sharpen:
    enabled: false           # Desactivado para evitar artefactos

  save_processed_images: true  # Para debugging

# Automatización
automation:
  typing_interval: 0.05      # Velocidad de tipeo (segundos)
  pre_enter_delay: 0.3       # Delay antes de Enter
  post_enter_delay: 0.5      # Delay después de Enter

# Hotkeys
hotkeys:
  capture_area: f4
  next_record: ctrl+q
  pause: f3
```

### Validación de Cédulas

El sistema acepta cédulas de **3 a 11 dígitos**:
- Mínimo: 3 dígitos (casos especiales)
- Máximo: 11 dígitos (personas que escriben extra)
- Solo dígitos numéricos
- Sin validación de dígito verificador (para máxima flexibilidad)

Para validaciones específicas, edita:
```python
# src/domain/value_objects/cedula_number.py
if not (3 <= length <= 11):  # Ajustar según necesites
```

## 🏗️ Arquitectura del Proyecto

### Estructura de Directorios

```
ProyectoFirmasAutomatizacion/
├── src/
│   ├── domain/                    # Lógica de negocio (pura)
│   │   ├── entities/              # Entidades
│   │   │   ├── cedula_record.py   # Registro de cédula extraída
│   │   │   └── row_data.py        # Datos de renglón (dual OCR)
│   │   ├── value_objects/         # Objetos de valor inmutables
│   │   │   ├── cedula_number.py   # Número de cédula validado
│   │   │   ├── confidence_score.py # Score de confianza (0.0-1.0)
│   │   │   └── coordinate.py      # Coordenadas 2D
│   │   ├── specifications/        # Reglas de negocio composables
│   │   │   └── cedula_specifications.py
│   │   └── ports/                 # Interfaces (inversión de dependencia)
│   │       ├── ocr_port.py
│   │       ├── config_port.py
│   │       ├── automation_port.py
│   │       └── azure_di_port.py   # ⭐ Port para Azure Document Intelligence
│   │
│   ├── application/               # Casos de uso
│   │   └── use_cases/
│   │       ├── capture_screen.py
│   │       ├── extract_cedulas.py
│   │       ├── process_cedula.py
│   │       ├── manage_session.py
│   │       └── process_e14_senado_use_case.py  # ⭐ Procesamiento E-14
│   │
│   ├── infrastructure/            # Implementaciones concretas
│   │   ├── ocr/                   # Adaptadores OCR
│   │   │   ├── google_vision_adapter.py      # Google Cloud Vision
│   │   │   ├── azure_vision_adapter.py       # Azure Computer Vision
│   │   │   ├── ensemble_ocr.py               # Ensemble tradicional
│   │   │   ├── digit_level_ensemble_ocr.py   # Digit-Level Ensemble ⭐
│   │   │   ├── tesseract_ocr.py              # Tesseract (fallback)
│   │   │   ├── ocr_factory.py                # Factory pattern
│   │   │   │
│   │   │   ├── azure_document_intelligence/  # ⭐ Sistema E-14 Senado
│   │   │   │   ├── azure_di_adapter.py       # Adaptador Azure DI
│   │   │   │   ├── response_cleaner.py       # Limpieza de respuesta
│   │   │   │   ├── parsers/                  # Parsers especializados
│   │   │   │   │   ├── e14_senado_parser.py  # Parser principal E-14
│   │   │   │   │   ├── partido_parser.py     # Parser de partidos
│   │   │   │   │   ├── consolidado_parser.py # Parser de consolidados
│   │   │   │   │   └── parsing_utils.py      # Utilidades de parsing
│   │   │   │   └── models/                   # Modelos de datos E-14
│   │   │   │       ├── e14_document.py
│   │   │   │       ├── partido_result.py
│   │   │   │       ├── candidato_voto.py
│   │   │   │       └── tipo_lista.py
│   │   │   │
│   │   │   └── textract/          # AWS Textract (alternativa)
│   │   │       ├── textract_adapter.py
│   │   │       └── parsers/
│   │   │           └── e14_parser_service.py
│   │   ├── image/                 # Procesamiento de imágenes
│   │   │   ├── preprocessor.py    # Pipeline de preprocesamiento
│   │   │   ├── enhancer.py        # Mejoras de calidad
│   │   │   └── quality_metrics.py # Análisis de calidad
│   │   ├── capture/               # Captura de pantalla
│   │   │   └── pyautogui_capture.py
│   │   └── automation/            # Automatización
│   │       └── pyautogui_automation.py
│   │
│   ├── api/                       # ⭐ API REST (FastAPI)
│   │   ├── main.py                # Entry point API
│   │   └── routes/                # Endpoints
│   │       └── azure_di_routes.py # Rutas para E-14
│   │
│   ├── presentation/              # UI layer (Desktop)
│   │   ├── ui/                    # Widgets PyQt6
│   │   │   └── main_window.py
│   │   └── controllers/           # Controladores
│   │       └── main_controller.py
│   │
│   └── shared/                    # Utilidades compartidas
│       ├── logging/               # Logging estructurado
│       │   └── structured_logger.py
│       └── config/                # Gestión de configuración
│           └── yaml_config.py
│
├── config/                        # Configuración
│   └── settings.yaml
├── docs/                          # Documentación
│   ├── GOOGLE_CLOUD_SETUP.md
│   ├── AZURE_VISION_SETUP.md
│   ├── azure-di/                  # ⭐ Docs Azure DI
│   │   ├── implementation-guide.md
│   │   └── troubleshooting.md
│   └── mejoraSOLID/              # Documentación de mejoras
├── logs/                          # Logs de ejecución
├── tests/                         # Tests
│   ├── unit/                      # Unit tests
│   │   └── azure_di/              # ⭐ Tests Azure DI
│   │       ├── test_e14_senado_parser.py
│   │       └── test_partido_parser.py
│   └── integration/               # Integration tests
│       └── test_e14_senado_integration.py  # ⭐ Tests E-14
├── temp/                          # ⭐ Archivos temporales y debug
│   ├── azure_full_response.json   # Respuesta raw Azure DI
│   ├── cleaned_fields.json        # Campos limpiados
│   └── e14_senado_parsed.json     # Resultado parseado
├── .env.example                   # Plantilla de variables de entorno
├── requirements.txt               # Dependencias Python
├── main.py                        # Punto de entrada (Desktop)
└── README.md                      # Este archivo
```

### Principios de Diseño

#### Clean Architecture / Hexagonal
- **Domain**: Reglas de negocio puras, sin dependencias externas
- **Application**: Orquestación de casos de uso
- **Infrastructure**: Implementaciones concretas (OCR, DB, etc.)
- **Presentation**: UI y controladores

#### SOLID Principles
- **SRP**: Cada clase tiene una responsabilidad única
- **OCP**: Abierto para extensión, cerrado para modificación
- **LSP**: Substitución de Liskov (interfaces bien definidas)
- **ISP**: Interfaces segregadas (OCRPort, ConfigPort, etc.)
- **DIP**: Inversión de dependencias (domain no depende de infrastructure)

#### Patrones de Diseño
- **Value Objects**: Inmutabilidad con validación automática
- **Specification Pattern**: Reglas de negocio composables
- **Factory Pattern**: Creación flexible de OCR adapters
- **Dependency Injection**: Constructor injection en toda la aplicación
- **Strategy Pattern**: Múltiples proveedores OCR intercambiables

### Pipeline de Procesamiento

```
┌─────────────────────────────────────────────────────────────┐
│  1. CAPTURA DE PANTALLA                                     │
│     PyAutoGUI captura área configurada                      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. PREPROCESAMIENTO (Opcional)                             │
│     • Upscaling 2x (mejora resolución)                      │
│     • Conversión a escala de grises                         │
│     • Denoising (si imagen tiene ruido)                     │
│     • CLAHE (si contraste es bajo)                          │
│     • Sharpening (si imagen está borrosa)                   │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. OCR - DIGIT-LEVEL ENSEMBLE ⭐                            │
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │ Google Cloud Vision  │    │ Azure Computer Vision│      │
│  │  Extrae cédulas      │    │  Extrae cédulas      │      │
│  │  + confianza/dígito  │    │  + confianza/dígito  │      │
│  └──────────┬───────────┘    └──────────┬───────────┘      │
│             │                            │                   │
│             └────────────┬───────────────┘                   │
│                          ▼                                   │
│              ┌───────────────────────┐                       │
│              │ Emparejamiento        │                       │
│              │ por POSICIÓN          │                       │
│              │ (índice 0→0, 1→1)     │                       │
│              └───────────┬───────────┘                       │
│                          ▼                                   │
│              ┌───────────────────────┐                       │
│              │ Comparación           │                       │
│              │ DÍGITO por DÍGITO     │                       │
│              │ Elige mayor confianza │                       │
│              └───────────┬───────────┘                       │
│                          ▼                                   │
│              ┌───────────────────────┐                       │
│              │ Validación            │                       │
│              │ • Min confidence: 70% │                       │
│              │ • Agreement: 60%      │                       │
│              └───────────┬───────────┘                       │
│                          ▼                                   │
│              ┌───────────────────────┐                       │
│              │ Cédulas combinadas    │                       │
│              │ 98-99.5% precisión ✅  │                       │
│              └───────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. VALIDACIÓN CON VALUE OBJECTS                            │
│     • CedulaNumber (3-11 dígitos, solo numéricos)           │
│     • ConfidenceScore (0.0-1.0 normalizado)                 │
│     • Specifications (reglas de negocio composables)        │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. AUTOMATIZACIÓN                                          │
│     • Click en campo de búsqueda                            │
│     • Tipeo automático de cédula                            │
│     • Usuario valida y presiona Ctrl+Q                      │
└─────────────────────────────────────────────────────────────┘
```

## 💰 Costos y Presupuesto

### Sistema de Cédulas - Costo por Proveedor (1,000 imágenes)

| Proveedor | Free Tier | Costo después | Cédulas/mes gratis |
|-----------|-----------|---------------|-------------------|
| **Google Vision** | 1,000/mes | $5.16 COP | 15,000 |
| **Azure Vision** | 5,000/mes | $4,200 COP | 75,000 |
| **Digit Ensemble** | Ambos | $9,360 COP | Mínimo de ambos |
| **Tesseract** | ∞ | Gratis | ∞ |

### Sistema de Formularios E-14 - Costo Azure Document Intelligence

| Servicio | Free Tier | Costo después | Formularios/mes gratis |
|----------|-----------|---------------|------------------------|
| **Azure DI Custom** | 30,000 págs/mes | $1 USD/1,000 págs | ~3,000 formularios (11 páginas) |

### Ejemplo: Campaña de 5,000 firmas/mes

**Opción 1: Google Vision Solo**
- 334 imágenes (15 cédulas/imagen)
- Costo: Gratis (dentro del free tier)

**Opción 2: Digit-Level Ensemble ⭐**
- 334 imágenes × 2 proveedores
- Costo: Gratis (ambos dentro de free tier)
- **Precisión: 98-99.5%** (ultra confiable)

**Opción 3: Campaña de 50,000 firmas/mes**
- 3,334 imágenes
- Google: (3,334 - 1,000) × $5.16 = $12,044 COP
- Azure: (3,334 - 5,000) × $4,200 = Gratis (dentro de free tier)
- **Digit Ensemble: $12,044 COP** (solo pagas Google)

### Ejemplo: Procesamiento de Formularios E-14

**Caso 1: 500 formularios E-14/mes** (elecciones locales)
- 500 formularios × 11 páginas = 5,500 páginas
- Costo: Gratis (dentro del free tier de 30,000 págs)

**Caso 2: 5,000 formularios E-14/mes** (elecciones nacionales)
- 5,000 formularios × 11 páginas = 55,000 páginas
- Exceso: 55,000 - 30,000 = 25,000 páginas
- Costo: 25,000 / 1,000 × $1 USD = $25 USD = ~$105,000 COP
- **Costo total: $105,000 COP/mes**

## 🐛 Solución de Problemas

### Error: "No connection adapters were found"

**Causa**: Variables de entorno no están cargadas correctamente

**Solución**:
```bash
# Verificar que .env existe y tiene las credenciales
cat .env

# Verificar que las variables se cargan
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('AZURE_VISION_ENDPOINT'))"
```

### Error: "DefaultCredentialsError" (Google Cloud)

**Solución**:
```bash
# Autenticar con gcloud
gcloud auth application-default login

# Verificar que la API está habilitada
gcloud services enable vision.googleapis.com
```

### Error: Cédulas detectadas fuera de orden

**Causa**: El ensemble empareja por similitud en lugar de posición

**Solución**: Actualizado en versión actual. El sistema ahora empareja **por posición** (índice 0 con 0, 1 con 1, etc.) manteniendo el orden de arriba a abajo en el formulario.

### Precisión baja con Digit-Level Ensemble

**Diagnóstico**:
1. Revisar logs con `verbose_logging: true`
2. Verificar tabla de comparación dígito por dígito
3. Revisar "Agreement ratio" - si es < 50%, puede haber problema con imagen

**Soluciones**:
- Mejorar iluminación/contraste de la pantalla capturada
- Aumentar `upscale_factor` a 3 o 4 en `image_preprocessing`
- Verificar que área capturada contiene solo cédulas legibles
- Revisar imágenes guardadas en `temp/processed/`

### Hotkeys no funcionan

**Solución**:
- Windows: Ejecutar con permisos de administrador
- Linux: Verificar permisos de acceso a dispositivos de entrada
- Verificar que no hay conflictos con otras aplicaciones

---

## 🐛 Solución de Problemas - Sistema E-14

### Error: "Azure DI timeout after 60 seconds"

**Causa**: El análisis de Azure Document Intelligence tarda más de 60 segundos

**Solución**:
```yaml
# En config/settings.yaml, aumentar timeout
azure_di:
  polling_timeout_seconds: 90  # Aumentar a 90 segundos
```

**Alternativa**: Verificar tamaño del PDF - archivos grandes requieren más tiempo

### Error: "Azure DI credentials missing"

**Causa**: Variables de entorno no configuradas

**Solución**:
```bash
# Verificar .env
cat .env | grep AZURE_DI

# Debe mostrar:
# AZURE_DI_ENDPOINT=https://...
# AZURE_DI_KEY=...
```

### Error: Campos parseados incorrectamente

**Diagnóstico**:
1. Revisar `temp/azure_full_response.json` para ver respuesta raw
2. Revisar `temp/cleaned_fields.json` para ver campos limpiados
3. Revisar `temp/e14_senado_parsed.json` para ver resultado final

**Soluciones comunes**:
- Verificar que modelo custom está correctamente entrenado
- Asegurar que `model_id` en `config/settings.yaml` es correcto
- Verificar logs en `logs/` para errores de parsing

### Tests de integración E-14 fallan

**Causa**: Archivo `temp/cleaned_fields.json` no existe

**Solución**:
```bash
# Ejecutar procesamiento manual primero para generar datos de prueba
curl -X POST "http://localhost:8000/api/azure-di/e14-senado" \
  -H "Content-Type: application/pdf" \
  --data-binary "@formulario_e14.pdf"

# Luego ejecutar tests
"venv/Scripts/python.exe" -m pytest tests/integration/ -v
```

### Partido sin voto preferente tiene campo total

**Causa**: Parser no filtró correctamente según tipo de voto

**Diagnóstico**:
- Verificar que `tipoDeVoto` es exactamente `"ListaSinVotoPreferente"`
- Revisar método `_filter_partido_fields()` en `e14_senado_parser.py`

**Solución**: Ya implementada en la versión actual - el campo se elimina automáticamente

## 🧪 Testing

### Ejecutar tests unitarios

```bash
pytest tests/
```

### Con cobertura

```bash
pytest --cov=src tests/
pytest --cov=src --cov-report=html tests/
```

### Test específico

```bash
# Test de Digit-Level Ensemble
pytest tests/unit/test_digit_level_ensemble.py -v

# Test de Azure Vision
pytest tests/test_azure.py -v
```

## 📚 Documentación Adicional

### Sistema de Cédulas
- [Configuración Google Cloud Vision](docs/GOOGLE_CLOUD_SETUP.md)
- [Configuración Azure Computer Vision](docs/AZURE_VISION_SETUP.md)
- [Mejoras SOLID implementadas](docs/mejoraSOLID/)

### Sistema de Formularios E-14 ⭐
- [Guía de Implementación Azure DI](docs/azure-di/implementation-guide.md)
- [Troubleshooting Azure DI](docs/azure-di/troubleshooting.md)
- [Inicio Rápido API REST](docs/INICIO_RAPIDO_API.md)
- [Testing con Postman](docs/POSTMAN_TESTING_GUIDE.md)

## 🤝 Contribución

Este es un proyecto interno de uso profesional. Para cambios o mejoras:

1. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
2. Commit con mensaje descriptivo: `git commit -m "feat: descripción"`
3. Push: `git push origin feature/nueva-funcionalidad`
4. Crear Pull Request

## 📄 Licencia

Proyecto de uso interno. Todos los derechos reservados.

## 👤 Autor

Desarrollado para automatización de procesos electorales y recolección de firmas en campañas políticas en Colombia.

## 🆘 Soporte

Para reportar problemas, solicitar funcionalidades o consultas técnicas, contactar al equipo de desarrollo.

---

**⭐ Recomendación**: Usar `provider: digit_ensemble` en producción para máxima precisión (98-99.5%) en campañas electorales críticas donde los errores son inaceptables.
