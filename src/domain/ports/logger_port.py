"""Puerto para servicios de logging."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LoggerPort(ABC):
    """Interfaz para servicios de logging estructurado."""

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """
        Registra un mensaje informativo.

        Args:
            message: Mensaje a registrar
            **kwargs: Contexto adicional
        """
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Registra una advertencia.

        Args:
            message: Mensaje a registrar
            **kwargs: Contexto adicional
        """
        pass

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """
        Registra un error.

        Args:
            message: Mensaje a registrar
            **kwargs: Contexto adicional
        """
        pass

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Registra un mensaje de depuración.

        Args:
            message: Mensaje a registrar
            **kwargs: Contexto adicional
        """
        pass

    @abstractmethod
    def bind(self, **kwargs: Any) -> 'LoggerPort':
        """
        Crea un logger con contexto vinculado.

        Args:
            **kwargs: Contexto a vincular

        Returns:
            Nuevo logger con contexto
        """
        pass
