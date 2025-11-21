"""Entidad de dominio para datos de un renglón del formulario manuscrito (sistema dual OCR)."""
from dataclasses import dataclass
from typing import Dict, Optional

from ..value_objects import CedulaNumber, ConfidenceScore


@dataclass
class RowData:
    """
    Representa los datos extraídos de un renglón del formulario manuscrito (SISTEMA DUAL OCR).

    Esta entidad se usa para el flujo de extracción COMPLETA donde se extraen
    NOMBRES + CÉDULAS organizados por renglones, para luego validar contra
    un formulario web digital usando fuzzy matching.

    **Caso de uso:**
        Sistema dual OCR que extrae nombres y cédulas manuscritos,
        digita la cédula automáticamente, lee el formulario web resultante,
        y valida fuzzy para decidir si guardar automáticamente o requerir
        validación manual.

    **Cuándo usar:**
        - Necesitas nombres + cédulas juntos
        - Usas sistema dual OCR (Google Vision + Tesseract)
        - Necesitas validación fuzzy automática
        - Trabajas con formularios estructurados por renglones
        - Necesitas detectar renglones vacíos

    **Cuándo NO usar:**
        - Si solo necesitas números de cédula → usa CedulaRecord
        - Si no usas validación fuzzy → usa CedulaRecord
        - Si no trabajas con formularios estructurados → usa CedulaRecord

    Ver docs/mejoraSOLID/01_CEDULA_RECORD_VS_ROW_DATA.md para detalles.

    **Flujo típico:**
        1. Google Vision extrae RowData de formulario manuscrito
        2. Para cada RowData:
           - Si is_empty: click botón "renglón vacío"
           - Si tiene datos:
             a. Digitar cedula automáticamente
             b. Tesseract lee formulario web → FormData
             c. FuzzyValidator compara RowData vs FormData
             d. Si match >85%: AUTO_SAVE
             e. Si match <85%: REQUIRE_VALIDATION

    Extraído por Google Cloud Vision API del formulario físico/manuscrito.

    Example:
        >>> # Sistema dual OCR
        >>> rows = google_vision.extract_full_form_data(image, expected_rows=15)
        >>> for row in rows:
        ...     if row.is_empty:
        ...         automation.click_empty_row_button()
        ...         continue
        ...     automation.type_cedula(row.cedula)
        ...     form_data = tesseract.get_all_fields()
        ...     validation = fuzzy_validator.validate_person(row, form_data)
        ...     if validation.can_auto_save:
        ...         automation.click_save()
    """

    row_index: int
    """Índice del renglón (0-14 para ~15 renglones)"""

    nombres_manuscritos: str
    """Nombres completos manuscritos (columna izquierda)"""

    cedula: CedulaNumber
    """Número de cédula manuscrito (Value Object)"""

    is_empty: bool
    """True si el renglón está completamente vacío"""

    confidence: Dict[str, ConfidenceScore]
    """Confianza del OCR para cada campo: {'nombres': ConfidenceScore(0.89), 'cedula': ConfidenceScore(0.95)}"""

    raw_text: Optional[str] = None
    """Texto crudo detectado por Google Vision (para debugging)"""

    def __post_init__(self):
        """Normaliza los datos después de inicialización."""
        # Limpiar espacios en nombres
        self.nombres_manuscritos = self.nombres_manuscritos.strip()

        # Marcar como vacío si no tiene datos
        # CedulaNumber.value está pre-validado y limpio
        if not self.nombres_manuscritos and not self.cedula.value:
            self.is_empty = True

    @property
    def has_cedula(self) -> bool:
        """Verifica si el renglón tiene cédula."""
        return bool(self.cedula.value and len(self.cedula.value) >= 3)

    @property
    def has_nombres(self) -> bool:
        """Verifica si el renglón tiene nombres."""
        return bool(self.nombres_manuscritos and len(self.nombres_manuscritos) >= 3)

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización."""
        return {
            'row_index': self.row_index,
            'nombres_manuscritos': self.nombres_manuscritos,
            'cedula': self.cedula.value,
            'is_empty': self.is_empty,
            'confidence': {
                key: score.as_percentage()
                for key, score in self.confidence.items()
            },
            'raw_text': self.raw_text
        }

    def __str__(self) -> str:
        """Representación en string."""
        if self.is_empty:
            return f"Renglón {self.row_index}: [VACÍO]"
        return f"Renglón {self.row_index}: {self.nombres_manuscritos} - {self.cedula.value}"

    @classmethod
    def from_primitives(
        cls,
        row_index: int,
        nombres_manuscritos: str,
        cedula: str,
        is_empty: bool,
        confidence: Dict[str, float],
        raw_text: Optional[str] = None
    ) -> 'RowData':
        """
        Factory method para crear RowData desde tipos primitivos.

        Este método facilita la migración de código legacy y la creación
        desde la capa de infraestructura que trabaja con primitivos.

        Args:
            row_index: Índice del renglón
            nombres_manuscritos: Nombres como string
            cedula: Cédula como string
            is_empty: Si el renglón está vacío
            confidence: Dict con confianzas como floats (0.0-1.0 o 0-100)
            raw_text: Texto crudo opcional

        Returns:
            RowData con Value Objects

        Example:
            >>> row = RowData.from_primitives(
            ...     row_index=0,
            ...     nombres_manuscritos="JUAN PEREZ",
            ...     cedula="12345678",
            ...     is_empty=False,
            ...     confidence={'nombres': 0.89, 'cedula': 0.95}
            ... )

        Note:
            - Auto-detecta si confidence values son porcentajes (>1.0) o decimales (0.0-1.0)
            - CedulaNumber valida automáticamente el formato de la cédula
        """
        # Crear CedulaNumber (con validación automática)
        # Si la cédula está vacía, usar un valor por defecto que pase validación
        cedula_vo = CedulaNumber(cedula) if cedula.strip() else CedulaNumber("000000")

        # Convertir confidence dict a ConfidenceScore
        confidence_vo = {}
        for key, value in confidence.items():
            if value > 1.0:
                # Es porcentaje (0-100)
                confidence_vo[key] = ConfidenceScore.from_percentage(value)
            else:
                # Es decimal (0.0-1.0)
                confidence_vo[key] = ConfidenceScore(value)

        return cls(
            row_index=row_index,
            nombres_manuscritos=nombres_manuscritos,
            cedula=cedula_vo,
            is_empty=is_empty,
            confidence=confidence_vo,
            raw_text=raw_text
        )
