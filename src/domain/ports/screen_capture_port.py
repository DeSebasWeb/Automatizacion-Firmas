"""Puerto para servicios de captura de pantalla."""
from abc import ABC, abstractmethod
from typing import Optional, Callable
from PIL import Image

from ..entities import CaptureArea


class ScreenCapturePort(ABC):
    """Interfaz para servicios de captura de pantalla."""

    @abstractmethod
    def capture_area(self, area: CaptureArea) -> Image.Image:
        """
        Captura un área específica de la pantalla.

        Args:
            area: Área a capturar

        Returns:
            Imagen capturada
        """
        pass

    @abstractmethod
    def select_area_interactive(self, callback: Optional[Callable[[CaptureArea], None]] = None) -> CaptureArea:
        """
        Permite al usuario seleccionar un área de la pantalla interactivamente.

        Args:
            callback: Función a llamar cuando se seleccione el área

        Returns:
            Área seleccionada por el usuario
        """
        pass

    @abstractmethod
    def get_screen_size(self) -> tuple[int, int]:
        """
        Obtiene el tamaño de la pantalla.

        Returns:
            Tupla (width, height)
        """
        pass
