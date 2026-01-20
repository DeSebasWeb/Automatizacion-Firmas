"""E-14 electoral document schemas (DTOs)."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DivipolResponse(BaseModel):
    """DIVIPOL (electoral location) data."""
    departamento_codigo: str = Field(description="Department code (e.g., '16')")
    departamento_nombre: str = Field(description="Department name (e.g., 'BOGOTA D.C.')")
    municipio_codigo: str = Field(description="Municipality code (e.g., '001')")
    municipio_nombre: str = Field(description="Municipality name")
    lugar: str = Field(description="Location name (e.g., 'USAQUÉN')")
    zona: str = Field(description="Electoral zone")
    puesto: str = Field(description="Polling station")
    mesa: str = Field(description="Table/mesa number")


class CandidatoVotos(BaseModel):
    """Candidate vote data."""
    id: int = Field(description="Candidate ID (101-118, 201-206, 301-303)")
    votos: Optional[int] = Field(
        None,
        description="Votes received (null if no votes)"
    )


class PartidoResult(BaseModel):
    """Party voting results."""
    numero_lista: str = Field(description="Party list number (e.g., '0261')")
    nombre_partido: str = Field(description="Party name")
    tipo_voto: str = Field(
        description="Vote type: 'CON_VOTO_PREFERENTE' or 'SIN_VOTO_PREFERENTE'"
    )
    votos_agrupacion: int = Field(
        description="Votes for party list only (no candidate preference)"
    )
    candidatos: List[CandidatoVotos] = Field(
        default_factory=list,
        description="Individual candidate votes"
    )
    total: int = Field(description="Total votes for this party")


class VotosEspeciales(BaseModel):
    """Special vote types."""
    votos_blanco: int = Field(description="Blank votes")
    votos_nulos: int = Field(description="Null/invalid votes")
    votos_no_marcados: int = Field(description="Unmarked votes")


class E14Metadata(BaseModel):
    """E-14 document metadata."""
    pdf_filename: str = Field(description="Original filename")
    tipo_documento: str = Field(default="E-14", description="Document type")
    tipo_eleccion: str = Field(description="Election type: 'CAMARA' or 'SENADO'")
    processed_at: datetime = Field(description="Processing timestamp (UTC)")


class E14ProcessResult(BaseModel):
    """Complete E-14 processing result."""
    metadata: E14Metadata
    divipol: DivipolResponse
    partidos: List[PartidoResult]
    votos_especiales: VotosEspeciales

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "pdf_filename": "e14_camara_066.pdf",
                    "tipo_documento": "E-14",
                    "tipo_eleccion": "CAMARA",
                    "processed_at": "2025-01-21T10:30:00Z"
                },
                "divipol": {
                    "departamento_codigo": "16",
                    "departamento_nombre": "BOGOTA D.C.",
                    "municipio_codigo": "001",
                    "municipio_nombre": "BOGOTA. D.C.",
                    "lugar": "USAQUÉN",
                    "zona": "01",
                    "puesto": "01",
                    "mesa": "066"
                },
                "partidos": [
                    {
                        "numero_lista": "0261",
                        "nombre_partido": "COALICIÓN CENTRO ESPERANZA",
                        "tipo_voto": "CON_VOTO_PREFERENTE",
                        "votos_agrupacion": 0,
                        "candidatos": [
                            {"id": 101, "votos": None},
                            {"id": 106, "votos": 1}
                        ],
                        "total": 6
                    }
                ],
                "votos_especiales": {
                    "votos_blanco": 6,
                    "votos_nulos": 3,
                    "votos_no_marcados": 1
                }
            }
        }
