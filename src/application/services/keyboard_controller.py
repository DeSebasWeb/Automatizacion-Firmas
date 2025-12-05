"""Controlador de eventos de teclado para pausas y reanudaciones."""
from typing import Optional, Callable
from pynput import keyboard

from ...domain.ports import LoggerPort


class KeyboardController:
    """
    Controlador especializado para manejo de eventos de teclado.

    Responsabilidades:
    - Escuchar teclas ESC (pausar) y F9 (reanudar)
    - Notificar mediante callbacks cuando se presionan
    - Gestionar lifecycle del listener

    Example:
        >>> def on_pause():
        ...     print("Pausa solicitada")
        >>> def on_resume():
        ...     print("Reanudación solicitada")
        >>>
        >>> controller = KeyboardController(
        ...     on_pause=on_pause,
        ...     on_resume=on_resume,
        ...     logger=logger
        ... )
        >>> controller.start()
        >>> # ... proceso ...
        >>> controller.stop()
    """

    def __init__(
        self,
        on_pause: Optional[Callable[[], None]] = None,
        on_resume: Optional[Callable[[], None]] = None,
        logger: Optional[LoggerPort] = None
    ):
        """
        Inicializa el controlador de teclado.

        Args:
            on_pause: Callback a ejecutar cuando se presiona ESC
            on_resume: Callback a ejecutar cuando se presiona F9
            logger: Logger para registrar eventos
        """
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.logger = logger.bind(component="KeyboardController") if logger else None

        self._listener: Optional[keyboard.Listener] = None
        self._is_active = False

    def start(self) -> None:
        """
        Inicia el listener de teclado.

        Raises:
            RuntimeError: Si el listener ya está activo
        """
        if self._is_active:
            raise RuntimeError("Keyboard listener ya está activo")

        def on_press(key):
            try:
                if key == keyboard.Key.esc:
                    self._handle_pause()
                elif key == keyboard.Key.f9:
                    self._handle_resume()
            except AttributeError:
                pass  # Teclas especiales no soportadas

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()
        self._is_active = True

        if self.logger:
            self.logger.info("Keyboard listener iniciado", pause_key="ESC", resume_key="F9")

    def stop(self) -> None:
        """Detiene el listener de teclado."""
        if self._listener:
            self._listener.stop()
            self._listener = None
            self._is_active = False

            if self.logger:
                self.logger.info("Keyboard listener detenido")

    def is_active(self) -> bool:
        """Verifica si el listener está activo."""
        return self._is_active

    def _handle_pause(self) -> None:
        """Maneja el evento de pausa (ESC)."""
        if self.logger:
            self.logger.info("Tecla ESC presionada - Solicitando pausa")

        if self.on_pause:
            try:
                self.on_pause()
            except Exception as e:
                if self.logger:
                    self.logger.error("Error en callback on_pause", error=str(e))

    def _handle_resume(self) -> None:
        """Maneja el evento de reanudación (F9)."""
        if self.logger:
            self.logger.info("Tecla F9 presionada - Solicitando reanudación")

        if self.on_resume:
            try:
                self.on_resume()
            except Exception as e:
                if self.logger:
                    self.logger.error("Error en callback on_resume", error=str(e))

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False  # No suprimir excepciones
