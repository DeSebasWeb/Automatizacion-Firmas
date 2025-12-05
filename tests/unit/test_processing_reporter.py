"""Tests unitarios para ProcessingReporter y ProcessingStats.

Cobertura:
- ProcessingStats dataclass
- Propiedades calculadas (success_rate, progress_percentage, pending_rows)
- Métodos de incremento
- Conversión a diccionario
- ProcessingReporter
- Generación de reportes
- Mensajes de progreso
- Reset de estadísticas
"""

import pytest

from src.application.services.processing_reporter import (
    ProcessingStats,
    ProcessingReporter
)


class TestProcessingStatsInitialization:
    """Tests de inicialización de ProcessingStats."""

    def test_default_initialization(self):
        """Test inicialización con valores por defecto."""
        stats = ProcessingStats()

        assert stats.total_rows == 0
        assert stats.processed_rows == 0
        assert stats.auto_saved == 0
        assert stats.required_validation == 0
        assert stats.empty_rows == 0
        assert stats.not_found == 0
        assert stats.errors == 0

    def test_custom_initialization(self):
        """Test inicialización con valores personalizados."""
        stats = ProcessingStats(
            total_rows=15,
            processed_rows=10,
            auto_saved=7,
            required_validation=2,
            empty_rows=1,
            not_found=0,
            errors=0
        )

        assert stats.total_rows == 15
        assert stats.processed_rows == 10
        assert stats.auto_saved == 7
        assert stats.required_validation == 2
        assert stats.empty_rows == 1


class TestProcessingStatsProperties:
    """Tests de propiedades calculadas."""

    def test_pending_rows(self):
        """Test cálculo de renglones pendientes."""
        stats = ProcessingStats(total_rows=15, processed_rows=10)
        assert stats.pending_rows == 5

    def test_pending_rows_all_processed(self):
        """Test pending_rows cuando todo está procesado."""
        stats = ProcessingStats(total_rows=15, processed_rows=15)
        assert stats.pending_rows == 0

    def test_pending_rows_none_processed(self):
        """Test pending_rows cuando no se ha procesado nada."""
        stats = ProcessingStats(total_rows=15, processed_rows=0)
        assert stats.pending_rows == 15

    def test_success_rate_perfect(self):
        """Test tasa de éxito del 100%."""
        stats = ProcessingStats(processed_rows=10, auto_saved=10)
        assert stats.success_rate == 100.0

    def test_success_rate_half(self):
        """Test tasa de éxito del 50%."""
        stats = ProcessingStats(processed_rows=10, auto_saved=5)
        assert stats.success_rate == 50.0

    def test_success_rate_zero(self):
        """Test tasa de éxito del 0%."""
        stats = ProcessingStats(processed_rows=10, auto_saved=0)
        assert stats.success_rate == 0.0

    def test_success_rate_no_processed(self):
        """Test tasa de éxito cuando no hay procesados (evita división por cero)."""
        stats = ProcessingStats(processed_rows=0, auto_saved=0)
        assert stats.success_rate == 0.0

    def test_progress_percentage_complete(self):
        """Test porcentaje de progreso al 100%."""
        stats = ProcessingStats(total_rows=15, processed_rows=15)
        assert stats.progress_percentage == 100.0

    def test_progress_percentage_half(self):
        """Test porcentaje de progreso al 50%."""
        stats = ProcessingStats(total_rows=10, processed_rows=5)
        assert stats.progress_percentage == 50.0

    def test_progress_percentage_zero(self):
        """Test porcentaje de progreso al 0%."""
        stats = ProcessingStats(total_rows=15, processed_rows=0)
        assert stats.progress_percentage == 0.0

    def test_progress_percentage_no_total(self):
        """Test porcentaje de progreso cuando no hay total (evita división por cero)."""
        stats = ProcessingStats(total_rows=0, processed_rows=0)
        assert stats.progress_percentage == 0.0


