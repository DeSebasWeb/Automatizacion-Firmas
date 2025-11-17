"""Implementación de gestor de configuración usando YAML."""
import yaml
from pathlib import Path
from typing import Any, Optional

from ...domain.ports import ConfigPort


class YAMLConfig(ConfigPort):
    """
    Gestor de configuración usando archivos YAML.

    Attributes:
        config_file: Ruta al archivo de configuración
        config: Diccionario con la configuración
    """

    def __init__(self, config_file: str = "config/settings.yaml"):
        """
        Inicializa el gestor de configuración.

        Args:
            config_file: Ruta al archivo de configuración
        """
        self.config_file = Path(config_file)
        self.config: dict = {}
        self._ensure_config_dir()
        self._load_defaults()
        self.load()

    def _ensure_config_dir(self) -> None:
        """Asegura que el directorio de configuración exista."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_defaults(self) -> None:
        """Carga valores por defecto de configuración."""
        self.config = {
            'capture_area': None,
            'search_field': {
                'x': None,
                'y': None
            },
            'automation': {
                'typing_interval': 0.05,
                'pre_enter_delay': 0.3,
                'post_enter_delay': 0.5
            },
            'ocr': {
                'language': 'spa',
                'min_confidence': 50.0,
                'psm': 6  # Assume uniform block of text
            },
            'hotkeys': {
                'next_record': 'ctrl+q',
                'pause': 'f3',
                'capture_area': 'f4'
            },
            'ui': {
                'theme': 'light',
                'window_width': 900,
                'window_height': 700
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de punto.

        Args:
            key: Clave de configuración (ej: 'automation.typing_interval')
            default: Valor por defecto si no existe

        Returns:
            Valor de configuración
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración usando notación de punto.

        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        keys = key.split('.')
        config = self.config

        # Navegar hasta el penúltimo nivel
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Establecer el valor
        config[keys[-1]] = value

    def save(self) -> None:
        """Guarda la configuración en el archivo YAML."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise RuntimeError(f"Error al guardar configuración: {e}")

    def load(self) -> None:
        """Carga la configuración desde el archivo YAML."""
        if not self.config_file.exists():
            # Si no existe, crear con valores por defecto
            self.save()
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config:
                    # Merge con defaults
                    self._merge_configs(self.config, loaded_config)
        except Exception as e:
            raise RuntimeError(f"Error al cargar configuración: {e}")

    def _merge_configs(self, default: dict, loaded: dict) -> None:
        """
        Mezcla la configuración cargada con los valores por defecto.

        Args:
            default: Diccionario de configuración por defecto
            loaded: Diccionario de configuración cargada
        """
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value

    def get_all(self) -> dict:
        """
        Obtiene toda la configuración.

        Returns:
            Diccionario con toda la configuración
        """
        return self.config.copy()
