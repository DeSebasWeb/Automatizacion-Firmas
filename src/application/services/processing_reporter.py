"""Generador de reportes y estadísticas de procesamiento."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ProcessingStats:
    """
    Estadísticas del procesamiento de formularios.

    Attributes:
        total_rows: Total de renglones en el formulario
        processed_rows: Renglones procesados hasta ahora
        auto_saved: Renglones guardados automáticamente
        required_validation: Renglones que requirieron validación manual
        empty_rows: Renglones vacíos detectados
        not_found: Cédulas no encontradas en BD
        errors: Errores críticos durante procesamiento
    """
    total_rows: int = 0
    processed_rows: int = 0
    auto_saved: int = 0
    required_validation: int = 0
    empty_rows: int = 0
    not_found: int = 0
    errors: int = 0

    @property
    def pending_rows(self) -> int:
        """Renglones pendientes de procesar."""
        return self.total_rows - self.processed_rows

    @property
    def success_rate(self) -> float:
        """Tasa de éxito (auto_saved / procesados)."""
        if self.processed_rows == 0:
            return 0.0
        return (self.auto_saved / self.processed_rows) * 100

    @property
    def progress_percentage(self) -> float:
        """Porcentaje de progreso."""
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100

    def to_dict(self) -> Dict:
        """Convierte a diccionario."""
        return {
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'pending_rows': self.pending_rows,
            'auto_saved': self.auto_saved,
            'required_validation': self.required_validation,
            'empty_rows': self.empty_rows,
            'not_found': self.not_found,
            'errors': self.errors,
            'success_rate': self.success_rate,
            'progress_percentage': self.progress_percentage
        }

    def increment_auto_saved(self) -> None:
        """Incrementa contador de guardados automáticos."""
        self.auto_saved += 1

    def increment_required_validation(self) -> None:
        """Incrementa contador de validaciones requeridas."""
        self.required_validation += 1

    def increment_empty_rows(self) -> None:
        """Incrementa contador de renglones vacíos."""
        self.empty_rows += 1

    def increment_not_found(self) -> None:
        """Incrementa contador de no encontrados."""
        self.not_found += 1

    def increment_errors(self) -> None:
        """Incrementa contador de errores."""
        self.errors += 1

    def increment_processed(self) -> None:
        """Incrementa contador de procesados."""
        self.processed_rows += 1


class ProcessingReporter:
    """
    Generador de reportes y estadísticas de procesamiento.

    Responsabilidades:
    - Mantener estadísticas actualizadas
    - Generar reportes formateados
    - Calcular métricas derivadas

    Example:
        >>> reporter = ProcessingReporter()
        >>> reporter.stats.total_rows = 15
        >>> reporter.stats.increment_processed()
        >>> reporter.stats.increment_auto_saved()
        >>> print(reporter.get_summary())
    """

    def __init__(self):
        """Inicializa el reporter con estadísticas en cero."""
        self.stats = ProcessingStats()

    def get_summary(self) -> str:
        """
        Genera resumen formateado del procesamiento.

        Returns:
            String con tabla formateada de estadísticas

        Example:
            >>> print(reporter.get_summary())
            ╔═══════════════════════════════════════╗
            ║     RESUMEN DE PROCESAMIENTO          ║
            ╠═══════════════════════════════════════╣
            ║ Total de renglones:            15     ║
            ║ Procesados:                    15     ║
            ║ ✓ Guardados automáticamente:   12     ║
            ...
        """
        s = self.stats

        return f"""
╔═══════════════════════════════════════════════════════════╗
║           RESUMEN DE PROCESAMIENTO                        ║
╠═══════════════════════════════════════════════════════════╣
║ Total de renglones:              {s.total_rows:>3}                  ║
║ Procesados:                      {s.processed_rows:>3}                  ║
║ Pendientes:                      {s.pending_rows:>3}                  ║
║                                                           ║
║ ✓ Guardados automáticamente:     {s.auto_saved:>3}                  ║
║ ⚠ Requirieron validación:        {s.required_validation:>3}                  ║
║ ○ Renglones vacíos:              {s.empty_rows:>3}                  ║
║ ✗ No encontrados:                {s.not_found:>3}                  ║
║ ⚠ Errores:                       {s.errors:>3}                  ║
║                                                           ║
║ Tasa de éxito:                   {s.success_rate:>5.1f}%              ║
║ Progreso:                        {s.progress_percentage:>5.1f}%              ║
╚═══════════════════════════════════════════════════════════╝
"""

    def get_progress_message(self, current_row: int) -> str:
        """
        Genera mensaje de progreso para renglón actual.

        Args:
            current_row: Número de renglón actual (1-indexed)

        Returns:
            Mensaje formateado del progreso

        Example:
            >>> reporter.get_progress_message(5)
            "Renglón 5/15 (33.3%) - 4 procesados, 3 guardados"
        """
        s = self.stats
        return (
            f"Renglón {current_row}/{s.total_rows} ({s.progress_percentage:.1f}%) - "
            f"{s.processed_rows} procesados, {s.auto_saved} guardados"
        )

    def reset(self) -> None:
        """Reinicia todas las estadísticas a cero."""
        self.stats = ProcessingStats()
