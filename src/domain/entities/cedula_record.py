"""Entidad que representa un registro de cédula extraído."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class RecordStatus(Enum):
    """Estados posibles de un registro de cédula."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class CedulaRecord:
    """
    Entidad que representa un registro de cédula.

    Attributes:
        cedula: Número de cédula extraído
        confidence: Nivel de confianza del OCR (0-100)
        status: Estado actual del registro
        index: Posición en la lista de registros
        created_at: Timestamp de creación
        processed_at: Timestamp de procesamiento
        error_message: Mensaje de error si aplica
    """
    cedula: str
    confidence: float
    status: RecordStatus = RecordStatus.PENDING
    index: int = 0
    created_at: datetime = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        """Inicializa valores por defecto."""
        if self.created_at is None:
            self.created_at = datetime.now()

    def mark_as_processing(self) -> None:
        """Marca el registro como en procesamiento."""
        self.status = RecordStatus.PROCESSING

    def mark_as_completed(self) -> None:
        """Marca el registro como completado."""
        self.status = RecordStatus.COMPLETED
        self.processed_at = datetime.now()

    def mark_as_error(self, error_message: str) -> None:
        """Marca el registro como error."""
        self.status = RecordStatus.ERROR
        self.error_message = error_message
        self.processed_at = datetime.now()

    def mark_as_skipped(self) -> None:
        """Marca el registro como omitido."""
        self.status = RecordStatus.SKIPPED
        self.processed_at = datetime.now()

    def is_valid(self) -> bool:
        """
        Valida si la cédula tiene un formato válido.

        Returns:
            True si la cédula es válida, False en caso contrario
        """
        # Validación básica: solo dígitos y longitud razonable
        return (
            self.cedula.isdigit() and
            6 <= len(self.cedula) <= 15 and
            self.confidence >= 50.0
        )
