# Resumen del Proyecto

## Información General

**Nombre**: Asistente de Digitación de Cédulas
**Versión**: 1.0.0
**Lenguaje**: Python 3.10+
**Arquitectura**: Hexagonal / Clean Architecture
**GUI Framework**: PyQt6
**Licencia**: Uso Interno

## Descripción

Aplicación de escritorio que automatiza la digitación de números de cédula extraídos de capturas de pantalla mediante OCR, permitiendo validación manual por registro.

## Características Principales

### Funcionalidades Core

1. **Captura Selectiva de Pantalla**
   - Selector interactivo de área
   - Guardado automático de coordenadas
   - Vista previa en tiempo real

2. **OCR Avanzado**
   - Tesseract con pre-procesamiento OpenCV
   - Filtrado inteligente de cédulas
   - Nivel de confianza por registro

3. **Automatización Inteligente**
   - Digitación automática de cédulas
   - Control de velocidad configurable
   - Hotkeys globales (F2, F3, F4)

4. **Control Manual**
   - Validación usuario por registro
   - Pausar/Reanudar en cualquier momento
   - Navegación con teclado

5. **Logging Completo**
   - Logs estructurados en JSON
   - Rotación diaria automática
   - Panel de logs en UI

6. **Interfaz Moderna**
   - GUI profesional con PyQt6
   - Indicadores de progreso
   - Estadísticas en tiempo real

## Tecnologías Utilizadas

### Backend
- **Python 3.10+**: Lenguaje principal
- **Tesseract OCR**: Reconocimiento de texto
- **OpenCV**: Pre-procesamiento de imágenes
- **PyAutoGUI**: Automatización de pantalla
- **pynput**: Hotkeys globales

### Frontend
- **PyQt6**: Framework de interfaz gráfica
- **PIL/Pillow**: Manipulación de imágenes

### Infraestructura
- **structlog**: Logging estructurado
- **PyYAML**: Configuración
- **pytest**: Testing

## Estructura del Código

```
src/
├── domain/           # Lógica de negocio pura
├── application/      # Casos de uso
├── infrastructure/   # Implementaciones
├── presentation/     # UI y controladores
└── shared/          # Utilidades compartidas
```

## Casos de Uso Implementados

1. **CaptureScreenUseCase**: Captura área de pantalla
2. **ExtractCedulasUseCase**: Extrae cédulas con OCR
3. **ProcessCedulaUseCase**: Automatiza digitación
4. **ManageSessionUseCase**: Gestiona sesión de procesamiento

## Entidades del Dominio

1. **CedulaRecord**: Registro individual de cédula
2. **CaptureArea**: Área de captura de pantalla
3. **ProcessingSession**: Sesión de procesamiento

## Puertos (Interfaces)

1. **OCRPort**: Servicio de OCR
2. **ScreenCapturePort**: Servicio de captura
3. **AutomationPort**: Servicio de automatización
4. **ConfigPort**: Servicio de configuración
5. **LoggerPort**: Servicio de logging

## Adaptadores Implementados

1. **TesseractOCR**: OCR con Tesseract
2. **PyAutoGUICapture**: Captura con PyAutoGUI
3. **PyAutoGUIAutomation**: Automatización con PyAutoGUI
4. **YAMLConfig**: Configuración con YAML
5. **StructuredLogger**: Logging estructurado

## Flujo de Trabajo

```
1. Seleccionar área de captura
2. Capturar pantalla
3. Extraer cédulas con OCR
4. Iniciar procesamiento
5. Validar manualmente
6. Presionar F2 para siguiente
7. Repetir hasta completar
```

## Configuración

Archivo: `config/settings.yaml`

```yaml
capture_area: {x, y, width, height}
search_field: {x, y}
automation: {typing_interval, delays}
ocr: {language, min_confidence, psm}
hotkeys: {next_record, pause, capture_area}
ui: {theme, window_size}
```

## Logging

- **Ubicación**: `logs/app_YYYYMMDD.log`
- **Formato**: JSON estructurado
- **Niveles**: INFO, WARNING, ERROR, DEBUG
- **Rotación**: Diaria automática

## Testing

```bash
pytest tests/                    # Ejecutar todos los tests
pytest tests/unit/              # Solo tests unitarios
pytest --cov=src tests/         # Con cobertura
```

## Instalación

### Prerrequisitos
- Python 3.10+
- Tesseract OCR

### Pasos
```bash
# 1. Clonar proyecto
git clone <repo>

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar aplicación
python main.py
```

