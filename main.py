"""Punto de entrada principal de la aplicación."""
import sys
from PyQt6.QtWidgets import QApplication

from src.presentation.ui import MainWindow
from src.presentation.controllers import MainController
from src.application.use_cases import (
    CaptureScreenUseCase,
    ExtractCedulasUseCase,
    ProcessCedulaUseCase,
    ManageSessionUseCase
)
from src.infrastructure import ocr as ocr_module
from src.infrastructure.capture import PyAutoGUICapture
from src.infrastructure.automation import PyAutoGUIAutomation
from src.shared.config import YAMLConfig
from src.shared.logging import StructuredLogger


def exception_hook(exc_type, exc_value, exc_traceback):
    """Hook personalizado para capturar excepciones no manejadas."""
    import traceback
    # Imprimir el traceback completo
    print("\n" + "="*80)
    print("EXCEPCIÓN NO MANEJADA CAPTURADA:")
    print("="*80)
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print("="*80 + "\n")

    # NO cerrar la aplicación, solo registrar el error
    # La aplicación debe continuar ejecutándose


def main():
    """
    Función principal de la aplicación.

    Configura la inyección de dependencias y lanza la aplicación.
    """
    # Instalar hook de excepciones personalizado
    sys.excepthook = exception_hook

    # Suprimir warnings de Qt que pueden causar crashes
    import os
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.*=false"

    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Asistente de Digitación de Cédulas")
    app.setOrganizationName("Automatización")

    # Configurar dependencias (Dependency Injection)

    # Servicios compartidos
    config = YAMLConfig("config/settings.yaml")
    logger = StructuredLogger("app", log_dir="logs")

    # Adaptadores de infraestructura - Usar Google Cloud Vision (lo mejor para escritura manual)
    print("\n" + "="*60)
    print("Inicializando motor de OCR...")
    print("="*60)

    ocr_service = None

    # Intentar Google Cloud Vision primero (MEJOR OPCIÓN para escritura manual)
    try:
        print("→ Intentando usar Google Cloud Vision (Óptimo para manuscritos)...")
        from src.infrastructure.ocr.google_vision_adapter import GoogleVisionAdapter
        ocr_service = GoogleVisionAdapter(config)
        print("✓ Google Cloud Vision inicializado correctamente")
        print("💰 1,000 imágenes gratis/mes = 15,000 cédulas gratis/mes")
        print("="*60 + "\n")
    except ImportError as e:
        print(f"✗ Google Cloud Vision no está instalado: {e}")
    except Exception as e:
        print(f"✗ Error al inicializar Google Cloud Vision: {e}")
        print("   Asegúrate de configurar GOOGLE_APPLICATION_CREDENTIALS")

    # Fallback a TrOCR
    if ocr_service is None:
        try:
            print("\n→ Intentando usar TrOCR (Microsoft - Estado del arte para manuscritos)...")
            from src.infrastructure.ocr.trocr_adapter import TrOCRAdapter
            ocr_service = TrOCRAdapter(config)
            print("✓ TrOCR inicializado correctamente")
            print("="*60 + "\n")
        except ImportError as e:
            print(f"✗ TrOCR no está instalado: {e}")
        except Exception as e:
            print(f"✗ Error al inicializar TrOCR: {e}")

    # Fallback a PaddleOCR
    if ocr_service is None:
        try:
            print("\n→ Intentando usar PaddleOCR (alternativa para escritura manual)...")
            from src.infrastructure.ocr.paddleocr_adapter import PaddleOCRAdapter
            ocr_service = PaddleOCRAdapter(config)
            print("✓ PaddleOCR inicializado correctamente")
            print("="*60 + "\n")
        except Exception as e:
            print(f"✗ PaddleOCR no disponible: {e}")

    # Fallback a Tesseract (no óptimo para escritura manual)
    if ocr_service is None:
        try:
            print("\n→ Usando Tesseract OCR (limitado para escritura manual)...")
            ocr_service = ocr_module.TesseractOCR(config)
            print("✓ Tesseract OCR inicializado")
            print("⚠ ADVERTENCIA: Tesseract no es óptimo para escritura manual")
            print("="*60 + "\n")
        except Exception as e:
            print(f"✗ Tesseract no disponible: {e}")

    # Fallback final: Entrada manual
    if ocr_service is None:
        print("\n" + "="*60)
        print("⚠ MODO MANUAL ACTIVADO")
        print("="*60)
        print("No hay motores de OCR disponibles.")
        print("Deberá ingresar las cédulas manualmente en la consola.")
        print("="*60 + "\n")
        ocr_service = ocr_module.ManualOCR(config)
    screen_capture = PyAutoGUICapture()
    automation = PyAutoGUIAutomation()

    # Casos de uso
    capture_use_case = CaptureScreenUseCase(screen_capture, config, logger)
    extract_use_case = ExtractCedulasUseCase(ocr_service, logger)
    process_use_case = ProcessCedulaUseCase(automation, config, logger)
    session_use_case = ManageSessionUseCase(logger)

    # UI y Controller
    window = MainWindow()
    controller = MainController(
        window=window,
        capture_use_case=capture_use_case,
        extract_use_case=extract_use_case,
        process_use_case=process_use_case,
        session_use_case=session_use_case,
        automation=automation,
        logger=logger
    )

    # Nota: El controlador ya maneja la extracción y creación de sesión
    # No es necesario conectar señales adicionales aquí

    # Logging inicial
    logger.info("Aplicación iniciada")
    window.add_log("Aplicación iniciada correctamente", "INFO")
    window.add_log("Presione 'Seleccionar Área' para comenzar", "INFO")

    # Mostrar ventana
    window.show()

    # Ejecutar aplicación
    exit_code = app.exec()

    # Cleanup
    automation.unregister_all_hotkeys()
    logger.info("Aplicación cerrada")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
