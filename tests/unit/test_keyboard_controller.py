"""Tests unitarios para KeyboardController.

Cobertura:
- Inicialización con callbacks
- Start/Stop del listener
- Manejo de teclas ESC y F9
- Context manager protocol
- Estado activo/inactivo
- Manejo de errores en callbacks
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pynput import keyboard

from src.application.services.keyboard_controller import KeyboardController


class TestKeyboardControllerInitialization:
    """Tests de inicialización."""

    def test_default_initialization(self):
        """Test inicialización sin callbacks."""
        controller = KeyboardController()

        assert controller.on_pause is None
        assert controller.on_resume is None
        assert controller._listener is None
        assert controller._is_active is False

    def test_initialization_with_callbacks(self):
        """Test inicialización con callbacks."""
        on_pause_mock = Mock()
        on_resume_mock = Mock()

        controller = KeyboardController(
            on_pause=on_pause_mock,
            on_resume=on_resume_mock
        )

        assert controller.on_pause is on_pause_mock
        assert controller.on_resume is on_resume_mock

    def test_initialization_with_logger(self):
        """Test inicialización con logger."""
        logger_mock = Mock()
        logger_mock.bind.return_value = logger_mock

        controller = KeyboardController(logger=logger_mock)

        assert controller.logger is not None
        logger_mock.bind.assert_called_once_with(component="KeyboardController")

    def test_initialization_without_logger(self):
        """Test inicialización sin logger."""
        controller = KeyboardController()

        assert controller.logger is None


class TestKeyboardControllerStart:
    """Tests de inicio del listener."""

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_start_creates_listener(self, mock_listener_class):
        """Test que start crea y arranca el listener."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener

        controller = KeyboardController()
        controller.start()

        # Verificar que se creó el listener
        mock_listener_class.assert_called_once()
        mock_listener.start.assert_called_once()

        # Verificar estado
        assert controller._is_active is True
        assert controller._listener is mock_listener

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_start_when_already_active_raises_error(self, mock_listener_class):
        """Test que start cuando ya está activo lanza error."""
        controller = KeyboardController()
        controller.start()

        with pytest.raises(RuntimeError, match="Keyboard listener ya está activo"):
            controller.start()

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_start_logs_when_logger_present(self, mock_listener_class):
        """Test que start logea cuando hay logger."""
        logger_mock = Mock()
        logger_mock.bind.return_value = logger_mock

        controller = KeyboardController(logger=logger_mock)
        controller.start()

        # Verificar que se loguó el inicio
        logger_mock.info.assert_called()


