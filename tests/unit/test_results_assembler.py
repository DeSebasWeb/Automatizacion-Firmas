import pytest
from src.infrastructure.ocr.textract_queries.results_assembler import ResultsAssembler


def test_get_query_answer():
    assembler = ResultsAssembler()

    results = {
        'pagina': {'answer': '01 de 11', 'confidence': 99.5},
        'cod_dep': {'answer': '68', 'confidence': 98.2}
    }

    assert assembler._get_query_answer(results, 'pagina') == '01 de 11'
    assert assembler._get_query_answer(results, 'cod_dep') == '68'
    assert assembler._get_query_answer(results, 'missing', 'default') == 'default'


def test_normalize_tipo_voto():
    assembler = ResultsAssembler()

    assert assembler._normalize_tipo_voto('LISTA CON VOTO PREFERENTE') == 'ListaConVotoPreferente'
    assert assembler._normalize_tipo_voto('LISTA SIN VOTO PREFERENTE') == 'ListaSinVotoPreferente'
    assert assembler._normalize_tipo_voto('invalid') == ''


def test_normalize_votos():
    assembler = ResultsAssembler()

    assert assembler._normalize_votos('-') == '0'
    assert assembler._normalize_votos('/') == '0'
    assert assembler._normalize_votos('\\') == '0'
    assert assembler._normalize_votos('*') == '0'
    assert assembler._normalize_votos('#') == '0'
    assert assembler._normalize_votos('15') == '15'


def test_needs_audit_missing_nombre():
    assembler = ResultsAssembler()

    partido = {
        'nombrePartido': '',
        'votosSoloPorLaAgrupacionPolitica': '5'
    }

    assert assembler._needs_audit(partido) is True


def test_needs_audit_non_numeric_votos():
    assembler = ResultsAssembler()

    partido = {
        'nombrePartido': 'PARTIDO CONSERVADOR',
        'votosSoloPorLaAgrupacionPolitica': '***'
    }

    assert assembler._needs_audit(partido) is True


def test_needs_audit_valid():
    assembler = ResultsAssembler()

    partido = {
        'nombrePartido': 'PARTIDO CONSERVADOR',
        'votosSoloPorLaAgrupacionPolitica': '5'
    }

    assert assembler._needs_audit(partido) is False


def test_assemble_divipol():
    assembler = ResultsAssembler()

    query_results = {
        'cod_dep': {'answer': '68'},
        'cod_mun': {'answer': '001'},
        'zona': {'answer': '01'},
        'mesa': {'answer': '066'}
    }

    divipol = assembler._assemble_divipol(query_results)

    assert divipol['CodDep'] == '68'
    assert divipol['CodMun'] == '001'
    assert divipol['zona'] == '01'
    assert divipol['Mesa'] == '066'
    assert divipol['Puesto'] == ''


def test_assemble_candidatos_empty():
    assembler = ResultsAssembler()

    partido_structure = {
        'tiene_candidatos': False,
        'candidatos': []
    }

    candidatos = assembler._assemble_candidatos(partido_structure)

    assert len(candidatos) == 0


def test_assemble_candidatos_with_data():
    assembler = ResultsAssembler()

    partido_structure = {
        'tiene_candidatos': True,
        'candidatos': [
            {'id': '101', 'votos': '15'},
            {'id': '102', 'votos': '/'}
        ]
    }

    candidatos = assembler._assemble_candidatos(partido_structure)

    assert len(candidatos) == 2
    assert candidatos[0]['idcandidato'] == '101'
    assert candidatos[0]['votos'] == '15'
    assert candidatos[0]['necesita_auditoria'] is False
    assert candidatos[1]['idcandidato'] == '102'
    assert candidatos[1]['votos'] == '0'
    assert candidatos[1]['necesita_auditoria'] is True


def test_assemble_complete():
    assembler = ResultsAssembler()

    structure = {
        'num_partidos': 1,
        'tipo_eleccion': 'SENADO',
        'partidos': [
            {
                'codigo': '0017',
                'tiene_candidatos': False,
                'candidatos': [],
                'total': '5'
            }
        ]
    }

    query_results = {
        'pagina': {'answer': '01 de 11'},
        'cod_dep': {'answer': '68'},
        'cod_mun': {'answer': '001'},
        'zona': {'answer': '01'},
        'mesa': {'answer': '001'},
        'total_sufragantes': {'answer': '150'},
        'total_votos_urna': {'answer': '147'},
        'total_incinerados': {'answer': '***'},
        'partido_1_nombre': {'answer': 'PARTIDO CONSERVADOR'},
        'partido_1_tipo_lista': {'answer': 'LISTA SIN VOTO PREFERENTE'},
        'partido_1_votos_agrupacion': {'answer': '5'}
    }

    result = assembler.assemble(structure, query_results)

    assert result['e14']['pagina'] == '01 de 11'
    assert result['e14']['divipol']['CodDep'] == '68'
    assert result['e14']['TotalSufragantesE14'] == '150'
    assert len(result['e14']['Partido']) == 1
    assert result['e14']['Partido'][0]['numPartido'] == '0017'
    assert result['e14']['Partido'][0]['nombrePartido'] == 'PARTIDO CONSERVADOR'
