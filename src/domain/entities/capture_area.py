"""Entidad que representa el área de captura de pantalla."""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class CaptureArea:
    """
    Entidad que representa el área de captura en la pantalla.

    Attributes:
        x: Coordenada X de la esquina superior izquierda
        y: Coordenada Y de la esquina superior izquierda
        width: Ancho del área de captura
        height: Alto del área de captura
    """
    x: int
    y: int
    width: int
    height: int

    @property
    def coordinates(self) -> Tuple[int, int, int, int]:
        """
        Retorna las coordenadas como tupla.

        Returns:
            Tupla (x, y, width, height)
        """
        return (self.x, self.y, self.width, self.height)

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """
        Retorna los límites del área como coordenadas absolutas.

        Returns:
            Tupla (x1, y1, x2, y2)
        """
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def is_valid(self) -> bool:
        """
        Valida si el área de captura tiene dimensiones válidas.

        Returns:
            True si el área es válida, False en caso contrario
        """
        return (
            self.width > 0 and
            self.height > 0 and
            self.x >= 0 and
            self.y >= 0
        )

    def to_dict(self) -> dict:
        """
        Convierte el área a diccionario para serialización.

        Returns:
            Diccionario con las coordenadas
        """
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CaptureArea':
        """
        Crea una instancia desde un diccionario.

        Args:
            data: Diccionario con las coordenadas

        Returns:
            Instancia de CaptureArea
        """
        return cls(
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height']
        )
