import pytest
from src.infrastructure.ocr.textract.parsers.candidato_state_machine import CandidatoStateMachine


class TestCandidatoStateMachine:

    def test_caso_simbolos_multiples(self):
        machine = CandidatoStateMachine(page_offset=100)
        tokens = ["101", "/", "/", "/", "*", "1", "103"]
        candidatos = machine.parse_candidatos(tokens)

        assert len(candidatos) == 2
        assert candidatos[0]["idcandidato"] == "101"
        assert candidatos[0]["votos"] == "1"
        assert candidatos[0]["necesita_auditoria"] == True
        assert candidatos[1]["idcandidato"] == "103"

    def test_caso_candidato_sin_voto(self):
        machine = CandidatoStateMachine(page_offset=100)
        candidatos = machine.parse_candidatos(["101", "103", "105"])

        assert len(candidatos) == 3
        assert all(c["votos"] == "0" for c in candidatos)
        assert all(c["necesita_auditoria"] for c in candidatos)

    def test_caso_offset_variable(self):
        machine = CandidatoStateMachine(page_offset=200)
        candidatos = machine.parse_candidatos(["201", "5", "203", "12"])

        assert len(candidatos) == 2
        assert candidatos[0]["idcandidato"] == "201"
        assert candidatos[0]["votos"] == "5"
        assert candidatos[1]["idcandidato"] == "203"
        assert candidatos[1]["votos"] == "12"

    def test_caso_letra_o(self):
        machine = CandidatoStateMachine(page_offset=100)
        candidatos = machine.parse_candidatos(["1O1", "5"])

        assert candidatos[0]["idcandidato"] == "101"
        assert candidatos[0]["votos"] == "5"

    def test_caso_candidatos_consecutivos_con_votos(self):
        machine = CandidatoStateMachine(page_offset=100)
        candidatos = machine.parse_candidatos(["101", "2", "102", "3", "103", "1"])

        assert len(candidatos) == 3
        assert candidatos[0]["idcandidato"] == "101"
        assert candidatos[0]["votos"] == "2"
        assert candidatos[1]["idcandidato"] == "102"
        assert candidatos[1]["votos"] == "3"
        assert candidatos[2]["idcandidato"] == "103"
        assert candidatos[2]["votos"] == "1"

    def test_caso_solo_simbolos_sin_votos(self):
        machine = CandidatoStateMachine(page_offset=100)
        candidatos = machine.parse_candidatos(["101", "/", "/", "103", "*"])

        assert len(candidatos) == 2
        assert candidatos[0]["votos"] == "0"
        assert candidatos[1]["votos"] == "0"
        assert all(c["necesita_auditoria"] for c in candidatos)

    def test_caso_offset_300(self):
        machine = CandidatoStateMachine(page_offset=300)
        candidatos = machine.parse_candidatos(["301", "10", "305", "2"])

        assert len(candidatos) == 2
        assert candidatos[0]["idcandidato"] == "301"
        assert candidatos[0]["votos"] == "10"
        assert candidatos[1]["idcandidato"] == "305"
        assert candidatos[1]["votos"] == "2"

    def test_caso_vacio(self):
        machine = CandidatoStateMachine(page_offset=100)
        candidatos = machine.parse_candidatos([])

        assert len(candidatos) == 0

    def test_caso_ultimo_candidato_sin_voto(self):
        machine = CandidatoStateMachine(page_offset=100)
        candidatos = machine.parse_candidatos(["101", "5", "102"])

        assert len(candidatos) == 2
        assert candidatos[0]["votos"] == "5"
        assert candidatos[1]["votos"] == "0"
        assert candidatos[1]["razon_auditoria"] == "fin_de_bloque"
