"""Handlers para uso en API REST (sin GUI).

Estos handlers implementan las interfaces AlertHandlerPort y ProgressHandlerPort
pero sin mostrar diálogos ni barras de progreso. En su lugar, solo loguean
las operaciones.

Útiles para:
- API REST endpoints
- Scripts CLI
- Tests automatizados
- Procesamiento batch
"""

from typing import Optional

from ...domain.ports import AlertHandlerPort, ProgressHandlerPort, LoggerPort, ConfigPort
from ...domain.entities import ValidationResult


class APIAlertHandler(AlertHandlerPort):
    """
    Handler de alertas para API REST (sin GUI).

    Características:
    - NO muestra diálogos
    - Retorna respuestas automáticas según configuración
    - Logea todas las alertas para debugging
    - Permite monitorear via logs

    Example:
        >>> handler = APIAlertHandler(config, logger)
        >>> action = handler.show_not_found_alert("123456", "JUAN PEREZ", 5)
        >>> # Retorna "skip" automáticamente (configurable)
    """

    def __init__(self, config: ConfigPort, logger: LoggerPort):
        """
        Inicializa el handler de alertas para API.

        Args:
            config: Servicio de configuración
            logger: Logger estructurado
        """
        self.config = config
        self.logger = logger.bind(component="APIAlertHandler")

        # Configuración de comportamiento automático
        self._auto_not_found_action = config.get('api.auto_not_found_action', 'skip')
        self._auto_validation_action = config.get('api.auto_validation_action', 'skip')
        self._auto_empty_row_action = config.get('api.auto_empty_row_action', 'skip')
        self._auto_error_action = config.get('api.auto_error_action', 'pause')

    def show_not_found_alert(
        self,
        cedula: str,
        nombres: str,
        row_number: int
    ) -> str:
        """
        Logea alerta de cédula no encontrada y retorna acción automática.

        Args:
            cedula: Cédula que no se encontró
            nombres: Nombres manuscritos
            row_number: Número de renglón

        Returns:
            Acción a tomar ("skip", "pause", "retry")
        """
        self.logger.warning(
            "Cédula no encontrada en BD",
            cedula=cedula,
            nombres=nombres,
            row_number=row_number,
            auto_action=self._auto_not_found_action
        )

        return self._auto_not_found_action

    def show_validation_mismatch_alert(
        self,
        validation_result: ValidationResult,
        row_number: int
    ) -> str:
        """
        Logea alerta de validación fallida y retorna acción automática.

        Args:
            validation_result: Resultado de validación con detalles
            row_number: Número de renglón

        Returns:
            Acción a tomar ("save", "skip", "correct", "pause")
        """
        self.logger.warning(
            "Validación requiere intervención manual",
            row_number=row_number,
            confidence=f"{validation_result.confidence:.2%}",
            details=validation_result.details,
            auto_action=self._auto_validation_action
        )

        return self._auto_validation_action

    def show_empty_row_prompt(self, row_number: int) -> str:
        """
        Logea renglón vacío y retorna acción automática.

        Args:
            row_number: Número de renglón vacío

        Returns:
            Acción a tomar ("click_button", "skip", "pause")
        """
        self.logger.info(
            "Renglón vacío detectado",
            row_number=row_number,
            auto_action=self._auto_empty_row_action
        )

        return self._auto_empty_row_action

    def show_error_alert(
        self,
        error_message: str,
        row_number: Optional[int] = None
    ) -> str:
        """
        Logea error crítico y retorna acción automática.

        Args:
            error_message: Mensaje de error
            row_number: Número de renglón (opcional)

        Returns:
            Acción a tomar ("retry", "skip", "pause")
        """
        self.logger.error(
            "Error crítico durante procesamiento",
            error=error_message,
            row_number=row_number,
            auto_action=self._auto_error_action
        )

        return self._auto_error_action


class APIProgressHandler(ProgressHandlerPort):
    """
    Handler de progreso para API REST (sin GUI).

    Características:
    - NO muestra barras de progreso
    - Logea todo el progreso
    - Permite monitorear via logs
    - Útil para debugging

    Example:
        >>> handler = APIProgressHandler(logger)
        >>> handler.update_progress(5, 15, "Procesando renglón 5/15")
        >>> # Solo logea, no muestra nada en pantalla
    """

    def __init__(self, logger: LoggerPort):
        """
        Inicializa el handler de progreso para API.

        Args:
            logger: Logger estructurado
        """
        self.logger = logger.bind(component="APIProgressHandler")

    def update_progress(
        self,
        current: int,
        total: int,
        message: str
    ) -> None:
        """
        Logea actualización de progreso.

        Args:
            current: Renglón actual
            total: Total de renglones
            message: Mensaje de progreso
        """
        percentage = (current / total * 100) if total > 0 else 0

        self.logger.info(
            "Progreso actualizado",
            current=current,
            total=total,
            percentage=f"{percentage:.1f}%",
            message=message
        )

    def set_status(self, status: str) -> None:
        """
        Logea cambio de estado.

        Args:
            status: Nuevo estado del proceso
        """
        self.logger.info(
            "Estado cambiado",
            status=status
        )

    def show_completion_summary(self, stats: dict) -> None:
        """
        Logea resumen de completación.

        Args:
            stats: Diccionario con estadísticas del procesamiento
        """
        self.logger.info(
            "Procesamiento completado",
            total_rows=stats.get('total_rows', 0),
            processed_rows=stats.get('processed_rows', 0),
            auto_saved=stats.get('auto_saved', 0),
            required_validation=stats.get('required_validation', 0),
            empty_rows=stats.get('empty_rows', 0),
            not_found=stats.get('not_found', 0),
            errors=stats.get('errors', 0),
            success_rate=f"{stats.get('success_rate', 0):.1f}%"
        )
