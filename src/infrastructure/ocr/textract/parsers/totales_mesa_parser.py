"""
TotalesMesaParser - Specialized parser for extracting mesa totals from E-14 forms.

This parser extracts three critical totals from the horizontal OCR text:
- TotalSufragantesE14: Total number of voters
- TotalVotosEnUrna: Total votes in ballot box
- TotalIncinerados: Total incinerated votes (can be numbers, symbols, or corrupted text)

Algorithm:
1. Find 3 consecutive "TOTAL" keywords (within 5-line window)
2. Extract lines until end marker (CIRCUNSCRIPCIÓN, X-X-X-X pattern, or empty)
3. Reconstruct 3 columns using modulo pattern (every 3rd line)
4. Identify columns by keywords (SUFRAGANTES, VOTOS+URNA, INCINERADOS)
5. Extract value from last element of each column, preserving exactly as extracted
"""

import re
from typing import List, Dict, Optional
import structlog

from .base_parser import BaseParser

logger = structlog.get_logger(__name__)


class TotalesMesaParser(BaseParser):
    """
    Parser specialized in extracting mesa totals from horizontal OCR text.

    Principles applied:
    - SRP: Only extracts mesa totals (TotalSufragantesE14, TotalVotosEnUrna, TotalIncinerados)
    - OCP: Extensible via inheritance from BaseParser
    - DIP: Depends on BaseParser abstraction

    Attributes:
        MAX_WINDOW_SIZE: Maximum lines to look for 3 consecutive TOTAL (default: 5)
        MAX_BLOCK_SIZE: Maximum lines to extract after TOTAL markers (default: 15)
    """

    MAX_WINDOW_SIZE = 5
    MAX_BLOCK_SIZE = 15

    def parse(self, lines: List[str]) -> Dict[str, str]:
        """
        Extract mesa totals using horizontal OCR pattern.

        Algorithm:
        1. Find start index where 3 "TOTAL" keywords appear consecutively
        2. Extract following N lines after TOTAL markers
        3. Reconstruct 3 columns by grouping every 3 lines (modulo pattern)
        4. Identify each column by its keywords
        5. Extract value (last line of each column), preserving exactly

        Args:
            lines: List of OCR text lines (horizontal extraction)

        Returns:
            Dict with three keys:
            {
                "TotalSufragantesE14": "134",     # Can be number or symbols
                "TotalVotosEnUrna": "131",        # Can be number or symbols
                "TotalIncinerados": "***"         # Can be number, symbols, or text
            }

        Examples:
            >>> lines = ["TOTAL", "TOTAL", "TOTAL", "SUFRAGANTES", "VOTOS", ...]
            >>> parser = TotalesMesaParser()
            >>> result = parser.parse(lines)
            >>> result["TotalSufragantesE14"]
            "134"
        """
        self.logger.info("parse_started", lines_count=len(lines))
        self.reset_warnings()

        # Initialize result with empty values
        result = {
            "TotalSufragantesE14": "",
            "TotalVotosEnUrna": "",
            "TotalIncinerados": ""
        }

        # Validate input
        if not self._validate_lines(lines):
            self.logger.warning("parse_failed_validation")
            return result

        # Step 1: Find start of totales block (3 consecutive TOTAL)
        start_idx = self._find_totales_block_start(lines)
        if start_idx is None:
            self.add_warning("totales_block_not_found")
            self.logger.warning("parse_failed_no_totales_block")
            return result

        self.logger.info("totales_block_detected", start_line=start_idx)

        # Step 2: Extract lines from totales block
        totales_lines = self._extract_totales_lines(lines, start_idx)
        if not totales_lines:
            self.add_warning("totales_lines_empty")
            self.logger.warning("parse_failed_empty_totales_lines")
            return result

        self.logger.debug(
            "totales_lines_extracted",
            lines=totales_lines,
            count=len(totales_lines)
        )

        # Step 3: Reconstruct columns (every 3 lines forms a column)
        columns = self._reconstruct_columns(totales_lines)
        self.logger.debug(
            "columns_reconstructed",
            col1=columns[0],
            col2=columns[1],
            col3=columns[2]
        )

        # Step 4: Identify and extract totals from columns
        result = self._identify_and_extract_totales(columns)

        self.logger.info(
            "totales_extracted",
            sufragantes=result["TotalSufragantesE14"],
            votos_urna=result["TotalVotosEnUrna"],
            incinerados=result["TotalIncinerados"]
        )

        return result

    def _find_totales_block_start(self, lines: List[str]) -> Optional[int]:
        """
        Find index where 3 "TOTAL" keywords appear consecutively.

        The 3 TOTAL markers must appear within a window of MAX_WINDOW_SIZE lines.
        Other words can appear between them, but they must be close together.

        Args:
            lines: List of OCR text lines

        Returns:
            Index of first TOTAL marker, or None if not found

        Examples:
            >>> lines = ["NIVELACION", "TOTAL", "TOTAL", "TOTAL", "SUFRAGANTES"]
            >>> parser._find_totales_block_start(lines)
            1
        """
        total_count = 0
        start_idx = None

        for i, line in enumerate(lines):
            line_upper = line.upper().strip()

            if 'TOTAL' in line_upper and line_upper == 'TOTAL':
                # Found a TOTAL marker
                if total_count == 0:
                    start_idx = i
                total_count += 1

                self.logger.debug(
                    "total_marker_found",
                    index=i,
                    line=line,
                    count=total_count
                )

                # Check if we found all 3
                if total_count == 3:
                    self.logger.info(
                        "three_totals_found",
                        start=start_idx,
                        end=i
                    )
                    return start_idx

            elif total_count > 0 and (i - start_idx) > self.MAX_WINDOW_SIZE:
                # Window exceeded, reset count
                self.logger.debug(
                    "window_exceeded_resetting",
                    start=start_idx,
                    current=i,
                    found=total_count
                )
                total_count = 0
                start_idx = None

        # Did not find 3 consecutive TOTAL
        if total_count > 0:
            self.logger.warning(
                "incomplete_totals_block",
                found=total_count,
                expected=3
            )

        return None

    def _extract_totales_lines(
        self,
        lines: List[str],
        start_idx: int
    ) -> List[str]:
        """
        Extract lines from totales block after the 3 TOTAL markers.

        Extraction continues until finding an end marker:
        - "CIRCUNSCRIPCIÓN" keyword
        - Pattern "X digit-digit-digit-digit X"
        - Empty line
        - MAX_BLOCK_SIZE lines reached

        Args:
            lines: Full list of OCR text lines
            start_idx: Index where first TOTAL marker was found

        Returns:
            List of lines belonging to totales block (excluding TOTAL markers)

        Examples:
            >>> lines = ["TOTAL", "TOTAL", "TOTAL", "SUFRAGANTES", "VOTOS", ...]
            >>> parser._extract_totales_lines(lines, 0)
            ["SUFRAGANTES", "VOTOS", "VOTOS", ...]
        """
        # Skip the 3 TOTAL markers
        i = start_idx
        total_count = 0
        while i < len(lines) and total_count < 3:
            if lines[i].upper().strip() == 'TOTAL':
                total_count += 1
            i += 1

        self.logger.debug("skipped_total_markers", start=start_idx, resume_at=i)

        # Extract lines until end marker
        totales_lines = []
        while i < len(lines):
            line = lines[i].strip()

            # Check end conditions
            if not line:  # Empty line
                self.logger.debug("end_marker_empty_line", index=i)
                break

            if 'CIRCUNSCRIPCIÓN' in line.upper() or 'CIRCUNSCRIPCION' in line.upper():
                self.logger.debug("end_marker_circunscripcion", index=i, line=line)
                break

            if re.match(r'X\s*\d+-\d+-\d+-\d+\s*X', line):
                self.logger.debug("end_marker_x_pattern", index=i, line=line)
                break

            # Add line to block
            totales_lines.append(line)
            i += 1

            # Safety limit
            if len(totales_lines) >= self.MAX_BLOCK_SIZE:
                self.logger.warning(
                    "max_block_size_reached",
                    size=len(totales_lines),
                    max=self.MAX_BLOCK_SIZE
                )
                break

        self.logger.info(
            "totales_lines_extracted",
            count=len(totales_lines),
            lines=totales_lines[:12]  # Show first 12 lines for debugging
        )

        return totales_lines

    def _reconstruct_columns(self, totales_lines: List[str]) -> List[List[str]]:
        """
        Reconstruct 3 columns from sequential lines by trying both horizontal and vertical patterns.

        OCR can read in different orders:
        - Horizontal (row-by-row): [Col1, Col2, Col3, Col1, Col2, Col3, ...]
        - Mixed order: First row might be out of order, but pattern continues

        Algorithm:
        1. Try horizontal pattern (modulo-3)
        2. Score each reconstruction by counting keyword matches per column
        3. Choose reconstruction with highest confidence

        The key insight: FORMATO/E-11 MUST be in sufragantes column,
        URNA MUST be in votos_urna column, INCINERADOS MUST be in incinerados column.

        Args:
            totales_lines: Sequential lines from totales block

        Returns:
            List of 3 columns, each containing its respective lines

        Examples:
            >>> # Standard horizontal
            >>> lines = ["SUFRAGANTES", "VOTOS", "VOTOS",
            ...          "FORMATO E-11", "EN LA URNA", "INCINERADOS",
            ...          "134", "131", "***"]
            >>> columns = parser._reconstruct_columns(lines)
            >>> columns[0]  # Column 1
            ["SUFRAGANTES", "FORMATO E-11", "134"]

            >>> # Mixed order (VOTOS before SUFRAGANTES)
            >>> lines = ["VOTOS", "SUFRAGANTES", "VOTOS",
            ...          "FORMATO E-11", "EN LA URNA", "INCINERADOS",
            ...          "244", "240", "- - -"]
            >>> columns = parser._reconstruct_columns(lines)
            >>> # Should detect and handle correctly
        """
        if not totales_lines or len(totales_lines) < 3:
            self.logger.warning("insufficient_lines", count=len(totales_lines))
            return [[], [], []]

        # Try standard horizontal pattern (modulo-3)
        col1, col2, col3 = [], [], []
        for i, line in enumerate(totales_lines):
            if i % 3 == 0:
                col1.append(line)
            elif i % 3 == 1:
                col2.append(line)
            else:
                col3.append(line)

        # Score this reconstruction: check if keywords are in expected columns
        def score_columns(c1, c2, c3):
            """Score columns by checking keyword presence (higher = better match)"""
            score = 0
            c1_text = ' '.join(c1).upper()
            c2_text = ' '.join(c2).upper()
            c3_text = ' '.join(c3).upper()

            # Check for sufragantes keywords in c1
            if 'FORMATO' in c1_text or 'E-11' in c1_text:
                score += 10
            if 'SUFRAGANTES' in c1_text:
                score += 5

            # Check for votos_urna keywords in c2
            if 'URNA' in c2_text:
                score += 10
            if 'VOTOS' in c2_text and 'URNA' in c2_text:
                score += 5

            # Check for incinerados keywords in c3
            if 'INCINERADOS' in c3_text:
                score += 10

            # Penalties: keywords in wrong columns
            if 'FORMATO' in c2_text or 'FORMATO' in c3_text:
                score -= 20
            if 'URNA' in c1_text or 'URNA' in c3_text:
                score -= 20
            if 'INCINERADOS' in c1_text or 'INCINERADOS' in c2_text:
                score -= 20

            return score

        horizontal_score = score_columns(col1, col2, col3)

        self.logger.debug(
            "pattern_horizontal_scored",
            score=horizontal_score,
            col1_keywords=' '.join(col1).upper()[:50],
            col2_keywords=' '.join(col2).upper()[:50],
            col3_keywords=' '.join(col3).upper()[:50]
        )

        # Try alternative patterns (rotate first row)
        # Pattern 1: Rotate first row left (c2, c3, c1, ...)
        col1_alt1, col2_alt1, col3_alt1 = [], [], []
        for i, line in enumerate(totales_lines):
            mod_idx = (i + 1) % 3  # Shift by 1
            if mod_idx == 0:
                col1_alt1.append(line)
            elif mod_idx == 1:
                col2_alt1.append(line)
            else:
                col3_alt1.append(line)

        alt1_score = score_columns(col1_alt1, col2_alt1, col3_alt1)

        self.logger.debug(
            "pattern_rotate_left_scored",
            score=alt1_score,
            col1_keywords=' '.join(col1_alt1).upper()[:50],
            col2_keywords=' '.join(col2_alt1).upper()[:50],
            col3_keywords=' '.join(col3_alt1).upper()[:50]
        )

        # Pattern 2: Rotate first row right (c3, c1, c2, ...)
        col1_alt2, col2_alt2, col3_alt2 = [], [], []
        for i, line in enumerate(totales_lines):
            mod_idx = (i + 2) % 3  # Shift by 2
            if mod_idx == 0:
                col1_alt2.append(line)
            elif mod_idx == 1:
                col2_alt2.append(line)
            else:
                col3_alt2.append(line)

        alt2_score = score_columns(col1_alt2, col2_alt2, col3_alt2)

        self.logger.debug(
            "pattern_rotate_right_scored",
            score=alt2_score,
            col1_keywords=' '.join(col1_alt2).upper()[:50],
            col2_keywords=' '.join(col2_alt2).upper()[:50],
            col3_keywords=' '.join(col3_alt2).upper()[:50]
        )

        # Choose best pattern
        best_score = max(horizontal_score, alt1_score, alt2_score)

        # Log which pattern won
        if best_score == horizontal_score:
            winning_cols = [col1, col2, col3]
            pattern_name = "horizontal"
        elif best_score == alt1_score:
            winning_cols = [col1_alt1, col2_alt1, col3_alt1]
            pattern_name = "rotate_left"
        else:
            winning_cols = [col1_alt2, col2_alt2, col3_alt2]
            pattern_name = "rotate_right"

        self.logger.info(
            "columns_reconstructed",
            pattern=pattern_name,
            score=best_score,
            col1=winning_cols[0],
            col2=winning_cols[1],
            col3=winning_cols[2]
        )

        if best_score == alt1_score:
            self.logger.info(
                "pattern_detected",
                pattern="rotate_left",
                score=alt1_score,
                horizontal_score=horizontal_score
            )
            return [col1_alt1, col2_alt1, col3_alt1]
        elif best_score == alt2_score:
            self.logger.info(
                "pattern_detected",
                pattern="rotate_right",
                score=alt2_score,
                horizontal_score=horizontal_score
            )
            return [col1_alt2, col2_alt2, col3_alt2]
        else:
            self.logger.debug(
                "pattern_detected",
                pattern="horizontal",
                score=horizontal_score
            )
            return [col1, col2, col3]

    def _identify_and_extract_totales(
        self,
        columns: List[List[str]]
    ) -> Dict[str, str]:
        """
        Identify which column is which and extract its value using specificity scoring.

        Algorithm:
        1. First pass: Identify all candidate columns for each total with specificity scores
        2. Second pass: Select best candidate (highest specificity) for each field

        Specificity scoring (in order of priority):
        1. TotalIncinerados (checked FIRST):
          - 15 points if INCINERADOS present (HIGHEST priority, most specific)
          - Column is excluded from other checks to avoid conflicts
        2. TotalSufragantesE14:
          - 10 points if FORMATO or E-11 present (most reliable identifier)
          - Bonus: +2 if SUFRAGANTES also present
          - Fallback: 7 points if only SUFRAGANTES present (no FORMATO, no INCINERADOS)
        3. TotalVotosEnUrna:
          - 8 points if VOTOS + URNA present
          - Penalty: -5 (=3 total) if SUFRAGANTES or FORMATO also present

        This scoring system handles edge cases:
        - Columns in different order
        - Keywords spanning multiple rows
        - Overlapping keywords (e.g., SUFRAGANTES + URNA in same column)

        Value extraction:
        - Value is ALWAYS the LAST element of the column
        - NEVER transform the value (preserve exactly as extracted)
        - Can be numbers ("134"), symbols ("***"), or text ("XX")

        Args:
            columns: List of 3 columns reconstructed from lines

        Returns:
            Dict with extracted totals (empty strings for missing data)

        Examples:
            >>> # Standard order
            >>> columns = [
            ...     ["SUFRAGANTES", "FORMATO E-11", "134"],
            ...     ["VOTOS", "EN LA URNA", "131"],
            ...     ["VOTOS", "INCINERADOS", "***"]
            ... ]
            >>> result = parser._identify_and_extract_totales(columns)
            >>> result["TotalSufragantesE14"]
            "134"

            >>> # Different column order (FORMATO is primary identifier)
            >>> columns = [
            ...     ["VOTOS", "FORMATO E-11", "244"],
            ...     ["SUFRAGANTES", "EN LA URNA", "240"],
            ...     ["VOTOS", "INCINERADOS", "- - -"]
            ... ]
            >>> result = parser._identify_and_extract_totales(columns)
            >>> result["TotalSufragantesE14"]
            "244"  # Col 1 wins: FORMATO E-11 has specificity 10
            >>> result["TotalVotosEnUrna"]
            "240"  # Col 2: VOTOS+URNA (but deprioritized to 3 due to SUFRAGANTES)
            >>> result["TotalIncinerados"]
            "- - -"  # Col 3: INCINERADOS has specificity 15

            >>> # Edge case: SUFRAGANTES in incinerados column
            >>> columns = [
            ...     ["VOTOS", "FORMATO E-11", "205"],
            ...     ["VOTOS", "EN LA URNA", "205"],
            ...     ["SUFRAGANTES", "INCINERADOS", "**0"]
            ... ]
            >>> result = parser._identify_and_extract_totales(columns)
            >>> result["TotalSufragantesE14"]
            "205"  # Col 1 wins: FORMATO E-11 has specificity 10
            >>> result["TotalVotosEnUrna"]
            "205"  # Col 2: VOTOS+URNA has specificity 8
            >>> result["TotalIncinerados"]
            "**0"  # Col 3: INCINERADOS checked FIRST, specificity 15 (excludes SUFRAGANTES)
        """
        result = {
            "TotalSufragantesE14": "",
            "TotalVotosEnUrna": "",
            "TotalIncinerados": ""
        }

        # First pass: Identify each column with specificity scores
        # This allows us to handle cases where keywords might overlap
        column_candidates = {
            "sufragantes": [],  # (column_idx, value, specificity_score)
            "votos_urna": [],
            "incinerados": []
        }

        for column_idx, column in enumerate(columns):
            if not column:  # Empty column
                self.logger.debug("empty_column", index=column_idx)
                continue

            # Join all lines to search for keywords
            column_text = ' '.join(column).upper()
            value = column[-1].strip()

            # Check for TotalIncinerados FIRST (highest priority, most specific)
            # CRITICAL: Must check INCINERADOS first to avoid misclassification
            # Some E-14s have SUFRAGANTES in the incinerados column
            if 'INCINERADOS' in column_text or 'INCINERADO' in column_text:
                specificity = 15  # HIGHEST priority - most specific keyword
                column_candidates["incinerados"].append((column_idx, value, specificity))
                # Skip other checks for this column to avoid conflicts
                continue

            # Check for TotalSufragantesE14
            # Strategy: FORMATO E-11 is the primary identifier (always present in sufragantes column)
            # SUFRAGANTES keyword may appear in incinerados column, so we rely on FORMATO
            if 'FORMATO' in column_text or 'E-11' in column_text or 'E11' in column_text:
                specificity = 10  # High priority - FORMATO is most reliable
                if 'SUFRAGANTES' in column_text or 'SUFRAGANTE' in column_text:
                    specificity += 2  # Small bonus if SUFRAGANTES also present
                column_candidates["sufragantes"].append((column_idx, value, specificity))
            elif 'SUFRAGANTES' in column_text or 'SUFRAGANTE' in column_text:
                # Fallback: If FORMATO not found but SUFRAGANTES present
                # ONLY if this column doesn't have INCINERADOS (already checked above)
                specificity = 7  # Medium priority
                column_candidates["sufragantes"].append((column_idx, value, specificity))

            # Check for TotalVotosEnUrna
            # Primary identifier: "URNA" keyword (always present in this column)
            # Secondary: "VOTOS" keyword (may be missing if OCR splits header across columns)
            if 'URNA' in column_text:
                # Base score: URNA is present
                specificity = 6

                # Bonus: If VOTOS is also present
                if 'VOTOS' in column_text:
                    specificity += 2  # 8 total

                # Penalty: If this column also has SUFRAGANTES or FORMATO (likely sufragantes column)
                if ('SUFRAGANTES' in column_text or 'SUFRAGANTE' in column_text or
                    'FORMATO' in column_text or 'E-11' in column_text):
                    specificity = 3  # Deprioritize - likely misidentified

                column_candidates["votos_urna"].append((column_idx, value, specificity))

        # Log all candidates for debugging
        self.logger.info(
            "column_candidates_identified",
            sufragantes_count=len(column_candidates["sufragantes"]),
            votos_urna_count=len(column_candidates["votos_urna"]),
            incinerados_count=len(column_candidates["incinerados"]),
            sufragantes_candidates=column_candidates["sufragantes"],
            votos_urna_candidates=column_candidates["votos_urna"],
            incinerados_candidates=column_candidates["incinerados"]
        )

        # Second pass: Select best candidate for each total
        # Pick the column with highest specificity for each field

        if column_candidates["sufragantes"]:
            # Sort by specificity (highest first)
            best = max(column_candidates["sufragantes"], key=lambda x: x[2])
            column_idx, value, specificity = best
            result["TotalSufragantesE14"] = value

            self.logger.debug(
                "total_sufragantes_detected",
                value=value,
                column_index=column_idx,
                specificity=specificity
            )
            self._validate_extracted_value(value, "TotalSufragantesE14")

        if column_candidates["votos_urna"]:
            best = max(column_candidates["votos_urna"], key=lambda x: x[2])
            column_idx, value, specificity = best
            result["TotalVotosEnUrna"] = value

            self.logger.debug(
                "total_votos_urna_detected",
                value=value,
                column_index=column_idx,
                specificity=specificity
            )
            self._validate_extracted_value(value, "TotalVotosEnUrna")

        if column_candidates["incinerados"]:
            best = max(column_candidates["incinerados"], key=lambda x: x[2])
            column_idx, value, specificity = best
            result["TotalIncinerados"] = value

            self.logger.debug(
                "total_incinerados_detected",
                value=value,
                column_index=column_idx,
                specificity=specificity
            )
            self._validate_extracted_value(value, "TotalIncinerados")

        # Apply business rule validation and correction
        result = self._validate_and_correct_totales(result)

        return result

    def _validate_and_correct_totales(self, result: Dict[str, str]) -> Dict[str, str]:
        """
        Validate and correct extracted totals using business rules.

        Business Rule: TotalSufragantesE14 >= TotalVotosEnUrna (ALWAYS)

        This rule is ALWAYS true in E-14 forms:
        - If TotalVotosEnUrna has a value, TotalSufragantesE14 MUST have a value
        - TotalSufragantesE14 must be >= TotalVotosEnUrna numerically
        - If rule is violated, columns were extracted incorrectly by OCR

        Correction Strategy (tried in order):
        1. Normal case: TotalSufragantesE14 >= TotalVotosEnUrna → No correction needed
        2. Simple swap: Swap TotalSufragantesE14 ↔ TotalVotosEnUrna, validate
        3. Incinerados swap: TotalSufragantesE14 = TotalIncinerados (original), validate
           - If fails: TotalSufragantesE14 = TotalVotosEnUrna (original)
        4. Complex permutations: Try all possible combinations

        Args:
            result: Dict with extracted totals (may be incorrect)

        Returns:
            Dict with corrected totals (guaranteed to satisfy business rule if possible)

        Examples:
            >>> # Correct extraction - no changes
            >>> result = {"TotalSufragantesE14": "134", "TotalVotosEnUrna": "131", "TotalIncinerados": "***"}
            >>> corrected = parser._validate_and_correct_totales(result)
            >>> corrected["TotalSufragantesE14"]
            "134"  # 134 >= 131 ✓

            >>> # Simple swap needed
            >>> result = {"TotalSufragantesE14": "131", "TotalVotosEnUrna": "134", "TotalIncinerados": "***"}
            >>> corrected = parser._validate_and_correct_totales(result)
            >>> corrected["TotalSufragantesE14"]
            "134"  # Swapped: 134 >= 131 ✓

            >>> # Incinerados contains sufragantes value
            >>> result = {"TotalSufragantesE14": "***", "TotalVotosEnUrna": "160", "TotalIncinerados": "166"}
            >>> corrected = parser._validate_and_correct_totales(result)
            >>> corrected["TotalSufragantesE14"]
            "166"  # Used incinerados: 166 >= 160 ✓
            >>> corrected["TotalIncinerados"]
            "***"  # Original sufragantes value
        """
        sufragantes = result["TotalSufragantesE14"]
        votos_urna = result["TotalVotosEnUrna"]
        incinerados = result["TotalIncinerados"]

        # Store originals for swapping
        original_sufragantes = sufragantes
        original_votos_urna = votos_urna
        original_incinerados = incinerados

        # Helper: Convert to int, return -1 for non-numeric
        def to_int(value: str) -> int:
            """Convert value to int, return -1 if non-numeric (symbols like ***, ---)"""
            if not value or not value.strip():
                return -1
            # Remove spaces and common symbols
            cleaned = value.strip().replace(" ", "").replace("-", "").replace("*", "")
            if cleaned.isdigit():
                return int(cleaned)
            return -1

        # Helper: Check if business rule is satisfied
        def is_valid(suf: str, votos: str) -> bool:
            """
            Check if business rules are satisfied:
            1. TotalSufragantesE14 >= TotalVotosEnUrna (if both numeric)
            2. If TotalSufragantesE14 is numeric, TotalVotosEnUrna MUST be numeric too
            """
            suf_int = to_int(suf)
            votos_int = to_int(votos)

            # Rule 1: If both are numeric, check sufragantes >= votos_urna
            if suf_int >= 0 and votos_int >= 0:
                return suf_int >= votos_int

            # Rule 2: If sufragantes is numeric, votos_urna MUST be numeric too
            # (votos_urna cannot be *** if sufragantes is a number)
            if suf_int >= 0 and votos_int < 0:
                return False

            # If votos_urna is numeric but sufragantes isn't, it's invalid
            if votos_int >= 0 and suf_int < 0:
                return False

            # If both are non-numeric, assume valid (rare edge case)
            return True

        # Case 1: Normal case - already correct
        if is_valid(sufragantes, votos_urna):
            self.logger.debug(
                "totales_validation_passed",
                sufragantes=sufragantes,
                votos_urna=votos_urna,
                incinerados=incinerados,
                correction="none"
            )
            return result

        self.logger.warning(
            "totales_validation_failed",
            sufragantes=sufragantes,
            votos_urna=votos_urna,
            incinerados=incinerados,
            reason="TotalSufragantesE14 < TotalVotosEnUrna"
        )

        # Case 2: Simple swap - Sufragantes ↔ VotosUrna
        sufragantes_temp = original_votos_urna
        votos_urna_temp = original_sufragantes
        if is_valid(sufragantes_temp, votos_urna_temp):
            self.logger.info(
                "totales_corrected_simple_swap",
                old_sufragantes=original_sufragantes,
                new_sufragantes=sufragantes_temp,
                old_votos_urna=original_votos_urna,
                new_votos_urna=votos_urna_temp
            )
            return {
                "TotalSufragantesE14": sufragantes_temp,
                "TotalVotosEnUrna": votos_urna_temp,
                "TotalIncinerados": original_incinerados
            }

        # Case 3: Incinerados swap - Incinerados → Sufragantes
        # Try: TotalSufragantesE14 = TotalIncinerados (original)
        sufragantes_temp = original_incinerados
        votos_urna_temp = original_votos_urna
        if is_valid(sufragantes_temp, votos_urna_temp):
            self.logger.info(
                "totales_corrected_incinerados_to_sufragantes",
                old_sufragantes=original_sufragantes,
                new_sufragantes=sufragantes_temp,
                old_incinerados=original_incinerados,
                new_incinerados=original_sufragantes
            )
            return {
                "TotalSufragantesE14": sufragantes_temp,
                "TotalVotosEnUrna": votos_urna_temp,
                "TotalIncinerados": original_sufragantes  # Original sufragantes → incinerados
            }

        # Case 3b: If incinerados swap failed, try VotosUrna → Sufragantes
        sufragantes_temp = original_votos_urna
        votos_urna_temp = original_incinerados  # Now votos_urna gets incinerados
        if is_valid(sufragantes_temp, votos_urna_temp):
            self.logger.info(
                "totales_corrected_votos_urna_to_sufragantes",
                old_sufragantes=original_sufragantes,
                new_sufragantes=sufragantes_temp,
                old_votos_urna=original_votos_urna,
                new_votos_urna=votos_urna_temp,
                old_incinerados=original_incinerados,
                new_incinerados=original_sufragantes
            )
            return {
                "TotalSufragantesE14": sufragantes_temp,
                "TotalVotosEnUrna": votos_urna_temp,
                "TotalIncinerados": original_sufragantes
            }

        # Case 4: Complex permutations - try all combinations
        # Permutation: Sufragantes=Incinerados, VotosUrna=Sufragantes, Incinerados=VotosUrna
        sufragantes_temp = original_incinerados
        votos_urna_temp = original_sufragantes
        incinerados_temp = original_votos_urna
        if is_valid(sufragantes_temp, votos_urna_temp):
            self.logger.info(
                "totales_corrected_complex_permutation",
                old_sufragantes=original_sufragantes,
                new_sufragantes=sufragantes_temp,
                old_votos_urna=original_votos_urna,
                new_votos_urna=votos_urna_temp,
                old_incinerados=original_incinerados,
                new_incinerados=incinerados_temp
            )
            return {
                "TotalSufragantesE14": sufragantes_temp,
                "TotalVotosEnUrna": votos_urna_temp,
                "TotalIncinerados": incinerados_temp
            }

        # If no permutation works, return original with error flag
        self.logger.error(
            "totales_correction_failed",
            sufragantes=original_sufragantes,
            votos_urna=original_votos_urna,
            incinerados=original_incinerados,
            note="No valid permutation found - requires manual audit"
        )
        self.add_warning(
            "totales_validation_failed",
            sufragantes=original_sufragantes,
            votos_urna=original_votos_urna,
            incinerados=original_incinerados
        )

        # Return original values (no correction possible)
        return result

    def _validate_extracted_value(self, value: str, field_name: str) -> bool:
        """
        Validate that a value was extracted, but DO NOT transform it.

        This validation only checks if something was extracted and logs
        warnings for empty or non-numeric values. It NEVER changes the value.

        CRITICAL RULE: Never transform values, preserve exactly as extracted.

        Args:
            value: Extracted value (can be number, symbols, or text)
            field_name: Name of the field being validated

        Returns:
            True if value is not empty, False otherwise

        Examples:
            >>> parser._validate_extracted_value("134", "TotalSufragantesE14")
            True
            >>> parser._validate_extracted_value("***", "TotalIncinerados")
            True  # Non-numeric but valid
            >>> parser._validate_extracted_value("", "TotalIncinerados")
            False  # Empty is invalid
        """
        if not value or not value.strip():
            self.add_warning("campo_vacio", field=field_name)
            return False

        # Only log if non-numeric (potential corruption or symbols)
        if not value.isdigit():
            self.logger.info(
                "valor_no_numerico_detectado",
                field=field_name,
                value=value,
                note="Puede requerir auditoría"
            )

        return True
