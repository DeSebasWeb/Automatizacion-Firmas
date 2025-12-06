"""Factory para crear adaptadores OCR según configuración."""
from typing import Optional

from ...domain.ports import OCRPort, ConfigPort
from ...shared.logging import LoggerFactory, log_info_message, log_warning_message, log_error_message


def create_ocr_adapter(config: ConfigPort) -> Optional[OCRPort]:
    """
    Factory que crea el adaptador OCR según configuración.

    Lee la configuración 'ocr.provider' y retorna el adaptador apropiado:
    - "google_vision": GoogleVisionAdapter (recomendado para manuscritos)
    - "azure_vision": AzureVisionAdapter (alternativa para comparación)
    - "ensemble": EnsembleOCR (máxima precisión, doble costo)
    - "digit_ensemble": DigitLevelEnsembleOCR (ULTRA precisión por dígito, doble costo)

    Args:
        config: Servicio de configuración

    Returns:
        Adaptador OCR inicializado, o None si no se pudo crear

    Example:
        >>> config = YamlConfigAdapter('config/settings.yaml')
        >>> ocr = create_ocr_adapter(config)
        >>> if ocr:
        ...     records = ocr.extract_cedulas(image)

    Note:
        Si el proveedor configurado no está disponible, intenta fallback
        automático a otros proveedores disponibles.
    """
    logger = LoggerFactory.get_infrastructure_logger("ocr_factory")

    provider = config.get('ocr.provider', 'google_vision').lower()

    log_info_message(
        logger,
        "Inicializando proveedor OCR",
        provider=provider,
        component="ocr_factory"
    )

    # Intentar crear el proveedor configurado
    ocr_adapter = _try_create_provider(provider, config, logger)

    if ocr_adapter:
        return ocr_adapter

    # Si falló, intentar fallback automático
    log_warning_message(
        logger,
        "No se pudo inicializar proveedor configurado, intentando fallback",
        failed_provider=provider
    )

    fallback_order = ['google_vision', 'azure_vision', 'tesseract']

    for fallback_provider in fallback_order:
        if fallback_provider == provider:
            continue  # Ya lo intentamos

        logger.info("Intentando proveedor fallback", provider=fallback_provider)
        ocr_adapter = _try_create_provider(fallback_provider, config, logger)

        if ocr_adapter:
            log_info_message(
                logger,
                "Fallback exitoso",
                fallback_provider=fallback_provider,
                original_provider=provider
            )
            return ocr_adapter

    # Si ninguno funcionó
    log_error_message(
        logger,
        "No se pudo inicializar ningun proveedor OCR",
        attempted_providers=[provider] + fallback_order,
        solutions=[
            "Google Vision: Configurar gcloud auth application-default login",
            "Azure Vision: Configurar AZURE_VISION_ENDPOINT y AZURE_VISION_KEY",
            "Tesseract: Instalar con pip install pytesseract"
        ]
    )

    return None


