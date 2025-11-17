# Lista de Verificación de Instalación

## Pre-requisitos

### 1. Python

- [ ] Python 3.10 o superior instalado
- [ ] Python agregado al PATH del sistema
- [ ] Verificar versión:
  ```bash
  python --version
  ```
  Debe mostrar: `Python 3.10.x` o superior

### 2. Tesseract OCR

- [ ] Tesseract OCR instalado en el sistema
- [ ] Tesseract agregado al PATH (o configurar ruta en settings.yaml)
- [ ] Paquete de idioma español instalado
- [ ] Verificar instalación:
  ```bash
  tesseract --version
  ```
  Debe mostrar versión de Tesseract

**Descarga Windows**: https://github.com/UB-Mannheim/tesseract/wiki

**Linux**:
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

**macOS**:
```bash
brew install tesseract tesseract-lang
```

## Instalación del Proyecto

### Opción A: Instalación Automática (Windows)

1. [ ] Ejecutar `install.bat`
2. [ ] Esperar a que termine sin errores
3. [ ] Verificar que se creó la carpeta `venv/`

### Opción B: Instalación Manual

1. [ ] Navegar al directorio del proyecto
   ```bash
   cd E:\ProyectoFirmasAutomatizacion
   ```

2. [ ] Crear entorno virtual
   ```bash
   python -m venv venv
   ```

3. [ ] Activar entorno virtual

   **Windows**:
   ```bash
   venv\Scripts\activate
   ```

   **Linux/macOS**:
   ```bash
   source venv/bin/activate
   ```

4. [ ] Actualizar pip
   ```bash
   pip install --upgrade pip
   ```

5. [ ] Instalar dependencias
   ```bash
   pip install -r requirements.txt
   ```

6. [ ] Verificar instalación
   ```bash
   pip list
   ```
   Debe mostrar todas las dependencias instaladas

## Configuración Inicial

### 1. Crear Archivo de Configuración

- [ ] Copiar `config/settings.example.yaml` a `config/settings.yaml`
  ```bash
  # Windows
  copy config\settings.example.yaml config\settings.yaml

  # Linux/macOS
  cp config/settings.example.yaml config/settings.yaml
  ```

### 2. Configurar Tesseract (si es necesario)

Si Tesseract no está en el PATH:

- [ ] Editar `config/settings.yaml`
- [ ] Agregar/descomentar la línea:
  ```yaml
  ocr:
    tesseract_path: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
  ```

### 3. Crear Directorios (se crean automáticamente)

- [ ] Carpeta `logs/` se creará al ejecutar
- [ ] Carpeta `config/` debe existir

## Verificación de la Instalación

### 1. Test de Importaciones

- [ ] Ejecutar:
  ```bash
  python -c "import PyQt6; import pytesseract; import cv2; import pyautogui; print('OK')"
  ```
  Debe imprimir: `OK`

### 2. Test de Tesseract

- [ ] Ejecutar:
  ```bash
  python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
  ```
  Debe mostrar la versión de Tesseract

### 3. Ejecutar Tests (Opcional)

- [ ] Ejecutar:
  ```bash
  pytest tests/unit/ -v
  ```
  Todos los tests deben pasar

### 4. Primera Ejecución

- [ ] Ejecutar aplicación:
  ```bash
  python main.py
  ```

- [ ] Verificar que se abre la ventana principal
- [ ] Verificar que no hay errores en consola
- [ ] Verificar que se crea archivo de log en `logs/app_YYYYMMDD.log`

## Verificación de Funcionalidad

### Test Básico de Captura

1. [ ] Abrir la aplicación
2. [ ] Hacer clic en "Seleccionar Área (F4)"
3. [ ] Seleccionar un área de la pantalla
4. [ ] Verificar mensaje: "Área seleccionada: WxH en (X, Y)"
5. [ ] Verificar que el botón "Capturar Pantalla" se activa

### Test de Captura

1. [ ] Hacer clic en "Capturar Pantalla"
2. [ ] Verificar que aparece imagen en "Vista Previa"
3. [ ] Verificar que el botón "Extraer Cédulas" se activa

### Test de OCR

1. [ ] Preparar una imagen con números visibles
2. [ ] Capturar esa área
3. [ ] Hacer clic en "Extraer Cédulas"
4. [ ] Verificar que se procesan las cédulas (puede tardar 2-5 segundos)
5. [ ] Verificar que aparecen en la lista

### Test de Hotkeys (Opcional)

1. [ ] Presionar F4 → Debe abrir selector de área
2. [ ] Presionar ESC → Debe cancelar selección

## Solución de Problemas Comunes

### Error: "Python no reconocido"

**Causa**: Python no está en el PATH

**Solución**:
1. Reinstalar Python marcando "Add Python to PATH"
2. O agregar manualmente a variables de entorno

### Error: "No module named 'PyQt6'"

**Causa**: Dependencias no instaladas

**Solución**:
```bash
pip install -r requirements.txt
```

### Error: "TesseractNotFoundError"

**Causa**: Tesseract no instalado o no en PATH

**Solución**:
1. Instalar Tesseract OCR
2. Configurar ruta en `config/settings.yaml`

### Error: "Permission denied" (hotkeys)

**Causa**: Falta de permisos para hotkeys globales

**Solución**:
- Windows: Ejecutar como Administrador
- Linux: Agregar permisos de input

### Ventana no se muestra

**Causa**: Problema con PyQt6 o drivers de video

**Solución**:
```bash
pip install --upgrade PyQt6
```

## Lista de Archivos Creados

Después de la instalación exitosa, debes tener:

```
ProyectoFirmasAutomatizacion/
├── venv/                    ✓ Entorno virtual
├── config/
│   └── settings.yaml        ✓ Configuración
├── logs/
│   └── app_YYYYMMDD.log    ✓ Log del día (después de 1ra ejecución)
└── src/                     ✓ Código fuente
```

## Comandos Útiles

### Activar entorno virtual

```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### Ejecutar aplicación

```bash
python main.py

# o en Windows
run.bat
```

### Ejecutar tests

```bash
pytest tests/
```

### Ver logs

```bash
# Windows
type logs\app_*.log

# Linux/macOS
cat logs/app_*.log
```

### Actualizar dependencias

```bash
pip install --upgrade -r requirements.txt
```

## Checklist Final

- [ ] Python 3.10+ instalado
- [ ] Tesseract OCR instalado
- [ ] Entorno virtual creado
- [ ] Dependencias instaladas
- [ ] Configuración creada
- [ ] Aplicación ejecuta sin errores
- [ ] Selector de área funciona
- [ ] Captura de pantalla funciona
- [ ] OCR extrae texto
- [ ] Logs se generan correctamente

## Próximos Pasos

Una vez completada la instalación:

1. [ ] Leer `QUICK_START.md` para guía de uso rápido
2. [ ] Configurar coordenadas del campo de búsqueda
3. [ ] Ajustar parámetros de OCR según necesidad
4. [ ] Realizar prueba completa de flujo de trabajo

## Soporte

Si encuentras problemas no listados:

1. Revisar logs en `logs/`
2. Consultar `README.md` para detalles
3. Verificar versiones de dependencias
4. Contactar al equipo de desarrollo

---

**Instalación completada exitosamente cuando todos los checkboxes están marcados.**
