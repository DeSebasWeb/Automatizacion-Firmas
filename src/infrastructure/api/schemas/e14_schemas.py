"""E-14 electoral document schemas (DTOs)."""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
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


# ===== TEXTRACT SCHEMAS =====


class CandidatoTextract(BaseModel):
    """Candidato extraído por Textract."""
    idcandidato: str = Field(description="ID del candidato (3 dígitos: 101-999)")
    votos: str = Field(description="Votos recibidos (puede contener símbolos)")
    necesita_auditoria: bool = Field(description="True si contiene símbolos no numéricos")


class PartidoTextract(BaseModel):
    """Partido extraído por Textract."""
    numPartido: str = Field(description="Número de partido (formato 0XXX)")
    nombrePartido: str = Field(description="Nombre del partido en mayúsculas")
    tipoDeVoto: str = Field(description="ListaConVotoPreferente o ListaSinVotoPreferente")
    id: str = Field(default="0", description="ID del partido (siempre '0')")
    votosSoloPorLaAgrupacionPolitica: str = Field(
        description="Votos solo por la agrupación (puede contener símbolos)"
    )
    candidatos: List[CandidatoTextract] = Field(
        default_factory=list,
        description="Lista de candidatos (solo si tiene voto preferente)"
    )
    TotalVotosAgrupacion_VotosCandidatos: str = Field(
        alias="TotalVotosAgrupacion+VotosCandidatos",
        description="Total de votos del partido (puede contener símbolos)"
    )
    necesita_auditoria: bool = Field(description="True si algún campo necesita revisión manual")

    class Config:
        populate_by_name = True


class DivipolTextract(BaseModel):
    """DIVIPOL extraído por Textract."""
    CodDep: str = Field(default="", description="Código de departamento")
    CodMun: str = Field(default="", description="Código de municipio")
    zona: str = Field(default="", description="Zona electoral")
    Puesto: str = Field(default="", description="Número de puesto")
    Mesa: str = Field(default="", description="Número de mesa")


class E14DataTextract(BaseModel):
    """Datos completos de E-14 extraídos por Textract."""
    pagina: str = Field(description="Número de página (formato: '01 de 09')")
    divipol: DivipolTextract
    TotalSufragantesE14: str = Field(default="", description="Total de sufragantes")
    TotalVotosEnUrna: str = Field(default="", description="Total de votos en urna")
    TotalIncinerados: str = Field(default="***", description="Total incinerados (puede ser símbolos)")
    Partido: List[PartidoTextract] = Field(default_factory=list, description="Lista de partidos")


class E14TextractResponse(BaseModel):
    """Respuesta completa del procesamiento con Textract."""
    success: bool = Field(description="True si el procesamiento fue exitoso")
    structured_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Datos estructurados en formato JSON (contiene clave 'e14')"
    )
    raw_ocr_text: str = Field(description="Texto completo extraído por AWS Textract")
    warnings: List[str] = Field(
        default_factory=list,
        description="Lista de advertencias y campos que necesitan auditoría"
    )
    processing_time_ms: int = Field(description="Tiempo de procesamiento en milisegundos")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "structured_data": {
                    "e14": {
                        "pagina": "01 de 09",
                        "divipol": {
                            "CodDep": "16",
                            "CodMun": "001",
                            "zona": "01",
                            "Puesto": "01",
                            "Mesa": "001"
                        },
                        "TotalSufragantesE14": "134",
                        "TotalVotosEnUrna": "131",
                        "TotalIncinerados": "***",
                        "Partido": [
                            {
                                "numPartido": "0261",
                                "nombrePartido": "COALICION CENTRO ESPERANZA",
                                "tipoDeVoto": "ListaConVotoPreferente",
                                "id": "0",
                                "votosSoloPorLaAgrupacionPolitica": "1",
                                "candidatos": [
                                    {
                                        "idcandidato": "101",
                                        "votos": "2",
                                        "necesita_auditoria": False
                                    }
                                ],
                                "TotalVotosAgrupacion+VotosCandidatos": "4",
                                "necesita_auditoria": False
                            }
                        ]
                    }
                },
                "raw_ocr_text": "FORMATO E-14\nPAGINA 01 de 09\nZONA: 01\nPUESTO: 01\nMESA: 001\n...",
                "warnings": [],
                "processing_time_ms": 1234
            }
        }