def _try_create_provider(provider: str, config: ConfigPort, logger) -> Optional[OCRPort]:
    """
    Intenta crear un proveedor OCR específico.

    Args:
        provider: Nombre del proveedor ("google_vision", "azure_vision", etc.)
        config: Servicio de configuración
        logger: Logger para registrar eventos

    Returns:
        Adaptador OCR o None si falló
    """
    try:
        if provider == 'google_vision':
            from .google_vision_adapter import GoogleVisionAdapter
            logger.info("Inicializando Google Cloud Vision")
            adapter = GoogleVisionAdapter(config)
            log_info_message(
                logger,
                "Google Cloud Vision inicializado correctamente",
                free_tier="1,000 imagenes/mes",
                equivalent_cedulas="15,000 cedulas/mes"
            )
            return adapter

        elif provider == 'azure_vision':
            from .azure_vision_adapter import AzureVisionAdapter
            logger.info("Inicializando Azure Computer Vision")
            adapter = AzureVisionAdapter(config)
            log_info_message(
                logger,
                "Azure Computer Vision inicializado correctamente",
                free_tier="5,000 transacciones/mes",
                equivalent_cedulas="75,000 cedulas/mes"
            )
            return adapter

        elif provider == 'ensemble':
            from .ensemble_ocr import EnsembleOCR
            logger.info("Inicializando Ensemble OCR", providers=["google_vision", "azure_vision"])
            adapter = EnsembleOCR(config)
            log_info_message(
                logger,
                "Ensemble OCR inicializado correctamente",
                mode="maxima_precision",
                cost_multiplier=2,
                warning="Doble costo - usa ambas APIs"
            )
            return adapter

        elif provider == 'digit_ensemble':
            from .google_vision_adapter import GoogleVisionAdapter
            from .azure_vision_adapter import AzureVisionAdapter
            from .digit_level_ensemble_ocr import DigitLevelEnsembleOCR

            logger.info("Inicializando Digit-Level Ensemble OCR")
            logger.debug("Creando Azure Vision adapter (Primary)")
            azure = AzureVisionAdapter(config)
            logger.debug("Creando Google Vision adapter (Secondary)")
            google = GoogleVisionAdapter(config)
            logger.debug("Combinando ambos con logica de votacion por digito")

            adapter = DigitLevelEnsembleOCR(
                config=config,
                primary_ocr=azure,      # Azure como primary (mejor precisión)
                secondary_ocr=google    # Google como secondary
            )
            log_info_message(
                logger,
                "Digit-Level Ensemble inicializado correctamente",
                precision="98-99.5%",
                cost_multiplier=2,
                strategy="votacion_por_digito",
                warning="Doble costo - usa ambas APIs"
            )
            return adapter

        elif provider == 'tesseract':
            from .tesseract_ocr import TesseractOCR
            logger.info("Inicializando Tesseract OCR")
            adapter = TesseractOCR(config)
            log_info_message(
                logger,
                "Tesseract OCR inicializado correctamente",
                cost="gratis",
                precision="70-85%"
            )
            return adapter

        else:
            log_error_message(logger, "Proveedor OCR desconocido", provider=provider)
            return None

    except ImportError as e:
        log_error_message(
            logger,
            "Proveedor OCR no esta instalado",
            provider=provider,
            error=e
        )
        return None
    except Exception as e:
        log_error_message(
            logger,
            "Error inicializando proveedor OCR",
            provider=provider,
            error=e
        )
        return None


def get_available_providers() -> list:
    """
    Obtiene lista de proveedores OCR disponibles en el sistema.

    Returns:
        Lista de strings con nombres de proveedores disponibles

    Example:
        >>> providers = get_available_providers()
        >>> print(f"Proveedores disponibles: {', '.join(providers)}")
    """
    available = []

    # Verificar Google Vision
    try:
        from google.cloud import vision
        available.append('google_vision')
    except ImportError:
        pass

    # Verificar Azure Vision
    try:
        from azure.ai.vision.imageanalysis import ImageAnalysisClient
        available.append('azure_vision')
    except ImportError:
        pass

    # Verificar Tesseract
    try:
        import pytesseract
        available.append('tesseract')
    except ImportError:
        pass

    # Ensemble solo si hay Google Vision y Azure Vision
    if 'google_vision' in available and 'azure_vision' in available:
        available.append('ensemble')
        available.append('digit_ensemble')

    return available


def get_provider_comparison() -> dict:
    """
    Obtiene datos comparativos de proveedores OCR disponibles.

    Returns:
        Dict con información de cada proveedor y recomendaciones
    """
    return {
        'providers': {
            'google_vision': {
                'precision': '95-98%',
                'cost_per_1000': '$5.16 COP',
                'speed': '1-2 seg',
                'free_tier': '1,000 imgs/mes'
            },
            'azure_vision': {
                'precision': '96-98%',
                'cost_per_1000': '$4,200 COP',
                'speed': '1-2 seg',
                'free_tier': '5,000 trans/mes'
            },
            'ensemble': {
                'precision': '>99%',
                'cost_per_1000': '$9,360 COP',
                'speed': '2-3 seg',
                'note': 'Doble costo'
            },
            'digit_ensemble': {
                'precision': '98-99.5%',
                'cost_per_1000': '$9,360 COP',
                'speed': '2-3 seg',
                'recommended': True,
                'note': 'Votacion digito por digito'
            },
            'tesseract': {
                'precision': '70-85%',
                'cost_per_1000': 'Gratis',
                'speed': '0.5-1 seg',
                'note': 'Local, sin conexion'
            }
        },
        'recommendations': {
            'max_precision': 'digit_ensemble',
            'production': 'google_vision',
            'comparison': 'azure_vision',
            'high_precision': 'ensemble',
            'development': 'tesseract'
        },
        'available': get_available_providers()
    }
