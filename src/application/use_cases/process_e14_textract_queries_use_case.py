from typing import BinaryIO, Dict
import structlog

logger = structlog.get_logger(__name__)


class ProcessE14TextractQueriesUseCase:

    def __init__(self, textract_adapter):
        self.textract_adapter = textract_adapter

    async def execute(self, document: BinaryIO) -> Dict:
        logger.info("use_case_started", use_case="process_e14_textract_queries")

        try:
            result = await self.textract_adapter.extract_e14_data(document)

            logger.info("use_case_completed", use_case="process_e14_textract_queries")

            return result

        except Exception as e:
            logger.error("use_case_failed",
                        use_case="process_e14_textract_queries",
                        error=str(e))
            raise
