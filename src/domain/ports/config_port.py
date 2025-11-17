"""Puerto para servicios de configuración."""
from abc import ABC, abstractmethod
from typing import Any, Optional


class ConfigPort(ABC):
    """Interfaz para servicios de gestión de configuración."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.

        Args:
            key: Clave de configuración (puede usar notación de punto)
            default: Valor por defecto si no existe

        Returns:
            Valor de configuración
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración.

        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        pass

    @abstractmethod
    def save(self) -> None:
        """Guarda la configuración en disco."""
        pass

    @abstractmethod
    def load(self) -> None:
        """Carga la configuración desde disco."""
        pass

    @abstractmethod
    def get_all(self) -> dict:
        """
        Obtiene toda la configuración.

        Returns:
            Diccionario con toda la configuración
        """
        pass
