from typing import Any, Dict, List, Set
import structlog

logger = structlog.get_logger(__name__)


class AzureResponseCleaner:

    FIELDS_TO_REMOVE: Set[str] = {
        'boundingRegions',
        'spans',
        'polygon',
        'pageNumber',
        'offset',
        'length'
    }

    def clean(self, data: Any) -> Any:
        if isinstance(data, dict):
            return self._clean_dict(data)
        elif isinstance(data, list):
            return self._clean_list(data)
        else:
            return data

    def _clean_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}

        for key, value in data.items():
            if key in self.FIELDS_TO_REMOVE:
                continue

            cleaned[key] = self.clean(value)

        return cleaned

    def _clean_list(self, data: List[Any]) -> List[Any]:
        return [self.clean(item) for item in data]

    def count_fields(self, data: Any, level: int = 0) -> int:
        if isinstance(data, dict):
            count = len(data)
            for value in data.values():
                count += self.count_fields(value, level + 1)
            return count
        elif isinstance(data, list):
            count = 0
            for item in data:
                count += self.count_fields(item, level + 1)
            return count
        else:
            return 0


class AzureResponseValidator:

    @staticmethod
    def validate_response(response: Dict[str, Any]) -> bool:
        if "analyzeResult" in response:
            try:
                fields = response["analyzeResult"]["documents"][0]["fields"]
                if not isinstance(fields, dict):
                    logger.warning(
                        "Invalid response: fields is not a dictionary",
                        fields_type=type(fields).__name__
                    )
                    return False
                return True
            except (KeyError, IndexError, TypeError) as e:
                logger.error(
                    "Invalid Azure DI response structure (analyzeResult format)",
                    error=str(e),
                    error_type=type(e).__name__
                )
                return False
        elif "documents" in response:
            try:
                fields = response["documents"][0]["fields"]
                if not isinstance(fields, dict):
                    logger.warning(
                        "Invalid response: fields is not a dictionary",
                        fields_type=type(fields).__name__
                    )
                    return False
                return True
            except (KeyError, IndexError, TypeError) as e:
                logger.error(
                    "Invalid Azure DI response structure (documents format)",
                    error=str(e),
                    error_type=type(e).__name__
                )
                return False
        else:
            logger.error("Invalid Azure DI response: missing 'analyzeResult' or 'documents'")
            return False

    @staticmethod
    def extract_fields(response: Dict[str, Any]) -> Dict[str, Any]:
        if not AzureResponseValidator.validate_response(response):
            raise ValueError("Invalid Azure DI response structure")

        if "analyzeResult" in response:
            return response["analyzeResult"]["documents"][0]["fields"]
        else:
            return response["documents"][0]["fields"]


class CleaningVerifier:

    def __init__(self, cleaner: AzureResponseCleaner):
        self.cleaner = cleaner

    def verify_cleaning(
        self,
        original: Dict[str, Any],
        cleaned: Dict[str, Any]
    ) -> Dict[str, Any]:
        original_count = self.cleaner.count_fields(original)
        cleaned_count = self.cleaner.count_fields(cleaned)
        removed_count = original_count - cleaned_count

        retention_rate = (
            (cleaned_count / original_count * 100)
            if original_count > 0
            else 0
        )

        stats = {
            "original_fields": original_count,
            "cleaned_fields": cleaned_count,
            "removed_fields": removed_count,
            "retention_rate": round(retention_rate, 2)
        }

        logger.info(
            "Cleaning verification complete",
            **stats
        )

        return stats
