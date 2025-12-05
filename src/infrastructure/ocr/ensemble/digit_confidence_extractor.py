"""Extractor de confianzas por dígito para ensemble OCR."""
from dataclasses import dataclass
from typing import List, Dict, Tuple
from ....domain.entities import CedulaRecord
from ....domain.ports import OCRPort


@dataclass
class DigitConfidenceData:
    """Datos de confianza por dígito de un OCR."""
    text: str
    confidences: List[float]
    average: float
    source: str


class DigitConfidenceExtractor:
    """
    Extrae confianzas por dígito de ambos proveedores OCR.

    Responsabilidad única: Obtener confianzas detalladas por dígito
    desde Google Vision y Azure Vision para permitir comparación.

    Esta clase centraliza la lógica de extracción de confianzas que
    estaba duplicada en el método _combine_at_digit_level().
    """

    @staticmethod
    def extract_from_both_ocr(
        primary_record: CedulaRecord,
        secondary_record: CedulaRecord,
        primary_ocr: OCRPort,
        secondary_ocr: OCRPort
    ) -> Tuple[DigitConfidenceData, DigitConfidenceData]:
        """
        Extrae confianzas por dígito de ambos OCR providers.

        Args:
            primary_record: Registro del OCR primario
            secondary_record: Registro del OCR secundario
            primary_ocr: Instancia del OCR primario
            secondary_ocr: Instancia del OCR secundario

        Returns:
            Tupla con (primary_confidence_data, secondary_confidence_data)

        Raises:
            ValueError: Si no se pueden extraer las confianzas
        """
        primary_text = primary_record.cedula.value
        secondary_text = secondary_record.cedula.value

        try:
            # Extraer confianzas del OCR primario
            primary_conf_raw = primary_ocr.get_character_confidences(primary_text)
            primary_data = DigitConfidenceData(
                text=primary_text,
                confidences=primary_conf_raw['confidences'],
                average=primary_conf_raw['average'],
                source=primary_conf_raw.get('source', 'primary')
            )

            # Extraer confianzas del OCR secundario
            secondary_conf_raw = secondary_ocr.get_character_confidences(secondary_text)
            secondary_data = DigitConfidenceData(
                text=secondary_text,
                confidences=secondary_conf_raw['confidences'],
                average=secondary_conf_raw['average'],
                source=secondary_conf_raw.get('source', 'secondary')
            )

            return primary_data, secondary_data

        except Exception as e:
            raise ValueError(f"Error extrayendo confianzas por dígito: {e}")

    @staticmethod
    def get_digit_at_position(
        confidence_data: DigitConfidenceData,
        position: int
    ) -> Tuple[str, float]:
        """
        Obtiene dígito y confianza en una posición específica.

        Args:
            confidence_data: Datos de confianza
            position: Posición del dígito (0-indexed)

        Returns:
            Tupla (dígito, confianza) o (None, 0.0) si no existe
        """
        if position < len(confidence_data.text):
            digit = confidence_data.text[position]
            confidence = (
                confidence_data.confidences[position]
                if position < len(confidence_data.confidences)
                else 0.0
            )
            return digit, confidence
        return None, 0.0
