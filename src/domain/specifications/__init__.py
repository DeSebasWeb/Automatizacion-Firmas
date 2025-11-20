"""Patrón Specification para validaciones de dominio reutilizables."""
from .specification import Specification, AndSpecification, OrSpecification, NotSpecification
from .cedula_specifications import (
    CedulaFormatSpecification,
    CedulaLengthSpecification,
    ConfidenceSpecification,
    CedulaNotStartsWithZeroSpecification,
    ValidCedulaSpecification,
    CedulaSpecifications
)

__all__ = [
    # Clase base
    'Specification',
    'AndSpecification',
    'OrSpecification',
    'NotSpecification',

    # Especificaciones concretas
    'CedulaFormatSpecification',
    'CedulaLengthSpecification',
    'ConfidenceSpecification',
    'CedulaNotStartsWithZeroSpecification',

    # Especificaciones compuestas
    'ValidCedulaSpecification',

    # Factory
    'CedulaSpecifications',
]
