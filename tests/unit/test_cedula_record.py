"""Tests unitarios para la entidad CedulaRecord."""
import pytest
from datetime import datetime

from src.domain.entities import CedulaRecord, RecordStatus


class TestCedulaRecord:
    """Tests para la entidad CedulaRecord."""

    def test_create_cedula_record(self):
        """Test de creación de registro de cédula."""
        record = CedulaRecord(
            cedula="12345678",
            confidence=95.5,
            index=0
        )

        assert record.cedula == "12345678"
        assert record.confidence == 95.5
        assert record.status == RecordStatus.PENDING
        assert record.index == 0
        assert record.created_at is not None

    def test_is_valid_with_valid_cedula(self):
        """Test de validación con cédula válida."""
        record = CedulaRecord(
            cedula="12345678",
            confidence=85.0
        )

        assert record.is_valid() is True

    def test_is_valid_with_low_confidence(self):
        """Test de validación con baja confianza."""
        record = CedulaRecord(
            cedula="12345678",
            confidence=40.0
        )

        assert record.is_valid() is False

    def test_is_valid_with_invalid_format(self):
        """Test de validación con formato inválido."""
        record = CedulaRecord(
            cedula="ABC123",
            confidence=95.0
        )

        assert record.is_valid() is False

    def test_is_valid_with_short_cedula(self):
        """Test de validación con cédula muy corta."""
        record = CedulaRecord(
            cedula="12345",
            confidence=95.0
        )

        assert record.is_valid() is False

    def test_mark_as_processing(self):
        """Test de marcar como procesando."""
        record = CedulaRecord(
            cedula="12345678",
            confidence=95.0
        )

        record.mark_as_processing()

        assert record.status == RecordStatus.PROCESSING

    def test_mark_as_completed(self):
        """Test de marcar como completado."""
        record = CedulaRecord(
            cedula="12345678",
            confidence=95.0
        )

        record.mark_as_completed()

        assert record.status == RecordStatus.COMPLETED
        assert record.processed_at is not None

    def test_mark_as_error(self):
        """Test de marcar como error."""
        record = CedulaRecord(
            cedula="12345678",
            confidence=95.0
        )

        error_msg = "Error de conexión"
        record.mark_as_error(error_msg)

        assert record.status == RecordStatus.ERROR
        assert record.error_message == error_msg
        assert record.processed_at is not None

    def test_mark_as_skipped(self):
        """Test de marcar como omitido."""
        record = CedulaRecord(
            cedula="12345678",
            confidence=95.0
        )

        record.mark_as_skipped()

        assert record.status == RecordStatus.SKIPPED
        assert record.processed_at is not None
