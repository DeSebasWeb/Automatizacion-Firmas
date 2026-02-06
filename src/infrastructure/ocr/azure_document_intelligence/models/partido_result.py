from pydantic import BaseModel, Field
from typing import List, Optional

from .candidato_voto import CandidatoVoto


class PartidoResult(BaseModel):
    partido: str = Field(..., description="Political party name")
    numero_lista: str = Field(..., description="List number")
    votos_partido: int = Field(..., description="Total votes for party list")
    candidatos: List[CandidatoVoto] = Field(default_factory=list, description="List of candidates with votes")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence (0.0-1.0)")

    class Config:
        frozen = True
