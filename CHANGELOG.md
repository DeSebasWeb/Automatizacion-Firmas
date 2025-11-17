# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2024-01-15

### Agregado
- Funcionalidad de captura de área de pantalla con selector interactivo
- Extracción de números de cédula usando OCR (Tesseract)
- Pre-procesamiento de imágenes para mejorar precisión del OCR
- Automatización de digitación de cédulas en formularios web
- Sistema de logging estructurado con archivos rotativos diarios
- Gestión de configuración con archivos YAML
- Interfaz gráfica moderna con PyQt6
- Atajos de teclado globales (F2, F3, F4)
- Control manual de validación por registro
- Barra de progreso y estadísticas de procesamiento
- Panel de logs en tiempo real
- Arquitectura hexagonal con separación clara de capas
- Tests unitarios para entidades del dominio
- Scripts de instalación para Windows
- Documentación completa en README.md

### Características
- Vista previa de imagen capturada
- Lista de cédulas extraídas con nivel de confianza
- Contador de registros procesados/pendientes
- Pausar y reanudar procesamiento
- Validación de formato de cédulas
- Configuración persistente de área de captura
- Manejo robusto de errores

### Técnico
- Python 3.10+
- PyQt6 para interfaz gráfica
- Tesseract OCR con OpenCV para pre-procesamiento
- PyAutoGUI y pynput para automatización
- Structlog para logging estructurado
- YAML para configuración
- Pytest para testing
- Type hints completos
- Principios SOLID aplicados
