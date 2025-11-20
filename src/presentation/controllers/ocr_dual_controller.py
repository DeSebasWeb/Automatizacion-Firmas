"""Controlador para el procesamiento OCR dual automático."""
from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QMessageBox
from typing import Optional
from PIL import Image

from ..ui import ValidationAlertDialog, PersonNotFoundDialog, ProgressPanel
from ...application.controllers import AutomationController, AutomationState, ProcessingStats
from ...domain.entities import ValidationResult
from ...domain.ports import LoggerPort


class OCRDualController(QObject):
    """
    Controlador para el procesamiento OCR dual automático.

    Integra el AutomationController con la UI principal y maneja:
    - Callbacks de alertas
    - Callbacks de progreso
    - Diálogos de validación
    - Panel de estadísticas
    """

    def __init__(
        self,
        automation_controller: AutomationController,
        progress_panel: ProgressPanel,
        logger: LoggerPort,
        parent=None
    ):
        """
        Inicializa el controlador OCR dual.

        Args:
            automation_controller: Controlador de automatización
            progress_panel: Panel de progreso visual
            logger: Servicio de logging
            parent: Widget padre
        """
        super().__init__(parent)
        self.automation_controller = automation_controller
        self.progress_panel = progress_panel
        self.logger = logger.bind(component="OCRDualController")

        # Configurar callbacks
        self.automation_controller.on_alert = self._handle_alert
        self.automation_controller.on_progress = self._handle_progress

        # Timer para actualizar estadísticas en UI thread
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_stats_ui)
        self.update_timer.setInterval(500)  # Actualizar cada 500ms

    def start_processing(self, form_image: Image.Image):
        """
        Inicia el procesamiento OCR dual automático.

        Args:
            form_image: Imagen del formulario manuscrito capturado
        """
        self.logger.info("Iniciando procesamiento OCR dual automático")

        # Resetear estadísticas
        self.progress_panel.reset_stats()
        self.progress_panel.set_processing_state()

        # Iniciar timer de actualización
        self.update_timer.start()

        # Iniciar procesamiento en thread separado para no bloquear UI
        # (Nota: Por simplicidad, lo ejecutamos en el mismo thread por ahora)
        # TODO: Mover a QThread para no bloquear la UI
        try:
            stats = self.automation_controller.process_all_rows(form_image)

            # Detener timer
            self.update_timer.stop()

            # Actualizar estadísticas finales
            self._update_stats_from_object(stats)

            # Cambiar estado según resultado
            if self.automation_controller.state == AutomationState.COMPLETED:
                self.progress_panel.set_completed_state()
                self.logger.info("Procesamiento OCR dual completado", stats=stats.__dict__)
            elif self.automation_controller.state == AutomationState.PAUSED_ESC:
                self.progress_panel.set_paused_state()
                self.logger.info("Procesamiento pausado por usuario")
            else:
                self.progress_panel.set_error_state()
                self.logger.warning("Procesamiento terminó con estado inesperado")

        except Exception as e:
            self.update_timer.stop()
            self.progress_panel.set_error_state()
            self.logger.error("Error en procesamiento OCR dual", error=str(e))

            # Mostrar mensaje de error
            QMessageBox.critical(
                None,
                "Error de Procesamiento",
                f"Ocurrió un error durante el procesamiento OCR dual:\n\n{str(e)}"
            )

    def _handle_alert(self, message: str, validation_result: Optional[ValidationResult]) -> str:
        """
        Maneja alertas del AutomationController mostrando diálogos.

        Args:
            message: Mensaje de alerta
            validation_result: Resultado de validación (si aplica)

        Returns:
            Acción seleccionada por el usuario
        """
        self.logger.info("Mostrando alerta de validación", message=message)

        # Pausar timer de actualización mientras se muestra el diálogo
        was_running = self.update_timer.isActive()
        if was_running:
            self.update_timer.stop()

        try:
            if validation_result is None:
                # Alerta de persona no encontrada
                # Extraer información del mensaje
                # (Idealmente deberíamos pasar más contexto)
                dialog = PersonNotFoundDialog(
                    cedula="",  # TODO: Pasar cédula real
                    nombres_manuscritos="",  # TODO: Pasar nombres reales
                    row_number=self.automation_controller.current_row_index + 1,
                    parent=None
                )
            else:
                # Alerta de validación con mismatch
                dialog = ValidationAlertDialog(
                    validation_result=validation_result,
                    row_number=self.automation_controller.current_row_index + 1,
                    parent=None
                )

            # Mostrar diálogo modal
            result = dialog.exec()

            if result:
                action = dialog.get_user_action()
                self.logger.info("Usuario seleccionó acción", action=action)
                return action or "pause"
            else:
                # Usuario cerró el diálogo
                return "pause"

        finally:
            # Reanudar timer si estaba corriendo
            if was_running:
                self.update_timer.start()

    def _handle_progress(self, current: int, total: int, state_text: str):
        """
        Maneja actualizaciones de progreso.

        Args:
            current: Renglones procesados
            total: Total de renglones
            state_text: Texto de estado actual
        """
        # Actualizar barra de progreso
        self.progress_panel.update_progress(current, total, state_text)

        self.logger.debug(
            "Progreso actualizado",
            current=current,
            total=total,
            state=state_text
        )

    def _update_stats_ui(self):
        """Actualiza las estadísticas en la UI (llamado por timer)."""
        stats = self.automation_controller.stats
        self._update_stats_from_object(stats)

    def _update_stats_from_object(self, stats: ProcessingStats):
        """
        Actualiza las estadísticas desde un objeto ProcessingStats.

        Args:
            stats: Objeto con estadísticas
        """
        self.progress_panel.update_stats(
            total=stats.total_rows,
            processed=stats.processed_rows,
            auto_saved=stats.auto_saved,
            required_validation=stats.required_validation,
            empty_rows=stats.empty_rows,
            not_found=stats.not_found,
            errors=stats.errors
        )

    def pause_processing(self):
        """Pausa el procesamiento actual."""
        self.automation_controller._request_pause()
        self.progress_panel.set_paused_state()
        self.logger.info("Pausa solicitada")

    def resume_processing(self):
        """Reanuda el procesamiento pausado."""
        self.automation_controller._request_resume()
        self.progress_panel.set_processing_state()
        self.logger.info("Procesamiento reanudado")

    def cancel_processing(self):
        """Cancela el procesamiento actual."""
        self.automation_controller.cancel()
        self.update_timer.stop()
        self.progress_panel.set_error_state()
        self.logger.info("Procesamiento cancelado")

    def get_stats_summary(self) -> str:
        """
        Obtiene un resumen de las estadísticas.

        Returns:
            String con resumen formateado
        """
        return self.automation_controller.stats.get_summary()
