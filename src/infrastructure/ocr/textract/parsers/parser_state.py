from enum import Enum, auto


class ParserState(Enum):
    BUSCANDO_ID = auto()
    BUSCANDO_VOTO = auto()
    SIMBOLOS_INTERMEDIOS = auto()
