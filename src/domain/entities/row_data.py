"""Entidad de dominio para datos de un renglón del formulario manuscrito (sistema dual OCR)."""
from dataclasses import dataclass
from typing import Dict, Optional


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

    cedula: str
    """Número de cédula manuscrito (columna centro)"""

    is_empty: bool
    """True si el renglón está completamente vacío"""

    confidence: Dict[str, float]
    """Confianza del OCR para cada campo: {'nombres': 0.89, 'cedula': 0.95}"""

    raw_text: Optional[str] = None
    """Texto crudo detectado por Google Vision (para debugging)"""

    def __post_init__(self):
        """Normaliza los datos después de inicialización."""
        # Limpiar espacios
        self.nombres_manuscritos = self.nombres_manuscritos.strip()
        self.cedula = self.cedula.strip()

        # Marcar como vacío si no tiene datos
        if not self.nombres_manuscritos and not self.cedula:
            self.is_empty = True

    @property
    def has_cedula(self) -> bool:
        """Verifica si el renglón tiene cédula."""
        return bool(self.cedula and len(self.cedula) >= 6)

    @property
    def has_nombres(self) -> bool:
        """Verifica si el renglón tiene nombres."""
        return bool(self.nombres_manuscritos and len(self.nombres_manuscritos) >= 3)

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización."""
        return {
            'row_index': self.row_index,
            'nombres_manuscritos': self.nombres_manuscritos,
            'cedula': self.cedula,
            'is_empty': self.is_empty,
            'confidence': self.confidence,
            'raw_text': self.raw_text
        }

    def __str__(self) -> str:
        """Representación en string."""
        if self.is_empty:
            return f"Renglón {self.row_index}: [VACÍO]"
        return f"Renglón {self.row_index}: {self.nombres_manuscritos} - {self.cedula}"
