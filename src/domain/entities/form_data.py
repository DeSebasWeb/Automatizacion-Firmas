"""Entidad de dominio para datos del formulario web digital."""
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime


@dataclass
class FormData:
    """
    Representa los datos extraídos del formulario web digital.

    Extraído por Tesseract OCR de los campos del formulario web después de buscar la cédula.
    """

    primer_nombre: str
    """Primer nombre leído del formulario web"""

    segundo_nombre: str
    """Segundo nombre leído del formulario web (puede estar vacío)"""

    primer_apellido: str
    """Primer apellido leído del formulario web"""

    segundo_apellido: str
    """Segundo apellido leído del formulario web"""

    is_empty: bool
    """True si TODOS los campos están vacíos (persona no existe en BD)"""

    extraction_time: Optional[datetime] = None
    """Timestamp de cuándo se extrajeron los datos"""

    cedula_consultada: Optional[str] = None
    """Cédula que se consultó para obtener estos datos"""

    confidence: Optional[float] = None
    """Confianza general del OCR (0-100)"""

    def __post_init__(self):
        """Normaliza los datos después de inicialización."""
        # Limpiar espacios y convertir a mayúsculas
        self.primer_nombre = self.primer_nombre.strip().upper()
        self.segundo_nombre = self.segundo_nombre.strip().upper()
        self.primer_apellido = self.primer_apellido.strip().upper()
        self.segundo_apellido = self.segundo_apellido.strip().upper()

        # Marcar como vacío si TODOS los campos principales están vacíos
        if not self.primer_nombre and not self.primer_apellido:
            self.is_empty = True

        # Timestamp si no se proporcionó
        if self.extraction_time is None:
            self.extraction_time = datetime.now()

    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo concatenado."""
        partes = [
            self.primer_nombre,
            self.segundo_nombre,
            self.primer_apellido,
            self.segundo_apellido
        ]
        return ' '.join([p for p in partes if p]).strip()

    @property
    def apellidos(self) -> str:
        """Retorna solo los apellidos."""
        partes = [self.primer_apellido, self.segundo_apellido]
        return ' '.join([p for p in partes if p]).strip()

    @property
    def nombres(self) -> str:
        """Retorna solo los nombres."""
        partes = [self.primer_nombre, self.segundo_nombre]
        return ' '.join([p for p in partes if p]).strip()

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización."""
        return {
            'primer_nombre': self.primer_nombre,
            'segundo_nombre': self.segundo_nombre,
            'primer_apellido': self.primer_apellido,
            'segundo_apellido': self.segundo_apellido,
            'is_empty': self.is_empty,
            'extraction_time': self.extraction_time.isoformat() if self.extraction_time else None,
            'cedula_consultada': self.cedula_consultada,
            'confidence': self.confidence
        }

    def __str__(self) -> str:
        """Representación en string."""
        if self.is_empty:
            return f"[PERSONA NO ENCONTRADA - Cédula: {self.cedula_consultada}]"
        return f"{self.nombre_completo}"
