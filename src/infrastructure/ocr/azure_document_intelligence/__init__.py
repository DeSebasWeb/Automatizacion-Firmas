from .azure_di_adapter import AzureDocumentIntelligenceAdapter
from .models import TipoLista, CandidatoVoto, PartidoResult, E14Document
from .field_extractors import (
    TipoVotoExtractor,
    VotosExtractor,
    DivipolExtractor,
    TablaCandidatosExtractor,
)

__all__ = [
    "AzureDocumentIntelligenceAdapter",
    "TipoLista",
    "CandidatoVoto",
    "PartidoResult",
    "E14Document",
    "TipoVotoExtractor",
    "VotosExtractor",
    "DivipolExtractor",
    "TablaCandidatosExtractor",
]
