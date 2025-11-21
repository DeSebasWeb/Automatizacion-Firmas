"""Caso de uso para gestionar la sesión de procesamiento."""
from typing import List, Optional

from ...domain.entities import CedulaRecord, ProcessingSession, SessionStatus
from ...domain.ports import LoggerPort


class ManageSessionUseCase:
    """
    Caso de uso para gestionar una sesión de procesamiento de cédulas.

    Attributes:
        session: Sesión actual de procesamiento
        logger: Servicio de logging
    """

    def __init__(self, logger: LoggerPort):
        """
        Inicializa el caso de uso.

        Args:
            logger: Servicio de logging
        """
        self.session = ProcessingSession()
        self.logger = logger.bind(use_case="ManageSession")

    def create_session(self, records: List[CedulaRecord]) -> ProcessingSession:
        """
        Crea una nueva sesión con los registros proporcionados.

        Args:
            records: Lista de registros de cédulas

        Returns:
            Sesión creada

        Raises:
            ValueError: Si la lista de registros está vacía
        """
        if not records:
            self.logger.error("Intento de crear sesión sin registros")
            raise ValueError("No se puede crear una sesión sin registros")

        self.session = ProcessingSession()
        self.session.add_records(records)

        self.logger.info(
            "Sesión creada",
            total_records=self.session.total_records
        )

        return self.session

    def start_session(self) -> None:
        """
        Inicia la sesión de procesamiento.

        Raises:
            ValueError: Si la sesión no está lista para iniciar
        """
        if self.session.status not in [SessionStatus.READY, SessionStatus.PAUSED]:
            self.logger.error(
                "Intento de iniciar sesión en estado inválido",
                status=self.session.status.value
            )
            raise ValueError(f"No se puede iniciar sesión en estado {self.session.status.value}")

        self.session.start()

        self.logger.info(
            "Sesión iniciada",
            total_records=self.session.total_records
        )

    def pause_session(self) -> None:
        """Pausa la sesión actual."""
        self.session.pause()
        self.logger.info("Sesión pausada", current_index=self.session.current_index)

    def resume_session(self) -> None:
        """Reanuda la sesión pausada."""
        self.session.resume()
        self.logger.info("Sesión reanudada", current_index=self.session.current_index)

    def get_next_record(self) -> Optional[CedulaRecord]:
        """
        Obtiene el siguiente registro a procesar.

        Returns:
            Siguiente registro o None si no hay más
        """
        record = self.session.next_record()

        if record:
            self.logger.debug(
                "Siguiente registro obtenido",
                cedula=record.cedula.value,
                index=record.index
            )
        else:
            self.logger.info("No hay más registros para procesar")

        return record

    def advance(self, success: bool = True) -> None:
        """
        Avanza al siguiente registro.

        Args:
            success: Indica si el procesamiento fue exitoso
        """
        if not success:
            self.session.record_error()

        self.session.advance()

        self.logger.info(
            "Avanzando al siguiente registro",
            current_index=self.session.current_index,
            total_records=self.session.total_records,
            progress=f"{self.session.progress_percentage:.1f}%"
        )

        # Si se completó la sesión
        if self.session.status == SessionStatus.COMPLETED:
            self.logger.info(
                "Sesión completada",
                total_processed=self.session.total_processed,
                total_errors=self.session.total_errors,
                duration=self.session.completed_at - self.session.started_at if self.session.completed_at and self.session.started_at else None
            )

    def get_current_record(self) -> Optional[CedulaRecord]:
        """
        Obtiene el registro actual.

        Returns:
            Registro actual o None
        """
        return self.session.get_current_record()

    def get_session(self) -> ProcessingSession:
        """
        Obtiene la sesión actual.

        Returns:
            Sesión actual
        """
        return self.session

    def get_statistics(self) -> dict:
        """
        Obtiene estadísticas de la sesión.

        Returns:
            Diccionario con estadísticas
        """
        return {
            'total_records': self.session.total_records,
            'current_index': self.session.current_index,
            'total_processed': self.session.total_processed,
            'pending_records': self.session.pending_records,
            'total_errors': self.session.total_errors,
            'progress_percentage': self.session.progress_percentage,
            'status': self.session.status.value
        }
