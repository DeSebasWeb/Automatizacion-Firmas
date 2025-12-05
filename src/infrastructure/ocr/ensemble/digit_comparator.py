"""Comparador de dígitos individuales para ensemble OCR."""
from dataclasses import dataclass
from typing import Optional
from .conflict_resolver import ConflictResolver, ConflictResolution


@dataclass
class DigitComparison:
    """Resultado de comparar un dígito entre dos OCR."""
    position: int
    chosen_digit: str
    chosen_confidence: float
    source: str  # 'primary', 'secondary', 'both', 'only_primary', 'only_secondary'
    consensus_type: str  # 'unanimous', 'highest_confidence', 'only_primary', 'only_secondary'
    primary_digit: Optional[str] = None
    primary_confidence: float = 0.0
    secondary_digit: Optional[str] = None
    secondary_confidence: float = 0.0


class DigitComparator:
    """
    Compara dígitos individuales y decide cuál elegir.

    Responsabilidad única: Comparar un dígito en una posición específica
    y decidir cuál usar basándose en:
    - Coincidencia (ambos iguales)
    - Confianza (uno mayor que otro)
    - Threshold mínimo
    - Resolución de conflictos (usando ConflictResolver)
    """

    def __init__(
        self,
        min_digit_confidence: float = 0.58,
        confidence_boost: float = 0.03,
        allow_low_confidence_override: bool = True,
        conflict_resolver: Optional[ConflictResolver] = None
    ):
        """
        Inicializa el comparador de dígitos.

        Args:
            min_digit_confidence: Confianza mínima aceptable por dígito
            confidence_boost: Boost de confianza cuando ambos coinciden
            allow_low_confidence_override: Permitir override del threshold en casos especiales
            conflict_resolver: Resolver de conflictos (se crea uno por defecto si no se proporciona)
        """
        self.min_digit_confidence = min_digit_confidence
        self.confidence_boost = confidence_boost
        self.allow_low_confidence_override = allow_low_confidence_override
        self.conflict_resolver = conflict_resolver or ConflictResolver()

    def compare_at_position(
        self,
        position: int,
        primary_digit: Optional[str],
        primary_confidence: float,
        secondary_digit: Optional[str],
        secondary_confidence: float,
        verbose: bool = False
    ) -> Optional[DigitComparison]:
        """
        Compara dígitos en una posición específica.

        CASOS:
        1. Solo uno tiene dígito → usar ese
        2. Ambos coinciden → usar con confianza boosted
        3. Difieren → usar ConflictResolver
        4. Confianza < threshold → rechazar (con excepciones)

        Args:
            position: Posición del dígito
            primary_digit: Dígito del OCR primario (o None)
            primary_confidence: Confianza del primario (0.0-1.0)
            secondary_digit: Dígito del OCR secundario (o None)
            secondary_confidence: Confianza del secundario (0.0-1.0)
            verbose: Si imprimir logging detallado

        Returns:
            DigitComparison o None si se rechaza por baja confianza
        """
        # Validar threshold mínimo (con posibles excepciones)
        min_threshold = self._get_effective_threshold(
            primary_digit, primary_confidence,
            secondary_digit, secondary_confidence,
            position, verbose
        )

        # Validar confianzas
        if primary_digit and primary_confidence < min_threshold:
            if verbose:
                print(f"Pos {position}: Primary '{primary_digit}' tiene confianza muy baja "
                      f"({primary_confidence:.2%} < {min_threshold:.2%})")
            return None

        if secondary_digit and secondary_confidence < min_threshold:
            if verbose:
                print(f"Pos {position}: Secondary '{secondary_digit}' tiene confianza muy baja "
                      f"({secondary_confidence:.2%} < {min_threshold:.2%})")
            return None

        # CASO 1: Solo uno tiene dígito
        if primary_digit is None:
            return DigitComparison(
                position=position,
                chosen_digit=secondary_digit,
                chosen_confidence=secondary_confidence,
                source='secondary',
                consensus_type='only_secondary',
                secondary_digit=secondary_digit,
                secondary_confidence=secondary_confidence
            )

        if secondary_digit is None:
            return DigitComparison(
                position=position,
                chosen_digit=primary_digit,
                chosen_confidence=primary_confidence,
                source='primary',
                consensus_type='only_primary',
                primary_digit=primary_digit,
                primary_confidence=primary_confidence
            )

        # CASO 2: Ambos coinciden (UNANIMIDAD)
        if primary_digit == secondary_digit:
            avg_conf = (primary_confidence + secondary_confidence) / 2
            # Boost por coincidencia
            boosted_conf = min(0.99, avg_conf + self.confidence_boost)

            if verbose:
                print(f"Pos {position}: COINCIDENCIA '{primary_digit}' "
                      f"Primary={primary_confidence:.2%} Secondary={secondary_confidence:.2%} → "
                      f"Final={boosted_conf:.2%}")

            return DigitComparison(
                position=position,
                chosen_digit=primary_digit,
                chosen_confidence=boosted_conf,
                source='both',
                consensus_type='unanimous',
                primary_digit=primary_digit,
                primary_confidence=primary_confidence,
                secondary_digit=secondary_digit,
                secondary_confidence=secondary_confidence
            )

        # CASO 3: Difieren (CONFLICTO) - usar ConflictResolver
        resolution = self.conflict_resolver.resolve_conflict(
            primary_digit=primary_digit,
            primary_confidence=primary_confidence,
            secondary_digit=secondary_digit,
            secondary_confidence=secondary_confidence,
            position=position,
            verbose=verbose
        )

        if resolution is None:
            # Conflicto ambiguo, rechazar
            return None

        return DigitComparison(
            position=position,
            chosen_digit=resolution.chosen_digit,
            chosen_confidence=resolution.chosen_confidence,
            source=resolution.source,
            consensus_type=resolution.resolution_type,
            primary_digit=primary_digit,
            primary_confidence=primary_confidence,
            secondary_digit=secondary_digit,
            secondary_confidence=secondary_confidence
        )

    def _get_effective_threshold(
        self,
        primary_digit: Optional[str],
        primary_confidence: float,
        secondary_digit: Optional[str],
        secondary_confidence: float,
        position: int,
        verbose: bool
    ) -> float:
        """
        Calcula threshold efectivo considerando pares de confusión.

        Permite relajar el threshold cuando:
        - Es un par de confusión conocido
        - El otro OCR tiene alta confianza (>75%)

        Args:
            primary_digit: Dígito del primario
            primary_confidence: Confianza del primario
            secondary_digit: Dígito del secundario
            secondary_confidence: Confianza del secundario
            position: Posición del dígito
            verbose: Si imprimir logging

        Returns:
            Threshold efectivo a usar
        """
        min_threshold = self.min_digit_confidence
        relaxed_threshold = min_threshold - 0.10  # 10% más permisivo

        # Si ambos dígitos existen y difieren, verificar contexto
        if (primary_digit and secondary_digit and primary_digit != secondary_digit
                and self.allow_low_confidence_override):

            is_confusion = ConflictResolver.is_confusion_pair(primary_digit, secondary_digit)

            # Si es par de confusión y uno tiene alta confianza, relajar threshold
            if is_confusion:
                if primary_confidence < min_threshold and secondary_confidence >= 0.75:
                    if verbose:
                        print(f"Pos {position}: ℹ️ Threshold relajado para Primary (par de confusión)")
                    return relaxed_threshold
                elif secondary_confidence < min_threshold and primary_confidence >= 0.75:
                    if verbose:
                        print(f"Pos {position}: ℹ️ Threshold relajado para Secondary (par de confusión)")
                    # No cambiamos el threshold aquí, solo para primary
                    # Este caso se validará normalmente

        return min_threshold
