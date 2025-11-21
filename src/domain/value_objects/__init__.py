"""Value Objects del dominio para conceptos inmutables con comportamiento rico."""
from .cedula_number import CedulaNumber, CedulaNumbers
from .confidence_score import ConfidenceScore, ConfidenceThresholds
from .coordinate import Coordinate, Rectangle

__all__ = [
    # Cédulas
    'CedulaNumber',
    'CedulaNumbers',

    # Confianza
    'ConfidenceScore',
    'ConfidenceThresholds',

    # Coordenadas
    'Coordinate',
    'Rectangle',
]
