import pytest
from src.infrastructure.ocr.textract_queries.queries_builder import QueriesBuilder


def test_build_metadata_queries():
    builder = QueriesBuilder()
    queries = builder._build_metadata_queries()

    assert len(queries) == 6
    assert any('page number' in q['Text'] for q in queries)
    assert any('department code' in q['Text'] for q in queries)
    assert any('municipality code' in q['Text'] for q in queries)
    assert any('zone number' in q['Text'] for q in queries)
    assert any('mesa' in q['Text'].lower() for q in queries)
    assert any('SENADO or CAMARA' in q['Text'] for q in queries)


def test_build_totales_queries():
    builder = QueriesBuilder()
    queries = builder._build_totales_queries()

    assert len(queries) == 3
    assert any('SUFRAGANTES' in q['Text'] for q in queries)
    assert any('VOTOS EN LA URNA' in q['Text'] for q in queries)
    assert any('INCINERADOS' in q['Text'] for q in queries)


def test_build_partido_queries():
    builder = QueriesBuilder()
    structure = {
        'partidos': [
            {'codigo': '0013'},
            {'codigo': '0255'}
        ]
    }

    queries = builder._build_partido_queries(structure)

    assert len(queries) == 6
    assert any('0013' in q['Text'] for q in queries)
    assert any('0255' in q['Text'] for q in queries)


def test_build_queries_complete():
    builder = QueriesBuilder()
    structure = {
        'partidos': [
            {'codigo': '0017'},
            {'codigo': '0002'},
            {'codigo': '0001'}
        ]
    }

    queries = builder.build_queries(structure)

    assert len(queries) == 6 + 3 + (3 * 3)
    aliases = [q['Alias'] for q in queries]

    assert 'pagina' in aliases
    assert 'total_sufragantes' in aliases
    assert 'partido_1_nombre' in aliases
    assert 'partido_1_tipo_lista' in aliases
    assert 'partido_1_votos_agrupacion' in aliases


def test_build_queries_empty_partidos():
    builder = QueriesBuilder()
    structure = {
        'partidos': []
    }

    queries = builder.build_queries(structure)

    assert len(queries) == 6 + 3
