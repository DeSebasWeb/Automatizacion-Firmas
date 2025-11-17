# Arquitectura del Proyecto

## Resumen

Este proyecto implementa **Clean Architecture (Arquitectura Hexagonal)** con separación clara de responsabilidades en capas concéntricas.

## Diagrama de Capas

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION                         │
│  (UI, Controllers, Widgets)                            │
│  - MainWindow (PyQt6)                                  │
│  - MainController                                      │
│  - AreaSelectorWidget                                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                    APPLICATION                          │
│  (Use Cases / Casos de Uso)                            │
│  - CaptureScreenUseCase                                │
│  - ExtractCedulasUseCase                               │
│  - ProcessCedulaUseCase                                │
│  - ManageSessionUseCase                                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                      DOMAIN                             │
│  (Entities, Ports/Interfaces)                          │
│  Entities:                                             │
│    - CedulaRecord                                      │
│    - CaptureArea                                       │
│    - ProcessingSession                                 │
│  Ports:                                                │
│    - OCRPort                                           │
│    - ScreenCapturePort                                 │
│    - AutomationPort                                    │
│    - ConfigPort                                        │
│    - LoggerPort                                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE                         │
│  (Implementaciones de Puertos)                         │
│  - TesseractOCR (OCRPort)                              │
│  - PyAutoGUICapture (ScreenCapturePort)                │
│  - PyAutoGUIAutomation (AutomationPort)                │
│  - YAMLConfig (ConfigPort)                             │
│  - StructuredLogger (LoggerPort)                       │
└─────────────────────────────────────────────────────────┘
```

## Flujo de Dependencias

```
Presentation → Application → Domain ← Infrastructure
                                ▲
                                │
                            (implements)
```

**Regla de Dependencia**: Las dependencias solo apuntan hacia adentro. Las capas internas no conocen las externas.

## Estructura de Directorios

```
src/
├── domain/                    # CAPA DE DOMINIO
│   ├── entities/             # Entidades del negocio
│   │   ├── cedula_record.py
│   │   ├── capture_area.py
│   │   └── processing_session.py
│   └── ports/                # Interfaces (Contratos)
│       ├── ocr_port.py
│       ├── screen_capture_port.py
│       ├── automation_port.py
│       ├── config_port.py
│       └── logger_port.py
│
├── application/              # CAPA DE APLICACIÓN
│   └── use_cases/           # Casos de uso (Orquestación)
│       ├── capture_screen_use_case.py
│       ├── extract_cedulas_use_case.py
│       ├── process_cedula_use_case.py
│       └── manage_session_use_case.py
│
├── infrastructure/          # CAPA DE INFRAESTRUCTURA
│   ├── ocr/                # Implementación OCR
│   │   └── tesseract_ocr.py
│   ├── capture/            # Implementación Captura
│   │   └── pyautogui_capture.py
│   └── automation/         # Implementación Automatización
│       └── pyautogui_automation.py
│
├── presentation/           # CAPA DE PRESENTACIÓN
│   ├── ui/                # Componentes de UI
│   │   ├── main_window.py
│   │   └── area_selector.py
│   └── controllers/       # Controladores
│       └── main_controller.py
│
└── shared/                # UTILIDADES COMPARTIDAS
    ├── logging/           # Sistema de logging
    │   └── structured_logger.py
    └── config/            # Gestión de configuración
        └── yaml_config.py
