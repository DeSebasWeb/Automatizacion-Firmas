"""Entidad de dominio para datos de un renglón del formulario manuscrito."""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RowData:
    """
    Representa los datos extraídos de un renglón del formulario manuscrito.

    Extraído por Google Cloud Vision API del formulario físico/manuscrito.
    """

    row_index: int
    """Índice del renglón (0-14 para ~15 renglones)"""

    nombres_manuscritos: str
    """Nombres completos manuscritos (columna izquierda)"""

    cedula: str
    """Número de cédula manuscrito (columna centro)"""

    is_empty: bool
    """True si el renglón está completamente vacío"""

    confidence: Dict[str, float]
    """Confianza del OCR para cada campo: {'nombres': 0.89, 'cedula': 0.95}"""

    raw_text: Optional[str] = None
    """Texto crudo detectado por Google Vision (para debugging)"""

    def __post_init__(self):
        """Normaliza los datos después de inicialización."""
        # Limpiar espacios
        self.nombres_manuscritos = self.nombres_manuscritos.strip()
        self.cedula = self.cedula.strip()

        # Marcar como vacío si no tiene datos
        if not self.nombres_manuscritos and not self.cedula:
            self.is_empty = True

    @property
    def has_cedula(self) -> bool:
        """Verifica si el renglón tiene cédula."""
        return bool(self.cedula and len(self.cedula) >= 6)

    @property
    def has_nombres(self) -> bool:
        """Verifica si el renglón tiene nombres."""
        return bool(self.nombres_manuscritos and len(self.nombres_manuscritos) >= 3)

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización."""
        return {
            'row_index': self.row_index,
            'nombres_manuscritos': self.nombres_manuscritos,
            'cedula': self.cedula,
            'is_empty': self.is_empty,
            'confidence': self.confidence,
            'raw_text': self.raw_text
        }

    def __str__(self) -> str:
        """Representación en string."""
        if self.is_empty:
            return f"Renglón {self.row_index}: [VACÍO]"
        return f"Renglón {self.row_index}: {self.nombres_manuscritos} - {self.cedula}"
