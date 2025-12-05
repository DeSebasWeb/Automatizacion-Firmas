"""Tests unitarios para ProcessingOrchestrator.

Cobertura:
- Inicialización con dependencies
- Flujo completo de procesamiento
- Extracción de renglones con OCR
- Configuración de keyboard
- Procesamiento secuencial de renglones
- Actualización de estadísticas
- Manejo de pausas
- Cleanup de recursos
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from PIL import Image

from src.application.services.processing_orchestrator import (
    ProcessingOrchestrator,
    OrchestratorState
)
from src.application.services.row_processor import ProcessingResult, ProcessingResultType
from src.domain.entities import RowData


class TestProcessingOrchestratorInitialization:
    """Tests de inicialización."""

    def test_initialization_with_all_dependencies(self):
        """Test que inicializa con todas las dependencias."""
        orchestrator = create_orchestrator()

        assert orchestrator.ocr_service is not None
        assert orchestrator.row_processor is not None
        assert orchestrator.alert_handler is not None
        assert orchestrator.progress_handler is not None
        assert orchestrator.keyboard is not None
        assert orchestrator.reporter is not None
        assert orchestrator.logger is not None

    def test_initial_state_is_idle(self):
        """Test que estado inicial es IDLE."""
        orchestrator = create_orchestrator()

        assert orchestrator.state == OrchestratorState.IDLE
        assert orchestrator._pause_requested is False


class TestProcessFormValidation:
    """Tests de validación de inputs."""

    def test_process_form_with_none_raises_error(self):
        """Test que None image lanza ValueError."""
        orchestrator = create_orchestrator()

        with pytest.raises(ValueError, match="form_image no puede ser None"):
            orchestrator.process_form(None)


class TestProcessFormFlow:
    """Tests del flujo completo de procesamiento."""

    def test_process_form_extracts_rows(self):
        """Test que extrae renglones con OCR."""
        ocr_mock = Mock()
        ocr_mock.preprocess_image.return_value = Mock()
        ocr_mock.extract_full_form_data.return_value = [
            RowData(cedula="123", nombres_manuscritos="JUAN PEREZ"),
            RowData(cedula="456", nombres_manuscritos="MARIA GOMEZ")
        ]

        orchestrator = create_orchestrator(ocr_service=ocr_mock)

        # Mock row processor to avoid actual processing
        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.AUTO_SAVED,
            success=True,
            row_number=1
        )

        # Mock image
        form_image = Mock(spec=Image.Image)

        orchestrator.process_form(form_image)

        # Verificar que se llamó extract_full_form_data
        ocr_mock.extract_full_form_data.assert_called_once()

    def test_process_form_processes_all_rows(self):
        """Test que procesa todos los renglones."""
        row_processor_mock = Mock()
        row_processor_mock.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.AUTO_SAVED,
            success=True,
            row_number=1
        )

        orchestrator = create_orchestrator(row_processor=row_processor_mock)

        # Mock OCR para retornar 3 renglones
        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN"),
            RowData(cedula="222", nombres_manuscritos="MARIA"),
            RowData(cedula="333", nombres_manuscritos="PEDRO")
        ]

        form_image = Mock(spec=Image.Image)
        orchestrator.process_form(form_image)

        # Verificar que se procesaron los 3 renglones
        assert row_processor_mock.process_row.call_count == 3

    def test_process_form_updates_stats(self):
        """Test que actualiza estadísticas correctamente."""
        orchestrator = create_orchestrator()

        # Mock OCR
        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN"),
            RowData(cedula="222", nombres_manuscritos="MARIA")
        ]

        # Mock row processor
        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.AUTO_SAVED,
            success=True,
            row_number=1
        )

        form_image = Mock(spec=Image.Image)
        stats = orchestrator.process_form(form_image)

        # Verificar estadísticas
        assert stats.total_rows == 2
        assert stats.processed_rows == 2
        assert stats.auto_saved == 2

    def test_process_form_starts_and_stops_keyboard(self):
        """Test que inicia y detiene keyboard controller."""
        keyboard_mock = Mock()
        keyboard_mock.is_active.return_value = True

        orchestrator = create_orchestrator(keyboard_controller=keyboard_mock)

        # Mock OCR
        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN")
        ]

        # Mock row processor
        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.AUTO_SAVED,
            success=True,
            row_number=1
        )

        form_image = Mock(spec=Image.Image)
        orchestrator.process_form(form_image)

        # Verificar que se inició y detuvo el keyboard
        keyboard_mock.start.assert_called_once()
        keyboard_mock.stop.assert_called_once()

    def test_process_form_notifies_progress(self):
        """Test que notifica progreso."""
        progress_mock = Mock()

        orchestrator = create_orchestrator(progress_handler=progress_mock)

        # Mock OCR
        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN"),
            RowData(cedula="222", nombres_manuscritos="MARIA")
        ]

        # Mock row processor
        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.AUTO_SAVED,
            success=True,
            row_number=1
        )

        form_image = Mock(spec=Image.Image)
        orchestrator.process_form(form_image)

        # Verificar que se notificó progreso
        assert progress_mock.update_progress.call_count >= 2  # Al menos 2 veces
        progress_mock.show_completion_summary.assert_called_once()

    def test_process_form_returns_stats(self):
        """Test que retorna estadísticas."""
        orchestrator = create_orchestrator()

        # Mock OCR
        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN")
        ]

        # Mock row processor
        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.AUTO_SAVED,
            success=True,
            row_number=1
        )

        form_image = Mock(spec=Image.Image)
        stats = orchestrator.process_form(form_image)

        # Verificar que retorna stats
        assert hasattr(stats, 'total_rows')
        assert hasattr(stats, 'processed_rows')
        assert hasattr(stats, 'auto_saved')


class TestStatsIncrement:
    """Tests de incremento de estadísticas según tipo de resultado."""

    def test_stats_increment_for_auto_saved(self):
        """Test incremento para AUTO_SAVED."""
        orchestrator = create_orchestrator()

        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN")
        ]

        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.AUTO_SAVED,
            success=True,
            row_number=1
        )

        form_image = Mock(spec=Image.Image)
        stats = orchestrator.process_form(form_image)

        assert stats.auto_saved == 1
        assert stats.processed_rows == 1

    def test_stats_increment_for_required_validation(self):
        """Test incremento para REQUIRED_VALIDATION."""
        orchestrator = create_orchestrator()

        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN")
        ]

        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.REQUIRED_VALIDATION,
            success=False,
            row_number=1
        )

        form_image = Mock(spec=Image.Image)
        stats = orchestrator.process_form(form_image)

        assert stats.required_validation == 1
        assert stats.processed_rows == 1

    def test_stats_increment_for_empty_row(self):
        """Test incremento para EMPTY_ROW."""
        orchestrator = create_orchestrator()

        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="", nombres_manuscritos="")
        ]

        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.EMPTY_ROW,
            success=True,
            row_number=1
        )

        form_image = Mock(spec=Image.Image)
        stats = orchestrator.process_form(form_image)

        assert stats.empty_rows == 1
        assert stats.processed_rows == 1

    def test_stats_increment_for_not_found(self):
        """Test incremento para NOT_FOUND."""
        orchestrator = create_orchestrator()

        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="999", nombres_manuscritos="NO EXISTE")
        ]

        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.NOT_FOUND,
            success=False,
            row_number=1
        )

        form_image = Mock(spec=Image.Image)
        stats = orchestrator.process_form(form_image)

        assert stats.not_found == 1
        assert stats.processed_rows == 1

    def test_stats_increment_for_error(self):
        """Test incremento para ERROR."""
        orchestrator = create_orchestrator()

        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN")
        ]

        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.ERROR,
            success=False,
            row_number=1,
            error_message="Test error"
        )

        form_image = Mock(spec=Image.Image)
        stats = orchestrator.process_form(form_image)

        assert stats.errors == 1
        assert stats.processed_rows == 1


class TestPauseHandling:
    """Tests de manejo de pausas."""

    def test_request_pause_sets_flag(self):
        """Test que _request_pause setea flag."""
        orchestrator = create_orchestrator()
        orchestrator.state = OrchestratorState.RUNNING

        orchestrator._request_pause()

        assert orchestrator._pause_requested is True

    def test_request_resume_clears_flag(self):
        """Test que _request_resume limpia flag."""
        orchestrator = create_orchestrator()
        orchestrator.state = OrchestratorState.PAUSED_ESC
        orchestrator._pause_requested = True

        orchestrator._request_resume()

        assert orchestrator._pause_requested is False
        assert orchestrator.state == OrchestratorState.RUNNING


class TestErrorHandling:
    """Tests de manejo de errores."""

    def test_exception_during_ocr_is_caught(self):
        """Test que excepción durante OCR es capturada."""
        ocr_mock = Mock()
        ocr_mock.preprocess_image.side_effect = Exception("OCR error")

        orchestrator = create_orchestrator(ocr_service=ocr_mock)

        alert_mock = Mock()
        alert_mock.show_error_alert.return_value = "pause"

        orchestrator.alert_handler = alert_mock

        form_image = Mock(spec=Image.Image)

        # No debe crashear
        stats = orchestrator.process_form(form_image)

        # Verificar que se registró el error
        assert stats.errors >= 1

        # Verificar que se mostró alerta de error
        alert_mock.show_error_alert.assert_called()

    def test_cleanup_is_called_even_on_error(self):
        """Test que cleanup se llama incluso si hay error."""
        ocr_mock = Mock()
        ocr_mock.preprocess_image.side_effect = Exception("OCR error")

        keyboard_mock = Mock()
        keyboard_mock.is_active.return_value = True

        orchestrator = create_orchestrator(
            ocr_service=ocr_mock,
            keyboard_controller=keyboard_mock
        )

        # Mock error alert
        orchestrator.alert_handler.show_error_alert.return_value = "pause"

        form_image = Mock(spec=Image.Image)

        orchestrator.process_form(form_image)

        # Verificar que se detuvo el keyboard (cleanup)
        keyboard_mock.stop.assert_called()


class TestStateManagement:
    """Tests de manejo de estados."""

    def test_initial_state_is_idle(self):
        """Test que estado inicial es IDLE."""
        orchestrator = create_orchestrator()
        assert orchestrator.state == OrchestratorState.IDLE

    def test_state_becomes_running_during_processing(self):
        """Test que estado cambia a RUNNING durante procesamiento."""
        orchestrator = create_orchestrator()

        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN")
        ]

        # Capture state during processing
        states_captured = []

        def capture_state(*args, **kwargs):
            states_captured.append(orchestrator.state)
            return ProcessingResult(
                result_type=ProcessingResultType.AUTO_SAVED,
                success=True,
                row_number=1
            )

        orchestrator.row_processor.process_row.side_effect = capture_state

        form_image = Mock(spec=Image.Image)
        orchestrator.process_form(form_image)

        # Verificar que estuvo en RUNNING durante procesamiento
        assert OrchestratorState.RUNNING in states_captured

    def test_final_state_is_completed_on_success(self):
        """Test que estado final es COMPLETED en éxito."""
        orchestrator = create_orchestrator()

        orchestrator.ocr_service.extract_full_form_data.return_value = [
            RowData(cedula="111", nombres_manuscritos="JUAN")
        ]

        orchestrator.row_processor.process_row.return_value = ProcessingResult(
            result_type=ProcessingResultType.AUTO_SAVED,
            success=True,
            row_number=1
        )

        form_image = Mock(spec=Image.Image)
        orchestrator.process_form(form_image)

        assert orchestrator.state == OrchestratorState.COMPLETED


# Helper function para crear orchestrator con mocks
def create_orchestrator(
    ocr_service=None,
    row_processor=None,
    alert_handler=None,
    progress_handler=None,
    keyboard_controller=None,
    reporter=None,
    logger=None
):
    """Helper para crear ProcessingOrchestrator con dependencias mockeadas."""
    if ocr_service is None:
        ocr_service = Mock()
        ocr_service.preprocess_image.return_value = Mock()
        ocr_service.extract_full_form_data.return_value = []

    if row_processor is None:
        row_processor = Mock()

    if alert_handler is None:
        alert_handler = Mock()

    if progress_handler is None:
        progress_handler = Mock()

    if keyboard_controller is None:
        keyboard_controller = Mock()
        keyboard_controller.is_active.return_value = False

    if reporter is None:
        from src.application.services.processing_reporter import ProcessingReporter
        reporter = ProcessingReporter()

    if logger is None:
        logger = Mock()
        logger.bind.return_value = logger

    return ProcessingOrchestrator(
        ocr_service=ocr_service,
        row_processor=row_processor,
        alert_handler=alert_handler,
        progress_handler=progress_handler,
        keyboard_controller=keyboard_controller,
        reporter=reporter,
        logger=logger
    )


# Fixtures
@pytest.fixture
def orchestrator():
    """Fixture de orchestrator básico."""
    return create_orchestrator()


@pytest.fixture
def form_image():
    """Fixture de imagen de formulario mockeada."""
    return Mock(spec=Image.Image)
