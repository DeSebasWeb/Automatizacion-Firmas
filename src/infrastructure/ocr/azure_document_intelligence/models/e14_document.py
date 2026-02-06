from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from .tipo_lista import TipoLista
from .partido_result import PartidoResult


class E14Document(BaseModel):
    tipo_lista: TipoLista = Field(..., description="Electoral list type")
    codigo_departamento: Optional[str] = Field(None, description="Department code (for CAMARA)")
    divipol: Dict[str, str] = Field(..., description="DIVIPOL geographic codes")
    votos_nulos: int = Field(..., description="Null votes")
    votos_no_marcados: int = Field(..., description="Unmarked votes")
    votos_blanco: int = Field(..., description="Blank votes")
    total_votos_validos: int = Field(..., description="Total valid votes")
    partidos: List[PartidoResult] = Field(default_factory=list, description="List of parties with results")
    confidence_promedio: float = Field(..., ge=0.0, le=1.0, description="Average OCR confidence")

    class Config:
        frozen = True