class TestProcessingStatsIncrements:
    """Tests de métodos de incremento."""

    def test_increment_processed(self):
        """Test incremento de procesados."""
        stats = ProcessingStats()
        assert stats.processed_rows == 0

        stats.increment_processed()
        assert stats.processed_rows == 1

        stats.increment_processed()
        assert stats.processed_rows == 2

    def test_increment_auto_saved(self):
        """Test incremento de guardados automáticos."""
        stats = ProcessingStats()
        assert stats.auto_saved == 0

        stats.increment_auto_saved()
        assert stats.auto_saved == 1

        stats.increment_auto_saved()
        assert stats.auto_saved == 2

    def test_increment_required_validation(self):
        """Test incremento de validaciones requeridas."""
        stats = ProcessingStats()
        assert stats.required_validation == 0

        stats.increment_required_validation()
        assert stats.required_validation == 1

    def test_increment_empty_rows(self):
        """Test incremento de renglones vacíos."""
        stats = ProcessingStats()
        assert stats.empty_rows == 0

        stats.increment_empty_rows()
        assert stats.empty_rows == 1

    def test_increment_not_found(self):
        """Test incremento de no encontrados."""
        stats = ProcessingStats()
        assert stats.not_found == 0

        stats.increment_not_found()
        assert stats.not_found == 1

    def test_increment_errors(self):
        """Test incremento de errores."""
        stats = ProcessingStats()
        assert stats.errors == 0

        stats.increment_errors()
        assert stats.errors == 1

    def test_multiple_increments(self):
        """Test múltiples incrementos simultáneos."""
        stats = ProcessingStats(total_rows=15)

        stats.increment_processed()
        stats.increment_auto_saved()

        stats.increment_processed()
        stats.increment_required_validation()

        stats.increment_processed()
        stats.increment_empty_rows()

        assert stats.processed_rows == 3
        assert stats.auto_saved == 1
        assert stats.required_validation == 1
        assert stats.empty_rows == 1


class TestProcessingStatsToDic:
    """Tests de conversión a diccionario."""

    def test_to_dict_structure(self):
        """Test que to_dict retorna todos los campos."""
        stats = ProcessingStats(
            total_rows=15,
            processed_rows=10,
            auto_saved=7,
            required_validation=2,
            empty_rows=1,
            not_found=0,
            errors=0
        )

        result = stats.to_dict()

        assert isinstance(result, dict)
        assert 'total_rows' in result
        assert 'processed_rows' in result
        assert 'pending_rows' in result
        assert 'auto_saved' in result
        assert 'required_validation' in result
        assert 'empty_rows' in result
        assert 'not_found' in result
        assert 'errors' in result
        assert 'success_rate' in result
        assert 'progress_percentage' in result

    def test_to_dict_values(self):
        """Test que los valores en to_dict son correctos."""
        stats = ProcessingStats(
            total_rows=15,
            processed_rows=10,
            auto_saved=7
        )

        result = stats.to_dict()

        assert result['total_rows'] == 15
        assert result['processed_rows'] == 10
        assert result['pending_rows'] == 5
        assert result['auto_saved'] == 7
        assert result['success_rate'] == 70.0  # 7/10 * 100
        assert result['progress_percentage'] == pytest.approx(66.67, rel=0.01)  # 10/15 * 100

    def test_to_dict_includes_calculated_properties(self):
        """Test que to_dict incluye propiedades calculadas."""
        stats = ProcessingStats(total_rows=10, processed_rows=5, auto_saved=3)

        result = stats.to_dict()

        # Verificar que las propiedades calculadas están presentes
        assert 'success_rate' in result
        assert 'progress_percentage' in result
        assert 'pending_rows' in result

        # Verificar que los valores son correctos
        assert result['success_rate'] == 60.0  # 3/5 * 100
        assert result['progress_percentage'] == 50.0  # 5/10 * 100
        assert result['pending_rows'] == 5  # 10 - 5


class TestProcessingReporterInitialization:
    """Tests de inicialización de ProcessingReporter."""

    def test_default_initialization(self):
        """Test que inicializa con stats en cero."""
        reporter = ProcessingReporter()

        assert hasattr(reporter, 'stats')
        assert isinstance(reporter.stats, ProcessingStats)
        assert reporter.stats.total_rows == 0
        assert reporter.stats.processed_rows == 0


