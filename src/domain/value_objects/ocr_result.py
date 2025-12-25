"""OCR extraction result value object."""
from dataclasses import dataclass
from typing import Dict, Any

from .cedula_number import CedulaNumber
from .confidence_score import ConfidenceScore


@dataclass(frozen=True)
class OCRResult:
    """
    Represents a single OCR extraction result.

    This is a simple value object for API usage that contains only
    the extracted data without UI-specific state management.

    Attributes:
        text: Extracted text (validated as CedulaNumber for cédulas)
        confidence: OCR confidence score (0.0-1.0)
        position: Optional position/index in source document
    """
    text: str
    confidence: ConfidenceScore
    position: int = 0

    @classmethod
    def from_primitives(
        cls,
        text: str,
        confidence: float,
        position: int = 0
    ) -> 'OCRResult':
        """
        Create OCRResult from primitive types.

        Args:
            text: Extracted text
            confidence: Confidence as decimal (0.0-1.0) or percentage (0-100)
            position: Position in source document

        Returns:
            OCRResult instance
        """
        # Auto-detect confidence format
        if confidence > 1.0:
            confidence_vo = ConfidenceScore.from_percentage(confidence)
        else:
            confidence_vo = ConfidenceScore(confidence)

        return cls(
            text=text,
            confidence=confidence_vo,
            position=position
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'text': self.text,
            'confidence': self.confidence.as_percentage(),
            'position': self.position
        }
