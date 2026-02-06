from enum import Enum


class TipoLista(str, Enum):
    SENADO = "SENADO"
    CAMARA = "CAMARA"

    @classmethod
    def from_string(cls, value: str) -> "TipoLista":
        value_upper = value.strip().upper()
        if "SENADO" in value_upper:
            return cls.SENADO
        elif "CAMARA" in value_upper or "CÁMARA" in value_upper:
            return cls.CAMARA
        else:
            raise ValueError(f"Invalid TipoLista value: {value}")
