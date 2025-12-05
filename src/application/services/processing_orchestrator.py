"""Orquestador del flujo completo de procesamiento de formularios."""
from enum import Enum
from typing import List
from PIL import Image

from ...domain.entities import RowData
from ...domain.ports import OCRPort, LoggerPort, AlertHandlerPort, ProgressHandlerPort
from .row_processor import RowProcessor, ProcessingResultType
from .keyboard_controller import KeyboardController
from .processing_reporter import ProcessingReporter, ProcessingStats


class OrchestratorState(Enum):
    """Estados del orchestrator."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED_ESC = "paused_esc"
    PAUSED_ALERT = "paused_alert"
    PAUSED_ERROR = "paused_error"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProcessingOrchestrator:
    """
    Orquestador del flujo completo de procesamiento de formularios.

    Responsabilidad ÚNICA: Coordinar componentes especializados.

    Coordina:
    - OCR Service: Extracción de renglones del formulario
    - RowProcessor: Procesamiento individual de cada renglón
    - KeyboardController: Eventos de pausa (ESC) y reanudación (F9)
    - ProcessingReporter: Estadísticas y reportes
    - AlertHandler: Alertas al usuario
    - ProgressHandler: Notificaciones de progreso

    Esta clase NO contiene lógica de procesamiento, solo coordinación.
    Toda la lógica está delegada a los componentes especializados.

    Example:
        >>> orchestrator = ProcessingOrchestrator(
        ...     ocr_service=digit_ensemble,
        ...     row_processor=processor,
        ...     alert_handler=gui_alerts,
        ...     progress_handler=progress_bar,
        ...     keyboard_controller=kb_controller,
        ...     reporter=reporter,
        ...     logger=logger
        ... )
        >>> stats = orchestrator.process_form(form_image)
        >>> print(f"Procesados: {stats.processed_rows}/{stats.total_rows}")
    """

    def __init__(
        self,
        ocr_service: OCRPort,
        row_processor: RowProcessor,
        alert_handler: AlertHandlerPort,
        progress_handler: ProgressHandlerPort,
        keyboard_controller: KeyboardController,
        reporter: ProcessingReporter,
        logger: LoggerPort
    ):
        """
        Inicializa el orchestrator con todas las dependencias.

        Args:
            ocr_service: Servicio OCR para extraer renglones (Google Vision / Azure / Ensemble)
            row_processor: Procesador de renglones individuales
            alert_handler: Manejador de alertas al usuario
            progress_handler: Manejador de notificaciones de progreso
            keyboard_controller: Controlador de eventos de teclado
            reporter: Generador de reportes y estadísticas
            logger: Logger estructurado

        Note:
            TODAS las dependencias son inyectadas - NO se instancia nada internamente.
            Esto hace que la clase sea 100% testeable con mocks.
        """
        self.ocr_service = ocr_service
        self.row_processor = row_processor
        self.alert_handler = alert_handler
        self.progress_handler = progress_handler
        self.keyboard = keyboard_controller
        self.reporter = reporter
        self.logger = logger.bind(component="ProcessingOrchestrator")

        self.state = OrchestratorState.IDLE
        self._pause_requested = False

    def process_form(self, form_image: Image.Image) -> ProcessingStats:
        """
        Procesa un formulario completo.

        Flujo principal:
        1. Extraer todos los renglones con OCR
        2. Configurar keyboard listener (ESC/F9)
        3. Para cada renglón:
           a. Verificar si se solicitó pausa
           b. Procesar renglón con row_processor
           c. Actualizar estadísticas
           d. Notificar progreso
        4. Mostrar resumen final
        5. Retornar estadísticas

        Args:
            form_image: Imagen del formulario manuscrito

        Returns:
            ProcessingStats con estadísticas del procesamiento

        Raises:
            ValueError: Si form_image es None o inválida
            RuntimeError: Si hay error crítico durante procesamiento

        Example:
            >>> stats = orchestrator.process_form(form_image)
            >>> print(f"✅ {stats.auto_saved} guardados")
            >>> print(f"⚠️  {stats.required_validation} requirieron validación")
        """
        if form_image is None:
            raise ValueError("form_image no puede ser None")

        self.logger.info("=" * 80)
        self.logger.info("Iniciando procesamiento de formulario")
        self.logger.info("=" * 80)

        self.state = OrchestratorState.IDLE
        self.reporter.reset()
        self._pause_requested = False

        try:
            # PASO 1: Extraer renglones con OCR
            rows_data = self._extract_rows(form_image)

            # PASO 2: Configurar keyboard listener
            self._setup_keyboard()

            # PASO 3: Procesar renglones secuencialmente
            self._process_all_rows(rows_data)

            # PASO 4: Mostrar resumen final
            self._show_completion_summary()

            self.state = OrchestratorState.COMPLETED

        except Exception as e:
            self.logger.error("Error crítico en procesamiento", error=str(e))
            self.state = OrchestratorState.PAUSED_ERROR
            self.reporter.stats.increment_errors()

            # Mostrar error al usuario
            action = self.alert_handler.show_error_alert(
                error_message=f"Error crítico: {str(e)}"
            )

        finally:
            # PASO 5: Limpiar recursos
            self._cleanup()

        return self.reporter.stats

    def _extract_rows(self, form_image: Image.Image) -> List[RowData]:
        """
        Extrae renglones del formulario con OCR.

        Args:
            form_image: Imagen del formulario

        Returns:
            Lista de RowData con los renglones detectados
        """
        self.logger.info("Extrayendo renglones con OCR...")
        self.progress_handler.set_status("Extrayendo renglones con OCR...")

        # Preprocesar imagen
        processed_image = self.ocr_service.preprocess_image(form_image)

        # Extraer renglones completos (nombres + cédulas)
        rows_data = self.ocr_service.extract_full_form_data(
            processed_image,
            expected_rows=15  # Formulario E-11 estándar
        )

        self.reporter.stats.total_rows = len(rows_data)

        self.logger.info(
            "Renglones extraídos exitosamente",
            total_rows=len(rows_data)
        )

        return rows_data

    def _setup_keyboard(self) -> None:
        """Configura el keyboard listener con callbacks."""
        # Configurar callbacks
        self.keyboard.on_pause = self._request_pause
        self.keyboard.on_resume = self._request_resume

        # Iniciar listener
        self.keyboard.start()

        self.logger.info("Keyboard listener configurado", pause="ESC", resume="F9")

    def _process_all_rows(self, rows_data: List[RowData]) -> None:
        """
        Procesa todos los renglones secuencialmente.

        Args:
            rows_data: Lista de renglones a procesar
        """
        self.logger.info("Iniciando procesamiento de renglones...")
        self.progress_handler.set_status("Procesando renglones...")

        self.state = OrchestratorState.RUNNING

        for row_index, row_data in enumerate(rows_data):
            row_number = row_index + 1

            # Verificar si se solicitó pausa
            if self._pause_requested:
                self._handle_pause(row_number)

                # Si no se reanudó, terminar
                if self.state != OrchestratorState.RUNNING:
                    break

            # Procesar renglón
            result = self._process_single_row(row_data, row_number)

            # Actualizar estadísticas según resultado
            self._update_stats(result)

            # Notificar progreso
            self._notify_progress(row_number)

    def _process_single_row(self, row_data: RowData, row_number: int):
        """
        Procesa un renglón individual (delega a row_processor).

        Args:
            row_data: Datos del renglón
            row_number: Número de renglón

        Returns:
            ProcessingResult del row_processor
        """
        self.logger.info(
            "Procesando renglón",
            row_number=row_number,
            total=self.reporter.stats.total_rows
        )

        # Delegar todo el procesamiento al row_processor
        result = self.row_processor.process_row(
            row_data=row_data,
            row_number=row_number,
            alert_handler=self.alert_handler
        )

        return result

    def _update_stats(self, result) -> None:
        """
        Actualiza estadísticas según el resultado del procesamiento.

        Args:
            result: ProcessingResult del row_processor
        """
        # Siempre incrementar procesados
        self.reporter.stats.increment_processed()

        # Incrementar contadores específicos según el tipo
        if result.result_type == ProcessingResultType.AUTO_SAVED:
            self.reporter.stats.increment_auto_saved()
        elif result.result_type == ProcessingResultType.REQUIRED_VALIDATION:
            self.reporter.stats.increment_required_validation()
        elif result.result_type == ProcessingResultType.EMPTY_ROW:
            self.reporter.stats.increment_empty_rows()
        elif result.result_type == ProcessingResultType.NOT_FOUND:
            self.reporter.stats.increment_not_found()
        elif result.result_type == ProcessingResultType.ERROR:
            self.reporter.stats.increment_errors()

    def _notify_progress(self, current_row: int) -> None:
        """
        Notifica progreso al progress_handler.

        Args:
            current_row: Renglón actual (1-indexed)
        """
        stats = self.reporter.stats

        self.progress_handler.update_progress(
            current=stats.processed_rows,
            total=stats.total_rows,
            message=self.reporter.get_progress_message(current_row)
        )

    def _request_pause(self) -> None:
        """Callback cuando se presiona ESC - solicita pausa."""
        if self.state == OrchestratorState.RUNNING:
            self._pause_requested = True
            self.logger.info("Pausa solicitada - completará renglón actual")

    def _request_resume(self) -> None:
        """Callback cuando se presiona F9 - solicita reanudación."""
        if self.state == OrchestratorState.PAUSED_ESC:
            self.logger.info("Reanudación solicitada")
            self.state = OrchestratorState.RUNNING
            self._pause_requested = False

    def _handle_pause(self, current_row: int) -> None:
        """
        Maneja la pausa del proceso.

        Args:
            current_row: Renglón actual cuando se pausó
        """
        self.logger.info(
            "Proceso pausado",
            current_row=current_row,
            total_rows=self.reporter.stats.total_rows
        )

        self.state = OrchestratorState.PAUSED_ESC
        self._pause_requested = False

        self.progress_handler.set_status(
            f"PAUSADO - Renglón {current_row}/{self.reporter.stats.total_rows}"
        )

        # Esperar a que el usuario presione F9 para continuar
        # El keyboard_controller llamará a _request_resume()
        import time
        while self.state == OrchestratorState.PAUSED_ESC:
            time.sleep(0.1)  # Polling cada 100ms

        if self.state == OrchestratorState.RUNNING:
            self.logger.info("Proceso reanudado")
            self.progress_handler.set_status("Procesando renglones...")

    def _show_completion_summary(self) -> None:
        """Muestra resumen de completación."""
        self.logger.info("=" * 80)
        self.logger.info("Procesamiento completado")
        self.logger.info("=" * 80)

        # Log del resumen
        summary = self.reporter.get_summary()
        self.logger.info(summary)

        # Notificar al progress_handler
        self.progress_handler.show_completion_summary(
            self.reporter.stats.to_dict()
        )

        self.progress_handler.set_status("Completado")

    def _cleanup(self) -> None:
        """Limpia recursos (keyboard listener, etc.)."""
        self.logger.info("Limpiando recursos...")

        # Detener keyboard listener
        if self.keyboard.is_active():
            self.keyboard.stop()

        self.logger.info("Recursos liberados")

    def cancel(self) -> None:
        """Cancela el procesamiento en curso."""
        self.logger.info("Cancelación solicitada")
        self.state = OrchestratorState.CANCELLED
        self._cleanup()
