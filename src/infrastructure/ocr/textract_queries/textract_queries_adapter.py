import boto3
from typing import Dict, BinaryIO, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
import structlog

from .queries_builder import QueriesBuilder
from .tables_parser import TablesParser
from .results_assembler import ResultsAssembler

logger = structlog.get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


class OCRExtractionError(Exception):
    pass


class TextractQueriesAdapter:

    def __init__(
        self,
        textract_client: boto3.client,
        queries_builder: QueriesBuilder,
        tables_parser: TablesParser,
        results_assembler: ResultsAssembler,
        max_queries_per_batch: int = 15
    ):
        self.client = textract_client
        self.queries_builder = queries_builder
        self.tables_parser = tables_parser
        self.results_assembler = results_assembler
        self.max_queries_per_batch = max_queries_per_batch

    async def extract_e14_data(self, document: BinaryIO) -> Dict:
        try:
            logger.info("textract_extraction_started")

            document_bytes = document.read()

            logger.info("document_loaded", size_bytes=len(document_bytes))

            logger.info("analyzing_combined")
            tables_response, query_results = await self._analyze_combined(document_bytes)

            structure = self.tables_parser.parse_structure(tables_response)

            logger.info("structure_detected",
                       num_partidos=structure.get('num_partidos', 0),
                       tipo_eleccion=structure.get('tipo_eleccion'))

            logger.info("assembling_results")
            result = self.results_assembler.assemble(
                structure=structure,
                query_results=query_results
            )

            logger.info("textract_extraction_completed")

            return result

        except Exception as e:
            logger.error("textract_extraction_failed", error=str(e))
            raise OCRExtractionError(f"Failed to extract E-14 data: {e}")

    async def _analyze_combined(self, document_bytes: bytes) -> tuple:
        loop = asyncio.get_event_loop()

        logger.info("step_1_analyzing_tables")
        tables_response = await loop.run_in_executor(
            _executor,
            lambda: self.client.analyze_document(
                Document={'Bytes': document_bytes},
                FeatureTypes=['TABLES']
            )
        )

        structure = self.tables_parser.parse_structure(tables_response)

        logger.info("step_2_building_queries")
        queries = self.queries_builder.build_queries(structure)

        logger.info("step_3_executing_queries", total_queries=len(queries))

        if len(queries) == 0:
            logger.warning("no_queries_to_execute")
            return tables_response, {}

        query_results = await self._execute_queries(document_bytes, queries)

        return tables_response, query_results

    async def _execute_queries(
        self,
        document_bytes: bytes,
        queries: List[Dict]
    ) -> Dict:
        all_results = {}
        batch_size = self.max_queries_per_batch
        loop = asyncio.get_event_loop()

        for i in range(0, len(queries), batch_size):
            batch = queries[i:i+batch_size]

            logger.info("executing_query_batch",
                        batch_num=i//batch_size + 1,
                        queries_count=len(batch),
                        sample_query=batch[0] if batch else None,
                        all_queries=batch)

            try:
                response = await loop.run_in_executor(
                    _executor,
                    lambda b=batch: self.client.analyze_document(
                        Document={'Bytes': document_bytes},
                        FeatureTypes=['QUERIES'],
                        QueriesConfig={'Queries': b}
                    )
                )

                # Log raw blocks for debugging
                query_blocks = [b for b in response.get('Blocks', []) if b['BlockType'] == 'QUERY']
                result_blocks = [b for b in response.get('Blocks', []) if b['BlockType'] == 'QUERY_RESULT']

                logger.info("raw_textract_response",
                           batch_num=i//batch_size + 1,
                           num_query_blocks=len(query_blocks),
                           num_result_blocks=len(result_blocks),
                           sample_query_block=query_blocks[0] if query_blocks else None,
                           sample_result_block=result_blocks[0] if result_blocks else None)

                batch_results = self._parse_query_results(response)

                logger.info("query_batch_results",
                           batch_num=i//batch_size + 1,
                           results_count=len(batch_results),
                           sample_results=dict(list(batch_results.items())[:3]) if batch_results else {})

                all_results.update(batch_results)

            except Exception as e:
                logger.error("query_batch_failed",
                            batch_num=i//batch_size + 1,
                            error=str(e),
                            batch_queries=batch)
                raise

        return all_results

    def _parse_query_results(self, response: Dict) -> Dict:
        results = {}

        # Build mapping: QUERY_RESULT block ID → answer data
        result_blocks = {}
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'QUERY_RESULT':
                block_id = block.get('Id')
                result_blocks[block_id] = {
                    'answer': block.get('Text', ''),
                    'confidence': block.get('Confidence', 0)
                }

        # Match QUERY blocks with their QUERY_RESULT using Relationships
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'QUERY':
                alias = block.get('Query', {}).get('Alias', '')

                # Get QUERY_RESULT IDs from Relationships
                for relationship in block.get('Relationships', []):
                    if relationship.get('Type') == 'ANSWER':
                        for result_id in relationship.get('Ids', []):
                            if result_id in result_blocks:
                                results[alias] = result_blocks[result_id]
                                break

        return results