```

## Responsabilidades por Capa

### 1. Domain (Dominio)

**Responsabilidad**: Lógica de negocio pura, sin dependencias externas.

**Características**:
- No depende de frameworks ni librerías externas
- Define las reglas del negocio
- Define interfaces (puertos) para servicios externos
- Contiene las entidades principales

**Ejemplos**:
- `CedulaRecord`: Representa un registro de cédula con validaciones
- `ProcessingSession`: Maneja el estado de una sesión de procesamiento
- `OCRPort`: Interface que define qué debe hacer un servicio OCR

### 2. Application (Aplicación)

**Responsabilidad**: Casos de uso que orquestan la lógica del dominio.

**Características**:
- Coordina el flujo de datos entre capas
- Implementa casos de uso específicos
- Depende solo del dominio
- Sin lógica de UI ni detalles de implementación

**Ejemplos**:
- `ExtractCedulasUseCase`: Orquesta la extracción de cédulas
- `ProcessCedulaUseCase`: Coordina el procesamiento de una cédula

### 3. Infrastructure (Infraestructura)

**Responsabilidad**: Implementaciones concretas de los puertos del dominio.

**Características**:
- Implementa las interfaces definidas en el dominio
- Usa librerías y frameworks externos
- Puede ser reemplazada sin afectar el dominio

**Ejemplos**:
- `TesseractOCR`: Implementa OCRPort usando Tesseract
- `PyAutoGUIAutomation`: Implementa AutomationPort usando PyAutoGUI

### 4. Presentation (Presentación)

**Responsabilidad**: Interfaz de usuario y manejo de eventos.

**Características**:
- Interactúa con el usuario
- Delega lógica a los casos de uso
- No contiene lógica de negocio

**Ejemplos**:
- `MainWindow`: Ventana principal con PyQt6
- `MainController`: Conecta UI con casos de uso

## Principios Aplicados

### SOLID

1. **Single Responsibility**: Cada clase tiene una única razón para cambiar
2. **Open/Closed**: Abierto a extensión, cerrado a modificación
3. **Liskov Substitution**: Las implementaciones son intercambiables
4. **Interface Segregation**: Interfaces específicas, no genéricas
5. **Dependency Inversion**: Dependencia en abstracciones, no en concreciones

### Dependency Injection

Todas las dependencias se inyectan en el constructor:

```python
class ExtractCedulasUseCase:
    def __init__(self, ocr_service: OCRPort, logger: LoggerPort):
        self.ocr_service = ocr_service
        self.logger = logger
```

### Inversion of Control

El flujo de control va de afuera hacia adentro, pero las dependencias apuntan hacia adentro.

## Patrones de Diseño Utilizados

### 1. Port & Adapter (Hexagonal)

Los puertos definen interfaces, los adaptadores las implementan.

```
Domain Port (OCRPort) ← Infrastructure Adapter (TesseractOCR)
```

### 2. Repository Pattern

Aunque no hay persistencia de datos, el patrón se aplica en ConfigPort.

### 3. Use Case Pattern

Cada caso de uso es una clase que implementa una operación específica.

### 4. Observer Pattern

PyQt6 usa signals/slots para comunicación entre componentes.

## Flujo de Ejecución Típico

```
1. Usuario → MainWindow (click "Extraer Cédulas")
2. MainWindow → MainController (emit signal)
3. MainController → ExtractCedulasUseCase
4. ExtractCedulasUseCase → TesseractOCR (via OCRPort)
5. TesseractOCR → Tesseract Library
6. Resultado ← Tesseract Library
7. Resultado ← TesseractOCR
8. CedulaRecords ← ExtractCedulasUseCase
9. CedulaRecords ← MainController
10. UI Update ← MainWindow
```

## Ventajas de esta Arquitectura

1. **Testabilidad**: Fácil hacer tests unitarios con mocks
2. **Mantenibilidad**: Cambios aislados por capa
3. **Flexibilidad**: Fácil cambiar implementaciones
4. **Escalabilidad**: Agregar funcionalidades sin romper existente
5. **Comprensibilidad**: Estructura clara y organizada

## Ejemplo de Extensión

Para agregar un nuevo servicio OCR (ej: EasyOCR):

1. Crear `EasyOCR` que implemente `OCRPort`
2. Inyectar `EasyOCR` en lugar de `TesseractOCR` en `main.py`
3. **No se modifica ninguna otra capa**

```python
# Nuevo adaptador
class EasyOCR(OCRPort):
    def extract_cedulas(self, image: Image.Image) -> List[CedulaRecord]:
        # Implementación con EasyOCR
        pass

# En main.py
ocr_service = EasyOCR(config)  # En lugar de TesseractOCR(config)
```

## Testing

Cada capa se testea independientemente:

- **Domain**: Tests de entidades y lógica de negocio
- **Application**: Tests de casos de uso con mocks de puertos
- **Infrastructure**: Tests de integración con servicios reales
- **Presentation**: Tests de UI y flujo de eventos

## Referencias

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture - Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html)
