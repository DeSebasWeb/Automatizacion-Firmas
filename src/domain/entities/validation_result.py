"""Entidad de dominio para resultados de validación fuzzy."""
from dataclasses import dataclass, field
from typing import Dict, Literal
from enum import Enum


class ValidationStatus(Enum):
    """Estados posibles de la validación."""
    OK = "OK"  # Validación exitosa
    WARNING = "WARNING"  # Advertencia, requiere revisión
    ERROR = "ERROR"  # Error, no se puede proceder


class ValidationAction(Enum):
    """Acciones a tomar según resultado de validación."""
    AUTO_SAVE = "AUTO_SAVE"  # Guardar automáticamente
    REQUIRE_VALIDATION = "REQUIRE_VALIDATION"  # Requiere validación manual
    ALERT_NOT_FOUND = "ALERT_NOT_FOUND"  # Alertar que persona no existe


@dataclass
class FieldMatch:
    """Resultado de comparación de un campo específico."""
    match: bool
    """True si los campos coinciden según umbral"""

    similarity: float
    """Similitud entre 0.0 y 1.0"""

    compared: str
    """String descriptivo: "MARIA vs OMAR" """

    field_name: str = ""
    """Nombre del campo comparado"""


@dataclass
class ValidationResult:
    """
    Resultado de validación fuzzy entre datos manuscritos y digitales.

    Determina si los datos coinciden y qué acción tomar.
    """

    status: ValidationStatus
    """Estado de la validación: OK, WARNING, ERROR"""

    action: ValidationAction
    """Acción a tomar: AUTO_SAVE, REQUIRE_VALIDATION, ALERT_NOT_FOUND"""

    confidence: float
    """Confianza general de la validación (0.0 - 1.0)"""

    matches: Dict[str, FieldMatch] = field(default_factory=dict)
    """Diccionario de comparaciones por campo"""

    details: str = ""
    """Descripción detallada del resultado"""

    manuscrito_nombres: str = ""
    """Nombres manuscritos originales (para referencia)"""

    digital_nombres: str = ""
    """Nombres digitales del formulario (para referencia)"""

    def __post_init__(self):
        """Validaciones después de inicialización."""
        # Asegurar que confidence esté entre 0 y 1
        self.confidence = max(0.0, min(1.0, self.confidence))

    @property
    def is_valid(self) -> bool:
        """Retorna True si la validación es exitosa."""
        return self.status == ValidationStatus.OK

    @property
    def requires_user_action(self) -> bool:
        """Retorna True si requiere intervención del usuario."""
        return self.action in [
            ValidationAction.REQUIRE_VALIDATION,
            ValidationAction.ALERT_NOT_FOUND
        ]

    @property
    def can_auto_save(self) -> bool:
        """Retorna True si se puede guardar automáticamente."""
        return self.action == ValidationAction.AUTO_SAVE

    def get_match_summary(self) -> str:
        """Genera un resumen de las coincidencias."""
        if not self.matches:
            return "Sin comparaciones disponibles"

        summary_parts = []
        for field_name, match in self.matches.items():
            status = "✓" if match.match else "✗"
            summary_parts.append(
                f"{status} {field_name}: {match.compared} ({match.similarity:.0%})"
            )

        return "\n".join(summary_parts)

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización."""
        return {
            'status': self.status.value,
            'action': self.action.value,
            'confidence': self.confidence,
            'details': self.details,
            'manuscrito_nombres': self.manuscrito_nombres,
            'digital_nombres': self.digital_nombres,
            'matches': {
                key: {
                    'match': val.match,
                    'similarity': val.similarity,
                    'compared': val.compared,
                    'field_name': val.field_name
                }
                for key, val in self.matches.items()
            }
        }

    def __str__(self) -> str:
        """Representación en string."""
        if self.status == ValidationStatus.OK:
            return f"✓ Validación exitosa ({self.confidence:.0%} confianza)"
        elif self.status == ValidationStatus.WARNING:
            return f"⚠️ {self.details}"
        else:
            return f"✗ Error: {self.details}"
