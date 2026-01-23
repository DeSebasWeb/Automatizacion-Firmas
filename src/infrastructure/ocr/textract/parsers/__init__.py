"""
E-14 Parsers Module.

Arquitectura modular siguiendo principios SOLID:
- BaseParser: Abstracción para todos los parsers
- TotalesMesaParser: Parser especializado en totales
- DivipolParser: Parser especializado en DIVIPOL
- PartidoParser: Parser especializado en partidos y candidatos
- PaginaParser: Parser especializado en número de página

Patrones de diseño:
- Strategy Pattern: Diferentes estrategias de parsing
- Template Method: BaseParser define el flujo, subclases implementan detalles
- Chain of Responsibility: Procesamiento secuencial del texto
"""

from .base_parser import BaseParser
from .totales_mesa_parser import TotalesMesaParser
from .divipol_parser import DivipolParser
from .partido_parser import PartidoParser
from .pagina_parser import PaginaParser

__all__ = [
    "BaseParser",
    "TotalesMesaParser",
    "DivipolParser",
    "PartidoParser",
    "PaginaParser",
]
