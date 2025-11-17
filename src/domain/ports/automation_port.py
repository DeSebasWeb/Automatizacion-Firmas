"""Puerto para servicios de automatización de teclado y mouse."""
from abc import ABC, abstractmethod
from typing import Tuple


class AutomationPort(ABC):
    """Interfaz para servicios de automatización de entrada."""

    @abstractmethod
    def type_text(self, text: str, interval: float = 0.05) -> None:
        """
        Escribe texto simulando pulsaciones de teclado.

        Args:
            text: Texto a escribir
            interval: Intervalo entre teclas en segundos
        """
        pass

    @abstractmethod
    def press_key(self, key: str) -> None:
        """
        Presiona una tecla específica.

        Args:
            key: Nombre de la tecla a presionar
        """
        pass

    @abstractmethod
    def click(self, x: int, y: int) -> None:
        """
        Hace click en coordenadas específicas.

        Args:
            x: Coordenada X
            y: Coordenada Y
        """
        pass

    @abstractmethod
    def move_to(self, x: int, y: int, duration: float = 0.5) -> None:
        """
        Mueve el cursor a coordenadas específicas.

        Args:
            x: Coordenada X
            y: Coordenada Y
            duration: Duración del movimiento en segundos
        """
        pass

    @abstractmethod
    def get_mouse_position(self) -> Tuple[int, int]:
        """
        Obtiene la posición actual del mouse.

        Returns:
            Tupla (x, y) con la posición
        """
        pass

    @abstractmethod
    def register_hotkey(self, key: str, callback: callable) -> None:
        """
        Registra un atajo de teclado global.

        Args:
            key: Combinación de teclas
            callback: Función a ejecutar al presionar el atajo
        """
        pass
