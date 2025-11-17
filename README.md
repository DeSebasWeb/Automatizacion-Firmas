# Asistente de Digitación de Cédulas

Aplicación de escritorio en Python para automatizar la digitación de números de cédula extraídos de capturas de pantalla mediante OCR.

## Características

- **Captura de pantalla selectiva**: Selecciona el área específica donde se encuentran los datos tabulares
- **OCR avanzado**: Extrae números de cédula usando Tesseract con pre-procesamiento de imágenes
- **Automatización inteligente**: Digita automáticamente cada cédula en formularios web
- **Control manual**: El usuario valida cada registro antes de continuar
- **Logging completo**: Registro estructurado de todas las operaciones
- **Interfaz moderna**: GUI profesional con PyQt6
- **Arquitectura limpia**: Implementada con arquitectura hexagonal

## Requisitos del Sistema

- **Python**: 3.10 o superior
- **Tesseract OCR**: Debe estar instalado en el sistema
  - Windows: Descargar desde [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
  - Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-spa`
  - macOS: `brew install tesseract tesseract-lang`

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

### 5. Configurar Tesseract (Windows)

Si Tesseract no está en el PATH del sistema, editar `config/settings.yaml` y agregar:

```yaml
ocr:
  tesseract_path: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

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

# OCR
ocr:
  language: spa              # Idioma (spa = español)
  min_confidence: 50.0       # Confianza mínima
  psm: 6                     # Page Segmentation Mode

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

### Tesseract no encontrado

**Error**: `TesseractNotFoundError`

**Solución**:
1. Verificar que Tesseract está instalado
2. Configurar la ruta en `config/settings.yaml`:
   ```yaml
   ocr:
     tesseract_path: "ruta/a/tesseract.exe"
   ```

### OCR no detecta cédulas

**Problema**: El OCR no extrae números correctamente

**Soluciones**:
1. Verificar que el área capturada contiene texto legible
2. Ajustar el nivel de confianza en la configuración
3. Probar con diferentes valores de `psm` (0-13)
4. Mejorar la calidad de la imagen capturada

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
- **Infrastructure**: Implementaciones concretas (OCR, DB, APIs)
- **Presentation**: Interfaz de usuario (PyQt6)

### Principios aplicados

- **Inversión de dependencias**: Las capas internas no dependen de las externas
- **Inyección de dependencias**: Las dependencias se inyectan en el constructor
- **SOLID**: Aplicado en toda la arquitectura
- **Separation of Concerns**: Cada capa tiene responsabilidades claras

## Licencia

Este proyecto es de uso interno. Todos los derechos reservados.

## Autor

Desarrollado para automatización de procesos de digitación.

## Soporte

Para reportar problemas o solicitar funcionalidades, contactar al equipo de desarrollo.
