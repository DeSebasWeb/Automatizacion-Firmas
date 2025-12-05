"""Factory para crear ProcessingOrchestrator con todas sus dependencias inyectadas.

Este factory encapsula la complejidad de crear y configurar el orchestrator
con todas sus dependencias. Será útil tanto para la GUI actual como para
la futura migración a API REST.

Example:
    >>> # Uso básico (con defaults):
    >>> factory = OrchestratorFactory()
    >>> orchestrator = factory.create()

    >>> # Con configuración personalizada:
    >>> from src.shared.config import YamlConfig
    >>> config = YamlConfig('config/settings.yaml')
    >>> orchestrator = factory.create(config=config, ocr_provider='digit_ensemble')

    >>> # Para API REST (sin GUI handlers):
    >>> orchestrator = factory.create_for_api(config=config)
"""

from typing import Optional

from ...domain.ports import (
    OCRPort,
    ConfigPort,
    LoggerPort,
    AlertHandlerPort,
    ProgressHandlerPort
)
from ..services import (
    ProcessingOrchestrator,
    RowProcessor,
    KeyboardController,
    ProcessingReporter,
    FuzzyValidator
)


class OrchestratorFactory:
    """
    Factory para crear ProcessingOrchestrator con dependency injection.

    Este factory:
    - Crea todas las dependencias necesarias
    - Configura cada componente según settings
    - Inyecta dependencias vía constructor (SOLID)
    - Separa creación de GUI vs API REST

    Beneficios:
    - ✅ Centraliza la lógica de creación
    - ✅ Facilita testing (mock del factory)
    - ✅ Facilita migración a API REST
    - ✅ Reduce acoplamiento
    """

    def __init__(self):
        """Inicializa el factory."""
        pass

    def create(
        self,
        config: Optional[ConfigPort] = None,
        logger: Optional[LoggerPort] = None,
        alert_handler: Optional[AlertHandlerPort] = None,
        progress_handler: Optional[ProgressHandlerPort] = None,
        ocr_provider: Optional[str] = None
    ) -> ProcessingOrchestrator:
        """
        Crea ProcessingOrchestrator con todas las dependencias inyectadas.

        Args:
            config: Servicio de configuración (default: YamlConfig)
            logger: Logger estructurado (default: StructuredLogger)
            alert_handler: Handler de alertas (DEBE proveerse desde GUI)
            progress_handler: Handler de progreso (DEBE proveerse desde GUI)
            ocr_provider: Proveedor OCR (default: desde config)

        Returns:
            ProcessingOrchestrator completamente configurado

        Raises:
            ValueError: Si no se proveen alert_handler o progress_handler

        Note:
            Para uso con GUI, DEBES proveer alert_handler y progress_handler
            desde la ventana principal.

            Para uso con API REST, usa create_for_api() en su lugar.

        Example:
            >>> # Desde GUI:
            >>> factory = OrchestratorFactory()
            >>> orchestrator = factory.create(
            ...     alert_handler=GUIAlertHandler(self),
            ...     progress_handler=GUIProgressHandler(self)
            ... )
        """
        # Validar que se provean handlers (requeridos para GUI)
        if alert_handler is None:
            raise ValueError(
                "alert_handler es requerido. "
                "Provéelo desde la GUI o usa create_for_api() para API REST."
            )

        if progress_handler is None:
            raise ValueError(
                "progress_handler es requerido. "
                "Provéelo desde la GUI o usa create_for_api() para API REST."
            )

        # 1. Config
        if config is None:
            from ...shared.config import YamlConfig
            config = YamlConfig('config/settings.yaml')

        # 2. Logger
        if logger is None:
            from ...shared.logging import StructuredLogger
            logger = StructuredLogger()

        # 3. OCR Service
        ocr_service = self._create_ocr_service(config, ocr_provider)

        # 4. Validator
        validator = self._create_validator(config, logger)

        # 5. Automation
        automation = self._create_automation(logger)

        # 6. Web OCR (para leer formulario web)
        web_ocr = self._create_web_ocr(config, logger)

        # 7. RowProcessor
        row_processor = RowProcessor(
            automation=automation,
            validator=validator,
            web_ocr=web_ocr,
            config=config,
            logger=logger
        )

        # 8. KeyboardController
        keyboard_controller = KeyboardController(
            on_pause=None,  # Se configura en orchestrator
            on_resume=None,  # Se configura en orchestrator
            logger=logger
        )

        # 9. ProcessingReporter
        reporter = ProcessingReporter()

        # 10. ProcessingOrchestrator (¡TODO junto!)
        orchestrator = ProcessingOrchestrator(
            ocr_service=ocr_service,
            row_processor=row_processor,
            alert_handler=alert_handler,
            progress_handler=progress_handler,
            keyboard_controller=keyboard_controller,
            reporter=reporter,
            logger=logger
        )

        logger.info(
            "ProcessingOrchestrator creado exitosamente",
            ocr_provider=ocr_provider or config.get('ocr.provider', 'digit_ensemble')
        )

        return orchestrator

    def create_for_api(
        self,
        config: Optional[ConfigPort] = None,
        logger: Optional[LoggerPort] = None,
        ocr_provider: Optional[str] = None
    ) -> ProcessingOrchestrator:
        """
        Crea ProcessingOrchestrator para uso en API REST (sin GUI).

        Usa handlers dummy que no requieren interfaz gráfica:
        - APIAlertHandler: Retorna respuestas automáticas
        - APIProgressHandler: Log de progreso (no muestra nada)

        Args:
            config: Servicio de configuración (default: YamlConfig)
            logger: Logger estructurado (default: StructuredLogger)
            ocr_provider: Proveedor OCR (default: desde config)

        Returns:
            ProcessingOrchestrator configurado para API REST

        Example:
            >>> # En FastAPI endpoint:
            >>> factory = OrchestratorFactory()
            >>> orchestrator = factory.create_for_api()
            >>> stats = orchestrator.process_form(form_image)
            >>> return {"stats": stats.to_dict()}
        """
        # 1. Config
        if config is None:
            from ...shared.config import YamlConfig
            config = YamlConfig('config/settings.yaml')

        # 2. Logger
        if logger is None:
            from ...shared.logging import StructuredLogger
            logger = StructuredLogger()

        # 3. Handlers para API (no GUI)
        alert_handler = self._create_api_alert_handler(config, logger)
        progress_handler = self._create_api_progress_handler(logger)

        # 4. Crear orchestrator con handlers de API
        return self.create(
            config=config,
            logger=logger,
            alert_handler=alert_handler,
            progress_handler=progress_handler,
            ocr_provider=ocr_provider
        )

    def _create_ocr_service(
        self,
        config: ConfigPort,
        ocr_provider: Optional[str] = None
    ) -> OCRPort:
        """
        Crea el servicio OCR según configuración.

        Args:
            config: Servicio de configuración
            ocr_provider: Override del proveedor (default: desde config)

        Returns:
            Adaptador OCR configurado

        Raises:
            RuntimeError: Si no se pudo crear ningún proveedor OCR
        """
        from ...infrastructure.ocr import ocr_factory

        # Override temporal del proveedor si se especificó
        original_provider = None
        if ocr_provider:
            original_provider = config.get('ocr.provider')
            config.set('ocr.provider', ocr_provider)

        try:
            ocr_service = ocr_factory.create_ocr_adapter(config)

            if ocr_service is None:
                raise RuntimeError(
                    "No se pudo inicializar ningún proveedor OCR. "
                    "Verifica tu configuración y credenciales."
                )

            return ocr_service

        finally:
            # Restaurar proveedor original
            if original_provider:
                config.set('ocr.provider', original_provider)

    def _create_validator(
        self,
        config: ConfigPort,
        logger: LoggerPort
    ) -> FuzzyValidator:
        """
        Crea el validador fuzzy.

        Args:
            config: Servicio de configuración
            logger: Logger estructurado

        Returns:
            FuzzyValidator configurado
        """
        min_similarity = config.get('validation.min_similarity', 0.85)

        validator = FuzzyValidator(min_similarity=min_similarity)

        logger.info(
            "FuzzyValidator creado",
            min_similarity=min_similarity
        )

        return validator

    def _create_automation(self, logger: LoggerPort):
        """
        Crea el servicio de automatización (PyAutoGUI).

        Args:
            logger: Logger estructurado

        Returns:
            Adaptador de automatización
        """
        from ...infrastructure.automation import PyAutoGUIAutomation

        automation = PyAutoGUIAutomation()

        logger.info("PyAutoGUIAutomation creado")

        return automation

    def _create_web_ocr(
        self,
        config: ConfigPort,
        logger: LoggerPort
    ) -> OCRPort:
        """
        Crea el servicio OCR para leer formulario web (Tesseract).

        Args:
            config: Servicio de configuración
            logger: Logger estructurado

        Returns:
            Adaptador OCR para web
        """
        from ...infrastructure.ocr.tesseract_web_scraper import TesseractWebScraper

        web_ocr = TesseractWebScraper(config)

        logger.info("TesseractWebScraper creado para formulario web")

        return web_ocr

    def _create_api_alert_handler(
        self,
        config: ConfigPort,
        logger: LoggerPort
    ) -> AlertHandlerPort:
        """
        Crea un handler de alertas para API REST (sin GUI).

        Este handler:
        - No muestra diálogos
        - Retorna respuestas automáticas según configuración
        - Logea todas las alertas

        Args:
            config: Servicio de configuración
            logger: Logger estructurado

        Returns:
            APIAlertHandler configurado
        """
        from .api_handlers import APIAlertHandler

        return APIAlertHandler(config, logger)

    def _create_api_progress_handler(
        self,
        logger: LoggerPort
    ) -> ProgressHandlerPort:
        """
        Crea un handler de progreso para API REST (sin GUI).

        Este handler:
        - No muestra barras de progreso
        - Logea todo el progreso
        - Permite monitorear via logs

        Args:
            logger: Logger estructurado

        Returns:
            APIProgressHandler configurado
        """
        from .api_handlers import APIProgressHandler

        return APIProgressHandler(logger)
