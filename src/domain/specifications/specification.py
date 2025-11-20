"""Patrón Specification - Clase base para especificaciones de dominio."""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')


class Specification(ABC, Generic[T]):
    """
    Patrón Specification para encapsular reglas de negocio reutilizables.

    El patrón Specification permite:
    - Separar lógica de validación de las entidades (SRP)
    - Reutilizar y combinar reglas de negocio
    - Testear reglas independientemente
    - Modificar reglas sin tocar entidades (OCP)

    Example:
        >>> # Crear especificaciones
        >>> valid_format = CedulaFormatSpecification()
        >>> valid_length = CedulaLengthSpecification(6, 15)
        >>> high_confidence = ConfidenceSpecification(0.85)
        >>>
        >>> # Combinar especificaciones
        >>> valid_cedula = valid_format.and_(valid_length).and_(high_confidence)
        >>>
        >>> # Evaluar
        >>> if valid_cedula.is_satisfied_by(record):
        ...     process(record)
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Verifica si el candidato satisface la especificación.

        Args:
            candidate: Objeto a verificar

        Returns:
            True si satisface la especificación, False en caso contrario
        """
        pass

    def and_(self, other: 'Specification[T]') -> 'Specification[T]':
        """
        Combina esta especificación con otra usando operador lógico AND.

        Args:
            other: Otra especificación del mismo tipo

        Returns:
            Nueva especificación que satisface ambas condiciones
        """
        return AndSpecification(self, other)

    def or_(self, other: 'Specification[T]') -> 'Specification[T]':
        """
        Combina esta especificación con otra usando operador lógico OR.

        Args:
            other: Otra especificación del mismo tipo

        Returns:
            Nueva especificación que satisface al menos una condición
        """
        return OrSpecification(self, other)

    def not_(self) -> 'Specification[T]':
        """
        Invierte esta especificación usando operador lógico NOT.

        Returns:
            Nueva especificación que invierte la condición
        """
        return NotSpecification(self)

    def __and__(self, other: 'Specification[T]') -> 'Specification[T]':
        """Sobrecarga del operador & para and_()"""
        return self.and_(other)

    def __or__(self, other: 'Specification[T]') -> 'Specification[T]':
        """Sobrecarga del operador | para or_()"""
        return self.or_(other)

    def __invert__(self) -> 'Specification[T]':
        """Sobrecarga del operador ~ para not_()"""
        return self.not_()


class AndSpecification(Specification[T]):
    """Especificación compuesta que evalúa AND lógico."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return (
            self.left.is_satisfied_by(candidate) and
            self.right.is_satisfied_by(candidate)
        )


class OrSpecification(Specification[T]):
    """Especificación compuesta que evalúa OR lógico."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return (
            self.left.is_satisfied_by(candidate) or
            self.right.is_satisfied_by(candidate)
        )


class NotSpecification(Specification[T]):
    """Especificación que invierte otra especificación."""

    def __init__(self, spec: Specification[T]):
        self.spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self.spec.is_satisfied_by(candidate)
