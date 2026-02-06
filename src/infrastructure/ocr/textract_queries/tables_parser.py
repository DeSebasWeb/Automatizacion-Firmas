from typing import Dict, List, Optional
import structlog
import re

logger = structlog.get_logger(__name__)


class TablesParser:

    def parse_structure(self, tables_response: Dict) -> Dict:
        structure = {
            'num_partidos': 0,
            'tipo_eleccion': None,
            'partidos': []
        }

        blocks = tables_response.get('Blocks', [])

        tables = self._extract_tables(blocks)

        for table in tables:
            if self._is_partido_table(table):
                partido = self._parse_partido_table(table)
                if partido:
                    structure['partidos'].append(partido)

        structure['num_partidos'] = len(structure['partidos'])
        structure['tipo_eleccion'] = self._detect_election_type(blocks)

        logger.info("structure_parsed",
                   num_partidos=structure['num_partidos'],
                   tipo_eleccion=structure['tipo_eleccion'])

        return structure

    def _extract_tables(self, blocks: List[Dict]) -> List[Dict]:
        block_map = {block['Id']: block for block in blocks}

        tables = []

        for block in blocks:
            if block['BlockType'] == 'TABLE':
                table = {
                    'id': block['Id'],
                    'cells': [],
                    'text_content': []
                }

                relationships = block.get('Relationships', [])
                for rel in relationships:
                    if rel['Type'] == 'CHILD':
                        for child_id in rel['Ids']:
                            child_block = block_map.get(child_id)
                            if child_block and child_block['BlockType'] == 'CELL':
                                cell_text = self._get_cell_text(child_block, block_map)
                                table['cells'].append({
                                    'text': cell_text,
                                    'row': child_block.get('RowIndex', 0),
                                    'col': child_block.get('ColumnIndex', 0)
                                })
                                if cell_text:
                                    table['text_content'].append(cell_text)

                tables.append(table)

        return tables

    def _get_cell_text(self, cell_block: Dict, block_map: Dict) -> str:
        text_parts = []

        relationships = cell_block.get('Relationships', [])
        for rel in relationships:
            if rel['Type'] == 'CHILD':
                for child_id in rel['Ids']:
                    child_block = block_map.get(child_id)
                    if child_block and child_block['BlockType'] == 'WORD':
                        text_parts.append(child_block.get('Text', ''))

        return ' '.join(text_parts)

    def _is_partido_table(self, table: Dict) -> bool:
        text_content = ' '.join(table.get('text_content', [])).upper()

        has_partido_code = bool(re.search(r'\b0\d{3}\b', text_content))
        has_agrupacion = 'AGRUPACI' in text_content or 'AGRUPACION' in text_content
        has_lista = 'LISTA' in text_content

        return has_partido_code and (has_agrupacion or has_lista)

    def _parse_partido_table(self, table: Dict) -> Optional[Dict]:
        text_content = ' '.join(table.get('text_content', []))

        codigo_match = re.search(r'\b(0\d{3})\b', text_content)
        if not codigo_match:
            return None

        codigo = codigo_match.group(1)

        tiene_candidatos = self._has_candidatos(table)
        candidatos = []

        if tiene_candidatos:
            candidatos = self._extract_candidatos(table)

        total = self._extract_total(table)

        partido = {
            'codigo': codigo,
            'tiene_candidatos': tiene_candidatos,
            'candidatos': candidatos,
            'total': total
        }

        return partido

    def _has_candidatos(self, table: Dict) -> bool:
        text_content = ' '.join(table.get('text_content', [])).upper()

        has_candidato_ids = bool(re.search(r'\b1\d{2}\b', text_content))

        has_preferente = 'PREFERENTE' in text_content or 'CON VOTO' in text_content

        return has_candidato_ids and has_preferente

    def _extract_candidatos(self, table: Dict) -> List[Dict]:
        candidatos = []

        text_content = ' '.join(table.get('text_content', []))

        candidato_ids = re.findall(r'\b(1\d{2})\b', text_content)

        for cid in candidato_ids:
            candidatos.append({
                'id': cid,
                'votos': '0'
            })

        return candidatos

    def _extract_total(self, table: Dict) -> str:
        cells = table.get('cells', [])

        for cell in cells:
            cell_text = cell.get('text', '').upper()
            if 'TOTAL' in cell_text:
                match = re.search(r'\b(\d{1,3})\b', cell_text)
                if match:
                    return match.group(1)

        return '0'

    def _detect_election_type(self, blocks: List[Dict]) -> Optional[str]:
        for block in blocks:
            if block['BlockType'] == 'LINE':
                text = block.get('Text', '').upper()
                if 'SENADO' in text:
                    return 'SENADO'
                if 'CÁMARA' in text or 'CAMARA' in text:
                    return 'CAMARA'

        return None
