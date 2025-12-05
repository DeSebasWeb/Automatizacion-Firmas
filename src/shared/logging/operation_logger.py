"""Context managers para logging de operaciones con tracking automatico."""
import time
import uuid
from contextlib import contextmanager
from typing import Any, Optional, Dict, Generator
from ...domain.ports import LoggerPort


class OperationLogger:
    """
    Context manager para logging estructurado de operaciones.

    Rastrea automaticamente:
    - Inicio y fin de operaciones
    - Duracion de operaciones
    - IDs unicos de operacion (para correlation en API REST)
    - Exitos y fallas
    - Metricas personalizadas

    Uso:
        logger = StructuredLogger("ocr")
        with OperationLogger(logger, "extract_cedulas", image_id=123):
            # Tu codigo aqui
            cedulas = extract_cedulas(image)

    En API REST futuro:
        with OperationLogger(logger, "process_request", request_id=req_id, user_id=user):
            # Procesar request
            result = process(data)
    """

    def __init__(
        self,
        logger: LoggerPort,
        operation: str,
        **context: Any
    ):
        """
        Inicializa el context manager.

        Args:
            logger: Logger a utilizar
            operation: Nombre de la operacion
            **context: Contexto adicional (request_id, user_id, image_id, etc.)
        """
        self.logger = logger
        self.operation = operation
        self.operation_id = str(uuid.uuid4())
        self.context = context
        self.start_time: Optional[float] = None
        self.metrics: Dict[str, Any] = {}

    def __enter__(self) -> 'OperationLogger':
        """Inicia el tracking de la operacion."""
        self.start_time = time.time()

        self.logger.info(
            f"Iniciando operacion: {self.operation}",
            operation=self.operation,
            operation_id=self.operation_id,
            **self.context
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza el tracking de la operacion."""
        duration = time.time() - self.start_time if self.start_time else 0

        if exc_type is None:
            # Operacion exitosa
            self.logger.info(
                f"Operacion completada: {self.operation}",
                operation=self.operation,
                operation_id=self.operation_id,
                duration_seconds=round(duration, 3),
                status="success",
                **self.context,
                **self.metrics
            )
        else:
            # Operacion fallida
            self.logger.error(
                f"Operacion fallida: {self.operation}",
                operation=self.operation,
                operation_id=self.operation_id,
                duration_seconds=round(duration, 3),
                status="error",
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                **self.context,
                **self.metrics
            )

        # No suprimimos la excepcion
        return False

    def add_metric(self, key: str, value: Any) -> None:
        """
        Agrega una metrica a reportar al finalizar.

        Args:
            key: Nombre de la metrica
            value: Valor de la metrica

        Example:
            with OperationLogger(logger, "extract_cedulas") as op:
                cedulas = extract_cedulas(image)
                op.add_metric("cedulas_extraidas", len(cedulas))
                op.add_metric("confianza_promedio", avg_conf)
        """
        self.metrics[key] = value

    def add_context(self, **kwargs: Any) -> None:
        """
        Agrega contexto adicional durante la operacion.

        Args:
            **kwargs: Contexto a agregar

        Example:
            with OperationLogger(logger, "process_image") as op:
                ocr_result = call_ocr(image)
                op.add_context(ocr_provider="google_vision")
        """
        self.context.update(kwargs)


@contextmanager
def log_operation(
    logger: LoggerPort,
    operation: str,
    **context: Any
) -> Generator[OperationLogger, None, None]:
    """
    Context manager conveniente para logging de operaciones.

    Funcion helper que puede usarse con 'with' directamente.

    Args:
        logger: Logger a utilizar
        operation: Nombre de la operacion
        **context: Contexto adicional

    Yields:
        OperationLogger instance

    Example:
        logger = StructuredLogger("ocr")
        with log_operation(logger, "extract_cedulas", image_id=123) as op:
            cedulas = extract_cedulas(image)
            op.add_metric("count", len(cedulas))
    """
    operation_logger = OperationLogger(logger, operation, **context)
    with operation_logger as op:
        yield op


class APIOperationLogger(OperationLogger):
    """
    Context manager especializado para operaciones de API REST.

    Agrega automaticamente campos relevantes para APIs:
    - request_id
    - endpoint
    - method (GET, POST, etc.)
    - user_id (si aplica)
    - client_ip (si aplica)

    Uso futuro en API REST:
        with APIOperationLogger(
            logger,
            "process_image_upload",
            request_id=request_id,
            endpoint="/api/v1/images/process",
            method="POST",
            user_id=user.id,
            client_ip=request.client.host
        ) as op:
            result = process_image(image_data)
            op.add_metric("processing_time_ms", processing_time)
            op.add_metric("cedulas_found", len(result.cedulas))
    """

    def __init__(
        self,
        logger: LoggerPort,
        operation: str,
        request_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        **context: Any
    ):
        """
        Inicializa el logger de operacion API.

        Args:
            logger: Logger a utilizar
            operation: Nombre de la operacion
            request_id: ID del request HTTP (auto-generado si no se provee)
            endpoint: Endpoint HTTP
            method: Metodo HTTP (GET, POST, etc.)
            **context: Contexto adicional (user_id, client_ip, etc.)
        """
        # Auto-generar request_id si no se provee
        if request_id is None:
            request_id = str(uuid.uuid4())

        # Agregar campos API al contexto
        api_context = {
            "request_id": request_id,
            **({"endpoint": endpoint} if endpoint else {}),
            **({"method": method} if method else {}),
            **context
        }

        super().__init__(logger, operation, **api_context)
