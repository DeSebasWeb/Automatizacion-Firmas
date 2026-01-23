"""
Base parser abstraction following SOLID principles.

This module defines the abstract base class for all E-14 parsers,
implementing the Template Method pattern and Strategy pattern.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class BaseParser(ABC):
    """
    Abstract base class for all E-14 parsers.

    Principles applied:
    - SRP (Single Responsibility): Each parser has single parsing responsibility
    - OCP (Open/Closed): Extensible via inheritance without modifying base
    - LSP (Liskov Substitution): All parsers are substitutable via this interface
    - ISP (Interface Segregation): Minimal interface - only parse() method required
    - DIP (Dependency Inversion): Depends on abstraction, not concrete implementations

    Design patterns:
    - Template Method: Defines parsing flow structure
    - Strategy: Each subclass is a parsing strategy
    - Observer: Structured logging with structlog
    """

    def __init__(self):
        """Initialize parser with structured logger."""
        self.logger = logger.bind(parser=self.__class__.__name__)
        self.warnings: List[str] = []

    @abstractmethod
    def parse(self, lines: List[str]) -> Dict[str, Any]:
        """
        Parse OCR lines and extract structured data.

        This is the main method that concrete parsers must implement.
        Each parser is responsible for extracting specific data from
        the OCR text lines.

        Args:
            lines: List of text lines from OCR output (horizontal extraction).
                  Lines are ordered left-to-right, top-to-bottom.

        Returns:
            Dictionary with extracted structured data. Structure depends on
            the specific parser implementation.

        Raises:
            Never raises exceptions for missing data. Returns empty dict
            with warnings logged instead.

        Examples:
            >>> parser = TotalesMesaParser()
            >>> lines = ["TOTAL", "TOTAL", "TOTAL", "SUFRAGANTES", ...]
            >>> result = parser.parse(lines)
            >>> print(result["TotalSufragantesE14"])
            "134"
        """
        pass

    def reset_warnings(self) -> None:
        """
        Clear accumulated warnings.

        Call this method before parsing a new document to reset
        the warning state.
        """
        self.warnings = []
        self.logger.debug("warnings_reset")

    def add_warning(self, message: str, **context) -> None:
        """
        Add a warning message with optional context.

        Warnings are accumulated and can be retrieved after parsing.
        They indicate non-critical issues like missing data or
        unexpected formats.

        Args:
            message: Warning message describing the issue
            **context: Additional context data for structured logging

        Examples:
            >>> parser.add_warning("campo_vacio", field="TotalIncinerados")
            >>> parser.add_warning("formato_inesperado", value="***", expected="numeric")
        """
        self.warnings.append(message)
        self.logger.warning(message, **context)

    def _validate_lines(self, lines: List[str]) -> bool:
        """
        Validate input lines are not empty.

        Args:
            lines: List of text lines to validate

        Returns:
            True if lines are valid (not None and not empty), False otherwise
        """
        if not lines:
            self.add_warning("input_vacio", lines_count=0)
            return False

        if not isinstance(lines, list):
            self.add_warning("input_invalido", type=type(lines).__name__)
            return False

        return True

    def _clean_line(self, line: str) -> str:
        """
        Clean a single line by stripping whitespace.

        Args:
            line: Text line to clean

        Returns:
            Cleaned line with leading/trailing whitespace removed
        """
        return line.strip() if isinstance(line, str) else ""

    def _find_line_index(
        self,
        lines: List[str],
        pattern: str,
        start: int = 0,
        case_sensitive: bool = False
    ) -> Optional[int]:
        """
        Find the first line containing a pattern.

        Args:
            lines: List of text lines to search
            pattern: Text pattern to find
            start: Index to start searching from (default: 0)
            case_sensitive: Whether search should be case-sensitive (default: False)

        Returns:
            Index of first line containing pattern, or None if not found

        Examples:
            >>> lines = ["TOTAL", "VOTOS", "SUFRAGANTES"]
            >>> parser._find_line_index(lines, "SUFRAGANTES")
            2
        """
        search_lines = lines[start:]

        if not case_sensitive:
            pattern = pattern.upper()
            search_lines = [line.upper() for line in search_lines]

        for i, line in enumerate(search_lines):
            if pattern in line:
                return start + i

        return None
