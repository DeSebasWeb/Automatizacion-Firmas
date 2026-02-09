import pytest
import json
from pathlib import Path
from src.infrastructure.ocr.azure_document_intelligence.parsers.e14_senado_parser import E14SenadoParser


class TestE14SenadoIntegration:

    @pytest.fixture
    def real_fields(self):
        test_data_path = Path(__file__).parent.parent.parent / "temp" / "cleaned_fields.json"

        if not test_data_path.exists():
            pytest.skip(f"Test data not found: {test_data_path}")

        with open(test_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("fields", {})

    def test_parseo_completo_con_datos_reales(self, real_fields):
        parser = E14SenadoParser()

        result = parser.parse(real_fields)

        assert "e14" in result
        e14_data = result["e14"]

        assert "pagina" in e14_data
        assert "divipol" in e14_data
        assert "Partido" in e14_data

    def test_partido_sin_voto_preferente_no_tiene_campo_total(self, real_fields):
        parser = E14SenadoParser()

        result = parser.parse(real_fields)
        e14_data = result["e14"]

        partidos_sin_voto = []
        partidos_sin_voto.extend([p for p in e14_data.get("Partido", [])
                                  if p.get("tipoDeVoto") == "ListaSinVotoPreferente"])

        for page_num in range(2, 12):
            partido_key = f"Partido{page_num}"
            if partido_key in e14_data:
                partidos_sin_voto.extend([p for p in e14_data[partido_key]
                                         if p.get("tipoDeVoto") == "ListaSinVotoPreferente"])

        assert len(partidos_sin_voto) > 0, "Debe haber al menos un partido sin voto preferente"

        for partido in partidos_sin_voto:
            assert "TotalVotosAgrupacion+VotosCandidatos" not in partido, \
                f"Partido {partido.get('nombrePartido')} no debe tener campo total"
            assert partido["candidatos"] == []

    def test_partido_con_voto_preferente_tiene_campo_total(self, real_fields):
        parser = E14SenadoParser()

        result = parser.parse(real_fields)
        e14_data = result["e14"]

        partidos_con_voto = []
        partidos_con_voto.extend([p for p in e14_data.get("Partido", [])
                                  if p.get("tipoDeVoto") == "ListaConVotoPreferente"])

        for page_num in range(2, 12):
            partido_key = f"Partido{page_num}"
            if partido_key in e14_data:
                partidos_con_voto.extend([p for p in e14_data[partido_key]
                                         if p.get("tipoDeVoto") == "ListaConVotoPreferente"])

        assert len(partidos_con_voto) > 0, "Debe haber al menos un partido con voto preferente"

        for partido in partidos_con_voto:
            assert "TotalVotosAgrupacion+VotosCandidatos" in partido, \
                f"Partido {partido.get('nombrePartido')} debe tener campo total"

    def test_total_sin_numero_partido_asignado_correctamente(self, real_fields):
        parser = E14SenadoParser()

        result = parser.parse(real_fields)
        e14_data = result["e14"]

        partido_pag2 = e14_data.get("Partido2", [])
        assert len(partido_pag2) == 1
        assert partido_pag2[0]["numPartido"] == "0255"
        assert partido_pag2[0]["TotalVotosAgrupacion+VotosCandidatos"] == "7"

        partido_pag3 = e14_data.get("Partido3", [])
        assert len(partido_pag3) == 1
        assert partido_pag3[0]["numPartido"] == "1140"
        assert partido_pag3[0]["TotalVotosAgrupacion+VotosCandidatos"] != "---"

    def test_estructura_json_completa(self, real_fields):
        parser = E14SenadoParser()

        result = parser.parse(real_fields)
        e14_data = result["e14"]

        assert "pagina" in e14_data
        assert "divipol" in e14_data
        assert "TotalSufragantesE14" in e14_data
        assert "TotalVotosEnUrna" in e14_data
        assert "TotalIncinerados" in e14_data

        assert "Partido" in e14_data
        assert isinstance(e14_data["Partido"], list)

        for page_num in range(2, 12):
            pagina_key = f"pagina{page_num}"
            divipol_key = f"divipol{page_num}"
            partido_key = f"Partido{page_num}"

            if partido_key in e14_data:
                assert pagina_key in e14_data
                assert divipol_key in e14_data
                assert isinstance(e14_data[partido_key], list)

    def test_validacion_tipos_de_voto(self, real_fields):
        parser = E14SenadoParser()

        result = parser.parse(real_fields)
        e14_data = result["e14"]

        tipos_validos = ["ListaConVotoPreferente", "ListaSinVotoPreferente"]

        for partido in e14_data.get("Partido", []):
            assert partido.get("tipoDeVoto") in tipos_validos

        for page_num in range(2, 12):
            partido_key = f"Partido{page_num}"
            if partido_key in e14_data:
                for partido in e14_data[partido_key]:
                    assert partido.get("tipoDeVoto") in tipos_validos

    def test_candidatos_solo_en_con_voto_preferente(self, real_fields):
        parser = E14SenadoParser()

        result = parser.parse(real_fields)
        e14_data = result["e14"]

        for partido in e14_data.get("Partido", []):
            if partido.get("tipoDeVoto") == "ListaSinVotoPreferente":
                assert partido["candidatos"] == []
            elif partido.get("tipoDeVoto") == "ListaConVotoPreferente":
                assert "candidatos" in partido

        for page_num in range(2, 12):
            partido_key = f"Partido{page_num}"
            if partido_key in e14_data:
                for partido in e14_data[partido_key]:
                    if partido.get("tipoDeVoto") == "ListaSinVotoPreferente":
                        assert partido["candidatos"] == []
                    elif partido.get("tipoDeVoto") == "ListaConVotoPreferente":
                        assert "candidatos" in partido
