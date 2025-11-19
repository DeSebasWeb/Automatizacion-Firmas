"""Controlador de automatización para el flujo completo OCR dual."""
import time
from typing import List, Optional, Dict, Callable
from enum import Enum
from dataclasses import dataclass
import pyautogui
from pynput import keyboard

from ...domain.entities import RowData, FormData, ValidationResult, ValidationAction
from ...infrastructure.ocr.google_vision_adapter import GoogleVisionAdapter
from ...infrastructure.ocr.tesseract_web_scraper import TesseractWebScraper
from ..services.fuzzy_validator import FuzzyValidator


class AutomationState(Enum):
    """Estados del sistema de automatización."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED_ESC = "PAUSED_ESC"
    PAUSED_ALERT = "PAUSED_ALERT"
    PAUSED_ERROR = "PAUSED_ERROR"
    COMPLETED = "COMPLETED"


@dataclass
class ProcessingStats:
    """Estadísticas del procesamiento."""
    total_rows: int = 0
    processed_rows: int = 0
    auto_saved: int = 0
    required_validation: int = 0
    empty_rows: int = 0
    not_found: int = 0
    errors: int = 0

    def get_summary(self) -> str:
        """Obtiene resumen de estadísticas."""
        return f"""
╔═══════════════════════════════════════════════════════════╗
║           RESUMEN DE PROCESAMIENTO                        ║
╠═══════════════════════════════════════════════════════════╣
║ Total de renglones:              {self.total_rows:>3}                  ║
║ Procesados:                      {self.processed_rows:>3}                  ║
║ ✓ Guardados automáticamente:     {self.auto_saved:>3}                  ║
║ ⚠ Requirieron validación:        {self.required_validation:>3}                  ║
║ ○ Renglones vacíos:              {self.empty_rows:>3}                  ║
║ ✗ No encontrados:                {self.not_found:>3}                  ║
║ ⚠ Errores:                       {self.errors:>3}                  ║
╚═══════════════════════════════════════════════════════════╝
"""


class AutomationController:
    """
    Controlador de automatización para el flujo completo OCR dual.

    Responsabilidades:
    - Coordinar flujo automático completo
    - Procesar cada renglón secuencialmente
    - Manejar pausas (ESC/F9)
    - Gestionar alertas
    - Logging detallado

    Flujo:
    1. Extraer todos los renglones con Google Vision
    2. Para cada renglón:
       A) Si vacío → click en "Renglón En Blanco"
       B) Si tiene datos:
          - Digitar cédula
          - Leer formulario web con Tesseract
          - Validar con FuzzyValidator
          - Decidir acción (AUTO_SAVE, REQUIRE_VALIDATION, ALERT_NOT_FOUND)
    3. Manejar pausas ESC en cualquier momento
    """

    def __init__(
        self,
        config: Optional[Dict] = None,
        on_alert: Optional[Callable[[str, ValidationResult], str]] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None
    ):
        """
        Inicializa el controlador de automatización.

        Args:
            config: Configuración del sistema
            on_alert: Callback para mostrar alertas (retorna acción del usuario)
            on_progress: Callback para actualizar progreso
        """
        self.config = config or self._get_default_config()
        self.on_alert = on_alert
        self.on_progress = on_progress

        # Componentes OCR
        self.google_vision = GoogleVisionAdapter(config=self.config.get('ocr', {}).get('google_vision'))
        self.tesseract = TesseractWebScraper(config=self.config.get('ocr', {}).get('tesseract'))
        self.validator = FuzzyValidator(
            min_similarity=self.config.get('validation', {}).get('min_similarity', 0.85)
        )

        # Estado
        self.state = AutomationState.IDLE
        self.stats = ProcessingStats()
        self.current_row_index = 0
        self.pause_requested = False

        # Configuración de automatización
        self.typing_delay = self.config.get('automation', {}).get('typing_delay_ms', 50) / 1000
        self.click_delay = self.config.get('automation', {}).get('click_delay_ms', 300) / 1000
        self.page_load_timeout = self.config.get('automation', {}).get('page_load_timeout', 5)

        # Listener de teclado
        self.keyboard_listener = None

    def _get_default_config(self) -> Dict:
        """Configuración por defecto."""
        return {
            'automation': {
                'enabled': True,
                'typing_delay_ms': 50,
                'click_delay_ms': 300,
                'page_load_timeout': 5,
                'auto_click_save': True,
                'auto_handle_empty_rows': True
            },
            'validation': {
                'enabled': True,
                'min_similarity': 0.85
            },
            'empty_row_handling': {
                'auto_click_button': True,
                'button_name': 'Renglón En Blanco',
                'log_empty_rows': True
            }
        }

    def start_keyboard_listener(self):
        """Inicia el listener de teclado para pausas ESC y resume F9."""
        def on_press(key):
            try:
                if key == keyboard.Key.esc:
                    self._request_pause()
                elif key == keyboard.Key.f9:
                    self._request_resume()
            except AttributeError:
                pass

        self.keyboard_listener = keyboard.Listener(on_press=on_press)
        self.keyboard_listener.start()
        print("✓ Listener de teclado activo - ESC: pausar | F9: reanudar")

    def stop_keyboard_listener(self):
        """Detiene el listener de teclado."""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

    def _request_pause(self):
        """Solicita pausa del proceso."""
        if self.state == AutomationState.RUNNING:
            self.pause_requested = True
            print("\n⏸️  PAUSA SOLICITADA - Se detendrá después del renglón actual...")

    def _request_resume(self):
        """Solicita reanudación del proceso pausado."""
        if self.state == AutomationState.PAUSED_ESC:
            print("\n▶️  REANUDANDO PROCESO...")
            self.state = AutomationState.RUNNING
            self.pause_requested = False
        elif self.state == AutomationState.PAUSED_ALERT:
            print("\n⚠️  No se puede reanudar - esperando decisión de alerta")

    def process_all_rows(self, form_image) -> ProcessingStats:
        """
        Procesa todos los renglones del formulario manuscrito.

        Args:
            form_image: Imagen del formulario manuscrito

        Returns:
            Estadísticas del procesamiento
        """
        print("\n" + "="*70)
        print("INICIANDO PROCESAMIENTO AUTOMÁTICO OCR DUAL")
        print("="*70)

        # Iniciar listener de teclado
        self.start_keyboard_listener()

        try:
            # Paso 1: Extraer todos los renglones con Google Vision
            print("\n[1/2] Extrayendo renglones con Google Vision...")
            rows_data = self.google_vision.extract_full_form_data(form_image)

            self.stats.total_rows = len(rows_data)
            print(f"✓ {len(rows_data)} renglones detectados\n")

            # Paso 2: Procesar cada renglón
            print("[2/2] Procesando renglones secuencialmente...\n")
            self.state = AutomationState.RUNNING

            for row_index, row_data in enumerate(rows_data):
                self.current_row_index = row_index

                # Verificar si se solicitó pausa
                if self.pause_requested:
                    self._handle_pause()
                    if self.state != AutomationState.RUNNING:
                        break

                # Procesar renglón
                self._process_single_row(row_data, row_index + 1)
                self.stats.processed_rows += 1

                # Actualizar progreso
                if self.on_progress:
                    self.on_progress(
                        self.stats.processed_rows,
                        self.stats.total_rows,
                        f"Renglón {row_index + 1}/{len(rows_data)}"
                    )

            # Completado
            self.state = AutomationState.COMPLETED
            print("\n" + "="*70)
            print("PROCESAMIENTO COMPLETADO")
            print("="*70)
            print(self.stats.get_summary())

        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO: {e}")
            self.state = AutomationState.PAUSED_ERROR
            self.stats.errors += 1

        finally:
            self.stop_keyboard_listener()

        return self.stats

    def _process_single_row(self, row_data: RowData, row_number: int):
        """
        Procesa un renglón individual.

        Args:
            row_data: Datos del renglón manuscrito
            row_number: Número de renglón (1-indexed)
        """
        print(f"\n{'─'*70}")
        print(f"Renglón {row_number}/{self.stats.total_rows}")
        print(f"{'─'*70}")

        # CASO 1: Renglón vacío
        if row_data.is_empty:
            self._handle_empty_row(row_number)
            return

        # CASO 2: Renglón con datos
        print(f"📝 Manuscrito: {row_data.nombres_manuscritos}")
        print(f"🔢 Cédula:     {row_data.cedula}")

        # Paso A: Digitar cédula
        print(f"\n[A] Digitando cédula {row_data.cedula}...")
        self._type_cedula(row_data.cedula)

        # Paso B: Esperar carga de página
        print(f"[B] Esperando carga (max {self.page_load_timeout}s)...")
        time.sleep(self.page_load_timeout)

        # Paso C: Leer formulario web con Tesseract
        print(f"[C] Leyendo formulario web con Tesseract...")
        digital_data = self.tesseract.get_all_fields(cedula_consultada=row_data.cedula)

        # Paso D: Validar con FuzzyValidator
        print(f"[D] Validando con fuzzy matching...")
        validation_result = self.validator.validate_person(row_data, digital_data)

        # Paso E: Ejecutar acción según validación
        self._execute_validation_action(validation_result, row_data, digital_data, row_number)

    def _handle_empty_row(self, row_number: int):
        """
        Maneja un renglón vacío.

        Args:
            row_number: Número de renglón
        """
        print(f"○ Renglón vacío detectado")

        auto_handle = self.config.get('empty_row_handling', {}).get('auto_click_button', True)

        if auto_handle:
            button_name = self.config.get('empty_row_handling', {}).get('button_name', 'Renglón En Blanco')
            print(f"✓ Click automático en '{button_name}'")

            # TODO: Implementar click en botón específico
            # self._click_button(button_name)

            self.stats.empty_rows += 1
        else:
            print(f"⚠️  Renglón vacío - requiere acción manual")
            if self.on_alert:
                action = self.on_alert(
                    f"Renglón {row_number} está vacío",
                    None
                )

    def _handle_person_not_found(self, row_data: RowData, row_number: int):
        """
        Maneja el caso de persona no encontrada en BD.

        Args:
            row_data: Datos del renglón manuscrito
            row_number: Número de renglón
        """
        print(f"\n⚠️  ALERTA: Persona NO encontrada en base de datos")
        print(f"Cédula: {row_data.cedula}")
        print(f"Nombres: {row_data.nombres_manuscritos}")

        self.stats.not_found += 1

        # Pausar y alertar
        if self.on_alert:
            action = self.on_alert(
                f"Cédula {row_data.cedula} no existe en base de datos",
                None
            )

            # Según la acción del usuario:
            # - "continue": continuar con siguiente renglón
            # - "mark_issue": marcar novedad
            # - "pause": pausar proceso

            if action == "pause":
                self.state = AutomationState.PAUSED_ALERT

    def _handle_validation_mismatch(
        self,
        validation_result: ValidationResult,
        row_data: RowData,
        digital_data: FormData,
        row_number: int
    ):
        """
        Maneja el caso de validación que requiere intervención.

        Args:
            validation_result: Resultado de validación
            row_data: Datos manuscritos
            digital_data: Datos digitales
            row_number: Número de renglón
        """
        print(f"\n⚠️  VALIDACIÓN REQUERIDA")
        print(f"\nComparación:")
        print(f"  Manuscrito: {validation_result.manuscrito_nombres}")
        print(f"  Digital:    {validation_result.digital_nombres}")
        print(f"\nDetalles: {validation_result.details}")

        if validation_result.matches:
            print(f"\nCampos comparados:")
            for field_name, match in validation_result.matches.items():
                status = "✓" if match.match else "✗"
                print(f"  {status} {field_name}: {match.compared} ({match.similarity:.0%})")

        self.stats.required_validation += 1

        # Pausar y mostrar alerta
        if self.on_alert:
            action = self.on_alert(
                f"Renglón {row_number} requiere validación manual",
                validation_result
            )

            # Según la acción del usuario:
            # - "save": guardar de todas formas
            # - "skip": saltar este renglón
            # - "correct": corregir manualmente

            if action == "save":
                self._click_save_button()
                self.stats.auto_saved += 1
            elif action == "skip":
                print(f"⏭️  Renglón saltado")

    def _execute_validation_action(
        self,
        validation_result: ValidationResult,
        row_data: RowData,
        digital_data: FormData,
        row_number: int
    ):
        """
        Ejecuta la acción según el resultado de validación.

        Args:
            validation_result: Resultado de validación
            row_data: Datos manuscritos
            digital_data: Datos digitales
            row_number: Número de renglón
        """
        action = validation_result.action

        if action == ValidationAction.AUTO_SAVE:
            # GUARDADO AUTOMÁTICO
            print(f"\n✓ VALIDACIÓN OK - Guardado automático")
            print(f"  Confianza: {validation_result.confidence:.0%}")

            if self.config.get('automation', {}).get('auto_click_save', True):
                self._click_save_button()
                self.stats.auto_saved += 1

        elif action == ValidationAction.ALERT_NOT_FOUND:
            # PERSONA NO ENCONTRADA
            self._handle_person_not_found(row_data, row_number)

        elif action == ValidationAction.REQUIRE_VALIDATION:
            # REQUIERE VALIDACIÓN MANUAL
            self._handle_validation_mismatch(validation_result, row_data, digital_data, row_number)

    def _type_cedula(self, cedula: str):
        """
        Digita la cédula en el campo de búsqueda.

        Args:
            cedula: Cédula a digitar
        """
        # TODO: Implementar según el sistema real
        # Por ahora, simulación con pyautogui
        for char in cedula:
            pyautogui.write(char, interval=self.typing_delay)

        # Presionar Enter
        time.sleep(self.click_delay)
        pyautogui.press('enter')

    def _click_save_button(self):
        """Click en el botón de guardar."""
        print(f"  → Click en 'Guardar'")
        # TODO: Implementar click en botón específico según la UI
        # pyautogui.click(x, y)
        time.sleep(self.click_delay)

    def _click_button(self, button_name: str):
        """
        Click en un botón específico.

        Args:
            button_name: Nombre del botón
        """
        # TODO: Implementar búsqueda y click en botón
        print(f"  → Click en '{button_name}'")
        time.sleep(self.click_delay)

    def _handle_pause(self):
        """Maneja la pausa del proceso."""
        print("\n⏸️  PROCESO PAUSADO")
        print(f"Renglón actual: {self.current_row_index + 1}/{self.stats.total_rows}")
        print("Presiona F9 para continuar...")

        self.state = AutomationState.PAUSED_ESC
        self.pause_requested = False

        # Esperar a que el usuario presione F9 para continuar
        # El listener de teclado cambiará el estado cuando se presione F9
        while self.state == AutomationState.PAUSED_ESC:
            time.sleep(0.1)  # Polling cada 100ms

        if self.state == AutomationState.RUNNING:
            print("✓ Proceso reanudado")
        else:
            print("⚠️ Proceso interrumpido")

    def resume(self):
        """Resume el proceso pausado."""
        if self.state == AutomationState.PAUSED_ESC:
            print("\n▶️  REANUDANDO PROCESO...")
            self.state = AutomationState.RUNNING
            self.pause_requested = False

    def cancel(self):
        """Cancela el proceso."""
        print("\n❌ PROCESO CANCELADO")
        self.state = AutomationState.IDLE
        self.stop_keyboard_listener()
