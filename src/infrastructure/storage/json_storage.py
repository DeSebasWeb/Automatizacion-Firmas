"""JSON storage utility for saving processing results."""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import structlog

from src.shared.logging import LoggerFactory

logger = LoggerFactory.get_infrastructure_logger("json_storage")


class JSONStorage:
    """
    Save processing results as JSON files for testing and validation.

    Creates timestamped JSON files in configured output directory.
    """

    def __init__(self, output_dir: str = "data/results"):
        """
        Initialize JSON storage.

        Args:
            output_dir: Directory to save JSON files (created if doesn't exist)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.debug("json_storage_initialized", output_dir=str(self.output_dir))

    def save_result(
        self,
        result: Dict,
        filename_prefix: Optional[str] = None
    ) -> str:
        """
        Save processing result as JSON file.

        Args:
            result: Dictionary with processing results
            filename_prefix: Optional prefix for filename

        Returns:
            Path to saved JSON file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate filename
        if filename_prefix:
            # Clean filename (remove extension if present)
            clean_prefix = Path(filename_prefix).stem
            filename = f"{clean_prefix}_{timestamp}.json"
        else:
            # Auto-generate from result data
            filename = self._generate_filename(result, timestamp)

        filepath = self.output_dir / filename

        # Save JSON
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info("result_saved", filepath=str(filepath), size=len(json.dumps(result)))

            return str(filepath)

        except Exception as e:
            logger.error("json_save_failed", error=str(e), filepath=str(filepath))
            raise RuntimeError(f"Failed to save JSON: {e}") from e

    def _generate_filename(self, result: Dict, timestamp: str) -> str:
        """
        Generate filename from result data.

        Args:
            result: Processing result dictionary
            timestamp: Timestamp string

        Returns:
            Generated filename
        """
        # Try to extract identifying info
        tipo_doc = result.get('metadata', {}).get('tipo_documento', 'document')

        if tipo_doc == 'E-14':
            # Use mesa number if available
            mesa = result.get('divipol', {}).get('mesa', 'unknown')
            return f"e14_mesa_{mesa}_{timestamp}.json"

        else:
            # Generic fallback
            return f"{tipo_doc.lower()}_{timestamp}.json"

    def list_results(self, pattern: str = "*.json") -> list[Path]:
        """
        List all JSON result files.

        Args:
            pattern: Glob pattern for filtering (default: "*.json")

        Returns:
            List of result file paths
        """
        files = list(self.output_dir.glob(pattern))
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

    def load_result(self, filename: str) -> Dict:
        """
        Load result from JSON file.

        Args:
            filename: Filename to load

        Returns:
            Result dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid
        """
        filepath = self.output_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Result file not found: {filename}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                result = json.load(f)

            logger.debug("result_loaded", filename=filename)

            return result

        except json.JSONDecodeError as e:
            logger.error("json_load_failed", error=str(e), filename=filename)
            raise ValueError(f"Invalid JSON in file: {e}") from e
