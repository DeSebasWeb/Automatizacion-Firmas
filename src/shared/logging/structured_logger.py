"""Implementación de logger estructurado usando structlog."""
import logging
import structlog
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from ...domain.ports import LoggerPort


class StructuredLogger(LoggerPort):
    """
    Implementación de logger estructurado con soporte para archivos rotativos.

    Attributes:
        logger: Logger de structlog
        context: Contexto vinculado al logger
    """

    _initialized = False

    def __init__(self, name: str = "app", log_dir: str = "logs", **context: Any):
        """
        Inicializa el logger estructurado.

        Args:
            name: Nombre del logger
            log_dir: Directorio para archivos de log
            **context: Contexto inicial a vincular
        """
        if not StructuredLogger._initialized:
            self._configure_logging(log_dir)
            StructuredLogger._initialized = True

        self.logger = structlog.get_logger(name)
        self.context = context

        if context:
            self.logger = self.logger.bind(**context)

    @staticmethod
    def _configure_logging(log_dir: str) -> None:
        """
        Configura el sistema de logging.

        Args:
            log_dir: Directorio para archivos de log
        """
        # Crear directorio de logs si no existe
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        # Configurar archivo de log con timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_path / f"app_{timestamp}.log"

        # Configurar logging estándar de Python
        logging.basicConfig(
            format="%(message)s",
            level=logging.INFO,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        # Configurar structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def info(self, message: str, **kwargs: Any) -> None:
        """
        Registra un mensaje informativo.

        Args:
            message: Mensaje a registrar
            **kwargs: Contexto adicional
        """
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Registra una advertencia.

        Args:
            message: Mensaje a registrar
            **kwargs: Contexto adicional
        """
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """
        Registra un error.

        Args:
            message: Mensaje a registrar
            **kwargs: Contexto adicional
        """
        self.logger.error(message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Registra un mensaje de depuración.

        Args:
            message: Mensaje a registrar
            **kwargs: Contexto adicional
        """
        self.logger.debug(message, **kwargs)

    def bind(self, **kwargs: Any) -> 'StructuredLogger':
        """
        Crea un logger con contexto vinculado.

        Args:
            **kwargs: Contexto a vincular

        Returns:
            Nuevo logger con contexto
        """
        new_context = {**self.context, **kwargs}
        new_logger = StructuredLogger.__new__(StructuredLogger)
        new_logger.logger = self.logger.bind(**kwargs)
        new_logger.context = new_context
        return new_logger