class TestProcessingReporterReset:
    """Tests de reset de estadísticas."""

    def test_reset_clears_stats(self):
        """Test que reset limpia todas las estadísticas."""
        reporter = ProcessingReporter()

        # Modificar stats
        reporter.stats.total_rows = 15
        reporter.stats.processed_rows = 10
        reporter.stats.auto_saved = 7

        # Reset
        reporter.reset()

        # Verificar que todo está en cero
        assert reporter.stats.total_rows == 0
        assert reporter.stats.processed_rows == 0
        assert reporter.stats.auto_saved == 0

    def test_reset_creates_new_instance(self):
        """Test que reset crea nueva instancia de stats."""
        reporter = ProcessingReporter()

        old_stats = reporter.stats
        old_stats.total_rows = 15

        reporter.reset()

        # Debe ser una nueva instancia
        assert reporter.stats is not old_stats
        assert reporter.stats.total_rows == 0


class TestProcessingReporterProgressMessage:
    """Tests de mensajes de progreso."""

    def test_get_progress_message_format(self):
        """Test formato del mensaje de progreso."""
        reporter = ProcessingReporter()
        reporter.stats.total_rows = 15
        reporter.stats.processed_rows = 5
        reporter.stats.auto_saved = 3

        message = reporter.get_progress_message(current_row=5)

        # Verificar que contiene info clave
        assert "5/15" in message  # Current/Total
        assert "5 procesados" in message  # Processed count
        assert "3 guardados" in message  # Saved count
        assert "%" in message  # Porcentaje

    def test_get_progress_message_beginning(self):
        """Test mensaje al inicio del procesamiento."""
        reporter = ProcessingReporter()
        reporter.stats.total_rows = 15
        reporter.stats.processed_rows = 1
        reporter.stats.auto_saved = 0

        message = reporter.get_progress_message(current_row=1)

        assert "1/15" in message
        assert "1 procesados" in message

    def test_get_progress_message_end(self):
        """Test mensaje al final del procesamiento."""
        reporter = ProcessingReporter()
        reporter.stats.total_rows = 15
        reporter.stats.processed_rows = 15
        reporter.stats.auto_saved = 12

        message = reporter.get_progress_message(current_row=15)

        assert "15/15" in message
        assert "100.0%" in message
        assert "15 procesados" in message
        assert "12 guardados" in message


class TestProcessingReporterSummary:
    """Tests de resumen final."""

    def test_get_summary_returns_string(self):
        """Test que get_summary retorna un string."""
        reporter = ProcessingReporter()
        reporter.stats.total_rows = 15
        reporter.stats.processed_rows = 15
        reporter.stats.auto_saved = 12

        summary = reporter.get_summary()

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_get_summary_contains_key_info(self):
        """Test que el resumen contiene información clave."""
        reporter = ProcessingReporter()
        reporter.stats.total_rows = 15
        reporter.stats.processed_rows = 15
        reporter.stats.auto_saved = 12
        reporter.stats.required_validation = 2
        reporter.stats.empty_rows = 1
        reporter.stats.not_found = 0
        reporter.stats.errors = 0

        summary = reporter.get_summary()

        # Verificar que contiene las cifras clave
        assert "15" in summary  # Total rows
        assert "12" in summary  # Auto saved
        assert "2" in summary   # Required validation
        assert "1" in summary   # Empty rows
        assert "%" in summary   # Success rate

    def test_get_summary_formatted(self):
        """Test que el resumen está formateado (tiene bordes ASCII)."""
        reporter = ProcessingReporter()
        reporter.stats.total_rows = 15
        reporter.stats.processed_rows = 15

        summary = reporter.get_summary()

        # Verificar formato de tabla
        assert "╔" in summary or "=" in summary  # Borde superior
        assert "╚" in summary or "=" in summary  # Borde inferior
        assert "║" in summary or "|" in summary  # Bordes laterales

    def test_get_summary_with_all_zeros(self):
        """Test resumen cuando todo está en cero."""
        reporter = ProcessingReporter()

        summary = reporter.get_summary()

        # No debe crashear
        assert isinstance(summary, str)
        assert "0" in summary

    def test_get_summary_with_errors(self):
        """Test resumen cuando hay errores."""
        reporter = ProcessingReporter()
        reporter.stats.total_rows = 15
        reporter.stats.processed_rows = 10
        reporter.stats.errors = 5

        summary = reporter.get_summary()

        assert "5" in summary  # Error count
        assert "⚠" in summary or "ERROR" in summary.upper()


