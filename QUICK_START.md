# Guía de Inicio Rápido

## Instalación Rápida (Windows)

### Prerrequisitos

1. **Python 3.10+** instalado
   - Descargar: https://www.python.org/downloads/
   - Marcar "Add Python to PATH" durante instalación

2. **Tesseract OCR** instalado
   - Descargar: https://github.com/UB-Mannheim/tesseract/wiki
   - Instalar en ruta por defecto
   - Tesseract debe estar en PATH del sistema

### Instalación Automática

1. Ejecutar `install.bat` (doble click)
2. Esperar a que termine la instalación
3. Listo!

### Instalación Manual

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

## Uso Rápido

### Iniciar la Aplicación

**Opción 1**: Doble click en `run.bat`

**Opción 2**: Desde terminal
```bash
venv\Scripts\activate
python main.py
```

### Flujo de Trabajo en 5 Pasos

#### 1. Seleccionar Área de Captura

- Click en **"Seleccionar Área (F4)"**
- Arrastrar mouse sobre el área con las cédulas
- Soltar para confirmar
- El área se guarda automáticamente

#### 2. Capturar Pantalla

- Click en **"Capturar Pantalla"**
- La imagen aparecerá en "Vista Previa"

#### 3. Extraer Cédulas

- Click en **"Extraer Cédulas"**
- Esperar procesamiento OCR
- Las cédulas aparecerán en la lista

#### 4. Iniciar Procesamiento

- Posicionar cursor en el campo de búsqueda del formulario web
- Click en **"Iniciar Procesamiento"**
- La primera cédula se digitará automáticamente

#### 5. Validar y Continuar

- Validar manualmente los datos en el formulario
- Presionar **F2** o click en **"Siguiente"**
- Repetir hasta completar todos los registros

## Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| **F2** | Procesar siguiente registro |
| **F3** | Pausar/Reanudar procesamiento |
| **F4** | Seleccionar área de captura |
| **ESC** | Cancelar selección de área |

## Configuración Inicial

### Configurar Coordenadas del Campo de Búsqueda

1. Abrir `config/settings.yaml`
2. Posicionar mouse sobre el campo de búsqueda
3. Anotar coordenadas X, Y (mostradas en esquina)
4. Actualizar en el archivo:

```yaml
search_field:
  x: 500  # Tu coordenada X
  y: 300  # Tu coordenada Y
```

### Ajustar Velocidad de Tipeo

```yaml
automation:
  typing_interval: 0.05  # Más bajo = más rápido
  pre_enter_delay: 0.3   # Espera antes de Enter
  post_enter_delay: 0.5  # Espera después de Enter
```

### Mejorar Precisión de OCR

```yaml
ocr:
  min_confidence: 50.0  # Bajar para aceptar más resultados
  psm: 6               # Cambiar modo de segmentación (0-13)
```

## Solución de Problemas Rápidos

### Error: "Tesseract not found"

**Solución**: Agregar ruta en `config/settings.yaml`

```yaml
ocr:
  tesseract_path: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

### OCR no detecta números

**Solución**:
1. Capturar área más grande
2. Mejorar iluminación/contraste de la pantalla
3. Bajar `min_confidence` en configuración

### No se digita en el campo correcto

**Solución**: Configurar coordenadas exactas del campo:
1. Hover sobre el campo
2. Ver coordenadas del mouse
3. Actualizar `search_field` en config

### Atajos de teclado no funcionan

**Solución**: Ejecutar como Administrador (Windows)

## Tips y Mejores Prácticas

### Para Mejor Precisión de OCR

- Capturar solo la columna con cédulas
- Evitar incluir bordes o logos
- Usar fondo claro con texto oscuro
- Maximizar contraste en la pantalla

### Para Mayor Eficiencia

- Usar atajos de teclado (F2, F3, F4)
- Configurar correctamente las coordenadas
- Validar rápidamente sin interrumpir el flujo
- Pausar (F3) si necesitas más tiempo

### Para Procesamiento por Lotes

1. Capturar área con múltiples registros
2. Extraer todas las cédulas de una vez
3. Procesar de forma continua con F2
4. Pausar si necesitas descanso

## Logs y Depuración

Los logs se encuentran en `logs/app_YYYYMMDD.log`

Ver logs en tiempo real en la aplicación (panel inferior).

Niveles de log:
- **INFO**: Operaciones normales (verde)
- **WARNING**: Advertencias (naranja)
- **ERROR**: Errores (rojo)
- **DEBUG**: Información detallada (azul)

## Próximos Pasos

1. Leer [README.md](README.md) para documentación completa
2. Ver [ARCHITECTURE.md](ARCHITECTURE.md) para entender la estructura
3. Revisar [config/settings.example.yaml](config/settings.example.yaml) para todas las opciones
4. Ejecutar tests: `pytest tests/`

## Soporte

Para reportar problemas o solicitar ayuda:
- Revisar logs en `logs/`
- Verificar configuración en `config/settings.yaml`
- Consultar README.md para detalles técnicos

## Actualizaciones

Para actualizar la aplicación:

```bash
# Activar entorno
venv\Scripts\activate

# Actualizar dependencias
pip install --upgrade -r requirements.txt
```

## Desinstalación

1. Eliminar carpeta `venv/`
2. Eliminar carpeta del proyecto
3. Opcionalmente, desinstalar Tesseract OCR

---

**Listo!** Ya puedes empezar a usar la aplicación.

Para más información, consulta [README.md](README.md)
