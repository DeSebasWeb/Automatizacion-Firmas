"""Value Object para números de cédula."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CedulaNumber:
    """
    Value Object que representa un número de cédula válido.

    Encapsula toda la lógica de validación de cédulas en un objeto
    inmutable con comportamiento rico del dominio.

    **Características:**
    - Inmutable (frozen=True)
    - Auto-validación en construcción
    - Comparación por valor
    - Formateo inteligente

    **Reglas de negocio:**
    - Solo dígitos numéricos
    - Longitud entre 6 y 15 dígitos
    - No puede comenzar con 0 (configurable)
    - No puede estar vacío

    Example:
        >>> # Creación válida
        >>> cedula = CedulaNumber("12345678")
        >>> print(cedula)
        12345678
        >>> print(cedula.formatted())
        12.345.678
        >>>
        >>> # Validación automática
        >>> cedula = CedulaNumber("ABC")  # Raises ValueError
        >>> cedula = CedulaNumber("123")  # Raises ValueError (muy corto)
        >>>
        >>> # Comparación por valor
        >>> c1 = CedulaNumber("12345678")
        >>> c2 = CedulaNumber("12345678")
        >>> assert c1 == c2  # True
    """

    value: str
    """Número de cédula como string (inmutable)"""

    def __post_init__(self):
        """
        Validación automática al construir.

        Raises:
            ValueError: Si la cédula no cumple con las reglas de negocio
        """
        if not self.value:
            raise ValueError("Cédula no puede estar vacía")

        if not self.value.isdigit():
            raise ValueError(
                f"Cédula debe contener solo dígitos numéricos: '{self.value}'"
            )

        length = len(self.value)
        if not (3 <= length <= 11):
            raise ValueError(
                f"Longitud de cédula inválida: {length} dígitos. "
                f"Debe estar entre 3 y 11 dígitos."
            )

    @classmethod
    def from_string(cls, value: str, allow_leading_zero: bool = True) -> 'CedulaNumber':
        """
        Crea CedulaNumber desde string con validaciones adicionales.

        Args:
            value: String con el número de cédula
            allow_leading_zero: Si False, rechaza cédulas que empiezan con 0

        Returns:
            CedulaNumber validado

        Raises:
            ValueError: Si la cédula es inválida

        Example:
            >>> cedula = CedulaNumber.from_string("12345678")
            >>> cedula_col = CedulaNumber.from_string("01234567", allow_leading_zero=False)  # Raises
        """
        # Limpiar espacios
        value = value.strip()

        # Validar leading zero si es necesario
        if not allow_leading_zero and value.startswith('0'):
            raise ValueError(
                f"Cédula no puede comenzar con 0: '{value}'"
            )

        return cls(value)

    @classmethod
    def try_create(cls, value: str, allow_leading_zero: bool = True) -> Optional['CedulaNumber']:
        """
        Intenta crear CedulaNumber, retorna None si es inválido.

        Útil para parsing sin excepciones.

        Args:
            value: String con el número de cédula
            allow_leading_zero: Si False, rechaza cédulas que empiezan con 0

        Returns:
            CedulaNumber si es válido, None si es inválido

        Example:
            >>> cedula = CedulaNumber.try_create("12345678")
            >>> if cedula:
            ...     process(cedula)
            >>> invalid = CedulaNumber.try_create("ABC")
            >>> assert invalid is None
        """
        try:
            return cls.from_string(value, allow_leading_zero)
        except ValueError:
            return None

    def formatted(self, separator: str = '.') -> str:
        """
        Formatea la cédula con separadores de miles.

        Args:
            separator: Separador a usar (default: '.')

        Returns:
            Cédula formateada

        Example:
            >>> cedula = CedulaNumber("12345678")
            >>> cedula.formatted()
            '12.345.678'
            >>> cedula.formatted(',')
            '12,345,678'
        """
        # Convertir a entero para formatear
        num = int(self.value)

        # Formatear con separadores
        formatted = f"{num:,}".replace(',', separator)

        return formatted

    def is_colombian(self) -> bool:
        """
        Verifica si cumple con formato de cédula colombiana.

        Reglas:
        - Entre 6 y 10 dígitos
        - No comienza con 0

        Returns:
            True si cumple formato colombiano
        """
        return (
            6 <= len(self.value) <= 10 and
            not self.value.startswith('0')
        )

    def length(self) -> int:
        """Retorna la longitud de la cédula."""
        return len(self.value)

    def __str__(self) -> str:
        """String representation (sin formato)."""
        return self.value

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"CedulaNumber('{self.value}')"

    def __int__(self) -> int:
        """Conversión a entero."""
        return int(self.value)

    def __hash__(self) -> int:
        """Hash para usar en sets/dicts."""
        return hash(self.value)


# ========== FACTORY PARA CASOS COMUNES ==========

class CedulaNumbers:
    """Factory con métodos de conveniencia para crear CedulaNumber."""

    @staticmethod
    def colombian(value: str) -> CedulaNumber:
        """
        Crea cédula con validaciones específicas para Colombia.

        Reglas:
        - 6-10 dígitos
        - No comienza con 0

        Args:
            value: Número de cédula

        Returns:
            CedulaNumber validado

        Raises:
            ValueError: Si no cumple reglas colombianas
        """
        cedula = CedulaNumber.from_string(value, allow_leading_zero=False)

        if not cedula.is_colombian():
            raise ValueError(
                f"Cédula no cumple formato colombiano: '{value}'. "
                f"Debe tener 6-10 dígitos y no comenzar con 0."
            )

        return cedula

    @staticmethod
    def from_raw_ocr(value: str) -> Optional[CedulaNumber]:
        """
        Crea CedulaNumber desde output crudo de OCR.

        Aplica limpieza y correcciones antes de validar:
        - Elimina espacios
        - Elimina caracteres no numéricos
        - Intenta crear cédula

        Args:
            value: String crudo del OCR

        Returns:
            CedulaNumber si se pudo limpiar y validar, None si no

        Example:
            >>> cedula = CedulaNumbers.from_raw_ocr("  1234 5678  ")
            >>> cedula = CedulaNumbers.from_raw_ocr("1234-5678")
            >>> cedula = CedulaNumbers.from_raw_ocr("ABC123")  # None
        """
        if not value:
            return None

        # Limpiar: solo dígitos
        cleaned = ''.join(c for c in value if c.isdigit())

        if not cleaned:
            return None

        # Intentar crear
        return CedulaNumber.try_create(cleaned)
