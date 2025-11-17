"""Implementación de automatización usando PyAutoGUI y pynput."""
import pyautogui
import time
from typing import Tuple, Dict, Callable
from pynput import keyboard

from ...domain.ports import AutomationPort


class PyAutoGUIAutomation(AutomationPort):
    """
    Implementación de automatización usando PyAutoGUI y pynput.

    Attributes:
        hotkey_listeners: Diccionario de listeners de hotkeys
    """

    def __init__(self):
        """Inicializa el servicio de automatización."""
        # Configurar PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

        # Mapeo de teclas especiales
        self.key_mapping = {
            'enter': 'enter',
            'tab': 'tab',
            'space': 'space',
            'backspace': 'backspace',
            'delete': 'delete',
            'escape': 'esc',
            'ctrl+a': ['ctrl', 'a'],
            'ctrl+c': ['ctrl', 'c'],
            'ctrl+v': ['ctrl', 'v'],
            'alt+tab': ['alt', 'tab'],
        }

        self.hotkey_listeners: Dict[str, keyboard.GlobalHotKeys] = {}

    def type_text(self, text: str, interval: float = 0.05) -> None:
        """
        Escribe texto simulando pulsaciones de teclado.

        Args:
            text: Texto a escribir
            interval: Intervalo entre teclas en segundos
        """
        pyautogui.write(text, interval=interval)

    def press_key(self, key: str) -> None:
        """
        Presiona una tecla o combinación de teclas.

        Args:
            key: Nombre de la tecla a presionar
        """
        key_lower = key.lower()

        if key_lower in self.key_mapping:
            mapped_key = self.key_mapping[key_lower]

            if isinstance(mapped_key, list):
                # Es una combinación de teclas
                pyautogui.hotkey(*mapped_key)
            else:
                # Es una tecla simple
                pyautogui.press(mapped_key)
        else:
            # Tecla no mapeada, intentar presionarla directamente
            pyautogui.press(key_lower)

    def click(self, x: int, y: int) -> None:
        """
        Hace click en coordenadas específicas.

        Args:
            x: Coordenada X
            y: Coordenada Y
        """
        pyautogui.click(x, y)

    def move_to(self, x: int, y: int, duration: float = 0.5) -> None:
        """
        Mueve el cursor a coordenadas específicas.

        Args:
            x: Coordenada X
            y: Coordenada Y
            duration: Duración del movimiento en segundos
        """
        pyautogui.moveTo(x, y, duration=duration)

    def get_mouse_position(self) -> Tuple[int, int]:
        """
        Obtiene la posición actual del mouse.

        Returns:
            Tupla (x, y) con la posición
        """
        position = pyautogui.position()
        return (position.x, position.y)

    def register_hotkey(self, key: str, callback: Callable) -> None:
        """
        Registra un atajo de teclado global usando pynput.

        Args:
            key: Combinación de teclas (ej: '<f2>', '<ctrl>+<alt>+h')
            callback: Función a ejecutar al presionar el atajo
        """
        # Normalizar la tecla
        normalized_key = self._normalize_hotkey(key)

        # Si ya existe un listener para esta tecla, detenerlo
        if normalized_key in self.hotkey_listeners:
            self.hotkey_listeners[normalized_key].stop()

        # Crear nuevo listener
        hotkey_map = {normalized_key: callback}
        listener = keyboard.GlobalHotKeys(hotkey_map)

        # Guardar referencia y comenzar
        self.hotkey_listeners[normalized_key] = listener
        listener.start()

    def _normalize_hotkey(self, key: str) -> str:
        """
        Normaliza la representación de un hotkey para pynput.

        Args:
            key: Tecla en formato simple (ej: 'f2', 'ctrl+alt+h')

        Returns:
            Tecla en formato pynput (ej: '<f2>', '<ctrl>+<alt>+h')
        """
        # Si ya tiene el formato correcto, retornar
        if key.startswith('<'):
            return key

        # Separar por '+' si es combinación
        parts = key.lower().split('+')

        # Envolver cada parte en <>
        normalized_parts = [f'<{part.strip()}>' for part in parts]

        # Unir con +
        return '+'.join(normalized_parts)

    def unregister_all_hotkeys(self) -> None:
        """Desregistra todos los atajos de teclado."""
        for listener in self.hotkey_listeners.values():
            listener.stop()
        self.hotkey_listeners.clear()