class TestKeyboardControllerStop:
    """Tests de detención del listener."""

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_stop_stops_listener(self, mock_listener_class):
        """Test que stop detiene el listener."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener

        controller = KeyboardController()
        controller.start()
        controller.stop()

        # Verificar que se detuvo el listener
        mock_listener.stop.assert_called_once()

        # Verificar estado
        assert controller._is_active is False
        assert controller._listener is None

    def test_stop_when_not_active_does_nothing(self):
        """Test que stop cuando no está activo no crashea."""
        controller = KeyboardController()
        controller.stop()  # No debe crashear

        assert controller._is_active is False

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_stop_logs_when_logger_present(self, mock_listener_class):
        """Test que stop logea cuando hay logger."""
        logger_mock = Mock()
        logger_mock.bind.return_value = logger_mock

        controller = KeyboardController(logger=logger_mock)
        controller.start()

        logger_mock.reset_mock()  # Clear previous logs
        controller.stop()

        # Verificar que se loguó la detención
        logger_mock.info.assert_called()


class TestKeyboardControllerIsActive:
    """Tests del método is_active."""

    def test_is_active_returns_false_initially(self):
        """Test que is_active retorna False inicialmente."""
        controller = KeyboardController()
        assert controller.is_active() is False

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_is_active_returns_true_when_started(self, mock_listener_class):
        """Test que is_active retorna True cuando está activo."""
        controller = KeyboardController()
        controller.start()

        assert controller.is_active() is True

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_is_active_returns_false_after_stop(self, mock_listener_class):
        """Test que is_active retorna False después de stop."""
        controller = KeyboardController()
        controller.start()
        controller.stop()

        assert controller.is_active() is False


class TestKeyboardControllerCallbacks:
    """Tests de callbacks de pausa y reanudación."""

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_esc_key_triggers_on_pause(self, mock_listener_class):
        """Test que presionar ESC dispara on_pause."""
        on_pause_mock = Mock()
        on_resume_mock = Mock()

        # Capturar el callback on_press
        captured_on_press = None

        def capture_on_press(on_press):
            nonlocal captured_on_press
            captured_on_press = on_press
            listener_mock = Mock()
            return listener_mock

        mock_listener_class.side_effect = capture_on_press

        controller = KeyboardController(
            on_pause=on_pause_mock,
            on_resume=on_resume_mock
        )
        controller.start()

        # Simular presionar ESC
        if captured_on_press:
            captured_on_press(keyboard.Key.esc)

            # Verificar que se llamó on_pause
            on_pause_mock.assert_called_once()
            on_resume_mock.assert_not_called()

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_f9_key_triggers_on_resume(self, mock_listener_class):
        """Test que presionar F9 dispara on_resume."""
        on_pause_mock = Mock()
        on_resume_mock = Mock()

        captured_on_press = None

        def capture_on_press(on_press):
            nonlocal captured_on_press
            captured_on_press = on_press
            listener_mock = Mock()
            return listener_mock

        mock_listener_class.side_effect = capture_on_press

        controller = KeyboardController(
            on_pause=on_pause_mock,
            on_resume=on_resume_mock
        )
        controller.start()

        # Simular presionar F9
        if captured_on_press:
            captured_on_press(keyboard.Key.f9)

            # Verificar que se llamó on_resume
            on_resume_mock.assert_called_once()
            on_pause_mock.assert_not_called()

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_callback_error_is_caught_and_logged(self, mock_listener_class):
        """Test que errores en callbacks son capturados y logueados."""
        def failing_callback():
            raise ValueError("Test error")

        logger_mock = Mock()
        logger_mock.bind.return_value = logger_mock

        captured_on_press = None

        def capture_on_press(on_press):
            nonlocal captured_on_press
            captured_on_press = on_press
            listener_mock = Mock()
            return listener_mock

        mock_listener_class.side_effect = capture_on_press

        controller = KeyboardController(
            on_pause=failing_callback,
            logger=logger_mock
        )
        controller.start()

        # Simular presionar ESC (dispara callback que falla)
        if captured_on_press:
            captured_on_press(keyboard.Key.esc)

            # Verificar que se loguó el error
            logger_mock.error.assert_called()

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_no_callback_does_nothing(self, mock_listener_class):
        """Test que sin callbacks no crashea."""
        captured_on_press = None

        def capture_on_press(on_press):
            nonlocal captured_on_press
            captured_on_press = on_press
            listener_mock = Mock()
            return listener_mock

        mock_listener_class.side_effect = capture_on_press

        controller = KeyboardController()  # Sin callbacks
        controller.start()

        # Simular presionar ESC (no debe crashear)
        if captured_on_press:
            captured_on_press(keyboard.Key.esc)
            # No crashea


class TestKeyboardControllerContextManager:
    """Tests del protocolo context manager."""

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_context_manager_starts_on_enter(self, mock_listener_class):
        """Test que __enter__ inicia el listener."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener

        controller = KeyboardController()

        with controller:
            assert controller.is_active() is True
            mock_listener.start.assert_called_once()

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_context_manager_stops_on_exit(self, mock_listener_class):
        """Test que __exit__ detiene el listener."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener

        controller = KeyboardController()

        with controller:
            pass  # Salir del context

        # Verificar que se detuvo
        assert controller.is_active() is False
        mock_listener.stop.assert_called_once()

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_context_manager_stops_even_on_exception(self, mock_listener_class):
        """Test que __exit__ detiene incluso si hay excepción."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener

        controller = KeyboardController()

        with pytest.raises(ValueError):
            with controller:
                raise ValueError("Test error")

        # Verificar que se detuvo a pesar del error
        assert controller.is_active() is False
        mock_listener.stop.assert_called_once()

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_context_manager_returns_self(self, mock_listener_class):
        """Test que __enter__ retorna self."""
        controller = KeyboardController()

        with controller as ctx:
            assert ctx is controller


class TestKeyboardControllerIntegration:
    """Tests de escenarios completos."""

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_typical_usage_flow(self, mock_listener_class):
        """Test flujo típico de uso."""
        pause_called = []
        resume_called = []

        def on_pause():
            pause_called.append(True)

        def on_resume():
            resume_called.append(True)

        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener

        controller = KeyboardController(
            on_pause=on_pause,
            on_resume=on_resume
        )

        # 1. Inicialmente inactivo
        assert not controller.is_active()

        # 2. Start
        controller.start()
        assert controller.is_active()

        # 3. Stop
        controller.stop()
        assert not controller.is_active()

    @patch('src.application.services.keyboard_controller.keyboard.Listener')
    def test_multiple_start_stop_cycles(self, mock_listener_class):
        """Test múltiples ciclos de start/stop."""
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener

        controller = KeyboardController()

        # Ciclo 1
        controller.start()
        assert controller.is_active()
        controller.stop()
        assert not controller.is_active()

        # Reset mock para siguiente ciclo
        mock_listener_class.reset_mock()
        mock_listener = Mock()
        mock_listener_class.return_value = mock_listener

        # Ciclo 2
        controller.start()
        assert controller.is_active()
        controller.stop()
        assert not controller.is_active()


# Fixtures
@pytest.fixture
def controller():
    """Fixture de controller básico."""
    return KeyboardController()


@pytest.fixture
def controller_with_callbacks():
    """Fixture de controller con callbacks mockeados."""
    return KeyboardController(
        on_pause=Mock(),
        on_resume=Mock()
    )


@pytest.fixture
def controller_with_logger():
    """Fixture de controller con logger mockeado."""
    logger_mock = Mock()
    logger_mock.bind.return_value = logger_mock
    return KeyboardController(logger=logger_mock)
