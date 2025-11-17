@echo off
echo Iniciando Asistente de Digitacion...
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Entorno virtual no encontrado
    echo Por favor ejecute install.bat primero
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python main.py

pause
