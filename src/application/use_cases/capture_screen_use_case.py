"""Caso de uso para capturar área de pantalla."""
from typing import Optional, Callable
from PIL import Image

from ...domain.entities import CaptureArea
from ...domain.ports import ScreenCapturePort, ConfigPort, LoggerPort


class CaptureScreenUseCase:
    """
    Caso de uso para capturar un área específica de la pantalla.

    Attributes:
        screen_capture: Servicio de captura de pantalla
        config: Servicio de configuración
        logger: Servicio de logging
    """

    def __init__(
        self,
        screen_capture: ScreenCapturePort,
        config: ConfigPort,
        logger: LoggerPort
    ):
        """
        Inicializa el caso de uso.

        Args:
            screen_capture: Servicio de captura de pantalla
            config: Servicio de configuración
            logger: Servicio de logging
        """
        self.screen_capture = screen_capture
        self.config = config
        self.logger = logger.bind(use_case="CaptureScreen")

    def select_area(self, callback: Optional[Callable[[CaptureArea], None]] = None) -> CaptureArea:
        """
        Permite al usuario seleccionar el área de captura interactivamente.

        Args:
            callback: Función a llamar cuando se seleccione el área

        Returns:
            Área seleccionada
        """
        self.logger.info("Iniciando selección de área de captura")

        try:
            area = self.screen_capture.select_area_interactive(callback)

            if not area.is_valid():
                self.logger.error("Área seleccionada inválida", area=area.to_dict())
                raise ValueError("El área seleccionada no es válida")

            # Guardar el área en la configuración
            self.config.set('capture_area', area.to_dict())
            self.config.save()

            self.logger.info(
                "Área de captura seleccionada y guardada",
                area=area.to_dict()
            )

            return area

        except Exception as e:
            self.logger.error("Error al seleccionar área", error=str(e))
            raise

    def capture(self, area: Optional[CaptureArea] = None) -> Image.Image:
        """
        Captura el área especificada o la guardada en configuración.

        Args:
            area: Área a capturar (opcional, usa la guardada si no se especifica)

        Returns:
            Imagen capturada

        Raises:
            ValueError: Si no hay área configurada
        """
        if area is None:
            # Intentar obtener el área desde la configuración
            area_dict = self.config.get('capture_area')
            if area_dict is None:
                self.logger.error("No hay área de captura configurada")
                raise ValueError("No hay área de captura configurada")
            area = CaptureArea.from_dict(area_dict)

        self.logger.info("Capturando área", area=area.to_dict())

        try:
            image = self.screen_capture.capture_area(area)

            self.logger.info(
                "Área capturada exitosamente",
                image_size=(image.width, image.height)
            )

            return image

        except Exception as e:
            self.logger.error("Error al capturar área", error=str(e))
            raise

    def get_saved_area(self) -> Optional[CaptureArea]:
        """
        Obtiene el área guardada en la configuración.

        Returns:
            Área guardada o None si no existe
        """
        area_dict = self.config.get('capture_area')
        if area_dict:
            return CaptureArea.from_dict(area_dict)
        return None
