"""Entidad que representa un registro de cédula extraído (sistema legacy)."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class RecordStatus(Enum):
    """Estados posibles de un registro de cédula."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass
class CedulaRecord:
    """
    Entidad que representa un registro de cédula (SISTEMA LEGACY).

    Esta entidad se usa para el flujo de extracción SIMPLE donde solo
    se extraen números de cédula sin nombres asociados.

    **Caso de uso:**
        Sistema legacy que solo necesita extraer y digitar cédulas
        sin validación fuzzy ni nombres manuscritos.

    **Cuándo usar:**
        - Solo necesitas números de cédula
        - No necesitas validación fuzzy
        - Usas ProcessingSession tradicional
        - No trabajas con formularios estructurados por renglones

    **Cuándo NO usar:**
        - Si necesitas nombres + cédulas → usa RowData
        - Si usas sistema dual OCR → usa RowData
        - Si necesitas validación fuzzy → usa RowData + FormData

    Ver docs/mejoraSOLID/01_CEDULA_RECORD_VS_ROW_DATA.md para detalles.

    Attributes:
        cedula: Número de cédula extraído
        confidence: Nivel de confianza del OCR (0-100)
        status: Estado actual del registro (PENDING, PROCESSING, etc.)
        index: Posición en la lista de registros
        created_at: Timestamp de creación
        processed_at: Timestamp de procesamiento
        error_message: Mensaje de error si aplica

    Example:
        >>> # Sistema legacy simple
        >>> record = CedulaRecord(cedula="12345678", confidence=92.5)
        >>> if record.is_valid():
        ...     automation.type_cedula(record.cedula)
        ...     record.mark_as_completed()
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

    def is_valid(self, specification=None) -> bool:
        """
        Valida si la cédula cumple con una especificación dada.

        Este método ahora usa el Patrón Specification para validaciones
        flexibles y reutilizables, en lugar de lógica hardcodeada.

        Args:
            specification: Especificación a evaluar. Si es None, usa
                          validación estándar (formato + longitud + confianza)

        Returns:
            True si la cédula satisface la especificación, False en caso contrario

        Example:
            >>> # Usar validación por defecto
            >>> record.is_valid()
            True
            >>>
            >>> # Usar especificación personalizada
            >>> from domain.specifications import CedulaSpecifications
            >>> high_conf = CedulaSpecifications.high_confidence_only(min_confidence=85.0)
            >>> record.is_valid(high_conf)
            False
            >>>
            >>> # Combinar especificaciones
            >>> from domain.specifications import (
            ...     CedulaFormatSpecification,
            ...     CedulaLengthSpecification,
            ...     ConfidenceSpecification
            ... )
            >>> custom_spec = (
            ...     CedulaFormatSpecification()
            ...     .and_(CedulaLengthSpecification(8, 10))
            ...     .and_(ConfidenceSpecification(70.0))
            ... )
            >>> record.is_valid(custom_spec)
            True

        Note:
            Para evitar circular imports, la especificación por defecto
            se importa dinámicamente dentro del método.
        """
        if specification is None:
            # Importación dinámica para evitar circular imports
            from ..specifications import CedulaSpecifications
            specification = CedulaSpecifications.valid_for_processing(
                min_confidence=50.0
            )

        return specification.is_satisfied_by(self)