class TestIntegrationScenarios:
    """Tests de escenarios completos de uso."""

    def test_typical_processing_flow(self):
        """Test flujo típico de procesamiento."""
        reporter = ProcessingReporter()

        # Setup
        reporter.stats.total_rows = 15

        # Procesar 15 renglones
        for i in range(15):
            reporter.stats.increment_processed()

            # Simular resultados variados
            if i < 10:
                reporter.stats.increment_auto_saved()  # 10 auto-saved
            elif i < 12:
                reporter.stats.increment_required_validation()  # 2 required validation
            elif i < 14:
                reporter.stats.increment_empty_rows()  # 2 empty
            else:
                reporter.stats.increment_not_found()  # 1 not found

        # Verificar estadísticas finales
        assert reporter.stats.processed_rows == 15
        assert reporter.stats.auto_saved == 10
        assert reporter.stats.required_validation == 2
        assert reporter.stats.empty_rows == 2
        assert reporter.stats.not_found == 1
        assert reporter.stats.success_rate == pytest.approx(66.67, rel=0.01)  # 10/15
        assert reporter.stats.progress_percentage == 100.0

        # Verificar que el summary funciona
        summary = reporter.get_summary()
        assert "15" in summary
        assert "10" in summary

    def test_reset_and_reuse(self):
        """Test que el reporter puede resetearse y reutilizarse."""
        reporter = ProcessingReporter()

        # Primer procesamiento
        reporter.stats.total_rows = 10
        reporter.stats.increment_processed()
        reporter.stats.increment_auto_saved()

        assert reporter.stats.processed_rows == 1
        assert reporter.stats.auto_saved == 1

        # Reset
        reporter.reset()

        # Segundo procesamiento
        reporter.stats.total_rows = 20
        reporter.stats.increment_processed()
        reporter.stats.increment_processed()

        assert reporter.stats.total_rows == 20
        assert reporter.stats.processed_rows == 2
        assert reporter.stats.auto_saved == 0  # Reseteado

    def test_progress_messages_throughout_processing(self):
        """Test que los mensajes de progreso evolucionan correctamente."""
        reporter = ProcessingReporter()
        reporter.stats.total_rows = 5

        messages = []

        for i in range(1, 6):
            reporter.stats.increment_processed()
            if i <= 3:
                reporter.stats.increment_auto_saved()

            message = reporter.get_progress_message(current_row=i)
            messages.append(message)

        # Verificar que cada mensaje tiene el número correcto
        assert "1/5" in messages[0]
        assert "2/5" in messages[1]
        assert "3/5" in messages[2]
        assert "4/5" in messages[3]
        assert "5/5" in messages[4]

        # Verificar progreso creciente
        assert "20.0%" in messages[0]
        assert "40.0%" in messages[1]
        assert "60.0%" in messages[2]
        assert "80.0%" in messages[3]
        assert "100.0%" in messages[4]


# Fixtures
@pytest.fixture
def stats_empty():
    """Fixture de stats vacías."""
    return ProcessingStats()


@pytest.fixture
def stats_partial():
    """Fixture de stats parcialmente procesadas."""
    return ProcessingStats(
        total_rows=15,
        processed_rows=10,
        auto_saved=7,
        required_validation=2,
        empty_rows=1
    )


@pytest.fixture
def stats_complete():
    """Fixture de stats completamente procesadas."""
    return ProcessingStats(
        total_rows=15,
        processed_rows=15,
        auto_saved=12,
        required_validation=2,
        empty_rows=1
    )


@pytest.fixture
def reporter():
    """Fixture de reporter limpio."""
    return ProcessingReporter()
