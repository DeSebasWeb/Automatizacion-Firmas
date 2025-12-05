"""Puerto para manejadores de progreso."""
from abc import ABC, abstractmethod


class ProgressHandlerPort(ABC):
    """
    Interfaz para manejadores de progreso en el flujo de automatización.

    Los progress handlers se encargan de notificar al usuario sobre
    el avance del procesamiento.

    Implementaciones típicas:
    - GUIProgressHandler: Actualiza progress bar en PyQt6
    - CLIProgressHandler: Imprime progreso en consola
    - NoOpProgressHandler: No hace nada (para testing)

    Example:
        >>> handler = GUIProgressHandler(progress_bar)
        >>> handler.update_progress(5, 15, "Procesando renglón 5 de 15")
    """

    @abstractmethod
    def update_progress(
        self,
        current: int,
        total: int,
        message: str = ""
    ) -> None:
        """
        Actualiza el indicador de progreso.

        Args:
            current: Número de items procesados
            total: Total de items a procesar
            message: Mensaje descriptivo del progreso actual

        Example:
            >>> handler.update_progress(
            ...     current=8,
            ...     total=15,
            ...     message="Renglón 8: Validando datos..."
            ... )
        """
        pass

    @abstractmethod
    def set_status(self, status: str) -> None:
        """
        Establece el estado actual del proceso.

        Args:
            status: Estado descriptivo ("Iniciando", "Procesando", "Completado", etc.)

        Example:
            >>> handler.set_status("Extrayendo cédulas con OCR...")
            >>> # ... proceso ...
            >>> handler.set_status("Completado")
        """
        pass

    @abstractmethod
    def show_completion_summary(self, stats: dict) -> None:
        """
        Muestra resumen al completar el procesamiento.

        Args:
            stats: Diccionario con estadísticas del procesamiento:
                - total_rows: Total de renglones
                - processed_rows: Renglones procesados
                - auto_saved: Guardados automáticamente
                - required_validation: Requirieron validación
                - empty_rows: Renglones vacíos
                - not_found: No encontrados
                - errors: Errores

        Example:
            >>> handler.show_completion_summary({
            ...     'total_rows': 15,
            ...     'processed_rows': 15,
            ...     'auto_saved': 12,
            ...     'required_validation': 2,
            ...     'errors': 1
            ... })
        """
        pass
