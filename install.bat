@echo off
echo =====================================
echo Instalador - Asistente de Digitacion
echo =====================================
echo.

echo [1/4] Verificando Python...
python --version
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    pause
    exit /b 1
)
echo.

echo [2/4] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)
echo.

echo [3/4] Activando entorno virtual...
call venv\Scripts\activate.bat
echo.

echo [4/4] Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)
echo.

echo =====================================
echo Instalacion completada exitosamente!
echo =====================================
echo.
echo Para iniciar la aplicacion:
echo   1. Activar entorno: venv\Scripts\activate
echo   2. Ejecutar: python main.py
echo.
echo IMPORTANTE: Asegurese de tener Tesseract OCR instalado
echo Descarga: https://github.com/UB-Mannheim/tesseract/wiki
echo.
pause