### Instalación Rápida (Windows)
```bash
install.bat  # Instalación automática
run.bat      # Ejecutar aplicación
```

## Uso Básico

1. **F4**: Seleccionar área de captura
2. **Capturar**: Tomar screenshot del área
3. **Extraer**: Ejecutar OCR sobre la imagen
4. **Iniciar**: Comenzar procesamiento automático
5. **F2**: Procesar siguiente registro
6. **F3**: Pausar/Reanudar

## Métricas del Proyecto

### Código
- **Archivos Python**: ~30
- **Líneas de Código**: ~3000+
- **Cobertura de Tests**: Configurado
- **Type Hints**: 100%
- **Docstrings**: Completos

### Arquitectura
- **Capas**: 4 (Domain, Application, Infrastructure, Presentation)
- **Principios**: SOLID aplicados
- **Patrones**: Hexagonal, Dependency Injection, Use Case
- **Acoplamiento**: Bajo
- **Cohesión**: Alta

## Dependencias Principales

```
PyQt6==6.6.1
pytesseract==0.3.10
opencv-python==4.8.1.78
Pillow==10.1.0
pyautogui==0.9.54
pynput==1.7.6
structlog==24.1.0
pyyaml==6.0.1
pytest==7.4.3
```

## Puntos de Extensión

### Fácil de Cambiar

1. **OCR Engine**: Cambiar TesseractOCR por EasyOCR/PaddleOCR
2. **GUI Framework**: Cambiar PyQt6 por Tkinter/Kivy
3. **Automation**: Cambiar PyAutoGUI por Keyboard/Mouse
4. **Storage**: Agregar persistencia en DB
5. **Export**: Agregar exportación de resultados

### Ejemplo de Extensión

```python
# main.py
# Cambiar de Tesseract a EasyOCR
from src.infrastructure.ocr import EasyOCR  # Nueva implementación

ocr_service = EasyOCR(config)  # En lugar de TesseractOCR
# ¡No se modifica ninguna otra capa!
```

## Mejoras Futuras Sugeridas

### Corto Plazo
- [ ] Exportar resultados a CSV/Excel
- [ ] Modo oscuro para UI
- [ ] Múltiples configuraciones de área
- [ ] Estadísticas detalladas post-procesamiento

### Mediano Plazo
- [ ] Soporte para múltiples monitores
- [ ] Integración con bases de datos
- [ ] API REST para integración
- [ ] Scheduler para procesamiento automático

### Largo Plazo
- [ ] Machine Learning para mejorar OCR
- [ ] Versión web (FastAPI + React)
- [ ] Modo batch sin intervención manual
- [ ] Integración con RPA frameworks

## Problemas Conocidos

1. **Windows**: Requiere permisos de administrador para hotkeys globales
2. **OCR**: Precisión depende de calidad de imagen
3. **Coordinadas**: Deben configurarse manualmente para campo de búsqueda

## Soluciones Implementadas

1. **Failsafe**: PyAutoGUI failsafe habilitado
2. **Error Handling**: Try-catch en operaciones críticas
3. **Logging**: Trazabilidad completa de operaciones
4. **Validación**: Múltiples capas de validación de datos

## Performance

- **Tiempo de captura**: <1s
- **Tiempo de OCR**: 2-5s (depende de tamaño)
- **Tiempo de digitación**: ~1.5s + (longitud * 0.05s)
- **Memoria**: ~100-200 MB

## Seguridad

- **No almacena datos sensibles**
- **Logs locales únicamente**
- **Sin conexiones de red**
- **Configuración en texto plano (local)**

## Soporte

### Documentación
- `README.md`: Documentación completa
- `QUICK_START.md`: Guía rápida
- `ARCHITECTURE.md`: Detalles de arquitectura
- `WORKFLOW.md`: Flujos de trabajo
- `CHANGELOG.md`: Historial de cambios

### Reportar Problemas
1. Revisar logs en `logs/`
2. Verificar configuración en `config/settings.yaml`
3. Consultar documentación
4. Contactar al equipo de desarrollo

## Créditos

- **Arquitectura**: Clean Architecture / Hexagonal
- **Inspiración**: Domain-Driven Design
- **Frameworks**: PyQt6, Tesseract OCR
- **Desarrollo**: Equipo de Automatización

## Licencia

Uso interno. Todos los derechos reservados.

---

**Última actualización**: 2024-01-15
**Versión del documento**: 1.0.0
