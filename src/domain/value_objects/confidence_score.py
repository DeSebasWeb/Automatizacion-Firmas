"""Value Object para puntajes de confianza del OCR."""
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class ConfidenceScore:
    """
    Value Object que representa un puntaje de confianza normalizado.

    Encapsula la lógica de manejo de puntajes de confianza del OCR,
    normalizando siempre a rango 0.0-1.0 (0% - 100%).

    **Características:**
    - Inmutable (frozen=True)
    - Normalizado a 0.0-1.0
    - Auto-validación en construcción
    - Comparación por valor
    - Métodos de conveniencia

    **Reglas de negocio:**
    - Valor entre 0.0 y 1.0
    - 0.0 = 0% confianza (muy baja)
    - 1.0 = 100% confianza (muy alta)
    - Comparaciones de umbrales integradas

    Example:
        >>> # Creación desde valor normalizado (0.0-1.0)
        >>> conf = ConfidenceScore(0.85)
        >>> print(conf.as_percentage())
        85.0
        >>>
        >>> # Creación desde porcentaje (0-100)
        >>> conf = ConfidenceScore.from_percentage(85.0)
        >>> print(conf.value)
        0.85
        >>>
        >>> # Validaciones integradas
        >>> conf.is_high()  # >= 85%
        True
        >>> conf.is_acceptable()  # >= 50%
        True
        >>>
        >>> # Comparaciones
        >>> conf1 = ConfidenceScore(0.85)
        >>> conf2 = ConfidenceScore(0.90)
        >>> assert conf2 > conf1
    """

    value: float
    """Puntaje de confianza normalizado (0.0-1.0)"""

    def __post_init__(self):
        """
        Validación automática al construir.

        Raises:
            ValueError: Si el valor no está en rango 0.0-1.0
        """
        if not isinstance(self.value, (int, float)):
            raise TypeError(
                f"Confidence debe ser numérico, recibido: {type(self.value).__name__}"
            )

        if not (0.0 <= self.value <= 1.0):
            raise ValueError(
                f"Confidence debe estar entre 0.0 y 1.0, recibido: {self.value}"
            )

    @classmethod
    def from_percentage(cls, percentage: float) -> 'ConfidenceScore':
        """
        Crea ConfidenceScore desde porcentaje (0-100).

        Args:
            percentage: Porcentaje de confianza (0.0-100.0)

        Returns:
            ConfidenceScore normalizado

        Raises:
            ValueError: Si el porcentaje no está en rango 0-100

        Example:
            >>> conf = ConfidenceScore.from_percentage(85.0)
            >>> print(conf.value)
            0.85
            >>> conf = ConfidenceScore.from_percentage(120.0)  # Raises ValueError
        """
        if not (0.0 <= percentage <= 100.0):
            raise ValueError(
                f"Percentage debe estar entre 0 y 100, recibido: {percentage}"
            )

        return cls(percentage / 100.0)

    @classmethod
    def zero(cls) -> 'ConfidenceScore':
        """Retorna confianza de 0% (mínima)."""
        return cls(0.0)

    @classmethod
    def full(cls) -> 'ConfidenceScore':
        """Retorna confianza de 100% (máxima)."""
        return cls(1.0)

    def as_percentage(self) -> float:
        """
        Convierte a porcentaje (0-100).

        Returns:
            Porcentaje de confianza

        Example:
            >>> conf = ConfidenceScore(0.85)
            >>> conf.as_percentage()
            85.0
        """
        return self.value * 100.0

    def is_high(self, threshold: float = 0.85) -> bool:
        """
        Verifica si la confianza es alta.

        Args:
            threshold: Umbral de alta confianza (default: 0.85 = 85%)

        Returns:
            True si la confianza >= threshold

        Example:
            >>> conf = ConfidenceScore(0.90)
            >>> conf.is_high()  # >= 85%
            True
            >>> conf.is_high(threshold=0.95)  # >= 95%
            False
        """
        return self.value >= threshold

    def is_acceptable(self, threshold: float = 0.50) -> bool:
        """
        Verifica si la confianza es aceptable.

        Args:
            threshold: Umbral de confianza aceptable (default: 0.50 = 50%)

        Returns:
            True si la confianza >= threshold

        Example:
            >>> conf = ConfidenceScore(0.60)
            >>> conf.is_acceptable()  # >= 50%
            True
            >>> conf.is_acceptable(threshold=0.70)  # >= 70%
            False
        """
        return self.value >= threshold

    def is_low(self, threshold: float = 0.30) -> bool:
        """
        Verifica si la confianza es baja.

        Args:
            threshold: Umbral de confianza baja (default: 0.30 = 30%)

        Returns:
            True si la confianza < threshold

        Example:
            >>> conf = ConfidenceScore(0.25)
            >>> conf.is_low()  # < 30%
            True
        """
        return self.value < threshold

    def meets_threshold(self, threshold: float) -> bool:
        """
        Verifica si cumple un umbral específico.

        Args:
            threshold: Umbral a verificar (0.0-1.0)

        Returns:
            True si confianza >= threshold

        Example:
            >>> conf = ConfidenceScore(0.85)
            >>> conf.meets_threshold(0.80)
            True
            >>> conf.meets_threshold(0.90)
            False
        """
        return self.value >= threshold

    def formatted(self, decimals: int = 0) -> str:
        """
        Formatea como porcentaje con decimales.

        Args:
            decimals: Número de decimales (default: 0)

        Returns:
            String formateado con %

        Example:
            >>> conf = ConfidenceScore(0.8567)
            >>> conf.formatted()
            '86%'
            >>> conf.formatted(decimals=1)
            '85.7%'
            >>> conf.formatted(decimals=2)
            '85.67%'
        """
        percentage = self.as_percentage()
        return f"{percentage:.{decimals}f}%"

    def __str__(self) -> str:
        """String representation como porcentaje."""
        return self.formatted()

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"ConfidenceScore({self.value:.2f})"

    def __format__(self, format_spec: str) -> str:
        """
        Soporte para format strings (f-strings, .format()).

        Permite usar ConfidenceScore directamente en f-strings:
        - f"{conf}" → "85%"
        - f"{conf:.1f}" → "85.5%"
        - f"{conf:.2f}" → "85.67%"
        - f"{conf:d}" → "85"

        Args:
            format_spec: Especificador de formato (ej: '.1f', 'd', etc.)

        Returns:
            String formateado

        Example:
            >>> conf = ConfidenceScore(0.8567)
            >>> f"{conf}"
            '86%'
            >>> f"{conf:.1f}"
            '85.7%'
            >>> f"{conf:.2f}%"
            '85.67%'
            >>> f"{conf:d}"
            '86'
        """
        if not format_spec or format_spec == 'g':
            # Sin especificador o 'g': formato por defecto (porcentaje sin decimales)
            return self.formatted(decimals=0)
        elif format_spec == 'd':
            # Formato entero
            return str(int(round(self.as_percentage())))
        elif format_spec.endswith('f'):
            # Formato float (.1f, .2f, etc.)
            # Extraer número de decimales del spec
            try:
                decimals = int(format_spec[1]) if len(format_spec) >= 2 and format_spec[1].isdigit() else 1
                percentage = self.as_percentage()
                return f"{percentage:.{decimals}f}"
            except (ValueError, IndexError):
                # Fallback si no se puede parsear
                return self.formatted(decimals=1)
        else:
            # Para otros formatos, usar el valor como porcentaje
            percentage = self.as_percentage()
            return format(percentage, format_spec)

    def __float__(self) -> float:
        """Conversión a float."""
        return self.value

    def __int__(self) -> int:
        """Conversión a int (porcentaje redondeado)."""
        return int(round(self.as_percentage()))

    # Comparaciones
    def __lt__(self, other: Union['ConfidenceScore', float]) -> bool:
        other_val = other.value if isinstance(other, ConfidenceScore) else other
        return self.value < other_val

    def __le__(self, other: Union['ConfidenceScore', float]) -> bool:
        other_val = other.value if isinstance(other, ConfidenceScore) else other
        return self.value <= other_val

    def __gt__(self, other: Union['ConfidenceScore', float]) -> bool:
        other_val = other.value if isinstance(other, ConfidenceScore) else other
        return self.value > other_val

    def __ge__(self, other: Union['ConfidenceScore', float]) -> bool:
        other_val = other.value if isinstance(other, ConfidenceScore) else other
        return self.value >= other_val

    def __hash__(self) -> int:
        """Hash para usar en sets/dicts."""
        return hash(self.value)


# ========== THRESHOLDS PREDEFINIDOS ==========

class ConfidenceThresholds:
    """Umbrales de confianza comúnmente usados."""

    VERY_LOW = ConfidenceScore(0.30)    # 30%
    LOW = ConfidenceScore(0.50)         # 50%
    MEDIUM = ConfidenceScore(0.70)      # 70%
    HIGH = ConfidenceScore(0.85)        # 85%
    VERY_HIGH = ConfidenceScore(0.95)   # 95%

    @classmethod
    def get_level(cls, score: ConfidenceScore) -> str:
        """
        Clasifica un score en nivel textual.

        Args:
            score: Score a clasificar

        Returns:
            Nivel: "VERY_HIGH", "HIGH", "MEDIUM", "LOW", "VERY_LOW"

        Example:
            >>> score = ConfidenceScore(0.92)
            >>> ConfidenceThresholds.get_level(score)
            'VERY_HIGH'
        """
        if score >= cls.VERY_HIGH:
            return "VERY_HIGH"
        elif score >= cls.HIGH:
            return "HIGH"
        elif score >= cls.MEDIUM:
            return "MEDIUM"
        elif score >= cls.LOW:
            return "LOW"
        else:
            return "VERY_LOW"
