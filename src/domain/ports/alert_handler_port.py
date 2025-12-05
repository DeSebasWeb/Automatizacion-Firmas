"""Puerto para manejadores de alertas."""
from abc import ABC, abstractmethod
from typing import Optional

from ..entities import ValidationResult


class AlertHandlerPort(ABC):
    """
    Interfaz para manejadores de alertas en el flujo de automatización.

    Los alert handlers se encargan de mostrar alertas al usuario y
    obtener su decisión cuando se requiere intervención manual.

    Implementaciones típicas:
    - GUIAlertHandler: Muestra diálogos en PyQt6
    - CLIAlertHandler: Muestra alertas en consola
    - LogAlertHandler: Solo registra en logs (para testing)

    Example:
        >>> handler = GUIAlertHandler(parent_window)
        >>> action = handler.show_alert(
        ...     "Cédula no encontrada",
        ...     validation_result
        ... )
        >>> if action == "skip":
        ...     continue  # Saltar este renglón
    """

    @abstractmethod
    def show_not_found_alert(
        self,
        cedula: str,
        nombres: str,
        row_number: int
    ) -> str:
        """
        Muestra alerta cuando una cédula no existe en la base de datos.

        Args:
            cedula: Número de cédula que no fue encontrada
            nombres: Nombres manuscritos detectados
            row_number: Número de renglón en el formulario

        Returns:
            Acción decidida por el usuario:
                - "continue": Continuar con el siguiente renglón
                - "mark_issue": Marcar como novedad y continuar
                - "pause": Pausar el proceso completo
                - "retry": Reintentar búsqueda

        Example:
            >>> action = handler.show_not_found_alert(
            ...     cedula="12345678",
            ...     nombres="MARIA GARCIA",
            ...     row_number=5
            ... )
            >>> print(action)  # "continue", "pause", etc.
        """
        pass

    @abstractmethod
    def show_validation_mismatch_alert(
        self,
        validation_result: ValidationResult,
        row_number: int
    ) -> str:
        """
        Muestra alerta cuando los datos no coinciden suficientemente.

        Args:
            validation_result: Resultado de la validación fuzzy con detalles
            row_number: Número de renglón en el formulario

        Returns:
            Acción decidida por el usuario:
                - "save": Guardar de todas formas
                - "skip": Saltar este renglón
                - "correct": Permitir corrección manual
                - "pause": Pausar el proceso

        Example:
            >>> action = handler.show_validation_mismatch_alert(
            ...     validation_result,
            ...     row_number=3
            ... )
            >>> if action == "save":
            ...     save_to_database(data)
        """
        pass

    @abstractmethod
    def show_empty_row_prompt(self, row_number: int) -> str:
        """
        Muestra prompt cuando se detecta un renglón vacío.

        Args:
            row_number: Número de renglón vacío

        Returns:
            Acción decidida:
                - "click_button": Hacer click automático en "Renglón En Blanco"
                - "skip": Saltar este renglón
                - "pause": Pausar para revisión manual

        Example:
            >>> action = handler.show_empty_row_prompt(row_number=10)
            >>> if action == "click_button":
            ...     automation.click_button("Renglón En Blanco")
        """
        pass

    @abstractmethod
    def show_error_alert(self, error_message: str, row_number: Optional[int] = None) -> str:
        """
        Muestra alerta de error crítico.

        Args:
            error_message: Descripción del error
            row_number: Número de renglón donde ocurrió (opcional)

        Returns:
            Acción decidida:
                - "continue": Intentar continuar
                - "pause": Pausar el proceso
                - "abort": Abortar completamente

        Example:
            >>> action = handler.show_error_alert(
            ...     "Error de conexión con OCR",
            ...     row_number=7
            ... )
        """
        pass
