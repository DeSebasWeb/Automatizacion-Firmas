"""Calculador de estadísticas para ensemble OCR."""
from dataclasses import dataclass
from typing import List, Dict
from .digit_comparator import DigitComparison


@dataclass
class EnsembleStats:
    """Estadísticas del proceso de ensemble."""
    total_digits: int
    unanimous_count: int
    conflict_count: int
    unanimous_ratio: float
    conflict_ratio: float
    average_confidence: float
    comparison_table: List[Dict]


class EnsembleStatistics:
    """
    Calcula estadísticas y validaciones del proceso de ensemble.

    Responsabilidad única: Agregar comparaciones individuales y calcular
    métricas globales del ensemble (coincidencias, conflictos, confianza).
    """

    def __init__(self, max_conflict_ratio: float = 0.40):
        """
        Inicializa el calculador de estadísticas.

        Args:
            max_conflict_ratio: Ratio máximo aceptable de conflictos (default: 40%)
        """
        self.max_conflict_ratio = max_conflict_ratio

    def calculate_statistics(
        self,
        comparisons: List[DigitComparison]
    ) -> EnsembleStats:
        """
        Calcula estadísticas del ensemble desde las comparaciones.

        Args:
            comparisons: Lista de comparaciones dígito por dígito

        Returns:
            EnsembleStats con todas las métricas calculadas
        """
        if not comparisons:
            return EnsembleStats(
                total_digits=0,
                unanimous_count=0,
                conflict_count=0,
                unanimous_ratio=0.0,
                conflict_ratio=0.0,
                average_confidence=0.0,
                comparison_table=[]
            )

        total_digits = len(comparisons)

        # Contar tipos de consenso
        unanimous_count = sum(
            1 for c in comparisons if c.consensus_type == 'unanimous'
        )

        # Contar conflictos (casos donde hubo que elegir)
        conflict_count = sum(
            1 for c in comparisons
            if c.consensus_type == 'highest_confidence' and c.primary_digit != c.secondary_digit
        )

        # Calcular ratios
        unanimous_ratio = unanimous_count / total_digits if total_digits > 0 else 0.0
        conflict_ratio = conflict_count / total_digits if total_digits > 0 else 0.0

        # Calcular confianza promedio
        total_confidence = sum(c.chosen_confidence for c in comparisons)
        average_confidence = total_confidence / total_digits if total_digits > 0 else 0.0

        # Crear tabla de comparación
        comparison_table = self._create_comparison_table(comparisons)

        return EnsembleStats(
            total_digits=total_digits,
            unanimous_count=unanimous_count,
            conflict_count=conflict_count,
            unanimous_ratio=unanimous_ratio,
            conflict_ratio=conflict_ratio,
            average_confidence=average_confidence,
            comparison_table=comparison_table
        )

    def validate_statistics(
        self,
        stats: EnsembleStats,
        verbose: bool = False
    ) -> bool:
        """
        Valida que las estadísticas estén dentro de límites aceptables.

        Args:
            stats: Estadísticas calculadas
            verbose: Si imprimir advertencias

        Returns:
            True si las estadísticas son aceptables (no rechaza automáticamente)
        """
        # Verificar ratio de conflictos
        if stats.conflict_ratio > self.max_conflict_ratio:
            if verbose:
                print(f"\n⚠ ADVERTENCIA: {stats.conflict_count} conflictos "
                      f"({stats.conflict_ratio*100:.1f}%) es mucho "
                      f"(>{self.max_conflict_ratio*100:.0f}%). "
                      f"La cédula puede ser de baja calidad.")
            # No rechazamos automáticamente, solo advertimos
            return True

        return True

    def print_statistics(
        self,
        stats: EnsembleStats,
        verbose: bool = False
    ) -> None:
        """
        Imprime estadísticas del ensemble.

        Args:
            stats: Estadísticas a imprimir
            verbose: Si imprimir tabla detallada
        """
        if verbose and stats.comparison_table:
            self._print_comparison_table(stats.comparison_table)

        print(f"\n{'='*80}")
        print("ESTADÍSTICAS:")
        print(f"  Coincidencias: {stats.unanimous_count}/{stats.total_digits} "
              f"({stats.unanimous_ratio*100:.1f}%)")
        print(f"  Conflictos:    {stats.conflict_count}/{stats.total_digits} "
              f"({stats.conflict_ratio*100:.1f}%)")
        print(f"  Confianza promedio: {stats.average_confidence*100:.1f}%")

    def _create_comparison_table(
        self,
        comparisons: List[DigitComparison]
    ) -> List[Dict]:
        """
        Crea tabla de comparación para logging.

        Args:
            comparisons: Lista de comparaciones

        Returns:
            Lista de dicts con datos tabulares
        """
        table = []

        for comp in comparisons:
            table.append({
                'pos': comp.position,
                'primary_digit': comp.primary_digit or '-',
                'primary_conf': comp.primary_confidence * 100 if comp.primary_digit else 0,
                'secondary_digit': comp.secondary_digit or '-',
                'secondary_conf': comp.secondary_confidence * 100 if comp.secondary_digit else 0,
                'chosen': comp.chosen_digit,
                'chosen_conf': comp.chosen_confidence * 100,
                'source': comp.source,
                'type': comp.consensus_type
            })

        return table

    def _print_comparison_table(self, table: List[Dict]) -> None:
        """
        Imprime tabla de comparación dígito por dígito.

        Args:
            table: Tabla de datos a imprimir
        """
        print(f"\n{'Pos':<5} {'Primary':<15} {'Secondary':<15} {'Elegido':<15} {'Tipo':<12}")
        print(f"{'-'*5} {'-'*15} {'-'*15} {'-'*15} {'-'*12}")

        for row in table:
            primary_str = f"'{row['primary_digit']}' ({row['primary_conf']:.1f}%)"
            secondary_str = f"'{row['secondary_digit']}' ({row['secondary_conf']:.1f}%)"
            chosen_str = f"'{row['chosen']}' ({row['chosen_conf']:.1f}%)"
            type_str = row['type']

            print(f"{row['pos']:<5} {primary_str:<15} {secondary_str:<15} "
                  f"{chosen_str:<15} {type_str:<12}")
