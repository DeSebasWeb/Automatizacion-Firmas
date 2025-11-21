@echo off
REM ========================================
REM Launcher - Asistente de Digitación
REM ========================================

title Asistente de Digitacion - Launcher

echo.
echo ========================================
echo  Asistente de Digitacion de Cedulas
echo ========================================
echo.

REM ========== Paso 1: Verificar entorno virtual ==========
echo [1/4] Verificando entorno virtual...
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo ERROR: Entorno virtual no encontrado
    echo.
    echo Por favor ejecute 'install.bat' primero para:
    echo   - Crear el entorno virtual
    echo   - Instalar dependencias
    echo.
    pause
    exit /b 1
)
echo      [OK] Entorno virtual encontrado
echo.

REM ========== Paso 2: Activar entorno virtual ==========
echo [2/4] Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo ERROR: No se pudo activar el entorno virtual
    echo.
    echo Posibles soluciones:
    echo   1. Eliminar carpeta 'venv' y ejecutar 'install.bat'
    echo   2. Verificar permisos de ejecucion
    echo.
    pause
    exit /b 1
)
echo      [OK] Entorno activado
echo.

REM ========== Paso 3: Verificar Python ==========
echo [3/4] Verificando Python en entorno...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python no esta disponible en el entorno virtual
    echo.
    echo Solucion: Ejecute 'install.bat' nuevamente
    echo.
    pause
    exit /b 1
)
python --version
echo.

REM ========== Paso 4: Iniciar aplicacion ==========
echo [4/4] Iniciando aplicacion...
echo.
echo ========================================
echo  Aplicacion iniciada
echo ========================================
echo.
echo NOTA: Esta ventana permanecera abierta
echo       para mostrar mensajes de debug.
echo.
echo Para cerrar la aplicacion:
echo   - Cierre la ventana principal (GUI)
echo   - O presione Ctrl+C aqui
echo.
echo ----------------------------------------
echo.

REM Ejecutar aplicacion y capturar codigo de salida
python main.py

REM Verificar codigo de salida
if errorlevel 1 (
    echo.
    echo ========================================
    echo  ERROR: La aplicacion termino con error
    echo ========================================
    echo.
    echo Codigo de salida: %ERRORLEVEL%
    echo.
    echo Revise los mensajes arriba para mas detalles.
    echo.
    echo Si el problema persiste:
    echo   1. Verifique que Tesseract OCR este instalado
    echo   2. Verifique config/settings.yaml
    echo   3. Revise logs en carpeta 'logs/'
    echo.
) else (
    echo.
    echo ========================================
    echo  Aplicacion cerrada correctamente
    echo ========================================
    echo.
)

pause
