"""Especificaciones de dominio para validación de cédulas."""
from typing import TYPE_CHECKING

from .specification import Specification

if TYPE_CHECKING:
    from ..entities import CedulaRecord


class CedulaFormatSpecification(Specification['CedulaRecord']):
    """
    Verifica que la cédula tenga formato válido (solo dígitos).

    Esta especificación valida que el string de cédula contenga
    únicamente caracteres numéricos.

    Note:
        Con Value Objects, CedulaNumber ya garantiza formato válido
        en su construcción, por lo que esta especificación siempre
        retorna True si el CedulaRecord fue construido correctamente.
    """

    def is_satisfied_by(self, record: 'CedulaRecord') -> bool:
        """
        Verifica si la cédula contiene solo dígitos.

        Args:
            record: Registro de cédula a validar

        Returns:
            True si la cédula es numérica, False en caso contrario
        """
        # CedulaNumber ya valida formato en construcción
        # Pero mantenemos la verificación explícita por consistencia
        return record.cedula.value.isdigit()

    def __repr__(self) -> str:
        return "CedulaFormatSpecification(only_digits=True)"


class CedulaLengthSpecification(Specification['CedulaRecord']):
    """
    Verifica que la longitud de la cédula esté dentro del rango válido.

    En Colombia, las cédulas típicamente tienen entre 6 y 10 dígitos,
    pero este rango es configurable para otros países.
    """

    def __init__(self, min_length: int = 3, max_length: int = 11):
        """
        Inicializa la especificación de longitud.

        Args:
            min_length: Longitud mínima válida (default: 3)
            max_length: Longitud máxima válida (default: 11)

        Raises:
            ValueError: Si min_length > max_length
        """
        if min_length > max_length:
            raise ValueError(
                f"min_length ({min_length}) no puede ser mayor que "
                f"max_length ({max_length})"
            )

        self.min_length = min_length
        self.max_length = max_length

    def is_satisfied_by(self, record: 'CedulaRecord') -> bool:
        """
        Verifica si la longitud de la cédula está en el rango válido.

        Args:
            record: Registro de cédula a validar

        Returns:
            True si la longitud está en el rango, False en caso contrario
        """
        cedula_length = len(record.cedula.value)
        return self.min_length <= cedula_length <= self.max_length

    def __repr__(self) -> str:
        return (
            f"CedulaLengthSpecification("
            f"min={self.min_length}, max={self.max_length})"
        )


class ConfidenceSpecification(Specification['CedulaRecord']):
    """
    Verifica que el nivel de confianza del OCR sea aceptable.

    La confianza se especifica como porcentaje (0-100) pero se compara
    contra el Value Object ConfidenceScore (que almacena 0.0-1.0 internamente).
    """

    def __init__(self, min_confidence: float = 50.0):
        """
        Inicializa la especificación de confianza.

        Args:
            min_confidence: Confianza mínima requerida (0-100, default: 50.0)

        Raises:
            ValueError: Si min_confidence no está entre 0 y 100
        """
        if not (0.0 <= min_confidence <= 100.0):
            raise ValueError(
                f"min_confidence debe estar entre 0 y 100, "
                f"recibido: {min_confidence}"
            )

        self.min_confidence = min_confidence

    def is_satisfied_by(self, record: 'CedulaRecord') -> bool:
        """
        Verifica si la confianza del registro es aceptable.

        Args:
            record: Registro de cédula a validar

        Returns:
            True si la confianza es >= min_confidence, False en caso contrario
        """
        # Comparar usando el formato de porcentaje (0-100)
        # ConfidenceScore.as_percentage() convierte 0.0-1.0 → 0-100
        return record.confidence.as_percentage() >= self.min_confidence

    def __repr__(self) -> str:
        return f"ConfidenceSpecification(min={self.min_confidence}%)"


