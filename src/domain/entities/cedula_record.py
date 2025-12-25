"""Minimal cédula record for OCR results."""
from dataclasses import dataclass
from typing import Optional, Dict, Any

from ..value_objects import CedulaNumber, ConfidenceScore


@dataclass
class CedulaRecord:
    """
    Minimal entity representing an extracted cédula number from OCR.

    Simplified version for API usage without UI-specific state management.

    Attributes:
        cedula: Extracted cédula number (Value Object)
        confidence: OCR confidence score (Value Object 0.0-1.0)
        index: Position in the source document/list
    """
    cedula: CedulaNumber
    confidence: ConfidenceScore
    index: int = 0

    @classmethod
    def from_primitives(
        cls,
        cedula: str,
        confidence: float,
        index: int = 0
    ) -> 'CedulaRecord':
        """
        Create CedulaRecord from primitive types.

        Args:
            cedula: Cédula number as string
            confidence: Confidence as decimal (0.0-1.0) or percentage (0-100)
            index: Position in list

        Returns:
            CedulaRecord instance
        """
        # Create CedulaNumber (with validation)
        cedula_vo = CedulaNumber(cedula)

        # Create ConfidenceScore (auto-detect format)
        if confidence > 1.0:
            confidence_vo = ConfidenceScore.from_percentage(confidence)
        else:
            confidence_vo = ConfidenceScore(confidence)

        return cls(
            cedula=cedula_vo,
            confidence=confidence_vo,
            index=index
        )

    def is_valid(self, min_confidence: float = 0.5) -> bool:
        """
        Check if record meets minimum quality criteria.

        Args:
            min_confidence: Minimum confidence threshold (0.0-1.0)

        Returns:
            True if valid
        """
        return (
            self.cedula.is_valid() and
            self.confidence.value >= min_confidence
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'cedula': self.cedula.value,
            'confidence': self.confidence.as_percentage(),
            'index': self.index
        }
