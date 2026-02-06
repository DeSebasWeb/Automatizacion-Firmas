import pytest
from src.infrastructure.ocr.azure_document_intelligence.models.tipo_lista import TipoLista


class TestTipoLista:
    def test_from_string_senado(self):
        result = TipoLista.from_string("SENADO")
        assert result == TipoLista.SENADO

    def test_from_string_camara(self):
        result = TipoLista.from_string("CAMARA")
        assert result == TipoLista.CAMARA

    def test_from_string_camara_with_accent(self):
        result = TipoLista.from_string("CÁMARA")
        assert result == TipoLista.CAMARA

    def test_from_string_case_insensitive(self):
        result = TipoLista.from_string("senado")
        assert result == TipoLista.SENADO

        result = TipoLista.from_string("Cámara")
        assert result == TipoLista.CAMARA

    def test_from_string_with_whitespace(self):
        result = TipoLista.from_string("  SENADO  ")
        assert result == TipoLista.SENADO

    def test_from_string_invalid_value(self):
        with pytest.raises(ValueError):
            TipoLista.from_string("INVALID")

    def test_from_string_empty_value(self):
        with pytest.raises(ValueError):
            TipoLista.from_string("")
