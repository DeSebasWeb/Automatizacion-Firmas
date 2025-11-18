# Asistente de Digitación de Cédulas

Aplicación de escritorio en Python para automatizar la digitación de números de cédula extraídos de capturas de pantalla mediante **Google Cloud Vision API**.

## Características

- **Captura de pantalla selectiva**: Selecciona el área específica donde se encuentran los datos tabulares
- **OCR avanzado con Google Cloud Vision**: Extrae números de cédula con precisión superior al 95% (óptimo para escritura manual)
- **Preprocesamiento intensivo de imágenes**: Pipeline robusto para maximizar precisión sin aumentar costos
- **Automatización inteligente**: Digita automáticamente cada cédula en formularios web
- **Control manual**: El usuario valida cada registro antes de continuar
- **Logging completo**: Registro estructurado de todas las operaciones
- **Interfaz moderna**: GUI profesional con PyQt6
- **Arquitectura limpia**: Implementada con arquitectura hexagonal
- **Costo muy económico**: ~$6,450 - $10,750 COP/mes (primeras 1,000 detecciones gratis)

## Requisitos del Sistema

- **Python**: 3.10 o superior
- **Google Cloud Account**: Cuenta de Google Cloud con facturación habilitada
- **Google Cloud Vision API**: Habilitada en tu proyecto de Google Cloud
- **gcloud CLI**: Para autenticación con Application Default Credentials
  - Windows/Linux/macOS: Descargar desde [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

## Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone <repository-url>
cd ProyectoFirmasAutomatizacion
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar Google Cloud Vision

**Autenticación con Application Default Credentials:**

```bash
gcloud auth application-default login
```

Esto abrirá un navegador para autenticarte con tu cuenta de Google Cloud.

**Verificar que la API está habilitada:**
- Ir a [Google Cloud Console](https://console.cloud.google.com/)
- Habilitar "Cloud Vision API" en tu proyecto
- Configurar facturación (primeras 1,000 detecciones/mes son gratis)

Para más detalles, consulta [docs/GOOGLE_CLOUD_SETUP.md](docs/GOOGLE_CLOUD_SETUP.md)

## Uso

### 1. Iniciar la aplicación

```bash
python main.py
```

### 2. Seleccionar área de captura

1. Hacer clic en "Seleccionar Área (F4)"
2. Arrastrar el mouse para seleccionar el área donde están las cédulas
3. Soltar para confirmar
4. El área se guarda automáticamente para próximos usos

### 3. Capturar y extraer

1. Hacer clic en "Capturar Pantalla"
2. La aplicación capturará el área configurada
3. Hacer clic en "Extraer Cédulas"
4. El OCR procesará la imagen y mostrará las cédulas encontradas

### 4. Procesar registros

1. Hacer clic en "Iniciar Procesamiento"
2. La aplicación digitará la primera cédula
3. Validar manualmente el registro en el formulario web
4. Presionar "Siguiente (F2)" para continuar con el próximo registro
5. Repetir hasta completar todos los registros

### 5. Atajos de teclado

- **F2**: Procesar siguiente registro
- **F3**: Pausar/Reanudar procesamiento
- **F4**: Seleccionar área de captura
- **ESC**: Cancelar selección de área

## Estructura del Proyecto

```
ProyectoFirmasAutomatizacion/
├── src/
│   ├── domain/              # Lógica de negocio
│   │   ├── entities/        # Entidades del dominio
│   │   └── ports/           # Interfaces (puertos)
│   ├── application/         # Casos de uso
│   │   └── use_cases/
│   ├── infrastructure/      # Implementaciones
│   │   ├── ocr/            # OCR con Tesseract
│   │   ├── capture/        # Captura de pantalla
│   │   └── automation/     # Automatización de teclado
│   ├── presentation/        # Interfaz de usuario
│   │   ├── ui/             # Widgets PyQt6
│   │   └── controllers/    # Controladores
│   └── shared/             # Utilidades compartidas
│       ├── logging/        # Sistema de logging
│       └── config/         # Gestión de configuración
├── config/                 # Archivos de configuración
├── logs/                   # Archivos de log
├── tests/                  # Tests unitarios
├── main.py                # Punto de entrada
├── requirements.txt       # Dependencias
└── README.md             # Este archivo
```

## Configuración

El archivo `config/settings.yaml` permite personalizar:

```yaml
# Área de captura (se guarda automáticamente)
capture_area:
  x: 100
  y: 100
  width: 800
  height: 600

# Campo de búsqueda (se configura con el mouse)
search_field:
  x: null
  y: null

# Automatización
automation:
  typing_interval: 0.05      # Velocidad de tipeo
  pre_enter_delay: 0.3       # Delay antes de Enter
  post_enter_delay: 0.5      # Delay después de Enter

# OCR con Google Cloud Vision
ocr:
  provider: google_vision
  google_vision:
    authentication: application_default
    project_id: firmas-automatizacion
    confidence_threshold: 0.85

# Preprocesamiento de imágenes (CRÍTICO para precisión)
image_preprocessing:
  enabled: true
  upscale_factor: 3          # Aumenta resolución 3x (distingue 1 vs 7)
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

# Interfaz
ui:
  theme: light
  window_width: 900
  window_height: 700
```

## Logging

Los logs se guardan en la carpeta `logs/` con el formato:

```
logs/app_YYYYMMDD.log
```

Cada entrada de log incluye:
- Timestamp ISO
- Nivel de log (INFO, WARNING, ERROR, DEBUG)
- Mensaje
- Contexto adicional en formato JSON

Ejemplo:
```json
{
  "event": "Cédula procesada exitosamente",
  "cedula": "12345678",
  "confidence": 95.5,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

## Solución de Problemas

### Google Cloud Vision no está autenticado

**Error**: `DefaultCredentialsError` o `PermissionDenied`

**Solución**:
1. Ejecutar autenticación con gcloud:
   ```bash
   gcloud auth application-default login
   ```
2. Verificar que la Cloud Vision API está habilitada en tu proyecto
3. Verificar que la facturación está habilitada en Google Cloud

### API no está habilitada

**Error**: `API has not been used in project` o `PERMISSION_DENIED`

**Solución**:
1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Seleccionar tu proyecto
3. Ir a "APIs & Services" → "Library"
4. Buscar "Cloud Vision API"
5. Hacer clic en "Enable"

### OCR confunde números (1 vs 7)

**Problema**: El OCR confunde 1 con 7 u otros números similares

**Soluciones**:
1. Aumentar el factor de upscaling en `config/settings.yaml`:
   ```yaml
   image_preprocessing:
     upscale_factor: 4  # Aumentar a 4x
   ```
2. Activar guardado de imágenes procesadas para depuración:
   ```yaml
   image_preprocessing:
     save_processed_images: true
   ```
3. Verificar que el área capturada contiene texto legible
4. Mejorar la iluminación de la pantalla capturada

### Los atajos de teclado no funcionan

**Problema**: F2, F3, F4 no responden

**Solución**:
- Ejecutar la aplicación con permisos de administrador (Windows)
- Verificar que no hay otras aplicaciones usando los mismos atajos

### Automatización no escribe en el campo correcto

**Problema**: El texto se digita en lugar incorrecto

**Solución**:
1. Configurar las coordenadas del campo de búsqueda
2. Posicionar el mouse sobre el campo deseado
3. Anotar las coordenadas X, Y
4. Actualizar en `config/settings.yaml`:
   ```yaml
   search_field:
     x: 500
     y: 300
   ```

## Desarrollo

### Ejecutar tests

```bash
pytest tests/
```

### Ejecutar con cobertura

```bash
pytest --cov=src tests/
```

### Formatear código

```bash
black src/
isort src/
```

### Type checking

```bash
mypy src/
```

## Arquitectura

El proyecto sigue **Clean Architecture / Arquitectura Hexagonal**:

- **Domain**: Lógica de negocio pura, sin dependencias externas
- **Application**: Casos de uso que orquestan la lógica
- **Infrastructure**: Implementaciones concretas (OCR, Preprocesamiento, Automatización)
  - **OCR**: Google Cloud Vision API (principal), Tesseract (legacy)
  - **Image Processing**: Pipeline robusto de preprocesamiento para mejorar precisión
  - **Capture & Automation**: PyAutoGUI para captura y automatización
- **Presentation**: Interfaz de usuario (PyQt6)

### Principios aplicados

- **Inversión de dependencias**: Las capas internas no dependen de las externas
- **Inyección de dependencias**: Las dependencias se inyectan en el constructor
- **SOLID**: Aplicado en toda la arquitectura
- **Separation of Concerns**: Cada capa tiene responsabilidades claras

### Pipeline de Procesamiento

```
Captura de Pantalla
       ↓
Preprocesamiento Intensivo:
  1. Upscaling 3x (CRÍTICO para distinguir 1 vs 7)
  2. Conversión a escala de grises
  3. Reducción de ruido (fastNlMeansDenoising)
  4. Aumento de contraste adaptativo (CLAHE)
  5. Sharpening para nitidez
  6. Binarización método Otsu
  7. Operaciones morfológicas (Close + Open)
       ↓
Google Cloud Vision API (1 llamada por imagen)
       ↓
Extracción y Validación de Cédulas
       ↓
Automatización de Digitación
```

## Licencia

Este proyecto es de uso interno. Todos los derechos reservados.

## Autor

Desarrollado para automatización de procesos de digitación.

## Soporte

Para reportar problemas o solicitar funcionalidades, contactar al equipo de desarrollo.
