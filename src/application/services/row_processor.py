"""Procesador de renglones individuales del formulario."""
import time
from typing import Optional
from enum import Enum
from dataclasses import dataclass

from ...domain.entities import RowData, FormData, ValidationResult, ValidationAction
from ...domain.ports import (
    AutomationPort,
    ValidationPort,
    OCRPort,
    ConfigPort,
    LoggerPort,
    AlertHandlerPort
)


class ProcessingResultType(Enum):
    """Tipos de resultado del procesamiento de un renglón."""
    AUTO_SAVED = "auto_saved"
    REQUIRED_VALIDATION = "required_validation"
    EMPTY_ROW = "empty_row"
    NOT_FOUND = "not_found"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ProcessingResult:
    """
    Resultado del procesamiento de un renglón.

    Attributes:
        result_type: Tipo de resultado
        success: Si el procesamiento fue exitoso
        row_number: Número de renglón procesado
        cedula: Cédula procesada (si aplica)
        validation_result: Resultado de validación (si aplica)
        error_message: Mensaje de error (si aplica)
    """
    result_type: ProcessingResultType
    success: bool
    row_number: int
    cedula: Optional[str] = None
    validation_result: Optional[ValidationResult] = None
    error_message: Optional[str] = None


class RowProcessor:
    """
    Procesador especializado de renglones individuales.

    Responsabilidades:
    - Digitar cédula en formulario web
    - Leer datos digitales con OCR
    - Validar con fuzzy matching
    - Ejecutar acción según validación
    - Manejar errores de procesamiento

    Esta clase encapsula TODA la lógica de procesamiento de un renglón,
    permitiendo que el orchestrator solo coordine el flujo.

    Example:
        >>> processor = RowProcessor(
        ...     automation=automation_service,
        ...     validator=fuzzy_validator,
        ...     web_ocr=tesseract_service,
        ...     config=config,
        ...     logger=logger
        ... )
        >>> result = processor.process_row(
        ...     row_data=row_data,
        ...     row_number=5,
        ...     alert_handler=alert_handler
        ... )
        >>> if result.success:
        ...     stats.increment_auto_saved()
    """

    def __init__(
        self,
        automation: AutomationPort,
        validator: ValidationPort,
        web_ocr: OCRPort,
        config: ConfigPort,
        logger: LoggerPort
    ):
        """
        Inicializa el procesador de renglones.

        Args:
            automation: Servicio de automatización (pyautogui)
            validator: Servicio de validación (FuzzyValidator)
            web_ocr: Servicio OCR para leer formulario web (Tesseract)
            config: Servicio de configuración
            logger: Logger estructurado
        """
        self.automation = automation
        self.validator = validator
        self.web_ocr = web_ocr
        self.config = config
        self.logger = logger.bind(component="RowProcessor")

        # Cachear configuración (optimización)
        self._page_load_timeout = self.config.get('automation.page_load_timeout', 5)
        self._typing_interval = self.config.get('automation.typing_interval', 0.01)
        self._pre_enter_delay = self.config.get('automation.pre_enter_delay', 0.3)
        self._post_enter_delay = self.config.get('automation.post_enter_delay', 0.5)
        self._auto_click_save = self.config.get('automation.auto_click_save', True)

    def process_row(
        self,
        row_data: RowData,
        row_number: int,
        alert_handler: AlertHandlerPort
    ) -> ProcessingResult:
        """
        Procesa un renglón completo del formulario.

        Flujo:
        1. Verificar si está vacío → manejar vacío
        2. Digitar cédula
        3. Esperar carga de página
        4. Leer datos digitales con OCR
        5. Validar con fuzzy matching
        6. Ejecutar acción según validación

        Args:
            row_data: Datos del renglón manuscrito
            row_number: Número de renglón (1-indexed)
            alert_handler: Handler para mostrar alertas

        Returns:
            ProcessingResult con tipo y estado del procesamiento

        Example:
            >>> result = processor.process_row(row_data, 5, alert_handler)
            >>> if result.result_type == ProcessingResultType.AUTO_SAVED:
            ...     print("Guardado automáticamente")
        """
        self.logger.info(
            "Iniciando procesamiento de renglón",
            row_number=row_number,
            cedula=row_data.cedula if not row_data.is_empty else None
        )

        try:
            # CASO 1: Renglón vacío
            if row_data.is_empty:
                return self._handle_empty_row(row_number, alert_handler)

            # CASO 2: Renglón con datos
            return self._process_data_row(row_data, row_number, alert_handler)

        except Exception as e:
            error_msg = f"Error procesando renglón {row_number}: {str(e)}"
            self.logger.error("Error en procesamiento", row_number=row_number, error=str(e))

            return ProcessingResult(
                result_type=ProcessingResultType.ERROR,
                success=False,
                row_number=row_number,
                cedula=row_data.cedula if not row_data.is_empty else None,
                error_message=error_msg
            )

    def _process_data_row(
        self,
        row_data: RowData,
        row_number: int,
        alert_handler: AlertHandlerPort
    ) -> ProcessingResult:
        """
        Procesa un renglón con datos (no vacío).

        Args:
            row_data: Datos del renglón
            row_number: Número de renglón
            alert_handler: Handler de alertas

        Returns:
            ProcessingResult con el resultado
        """
        self.logger.info(
            "Procesando renglón con datos",
            row_number=row_number,
            cedula=row_data.cedula,
            nombres=row_data.nombres_manuscritos
        )

        # Paso 1: Digitar cédula
        self.logger.debug("Digitando cédula", cedula=row_data.cedula)
        self._digitize_cedula(row_data.cedula)

        # Paso 2: Esperar carga
        self.logger.debug("Esperando carga de página", timeout=self._page_load_timeout)
        time.sleep(self._page_load_timeout)

        # Paso 3: Leer formulario web con OCR
        self.logger.debug("Leyendo formulario web con OCR")
        digital_data = self._read_digital_data(row_data.cedula)

        # Paso 4: Validar con fuzzy matching
        self.logger.debug("Validando con fuzzy matching")
        validation_result = self.validator.validate_person(row_data, digital_data)

        # Paso 5: Ejecutar acción según validación
        return self._execute_validation_action(
            validation_result,
            row_data,
            digital_data,
            row_number,
            alert_handler
        )

    def _handle_empty_row(
        self,
        row_number: int,
        alert_handler: AlertHandlerPort
    ) -> ProcessingResult:
        """
        Maneja un renglón vacío.

        Args:
            row_number: Número de renglón
            alert_handler: Handler de alertas

        Returns:
            ProcessingResult indicando que fue un renglón vacío
        """
        self.logger.info("Renglón vacío detectado", row_number=row_number)

        auto_handle = self.config.get('empty_row_handling.auto_click_button', True)

        if auto_handle:
            button_name = self.config.get('empty_row_handling.button_name', 'Renglón En Blanco')
            self.logger.info(
                "Manejando renglón vacío automáticamente",
                button_name=button_name
            )

            # Solicitar decisión del usuario (aunque sea automático, permitir override)
            action = alert_handler.show_empty_row_prompt(row_number)

            if action == "click_button":
                # TODO: Implementar click en botón
                # self.automation.click_button(button_name)
                self.logger.info("Click automático en botón (no implementado)", button=button_name)
            elif action == "skip":
                self.logger.info("Renglón vacío saltado por usuario")
            elif action == "pause":
                # El orchestrator debe manejar la pausa
                pass

        return ProcessingResult(
            result_type=ProcessingResultType.EMPTY_ROW,
            success=True,
            row_number=row_number
        )

    def _digitize_cedula(self, cedula: str) -> None:
        """
        Digita la cédula en el campo de búsqueda y presiona Enter.

        Args:
            cedula: Cédula a digitar
        """
        # Limpiar campo (Ctrl+A + Delete)
        self.automation.press_key('ctrl+a')
        time.sleep(0.1)
        self.automation.press_key('delete')
        time.sleep(0.2)

        # Digitar cédula
        self.automation.type_text(cedula, interval=self._typing_interval)

        # Esperar antes de Enter
        time.sleep(self._pre_enter_delay)

        # Presionar Enter
        self.automation.press_key('enter')

        # Esperar después de Enter
        time.sleep(self._post_enter_delay)

    def _read_digital_data(self, cedula: str) -> FormData:
        """
        Lee datos del formulario web usando OCR.

        Args:
            cedula: Cédula consultada (para contexto)

        Returns:
            FormData con los datos leídos
        """
        # Aquí se usaría el web_ocr (Tesseract) para leer el formulario web
        # Por ahora es un placeholder

        # TODO: Implementar lectura real del formulario web
        # return self.web_ocr.extract_form_data()

        # Placeholder: retornar FormData vacía
        return FormData(
            primer_nombre="",
            segundo_nombre="",
            primer_apellido="",
            segundo_apellido=""
        )

    def _execute_validation_action(
        self,
        validation_result: ValidationResult,
        row_data: RowData,
        digital_data: FormData,
        row_number: int,
        alert_handler: AlertHandlerPort
    ) -> ProcessingResult:
        """
        Ejecuta la acción según el resultado de validación.

        Args:
            validation_result: Resultado de la validación
            row_data: Datos manuscritos
            digital_data: Datos digitales
            row_number: Número de renglón
            alert_handler: Handler de alertas

        Returns:
            ProcessingResult con el resultado de la acción
        """
        action = validation_result.action

        if action == ValidationAction.AUTO_SAVE:
            # GUARDADO AUTOMÁTICO
            self.logger.info(
                "Validación OK - Guardando automáticamente",
                row_number=row_number,
                confidence=f"{validation_result.confidence:.0%}"
            )

            if self._auto_click_save:
                # TODO: Implementar click en botón guardar
                # self.automation.click_button("Guardar")
                self.logger.info("Click en guardar (no implementado)")

            return ProcessingResult(
                result_type=ProcessingResultType.AUTO_SAVED,
                success=True,
                row_number=row_number,
                cedula=row_data.cedula,
                validation_result=validation_result
            )

        elif action == ValidationAction.ALERT_NOT_FOUND:
            # PERSONA NO ENCONTRADA
            self.logger.warning(
                "Cédula no encontrada en BD",
                row_number=row_number,
                cedula=row_data.cedula
            )

            user_action = alert_handler.show_not_found_alert(
                cedula=row_data.cedula,
                nombres=row_data.nombres_manuscritos,
                row_number=row_number
            )

            # El orchestrator debe manejar la decisión del usuario
            return ProcessingResult(
                result_type=ProcessingResultType.NOT_FOUND,
                success=False,
                row_number=row_number,
                cedula=row_data.cedula,
                validation_result=validation_result
            )

        elif action == ValidationAction.REQUIRE_VALIDATION:
            # REQUIERE VALIDACIÓN MANUAL
            self.logger.warning(
                "Validación requiere intervención manual",
                row_number=row_number,
                cedula=row_data.cedula,
                details=validation_result.details
            )

            user_action = alert_handler.show_validation_mismatch_alert(
                validation_result=validation_result,
                row_number=row_number
            )

            if user_action == "save":
                if self._auto_click_save:
                    # self.automation.click_button("Guardar")
                    self.logger.info("Usuario decidió guardar - Click en guardar (no implementado)")

                return ProcessingResult(
                    result_type=ProcessingResultType.AUTO_SAVED,
                    success=True,
                    row_number=row_number,
                    cedula=row_data.cedula,
                    validation_result=validation_result
                )
            elif user_action == "skip":
                self.logger.info("Usuario decidió saltar renglón")

                return ProcessingResult(
                    result_type=ProcessingResultType.SKIPPED,
                    success=False,
                    row_number=row_number,
                    cedula=row_data.cedula,
                    validation_result=validation_result
                )
            else:
                # "correct", "pause", etc.
                return ProcessingResult(
                    result_type=ProcessingResultType.REQUIRED_VALIDATION,
                    success=False,
                    row_number=row_number,
                    cedula=row_data.cedula,
                    validation_result=validation_result
                )

        # Caso inesperado
        self.logger.error(
            "Acción de validación no reconocida",
            action=action,
            row_number=row_number
        )

        return ProcessingResult(
            result_type=ProcessingResultType.ERROR,
            success=False,
            row_number=row_number,
            cedula=row_data.cedula,
            error_message=f"Acción no reconocida: {action}"
        )
