"""Entidad que representa una sesión de procesamiento."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from .cedula_record import CedulaRecord


class SessionStatus(Enum):
    """Estados posibles de una sesión de procesamiento."""
    IDLE = "idle"
    CAPTURING = "capturing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ProcessingSession:
    """
    Entidad que representa una sesión de procesamiento de cédulas.

    Attributes:
        records: Lista de registros de cédulas
        status: Estado actual de la sesión
        current_index: Índice del registro actual
        started_at: Timestamp de inicio
        completed_at: Timestamp de finalización
        total_processed: Total de registros procesados
        total_errors: Total de errores
    """
    records: List[CedulaRecord] = field(default_factory=list)
    status: SessionStatus = SessionStatus.IDLE
    current_index: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_processed: int = 0
    total_errors: int = 0

    def add_records(self, records: List[CedulaRecord]) -> None:
        """
        Agrega registros a la sesión.

        Args:
            records: Lista de registros a agregar
        """
        for idx, record in enumerate(records, start=len(self.records)):
            record.index = idx
        self.records.extend(records)
        self.status = SessionStatus.READY

    def start(self) -> None:
        """Inicia la sesión de procesamiento."""
        self.status = SessionStatus.RUNNING
        self.started_at = datetime.now()
        self.current_index = 0

    def pause(self) -> None:
        """Pausa la sesión de procesamiento."""
        if self.status == SessionStatus.RUNNING:
            self.status = SessionStatus.PAUSED

    def resume(self) -> None:
        """Reanuda la sesión de procesamiento."""
        if self.status == SessionStatus.PAUSED:
            self.status = SessionStatus.RUNNING

    def complete(self) -> None:
        """Completa la sesión de procesamiento."""
        self.status = SessionStatus.COMPLETED
        self.completed_at = datetime.now()

    def next_record(self) -> Optional[CedulaRecord]:
        """
        Obtiene el siguiente registro a procesar.

        Returns:
            Siguiente registro o None si no hay más
        """
        if self.current_index < len(self.records):
            record = self.records[self.current_index]
            return record
        return None

    def advance(self) -> None:
        """Avanza al siguiente registro."""
        if self.current_index < len(self.records):
            self.current_index += 1
            self.total_processed += 1

        if self.current_index >= len(self.records):
            self.complete()

    def record_error(self) -> None:
        """Registra un error en el procesamiento actual."""
        self.total_errors += 1

    @property
    def total_records(self) -> int:
        """Retorna el total de registros."""
        return len(self.records)

    @property
    def pending_records(self) -> int:
        """Retorna el total de registros pendientes."""
        return self.total_records - self.current_index

    @property
    def progress_percentage(self) -> float:
        """Retorna el porcentaje de progreso."""
        if self.total_records == 0:
            return 0.0
        return (self.current_index / self.total_records) * 100

    def get_current_record(self) -> Optional[CedulaRecord]:
        """
        Obtiene el registro actual.

        Returns:
            Registro actual o None
        """
        if 0 <= self.current_index < len(self.records):
            return self.records[self.current_index]
        return None
