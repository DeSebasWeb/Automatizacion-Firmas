"""Value Objects del dominio para conceptos inmutables con comportamiento rico."""
from .cedula_number import CedulaNumber, CedulaNumbers
from .confidence_score import ConfidenceScore, ConfidenceThresholds
from .coordinate import Coordinate, Rectangle
from .email import Email
from .hashed_password import HashedPassword
from .user_id import UserId

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

    # Autenticación
    'Email',
    'HashedPassword',
    'UserId',
]
