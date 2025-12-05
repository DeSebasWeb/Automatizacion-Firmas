"""Resolutor de conflictos entre OCR usando matriz de confusión."""
from dataclasses import dataclass
from typing import Dict, Tuple, Optional


@dataclass
class ConflictResolution:
    """Resultado de resolver un conflicto entre dígitos."""
    chosen_digit: str
    chosen_confidence: float
    source: str  # 'primary', 'secondary', 'primary (adjusted)', 'secondary (adjusted)'
    is_confusion_pair: bool
    confidence_difference: float
    resolution_type: str  # 'unanimous', 'highest_confidence', 'ambiguous'


class ConflictResolver:
    """
    Resuelve conflictos entre dígitos diferentes usando matriz de confusión.

    Responsabilidad única: Decidir qué dígito elegir cuando ambos OCR difieren,
    utilizando conocimiento de pares que frecuentemente se confunden en escritura manual.

    Matriz de confusión (pares problemáticos):
    - 1 ↔ 7: 15% probabilidad de confusión (muy común)
    - 2 ↔ 7: 12% probabilidad
    - 5 ↔ 6: 10% probabilidad
    - 3 ↔ 8: 8% probabilidad
    - 0 ↔ 6: 8% probabilidad
    - 4 ↔ 9: 7% probabilidad
    """

    # Matriz de confusión: pares de dígitos que frecuentemente se confunden
    CONFUSION_PAIRS = {
        ('1', '7'): 0.15,  # 1 y 7 se confunden mucho
        ('7', '1'): 0.15,
        ('5', '6'): 0.10,  # 5 y 6 pueden confundirse
        ('6', '5'): 0.10,
        ('8', '3'): 0.08,  # 8 y 3 a veces se confunden
        ('3', '8'): 0.08,
        ('2', '7'): 0.12,  # 2 y 7 pueden ser similares
        ('7', '2'): 0.12,
        ('0', '6'): 0.08,  # 0 y 6 pueden confundirse
        ('6', '0'): 0.08,
        ('9', '4'): 0.07,  # 9 y 4 a veces se confunden
        ('4', '9'): 0.07,
    }

    def __init__(
        self,
        ambiguity_threshold: float = 0.10,
        allow_adjustments: bool = True
    ):
        """
        Inicializa el resolver de conflictos.

        Args:
            ambiguity_threshold: Diferencia mínima de confianza para decidir (default: 10%)
            allow_adjustments: Si permitir ajustes de confianza para pares de confusión
        """
        self.ambiguity_threshold = ambiguity_threshold
        self.allow_adjustments = allow_adjustments

    def resolve_conflict(
        self,
        primary_digit: str,
        primary_confidence: float,
        secondary_digit: str,
        secondary_confidence: float,
        position: int,
        verbose: bool = False
    ) -> Optional[ConflictResolution]:
        """
        Resuelve conflicto entre dos dígitos diferentes.

        ESTRATEGIA:
        1. Detectar si es par de confusión conocido
        2. Ajustar threshold de ambigüedad basado en probabilidad de confusión
        3. Si diferencia < threshold ajustado → AMBIGUO (rechazar)
        4. Si diferencia >= threshold → elegir el de mayor confianza (posiblemente ajustada)

        Args:
            primary_digit: Dígito del OCR primario
            primary_confidence: Confianza del OCR primario (0.0-1.0)
            secondary_digit: Dígito del OCR secundario
            secondary_confidence: Confianza del OCR secundario (0.0-1.0)
            position: Posición del dígito (para logging)
            verbose: Si imprimir logging detallado

        Returns:
            ConflictResolution o None si es ambiguo (debe rechazarse)
        """
        conf_diff = abs(primary_confidence - secondary_confidence)

        # Detectar par de confusión
        is_confusion_pair = (primary_digit, secondary_digit) in self.CONFUSION_PAIRS
        confusion_prob = self.CONFUSION_PAIRS.get((primary_digit, secondary_digit), 0.0)

        # Calcular threshold efectivo
        effective_threshold = self.ambiguity_threshold
        if is_confusion_pair:
            # Para pares confusos, reducir el umbral para permitir decisión
            # con menores diferencias de confianza
            effective_threshold = max(0.05, self.ambiguity_threshold - confusion_prob)

            if verbose:
                print(f"Pos {position}: ⚠️ PAR DE CONFUSIÓN DETECTADO: "
                      f"'{primary_digit}' vs '{secondary_digit}' "
                      f"(prob confusión: {confusion_prob:.1%})")
                print(f"         Umbral ajustado: {self.ambiguity_threshold:.1%} → "
                      f"{effective_threshold:.1%}")

        # Verificar ambigüedad
        if conf_diff < effective_threshold:
            if verbose:
                print(f"Pos {position}: CONFLICTO AMBIGUO "
                      f"Primary='{primary_digit}' ({primary_confidence:.2%}) "
                      f"Secondary='{secondary_digit}' ({secondary_confidence:.2%}) "
                      f"Diferencia={conf_diff:.2%} < {effective_threshold:.2%} → RECHAZADO")
            return None  # Ambiguo, no se puede decidir

        # Aplicar ajustes de confianza para pares de confusión
        adjusted_primary = primary_confidence
        adjusted_secondary = secondary_confidence
        source_suffix = ""

        if is_confusion_pair and self.allow_adjustments:
            # Caso especial 1 vs 7: si uno tiene confianza baja, probablemente es 1
            if primary_digit in ['1', '7'] and secondary_digit in ['1', '7']:
                if primary_confidence < 0.70 and secondary_confidence > 0.80:
                    adjusted_primary *= 0.95  # Penalizar Primary
                    source_suffix = " (ajustado)" if adjusted_primary < adjusted_secondary else ""
                elif secondary_confidence < 0.70 and primary_confidence > 0.80:
                    adjusted_secondary *= 0.95  # Penalizar Secondary
                    source_suffix = " (ajustado)" if adjusted_secondary < adjusted_primary else ""

        # Elegir el de mayor confianza (ajustada)
        if adjusted_primary > adjusted_secondary:
            chosen_digit = primary_digit
            chosen_conf = primary_confidence  # Usar confianza original
            source = 'primary' + source_suffix
        else:
            chosen_digit = secondary_digit
            chosen_conf = secondary_confidence  # Usar confianza original
            source = 'secondary' + source_suffix

        if verbose:
            conflict_symbol = "⚠️" if is_confusion_pair else "→"
            print(f"Pos {position}: {conflict_symbol} CONFLICTO RESUELTO "
                  f"Primary='{primary_digit}' ({primary_confidence:.2%}) "
                  f"Secondary='{secondary_digit}' ({secondary_confidence:.2%}) "
                  f"→ Elegido '{chosen_digit}' de {source}")

        return ConflictResolution(
            chosen_digit=chosen_digit,
            chosen_confidence=chosen_conf,
            source=source,
            is_confusion_pair=is_confusion_pair,
            confidence_difference=conf_diff,
            resolution_type='highest_confidence'
        )

    @staticmethod
    def is_confusion_pair(digit1: str, digit2: str) -> bool:
        """
        Verifica si dos dígitos forman un par de confusión conocido.

        Args:
            digit1: Primer dígito
            digit2: Segundo dígito

        Returns:
            True si es un par de confusión
        """
        return (digit1, digit2) in ConflictResolver.CONFUSION_PAIRS

    @staticmethod
    def get_confusion_probability(digit1: str, digit2: str) -> float:
        """
        Obtiene la probabilidad de confusión entre dos dígitos.

        Args:
            digit1: Primer dígito
            digit2: Segundo dígito

        Returns:
            Probabilidad de confusión (0.0 si no es par conocido)
        """
        return ConflictResolver.CONFUSION_PAIRS.get((digit1, digit2), 0.0)
