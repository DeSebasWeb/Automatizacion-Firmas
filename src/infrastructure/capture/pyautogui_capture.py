"""Implementación de captura de pantalla usando PyAutoGUI."""
import pyautogui
from PIL import Image
from typing import Optional, Callable, Tuple

from ...domain.entities import CaptureArea
from ...domain.ports import ScreenCapturePort


class PyAutoGUICapture(ScreenCapturePort):
    """
    Implementación de captura de pantalla usando PyAutoGUI.

    Esta implementación proporciona funcionalidad básica de captura.
    La selección interactiva se implementa en la capa de presentación (UI).
    """

    def __init__(self):
        """Inicializa el servicio de captura."""
        # Configurar PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def capture_area(self, area: CaptureArea) -> Image.Image:
        """
        Captura un área específica de la pantalla.

        Args:
            area: Área a capturar

        Returns:
            Imagen capturada

        Raises:
            ValueError: Si el área es inválida
        """
        if not area.is_valid():
            raise ValueError("El área de captura no es válida")

        # Capturar región
        screenshot = pyautogui.screenshot(
            region=(area.x, area.y, area.width, area.height)
        )

        return screenshot

    def select_area_interactive(
        self,
        callback: Optional[Callable[[CaptureArea], None]] = None
    ) -> CaptureArea:
        """
        Permite al usuario seleccionar un área de la pantalla interactivamente.

        NOTA: Esta implementación es básica. La versión completa se implementa
        en la capa de presentación usando PyQt6 para mejor experiencia de usuario.

        Args:
            callback: Función a llamar cuando se seleccione el área

        Returns:
            Área seleccionada por el usuario
        """
        # Esta implementación básica requiere que el área sea proporcionada
        # La implementación real está en la capa de presentación
        raise NotImplementedError(
            "La selección interactiva se implementa en la capa de presentación (UI)"
        )

    def get_screen_size(self) -> Tuple[int, int]:
        """
        Obtiene el tamaño de la pantalla.

        Returns:
            Tupla (width, height)
        """
        size = pyautogui.size()
        return (size.width, size.height)
