"""Caso de uso para procesar una cédula individual."""
import time
from typing import Optional

from ...domain.entities import CedulaRecord
from ...domain.ports import AutomationPort, ConfigPort, LoggerPort


class ProcessCedulaUseCase:
    """
    Caso de uso para procesar una cédula individual.

    Este caso de uso maneja la automatización de digitar una cédula
    en el campo de búsqueda y presionar Enter.

    Attributes:
        automation: Servicio de automatización
        config: Servicio de configuración
        logger: Servicio de logging
    """

    def __init__(
        self,
        automation: AutomationPort,
        config: ConfigPort,
        logger: LoggerPort
    ):
        """
        Inicializa el caso de uso.

        Args:
            automation: Servicio de automatización
            config: Servicio de configuración
            logger: Servicio de logging
        """
        self.automation = automation
        self.config = config
        self.logger = logger.bind(use_case="ProcessCedula")

    def execute(self, record: CedulaRecord, do_alt_tab: bool = False) -> bool:
        """
        Procesa una cédula digitándola en el formulario web.

        Args:
            record: Registro de cédula a procesar
            do_alt_tab: Si True, hace Alt+Tab antes de procesar

        Returns:
            True si el procesamiento fue exitoso

        Raises:
            ValueError: Si el registro es inválido
        """
        if not record.is_valid():
            self.logger.error(
                "Intento de procesar registro inválido",
                cedula=record.cedula.value,
                confidence=record.confidence.as_percentage()
            )
            raise ValueError("El registro de cédula no es válido")

        self.logger.info(
            "Iniciando procesamiento de cédula",
            cedula=record.cedula.value,
            index=record.index
        )

        try:
            # OPCIONAL: Hacer Alt+Tab solo si se solicita (desde el botón)
            if do_alt_tab:
                self.logger.debug("Cambiando a ventana objetivo con Alt+Tab")
                self.automation.press_key('alt+tab')

                # Esperar a que la ventana se enfoque
                time.sleep(0.4)

                self.logger.debug("Ventana objetivo enfocada")

            # Marcar como en procesamiento
            record.mark_as_processing()

            # Obtener coordenadas del campo de búsqueda
            search_field_x = self.config.get('search_field.x')
            search_field_y = self.config.get('search_field.y')

            # Si están configuradas, hacer click en el campo
            if search_field_x and search_field_y:
                self.logger.debug(
                    "Haciendo click en campo de búsqueda",
                    x=search_field_x,
                    y=search_field_y
                )
                self.automation.click(search_field_x, search_field_y)
                time.sleep(0.3)  # Esperar a que el campo esté enfocado

            # Limpiar el campo (Ctrl+A + Delete)
            self.automation.press_key('ctrl+a')
            time.sleep(0.1)
            self.automation.press_key('delete')
            time.sleep(0.2)

            # Obtener intervalo de tipeo desde configuración
            typing_interval = self.config.get('automation.typing_interval', 0.05)

            # Digitar la cédula
            self.logger.debug(
                "Digitando cédula",
                cedula=record.cedula.value,
                interval=typing_interval
            )
            self.automation.type_text(record.cedula.value, interval=typing_interval)

            # Esperar antes de presionar Enter
            pre_enter_delay = self.config.get('automation.pre_enter_delay', 0.3)
            time.sleep(pre_enter_delay)

            # Presionar Enter
            self.logger.debug("Presionando Enter")
            self.automation.press_key('enter')

            # Esperar después de presionar Enter
            post_enter_delay = self.config.get('automation.post_enter_delay', 0.5)
            time.sleep(post_enter_delay)

            # Marcar como completado
            record.mark_as_completed()

            self.logger.info(
                "Cédula procesada exitosamente",
                cedula=record.cedula.value,
                index=record.index,
                processing_time=record.processed_at - record.created_at if record.processed_at else None
            )

            return True

        except Exception as e:
            error_message = f"Error al procesar cédula: {str(e)}"
            record.mark_as_error(error_message)

            self.logger.error(
                "Error al procesar cédula",
                cedula=record.cedula.value,
                error=str(e)
            )

            return False

    def focus_search_field(self) -> None:
        """
        Permite al usuario configurar la posición del campo de búsqueda.

        El usuario debe posicionar el mouse sobre el campo y presionar una tecla.
        """
        self.logger.info("Esperando posición del campo de búsqueda")

        x, y = self.automation.get_mouse_position()

        self.config.set('search_field.x', x)
        self.config.set('search_field.y', y)
        self.config.save()

        self.logger.info(
            "Posición del campo de búsqueda guardada",
            x=x,
            y=y
        )
