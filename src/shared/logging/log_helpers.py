"""Helpers para facilitar migracion de print() a logging estructurado."""
from typing import Any, Optional
from ...domain.ports import LoggerPort


def log_debug_message(logger: LoggerPort, message: str, **context: Any) -> None:
    """
    Helper para mensajes DEBUG (reemplazo de print para debugging).

    Usar para mensajes de debugging que solo importan en desarrollo.

    Args:
        logger: Logger a usar
        message: Mensaje a loguear
        **context: Contexto adicional

    Example (ANTES):
        print(f"DEBUG Google Vision: Texto completo detectado:\\n{full_text}")

    Example (DESPUES):
        log_debug_message(logger, "Texto completo detectado", full_text=full_text)
    """
    logger.debug(message, **context)


def log_info_message(logger: LoggerPort, message: str, **context: Any) -> None:
    """
    Helper para mensajes INFO (reemplazo de print para informacion general).

    Usar para flujo normal de la aplicacion.

    Args:
        logger: Logger a usar
        message: Mensaje a loguear
        **context: Contexto adicional

    Example (ANTES):
        print("✓ Google Vision: Respuesta recibida (1 llamada API)")

    Example (DESPUES):
        log_info_message(logger, "Respuesta recibida", api_calls=1)
    """
    logger.info(message, **context)


def log_warning_message(logger: LoggerPort, message: str, **context: Any) -> None:
    """
    Helper para mensajes WARNING (reemplazo de print para advertencias).

    Usar para situaciones que no son errores pero requieren atencion.

    Args:
        logger: Logger a usar
        message: Mensaje a loguear
        **context: Contexto adicional

    Example (ANTES):
        print(f"ADVERTENCIA: Texto '{text_clean}' no encontrado en respuesta")

    Example (DESPUES):
        log_warning_message(logger, "Texto no encontrado en respuesta", text=text_clean)
    """
    logger.warning(message, **context)


def log_error_message(
    logger: LoggerPort,
    message: str,
    error: Optional[Exception] = None,
    **context: Any
) -> None:
    """
    Helper para mensajes ERROR (reemplazo de print para errores).

    Usar para errores y excepciones.

    Args:
        logger: Logger a usar
        message: Mensaje de error
        error: Excepcion (opcional)
        **context: Contexto adicional

    Example (ANTES):
        print(f"ERROR Google Vision: {e}")

    Example (DESPUES):
        log_error_message(logger, "Error en Google Vision API", error=e)
    """
    error_context = context.copy()
    if error:
        error_context["error_type"] = type(error).__name__
        error_context["error_message"] = str(error)

    logger.error(message, **error_context)


def log_success(logger: LoggerPort, operation: str, **metrics: Any) -> None:
    """
    Helper para loguear operaciones exitosas con metricas.

    Args:
        logger: Logger a usar
        operation: Nombre de la operacion
        **metrics: Metricas de la operacion

    Example (ANTES):
        print(f"✓ Cedula extraida: '{num}' ({len(num)} digitos)")

    Example (DESPUES):
        log_success(logger, "cedula_extraida", cedula=num, digits=len(num))
    """
    logger.info(f"Operacion exitosa: {operation}", status="success", **metrics)


def log_failure(
    logger: LoggerPort,
    operation: str,
    error: Optional[Exception] = None,
    **context: Any
) -> None:
    """
    Helper para loguear operaciones fallidas.

    Args:
        logger: Logger a usar
        operation: Nombre de la operacion
        error: Excepcion (opcional)
        **context: Contexto adicional

    Example (ANTES):
        print(f"✗ Descartada (muy corta): '{num}' ({len(num)} digitos)")

    Example (DESPUES):
        log_failure(logger, "cedula_descartada", reason="too_short", cedula=num, length=len(num))
    """
    error_context = {"status": "failed", **context}
    if error:
        error_context["error_type"] = type(error).__name__
        error_context["error_message"] = str(error)

    logger.warning(f"Operacion fallida: {operation}", **error_context)


def log_api_call(
    logger: LoggerPort,
    provider: str,
    method: str,
    **context: Any
) -> None:
    """
    Helper para loguear llamadas a APIs externas.

    Args:
        logger: Logger a usar
        provider: Proveedor de API (google_vision, azure_vision, etc.)
        method: Metodo llamado
        **context: Contexto adicional

    Example (ANTES):
        print("DEBUG Google Vision: Llamando a DOCUMENT_TEXT_DETECTION (es)...")

    Example (DESPUES):
        log_api_call(logger, "google_vision", "document_text_detection", language="es")
    """
    logger.info(
        f"Llamando API: {provider}.{method}",
        api_provider=provider,
        api_method=method,
        **context
    )


def log_api_response(
    logger: LoggerPort,
    provider: str,
    success: bool,
    duration_ms: Optional[float] = None,
    **metrics: Any
) -> None:
    """
    Helper para loguear respuestas de APIs externas.

    Args:
        logger: Logger a usar
        provider: Proveedor de API
        success: Si la llamada fue exitosa
        duration_ms: Duracion en milisegundos (opcional)
        **metrics: Metricas adicionales

    Example (ANTES):
        print("✓ Azure Vision: Respuesta recibida (1 llamada API)")

    Example (DESPUES):
        log_api_response(logger, "azure_vision", True, duration_ms=150, api_calls=1)
    """
    status = "success" if success else "failed"

    context = {
        "api_provider": provider,
        "status": status,
        **metrics
    }

    if duration_ms is not None:
        context["duration_ms"] = round(duration_ms, 2)

    logger.info(f"Respuesta API: {provider}", **context)


def log_ocr_extraction(
    logger: LoggerPort,
    provider: str,
    items_extracted: int,
    **metrics: Any
) -> None:
    """
    Helper para loguear extraccion OCR.

    Args:
        logger: Logger a usar
        provider: Proveedor OCR
        items_extracted: Numero de items extraidos
        **metrics: Metricas adicionales

    Example (ANTES):
        print(f"DEBUG Google Vision: Total cedulas unicas: {len(unique_records)}")

    Example (DESPUES):
        log_ocr_extraction(logger, "google_vision", len(unique_records))
    """
    logger.info(
        f"Extraccion OCR completada: {provider}",
        ocr_provider=provider,
        items_extracted=items_extracted,
        **metrics
    )


def log_processing_step(
    logger: LoggerPort,
    step: str,
    step_number: Optional[int] = None,
    **context: Any
) -> None:
    """
    Helper para loguear pasos de procesamiento.

    Args:
        logger: Logger a usar
        step: Descripcion del paso
        step_number: Numero del paso (opcional)
        **context: Contexto adicional

    Example (ANTES):
        print(f"\\n[PASO 1] Enviando imagen completa a Google Vision API...")

    Example (DESPUES):
        log_processing_step(logger, "Enviando imagen a API", step_number=1, provider="google_vision")
    """
    step_info = {"processing_step": step, **context}

    if step_number is not None:
        step_info["step_number"] = step_number

    logger.info(f"Paso de procesamiento: {step}", **step_info)
