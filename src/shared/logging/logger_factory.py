"""Factory para crear loggers con configuracion consistente."""
from typing import Any, Dict, Optional
from .structured_logger import StructuredLogger
from ...domain.ports import LoggerPort


class LoggerFactory:
    """
    Factory para crear loggers con configuracion consistente.

    Provee loggers pre-configurados para diferentes modulos:
    - OCR operations
    - Image processing
    - API requests (futuro)
    - Database operations
    - Business logic

    Beneficios:
    - Configuracion centralizada
    - Consistencia en logging
    - Facil agregar contexto global (environment, version, etc.)
    """

    _default_config: Dict[str, Any] = {
        "log_dir": "logs"
    }

    _global_context: Dict[str, Any] = {}

    @classmethod
    def set_global_context(cls, **context: Any) -> None:
        """
        Configura contexto global para todos los loggers.

        Este contexto se incluira automaticamente en todos los logs.

        Args:
            **context: Contexto global (environment, app_version, etc.)

        Example:
            LoggerFactory.set_global_context(
                environment="production",
                app_version="1.0.0",
                instance_id="server-01"
            )
        """
        cls._global_context.update(context)

    @classmethod
    def set_default_config(cls, **config: Any) -> None:
        """
        Configura opciones por defecto para todos los loggers.

        Args:
            **config: Configuracion (log_dir, etc.)

        Example:
            LoggerFactory.set_default_config(log_dir="/var/log/myapp")
        """
        cls._default_config.update(config)

    @classmethod
    def get_logger(
        cls,
        name: str,
        **context: Any
    ) -> LoggerPort:
        """
        Crea un logger con configuracion estandar.

        Args:
            name: Nombre del logger (ej: "ocr.google_vision", "api.auth")
            **context: Contexto adicional especifico de este logger

        Returns:
            Logger configurado

        Example:
            logger = LoggerFactory.get_logger("ocr.google_vision", provider="google")
        """
        # Combinar contexto global con contexto especifico
        full_context = {**cls._global_context, **context}

        return StructuredLogger(
            name=name,
            **cls._default_config,
            **full_context
        )

    @classmethod
    def get_ocr_logger(
        cls,
        provider: str,
        **context: Any
    ) -> LoggerPort:
        """
        Crea un logger pre-configurado para operaciones OCR.

        Args:
            provider: Proveedor OCR (google_vision, azure_vision, etc.)
            **context: Contexto adicional

        Returns:
            Logger configurado para OCR

        Example:
            logger = LoggerFactory.get_ocr_logger("google_vision")
        """
        return cls.get_logger(
            f"ocr.{provider}",
            component="ocr",
            provider=provider,
            **context
        )

    @classmethod
    def get_api_logger(
        cls,
        endpoint: Optional[str] = None,
        **context: Any
    ) -> LoggerPort:
        """
        Crea un logger pre-configurado para operaciones API REST.

        Util para cuando migres a API REST.

        Args:
            endpoint: Endpoint de API (ej: "/api/v1/images")
            **context: Contexto adicional

        Returns:
            Logger configurado para API

        Example:
            logger = LoggerFactory.get_api_logger("/api/v1/process")
        """
        logger_context = {
            "component": "api",
            **context
        }

        if endpoint:
            logger_context["endpoint"] = endpoint

        return cls.get_logger("api", **logger_context)

    @classmethod
    def get_image_logger(cls, **context: Any) -> LoggerPort:
        """
        Crea un logger pre-configurado para procesamiento de imagenes.

        Args:
            **context: Contexto adicional

        Returns:
            Logger configurado para imagen

        Example:
            logger = LoggerFactory.get_image_logger()
        """
        return cls.get_logger(
            "image.processing",
            component="image",
            **context
        )

    @classmethod
    def get_domain_logger(cls, domain: str, **context: Any) -> LoggerPort:
        """
        Crea un logger pre-configurado para logica de dominio.

        Args:
            domain: Nombre del dominio (ej: "cedula", "form", "validation")
            **context: Contexto adicional

        Returns:
            Logger configurado para dominio

        Example:
            logger = LoggerFactory.get_domain_logger("validation")
        """
        return cls.get_logger(
            f"domain.{domain}",
            component="domain",
            domain=domain,
            **context
        )

    @classmethod
    def get_infrastructure_logger(
        cls,
        service: str,
        **context: Any
    ) -> LoggerPort:
        """
        Crea un logger pre-configurado para servicios de infraestructura.

        Args:
            service: Servicio (ej: "database", "cache", "storage")
            **context: Contexto adicional

        Returns:
            Logger configurado para infraestructura

        Example:
            logger = LoggerFactory.get_infrastructure_logger("database")
        """
        return cls.get_logger(
            f"infrastructure.{service}",
            component="infrastructure",
            service=service,
            **context
        )
