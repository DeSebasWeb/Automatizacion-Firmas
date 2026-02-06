import pytest
from src.infrastructure.ocr.azure_document_intelligence.parsers.parsing_utils import ParsingUtils


class TestParsingUtils:

    def test_parse_votos_preserve_format_with_empty_string(self):
        assert ParsingUtils.parse_votos_preserve_format("") == "---"

    def test_parse_votos_preserve_format_with_whitespace(self):
        assert ParsingUtils.parse_votos_preserve_format("   ") == "---"

    def test_parse_votos_preserve_format_with_dashes(self):
        assert ParsingUtils.parse_votos_preserve_format("---") == "---"
        assert ParsingUtils.parse_votos_preserve_format("--") == "--"

    def test_parse_votos_preserve_format_with_asterisks(self):
        assert ParsingUtils.parse_votos_preserve_format("***") == "***"

    def test_parse_votos_preserve_format_with_slashes(self):
        assert ParsingUtils.parse_votos_preserve_format("///") == "///"

    def test_parse_votos_preserve_format_with_digits_only(self):
        assert ParsingUtils.parse_votos_preserve_format("123") == "123"

    def test_parse_votos_preserve_format_with_mixed_format(self):
        assert ParsingUtils.parse_votos_preserve_format("-- 4-") == "4"
        assert ParsingUtils.parse_votos_preserve_format("1-2") == "12"
        assert ParsingUtils.parse_votos_preserve_format("  - 17  ") == "17"

    def test_extract_page_number_from_pag(self):
        assert ParsingUtils.extract_page_number("TipoDeVotoPartido1Pag4") == 4
        assert ParsingUtils.extract_page_number("DivipolPag10") == 10

    def test_extract_page_number_from_pagina(self):
        assert ParsingUtils.extract_page_number("Pagina5") == 5
        assert ParsingUtils.extract_page_number("Pagina11") == 11

    def test_extract_page_number_from_partidohoja(self):
        assert ParsingUtils.extract_page_number("PartidoHoja2") == 2
        assert ParsingUtils.extract_page_number("PartidoHoja9") == 9

    def test_extract_page_number_returns_none_for_invalid(self):
        assert ParsingUtils.extract_page_number("TipoDeDocumento") is None
        assert ParsingUtils.extract_page_number("SomeRandomField") is None

    def test_extract_partido_number_from_tipo_voto(self):
        assert ParsingUtils.extract_partido_number("TipoDeVotoPartido1Pag4") == 1
        assert ParsingUtils.extract_partido_number("TipoDeVotoPartido3Pag5") == 3

    def test_extract_partido_number_from_total(self):
        assert ParsingUtils.extract_partido_number("TotalVotosAgrupacion+VotosCandidatosPrt1Pag7") == 1
        assert ParsingUtils.extract_partido_number("TotalVotosAgrupacion+VotosCandidatosPtd1Pag6") == 1

    def test_is_table_field(self):
        assert ParsingUtils.is_table_field("PartidoHoja2") is True
        assert ParsingUtils.is_table_field("Partido3Pagina10") is True
        assert ParsingUtils.is_table_field("ConsolidadoVotos2Pag11") is True
        assert ParsingUtils.is_table_field("TipoDeVotoPartido1Pag1") is False

    def test_is_partido_field(self):
        assert ParsingUtils.is_partido_field("TipoDeVotoPartido1Pag1") is True
        assert ParsingUtils.is_partido_field("TipoDeVotoPartido2Pag4") is True
        assert ParsingUtils.is_partido_field("PartidoHoja2") is False

    def test_is_total_field(self):
        assert ParsingUtils.is_total_field("TotalVotosAgrupacion+VotosCandidatosPag2") is True
        assert ParsingUtils.is_total_field("TotalVotosUrna") is False

    def test_is_consolidado_field(self):
        assert ParsingUtils.is_consolidado_field("ConsolidadoVotos2Pag11") is True
        assert ParsingUtils.is_consolidado_field("TotalSufragantes") is False

    def test_parse_divipol(self):
        value = "DEPARTAMENTO: 72\nMUNICIPIO: 006\nZONA: 99 PUESTO: 48 MESA: 001"
        result = ParsingUtils.parse_divipol(value)

        assert result["CodDep"] == "72"
        assert result["CodMun"] == "006"
        assert result["zona"] == "99"
        assert result["Puesto"] == "48"
        assert result["Mesa"] == "001"

    def test_parse_divipol_returns_empty_for_invalid(self):
        result = ParsingUtils.parse_divipol("Invalid format")
        assert result == {}

    def test_format_page_number(self):
        assert ParsingUtils.format_page_number(1) == "01 de 11"
        assert ParsingUtils.format_page_number(5) == "05 de 11"
        assert ParsingUtils.format_page_number(11) == "11 de 11"

    def test_extract_total_from_string(self):
        assert ParsingUtils.extract_total_from_string(
            "TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS -- 9"
        ) == "9"
        assert ParsingUtils.extract_total_from_string(
            "TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS 1-2"
        ) == "12"
        assert ParsingUtils.extract_total_from_string(
            "TOTAL = VOTOS AGRUPACIÓN + VOTOS CANDIDATOS\n---"
        ) == "---"
