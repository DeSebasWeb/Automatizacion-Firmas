"""Tests unitarios para la entidad ProcessingSession."""
import pytest

from src.domain.entities import CedulaRecord, ProcessingSession, SessionStatus


class TestProcessingSession:
    """Tests para la entidad ProcessingSession."""

    def create_sample_records(self, count: int = 3):
        """Helper para crear registros de ejemplo."""
        return [
            CedulaRecord(cedula=f"1234567{i}", confidence=90.0, index=i)
            for i in range(count)
        ]

    def test_create_empty_session(self):
        """Test de creación de sesión vacía."""
        session = ProcessingSession()

        assert session.status == SessionStatus.IDLE
        assert session.total_records == 0
        assert session.current_index == 0

    def test_add_records(self):
        """Test de agregar registros a la sesión."""
        session = ProcessingSession()
        records = self.create_sample_records(3)

        session.add_records(records)

        assert session.total_records == 3
        assert session.status == SessionStatus.READY

    def test_start_session(self):
        """Test de iniciar sesión."""
        session = ProcessingSession()
        records = self.create_sample_records(3)
        session.add_records(records)

        session.start()

        assert session.status == SessionStatus.RUNNING
        assert session.started_at is not None
        assert session.current_index == 0

    def test_pause_and_resume(self):
        """Test de pausar y reanudar sesión."""
        session = ProcessingSession()
        records = self.create_sample_records(3)
        session.add_records(records)
        session.start()

        session.pause()
        assert session.status == SessionStatus.PAUSED

        session.resume()
        assert session.status == SessionStatus.RUNNING

    def test_next_record(self):
        """Test de obtener siguiente registro."""
        session = ProcessingSession()
        records = self.create_sample_records(3)
        session.add_records(records)
        session.start()

        first = session.next_record()
        assert first.cedula == "12345670"

    def test_advance(self):
        """Test de avanzar al siguiente registro."""
        session = ProcessingSession()
        records = self.create_sample_records(3)
        session.add_records(records)
        session.start()

        session.advance()

        assert session.current_index == 1
        assert session.total_processed == 1

    def test_complete_session(self):
        """Test de completar sesión."""
        session = ProcessingSession()
        records = self.create_sample_records(2)
        session.add_records(records)
        session.start()

        # Procesar todos
        session.advance()
        session.advance()

        assert session.status == SessionStatus.COMPLETED
        assert session.completed_at is not None

    def test_progress_percentage(self):
        """Test de cálculo de porcentaje de progreso."""
        session = ProcessingSession()
        records = self.create_sample_records(4)
        session.add_records(records)
        session.start()

        assert session.progress_percentage == 0.0

        session.advance()
        assert session.progress_percentage == 25.0

        session.advance()
        assert session.progress_percentage == 50.0

    def test_record_error(self):
        """Test de registrar error."""
        session = ProcessingSession()
        records = self.create_sample_records(3)
        session.add_records(records)
        session.start()

        session.record_error()

        assert session.total_errors == 1

    def test_get_current_record(self):
        """Test de obtener registro actual."""
        session = ProcessingSession()
        records = self.create_sample_records(3)
        session.add_records(records)
        session.start()

        current = session.get_current_record()

        assert current is not None
        assert current.cedula == "12345670"
        assert current.index == 0
