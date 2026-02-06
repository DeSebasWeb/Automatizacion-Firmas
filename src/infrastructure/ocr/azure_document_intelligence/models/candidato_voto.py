from pydantic import BaseModel, Field
from typing import Optional

from src.domain.value_objects.confidence_score import ConfidenceScore


class CandidatoVoto(BaseModel):
    numero: str = Field(..., description="Candidate number in list")
    nombre: str = Field(..., description="Candidate full name")
    votos: int = Field(..., description="Number of votes received")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence (0.0-1.0)")

    @classmethod
    def create(
        cls,
        numero: str,
        nombre: str,
        votos: int,
        confidence: ConfidenceScore
    ) -> "CandidatoVoto":
        return cls(
            numero=numero,
            nombre=nombre,
            votos=votos,
            confidence=confidence.value
        )

    def get_confidence_score(self) -> ConfidenceScore:
        return ConfidenceScore(self.confidence)

    class Config:
        frozen = True
