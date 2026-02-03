import pytest
from src.infrastructure.ocr.textract_queries.tables_parser import TablesParser


def test_is_partido_table_with_valid_partido():
    parser = TablesParser()

    table = {
        'text_content': ['0017', 'PARTIDO CONSERVADOR', 'AGRUPACIÓN POLÍTICA', 'LISTA']
    }

    assert parser._is_partido_table(table) is True


def test_is_partido_table_without_codigo():
    parser = TablesParser()

    table = {
        'text_content': ['PARTIDO', 'AGRUPACIÓN POLÍTICA', 'LISTA']
    }

    assert parser._is_partido_table(table) is False


def test_has_candidatos_with_preferente():
    parser = TablesParser()

    table = {
        'text_content': ['101', '102', 'CON VOTO PREFERENTE']
    }

    assert parser._has_candidatos(table) is True


def test_has_candidatos_sin_preferente():
    parser = TablesParser()

    table = {
        'text_content': ['SIN VOTO PREFERENTE', '0001']
    }

    assert parser._has_candidatos(table) is False


def test_extract_candidatos():
    parser = TablesParser()

    table = {
        'text_content': ['101 15', '102 8', '103 12']
    }

    candidatos = parser._extract_candidatos(table)

    assert len(candidatos) == 3
    assert candidatos[0]['id'] == '101'
    assert candidatos[1]['id'] == '102'
    assert candidatos[2]['id'] == '103'


def test_detect_election_type_senado():
    parser = TablesParser()

    blocks = [
        {'BlockType': 'LINE', 'Text': 'SENADO DE LA REPÚBLICA'},
        {'BlockType': 'LINE', 'Text': 'FORMATO E-14'}
    ]

    tipo = parser._detect_election_type(blocks)

    assert tipo == 'SENADO'


def test_detect_election_type_camara():
    parser = TablesParser()

    blocks = [
        {'BlockType': 'LINE', 'Text': 'CÁMARA DE REPRESENTANTES'},
        {'BlockType': 'LINE', 'Text': 'FORMATO E-14'}
    ]

    tipo = parser._detect_election_type(blocks)

    assert tipo == 'CAMARA'


def test_parse_structure_empty():
    parser = TablesParser()

    tables_response = {
        'Blocks': []
    }

    structure = parser.parse_structure(tables_response)

    assert structure['num_partidos'] == 0
    assert structure['tipo_eleccion'] is None
    assert len(structure['partidos']) == 0