class CedulaNotStartsWithZeroSpecification(Specification['CedulaRecord']):
    """
    Verifica que la cédula no comience con cero.

    En muchos países, las cédulas válidas no comienzan con 0.
    Esta regla puede variar según el contexto.
    """

    def is_satisfied_by(self, record: 'CedulaRecord') -> bool:
        """
        Verifica si la cédula no comienza con cero.

        Args:
            record: Registro de cédula a validar

        Returns:
            True si no comienza con 0, False en caso contrario
        """
        if not record.cedula.value:
            return False
        return record.cedula.value[0] != '0'

    def __repr__(self) -> str:
        return "CedulaNotStartsWithZeroSpecification()"


# ========== ESPECIFICACIONES COMPUESTAS PRE-CONFIGURADAS ==========

class ValidCedulaSpecification(Specification['CedulaRecord']):
    """
    Especificación compuesta que valida todos los criterios estándar de cédula.

    Esta es una especificación de conveniencia que combina todas las
    validaciones comunes en una sola. Es equivalente a:

        CedulaFormatSpecification()
            .and_(CedulaLengthSpecification(6, 15))
            .and_(ConfidenceSpecification(50.0))

    Parámetros configurables via constructor.
    """

    def __init__(
        self,
        min_length: int = 3,
        max_length: int = 11,
        min_confidence: float = 50.0,
        require_no_leading_zero: bool = False
    ):
        """
        Inicializa la especificación compuesta.

        Args:
            min_length: Longitud mínima de cédula
            max_length: Longitud máxima de cédula
            min_confidence: Confianza mínima del OCR
            require_no_leading_zero: Si True, rechaza cédulas que empiezan con 0
        """
        # Construir especificación compuesta
        self._spec = (
            CedulaFormatSpecification()
            .and_(CedulaLengthSpecification(min_length, max_length))
            .and_(ConfidenceSpecification(min_confidence))
        )

        if require_no_leading_zero:
            self._spec = self._spec.and_(CedulaNotStartsWithZeroSpecification())

        # Guardar parámetros para __repr__
        self.min_length = min_length
        self.max_length = max_length
        self.min_confidence = min_confidence
        self.require_no_leading_zero = require_no_leading_zero

    def is_satisfied_by(self, record: 'CedulaRecord') -> bool:
        """Delega a la especificación compuesta interna."""
        return self._spec.is_satisfied_by(record)

    def __repr__(self) -> str:
        return (
            f"ValidCedulaSpecification("
            f"length={self.min_length}-{self.max_length}, "
            f"confidence>={self.min_confidence}, "
            f"no_leading_zero={self.require_no_leading_zero})"
        )


# ========== FACTORY PARA ESPECIFICACIONES COMUNES ==========

class CedulaSpecifications:
    """
    Factory con especificaciones pre-configuradas comunes.

    Uso:
        >>> from domain.specifications import CedulaSpecifications
        >>> valid = CedulaSpecifications.valid_for_processing()
        >>> if valid.is_satisfied_by(record):
        ...     process(record)
    """

    @staticmethod
    def valid_for_processing(min_confidence: float = 50.0) -> Specification['CedulaRecord']:
        """
        Especificación estándar para cédulas válidas para procesamiento.

        Args:
            min_confidence: Confianza mínima del OCR

        Returns:
            Especificación compuesta con todas las validaciones estándar
        """
        return ValidCedulaSpecification(
            min_length=3,
            max_length=11,
            min_confidence=min_confidence,
            require_no_leading_zero=False
        )

    @staticmethod
    def valid_colombian_cedula(min_confidence: float = 50.0) -> Specification['CedulaRecord']:
        """
        Especificación para cédulas colombianas.

        Args:
            min_confidence: Confianza mínima del OCR

        Returns:
            Especificación con reglas específicas para Colombia
        """
        return ValidCedulaSpecification(
            min_length=3,
            max_length=11,  # Algunas personas escriben 11 dígitos
            min_confidence=min_confidence,
            require_no_leading_zero=True
        )

    @staticmethod
    def high_confidence_only(min_confidence: float = 85.0) -> Specification['CedulaRecord']:
        """
        Especificación para extracciones de alta confianza.

        Args:
            min_confidence: Confianza mínima (default: 85.0)

        Returns:
            Especificación con umbral de confianza alto
        """
        return ValidCedulaSpecification(
            min_length=3,
            max_length=11,
            min_confidence=min_confidence,
            require_no_leading_zero=False
        )
