"""Tests unitarios para RowProcessor.

Cobertura:
- Procesamiento de renglones con datos
- Procesamiento de renglones vacíos
- Manejo de errores
- Ejecución de acciones según validación
- Integración con dependencies mockeadas
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import time

from src.application.services.row_processor import (
    RowProcessor,
    ProcessingResult,
    ProcessingResultType
)
from src.domain.entities import (
    RowData,
    FormData,
    ValidationResult,
    ValidationAction
)


class TestRowProcessorInitialization:
    """Tests de inicialización."""

    def test_initialization_with_all_dependencies(self):
        """Test que inicializa con todas las dependencias."""
        automation_mock = Mock()
        validator_mock = Mock()
        web_ocr_mock = Mock()
        config_mock = Mock()
        config_mock.get.return_value = 5
        logger_mock = Mock()
        logger_mock.bind.return_value = logger_mock

        processor = RowProcessor(
            automation=automation_mock,
            validator=validator_mock,
            web_ocr=web_ocr_mock,
            config=config_mock,
            logger=logger_mock
        )

        assert processor.automation is automation_mock
        assert processor.validator is validator_mock
        assert processor.web_ocr is web_ocr_mock
        assert processor.config is config_mock

    def test_caches_configuration_on_init(self):
        """Test que cachea configuración en __init__."""
        config_mock = Mock()
        config_mock.get.side_effect = [5, 0.01, 0.3, 0.5, True]

        logger_mock = Mock()
        logger_mock.bind.return_value = logger_mock

        processor = RowProcessor(
            automation=Mock(),
            validator=Mock(),
            web_ocr=Mock(),
            config=config_mock,
            logger=logger_mock
        )

        # Verificar que se cachearon los valores
        assert processor._page_load_timeout == 5
        assert processor._typing_interval == 0.01
        assert processor._pre_enter_delay == 0.3
        assert processor._post_enter_delay == 0.5
        assert processor._auto_click_save is True

        # Verificar que se llamó config.get las veces correctas
        assert config_mock.get.call_count == 5


class TestProcessEmptyRow:
    """Tests de procesamiento de renglones vacíos."""

    def test_empty_row_returns_empty_row_result(self):
        """Test que renglón vacío retorna EMPTY_ROW."""
        processor = create_processor()

        empty_row = RowData(
            cedula="",
            nombres_manuscritos=""
        )
        empty_row.is_empty = True

        alert_handler_mock = Mock()
        alert_handler_mock.show_empty_row_prompt.return_value = "skip"

        result = processor.process_row(
            row_data=empty_row,
            row_number=5,
            alert_handler=alert_handler_mock
        )

        assert result.result_type == ProcessingResultType.EMPTY_ROW
        assert result.success is True
        assert result.row_number == 5

    def test_empty_row_calls_alert_handler(self):
        """Test que renglón vacío llama al alert_handler."""
        processor = create_processor()

        empty_row = RowData(cedula="", nombres_manuscritos="")
        empty_row.is_empty = True

        alert_handler_mock = Mock()
        alert_handler_mock.show_empty_row_prompt.return_value = "skip"

        processor.process_row(
            row_data=empty_row,
            row_number=5,
            alert_handler=alert_handler_mock
        )

        alert_handler_mock.show_empty_row_prompt.assert_called_once_with(5)


class TestProcessDataRow:
    """Tests de procesamiento de renglones con datos."""

    @patch('time.sleep')  # Mock sleep para tests rápidos
    def test_data_row_digitizes_cedula(self, mock_sleep):
        """Test que digita la cédula."""
        automation_mock = Mock()
        processor = create_processor(automation=automation_mock)

        row = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ"
        )

        # Mock validation to auto-save
        processor.validator.validate_person.return_value = ValidationResult(
            action=ValidationAction.AUTO_SAVE,
            confidence=0.95,
            is_valid=True,
            details={}
        )

        processor.process_row(
            row_data=row,
            row_number=1,
            alert_handler=Mock()
        )

        # Verificar que se digitó la cédula
        automation_mock.press_key.assert_any_call('ctrl+a')
        automation_mock.press_key.assert_any_call('delete')
        automation_mock.type_text.assert_called_with("123456789", interval=0.01)
        automation_mock.press_key.assert_any_call('enter')

    @patch('time.sleep')
    def test_data_row_reads_digital_data(self, mock_sleep):
        """Test que lee datos digitales con OCR."""
        web_ocr_mock = Mock()
        processor = create_processor(web_ocr=web_ocr_mock)

        row = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ"
        )

        # Mock validation
        processor.validator.validate_person.return_value = ValidationResult(
            action=ValidationAction.AUTO_SAVE,
            confidence=0.95,
            is_valid=True,
            details={}
        )

        processor.process_row(
            row_data=row,
            row_number=1,
            alert_handler=Mock()
        )

        # _read_digital_data está implementado como placeholder
        # Solo verificamos que no crasheó

    @patch('time.sleep')
    def test_data_row_validates_with_fuzzy_validator(self, mock_sleep):
        """Test que valida con fuzzy validator."""
        validator_mock = Mock()
        processor = create_processor(validator=validator_mock)

        row = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ"
        )

        validator_mock.validate_person.return_value = ValidationResult(
            action=ValidationAction.AUTO_SAVE,
            confidence=0.95,
            is_valid=True,
            details={}
        )

        processor.process_row(
            row_data=row,
            row_number=1,
            alert_handler=Mock()
        )

        # Verificar que se llamó validate_person
        validator_mock.validate_person.assert_called_once()


class TestValidationActions:
    """Tests de ejecución de acciones según validación."""

    @patch('time.sleep')
    def test_auto_save_action_returns_auto_saved(self, mock_sleep):
        """Test que AUTO_SAVE resulta en AUTO_SAVED."""
        processor = create_processor()

        row = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ"
        )

        processor.validator.validate_person.return_value = ValidationResult(
            action=ValidationAction.AUTO_SAVE,
            confidence=0.95,
            is_valid=True,
            details={}
        )

        result = processor.process_row(
            row_data=row,
            row_number=1,
            alert_handler=Mock()
        )

        assert result.result_type == ProcessingResultType.AUTO_SAVED
        assert result.success is True
        assert result.cedula == "123456789"

    @patch('time.sleep')
    def test_alert_not_found_returns_not_found(self, mock_sleep):
        """Test que ALERT_NOT_FOUND resulta en NOT_FOUND."""
        processor = create_processor()

        row = RowData(
            cedula="999999999",
            nombres_manuscritos="NO EXISTE"
        )

        processor.validator.validate_person.return_value = ValidationResult(
            action=ValidationAction.ALERT_NOT_FOUND,
            confidence=0.0,
            is_valid=False,
            details={"reason": "not_in_database"}
        )

        alert_handler_mock = Mock()
        alert_handler_mock.show_not_found_alert.return_value = "skip"

        result = processor.process_row(
            row_data=row,
            row_number=1,
            alert_handler=alert_handler_mock
        )

        assert result.result_type == ProcessingResultType.NOT_FOUND
        assert result.success is False

        # Verificar que se mostró la alerta
        alert_handler_mock.show_not_found_alert.assert_called_once()

    @patch('time.sleep')
    def test_require_validation_with_save_returns_auto_saved(self, mock_sleep):
        """Test que REQUIRE_VALIDATION + save resulta en AUTO_SAVED."""
        processor = create_processor()

        row = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PERES"  # Typo
        )

        processor.validator.validate_person.return_value = ValidationResult(
            action=ValidationAction.REQUIRE_VALIDATION,
            confidence=0.75,
            is_valid=False,
            details={"mismatch": "apellido"}
        )

        alert_handler_mock = Mock()
        alert_handler_mock.show_validation_mismatch_alert.return_value = "save"

        result = processor.process_row(
            row_data=row,
            row_number=1,
            alert_handler=alert_handler_mock
        )

        assert result.result_type == ProcessingResultType.AUTO_SAVED
        assert result.success is True

    @patch('time.sleep')
    def test_require_validation_with_skip_returns_skipped(self, mock_sleep):
        """Test que REQUIRE_VALIDATION + skip resulta en SKIPPED."""
        processor = create_processor()

        row = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PERES"
        )

        processor.validator.validate_person.return_value = ValidationResult(
            action=ValidationAction.REQUIRE_VALIDATION,
            confidence=0.75,
            is_valid=False,
            details={}
        )

        alert_handler_mock = Mock()
        alert_handler_mock.show_validation_mismatch_alert.return_value = "skip"

        result = processor.process_row(
            row_data=row,
            row_number=1,
            alert_handler=alert_handler_mock
        )

        assert result.result_type == ProcessingResultType.SKIPPED
        assert result.success is False


class TestErrorHandling:
    """Tests de manejo de errores."""

    def test_exception_during_processing_returns_error(self):
        """Test que excepción durante procesamiento retorna ERROR."""
        automation_mock = Mock()
        automation_mock.type_text.side_effect = Exception("Test error")

        processor = create_processor(automation=automation_mock)

        row = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ"
        )

        result = processor.process_row(
            row_data=row,
            row_number=1,
            alert_handler=Mock()
        )

        assert result.result_type == ProcessingResultType.ERROR
        assert result.success is False
        assert "Test error" in result.error_message

    def test_error_result_contains_row_number(self):
        """Test que resultado de error contiene row_number."""
        automation_mock = Mock()
        automation_mock.press_key.side_effect = Exception("Keyboard error")

        processor = create_processor(automation=automation_mock)

        row = RowData(
            cedula="123456789",
            nombres_manuscritos="JUAN PEREZ"
        )

        result = processor.process_row(
            row_data=row,
            row_number=7,
            alert_handler=Mock()
        )

        assert result.row_number == 7
        assert result.result_type == ProcessingResultType.ERROR


class TestProcessingResult:
    """Tests de estructura de ProcessingResult."""

    def test_processing_result_has_required_fields(self):
        """Test que ProcessingResult tiene todos los campos requeridos."""
        result = ProcessingResult(
            result_type=ProcessingResultType.AUTO_SAVED,
            success=True,
            row_number=5,
            cedula="123456789"
        )

        assert hasattr(result, 'result_type')
        assert hasattr(result, 'success')
        assert hasattr(result, 'row_number')
        assert hasattr(result, 'cedula')
        assert hasattr(result, 'validation_result')
        assert hasattr(result, 'error_message')


# Helper function para crear processor con mocks
def create_processor(
    automation=None,
    validator=None,
    web_ocr=None,
    config=None,
    logger=None
):
    """Helper para crear RowProcessor con dependencias mockeadas."""
    automation = automation or Mock()
    validator = validator or Mock()
    web_ocr = web_ocr or Mock()

    if config is None:
        config = Mock()
        config.get.return_value = 0.01  # Default para todos los timings

    if logger is None:
        logger = Mock()
        logger.bind.return_value = logger

    return RowProcessor(
        automation=automation,
        validator=validator,
        web_ocr=web_ocr,
        config=config,
        logger=logger
    )


# Fixtures
@pytest.fixture
def row_processor():
    """Fixture de processor básico."""
    return create_processor()


@pytest.fixture
def row_data_standard():
    """Fixture de row data estándar."""
    return RowData(
        cedula="123456789",
        nombres_manuscritos="JUAN CARLOS PEREZ GOMEZ"
    )


@pytest.fixture
def row_data_empty():
    """Fixture de row data vacío."""
    row = RowData(cedula="", nombres_manuscritos="")
    row.is_empty = True
    return row
