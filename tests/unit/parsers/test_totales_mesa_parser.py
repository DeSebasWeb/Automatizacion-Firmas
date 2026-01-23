"""
Unit tests for TotalesMesaParser.

Tests cover:
- Happy path with standard horizontal OCR pattern
- Edge cases: multiple TOTAL occurrences, symbols, incomplete columns
- Value preservation (numbers, symbols, corrupted text)
"""

import pytest
from src.infrastructure.ocr.textract.parsers.totales_mesa_parser import TotalesMesaParser


class TestTotalesMesaParser:
    """Test suite for TotalesMesaParser."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = TotalesMesaParser()

    def test_extract_totales_patron_horizontal_standard(self):
        """Test extraction with standard horizontal OCR pattern."""
        lines = [
            "NIVELACION DE LA MESA",
            "TOTAL",
            "TOTAL",
            "TOTAL",
            "SUFRAGANTES",
            "VOTOS",
            "VOTOS",
            "FORMATO E-11",
            "EN LA URNA",
            "INCINERADOS",
            "134",
            "131",
            "***",
            "CIRCUNSCRIPCIÓN TERRITORIAL"
        ]

        result = self.parser.parse(lines)

        assert result["TotalSufragantesE14"] == "134"
        assert result["TotalVotosEnUrna"] == "131"
        assert result["TotalIncinerados"] == "***"
        assert len(self.parser.warnings) == 0

    def test_extract_totales_with_numeric_incinerados(self):
        """Test that TotalIncinerados can be a number."""
        lines = [
            "TOTAL",
            "TOTAL",
            "TOTAL",
            "SUFRAGANTES",
            "VOTOS",
            "VOTOS",
            "FORMATO E-11",
            "EN LA URNA",
            "INCINERADOS",
            "150",
            "145",
            "5",  # Numeric incinerados
            "CIRCUNSCRIPCIÓN"
        ]

        result = self.parser.parse(lines)

        assert result["TotalIncinerados"] == "5"
        assert len(self.parser.warnings) == 0

    def test_extract_totales_with_symbol_incinerados(self):
        """Test that TotalIncinerados can be symbols."""
        test_cases = [
            ("***", "asteriscos"),
            ("///", "slashes"),
            ("###", "hashes"),
            ("XX", "corrupted text"),
            ("---", "dashes")
        ]

        for symbol, description in test_cases:
            lines = [
                "TOTAL", "TOTAL", "TOTAL",
                "SUFRAGANTES", "VOTOS", "VOTOS",
                "FORMATO E-11", "EN LA URNA", "INCINERADOS",
                "100", "95", symbol,
                "CIRCUNSCRIPCIÓN"
            ]

            result = self.parser.parse(lines)

            assert result["TotalIncinerados"] == symbol, f"Failed for {description}"
            assert result["TotalSufragantesE14"] == "100"
            assert result["TotalVotosEnUrna"] == "95"

    def test_extract_totales_with_empty_incinerados(self):
        """Test handling of empty TotalIncinerados."""
        lines = [
            "TOTAL", "TOTAL", "TOTAL",
            "SUFRAGANTES", "VOTOS", "VOTOS",
            "FORMATO E-11", "EN LA URNA", "INCINERADOS",
            "100", "95", "",  # Empty incinerados
            "CIRCUNSCRIPCIÓN"
        ]

        result = self.parser.parse(lines)

        assert result["TotalIncinerados"] == ""
        assert "campo_vacio" in self.parser.warnings

    def test_totales_not_found_returns_empty(self):
        """Test that missing TOTAL markers returns empty dict."""
        lines = [
            "SUFRAGANTES",
            "VOTOS",
            "FORMATO E-11",
            "134"
        ]

        result = self.parser.parse(lines)

        assert result["TotalSufragantesE14"] == ""
        assert result["TotalVotosEnUrna"] == ""
        assert result["TotalIncinerados"] == ""
        assert "totales_block_not_found" in self.parser.warnings

    def test_totales_with_extra_text_between_markers(self):
        """Test that parser handles text between TOTAL markers."""
        lines = [
            "TOTAL",
            "some extra text",
            "TOTAL",
            "TOTAL",
            "SUFRAGANTES",
            "VOTOS",
            "VOTOS",
            "FORMATO E-11",
            "EN LA URNA",
            "INCINERADOS",
            "120",
            "115",
            "5",
            "CIRCUNSCRIPCIÓN"
        ]

        result = self.parser.parse(lines)

        # Should still find the totales block
        assert result["TotalSufragantesE14"] == "120"
        assert result["TotalVotosEnUrna"] == "115"
        assert result["TotalIncinerados"] == "5"

    def test_multiple_total_occurrences_in_document(self):
        """Test that parser finds the correct TOTAL block."""
        lines = [
            "TOTAL",  # False positive
            "NIVELACION",
            "TOTAL",  # Real start
            "TOTAL",
            "TOTAL",
            "SUFRAGANTES",
            "VOTOS",
            "VOTOS",
            "FORMATO E-11",
            "EN LA URNA",
            "INCINERADOS",
            "200",
            "195",
            "***",
            "CIRCUNSCRIPCIÓN"
        ]

        result = self.parser.parse(lines)

        assert result["TotalSufragantesE14"] == "200"
        assert result["TotalVotosEnUrna"] == "195"
        assert result["TotalIncinerados"] == "***"

    def test_incomplete_columns_returns_empty_fields(self):
        """Test handling of incomplete column data."""
        lines = [
            "TOTAL",
            "TOTAL",
            "TOTAL",
            "SUFRAGANTES",
            "VOTOS",
            # Missing third column header
            "FORMATO E-11",
            "EN LA URNA",
            # Missing third column value
            "150",
            "145",
            # Missing incinerados value
            "CIRCUNSCRIPCIÓN"
        ]

        result = self.parser.parse(lines)

        # Should extract what it can
        assert result["TotalSufragantesE14"] == "150"
        assert result["TotalVotosEnUrna"] == "145"
        # TotalIncinerados should be empty
        assert result["TotalIncinerados"] == ""

    def test_end_marker_x_pattern(self):
        """Test that X-X-X-X pattern ends extraction correctly."""
        lines = [
            "TOTAL", "TOTAL", "TOTAL",
            "SUFRAGANTES", "VOTOS", "VOTOS",
            "FORMATO E-11", "EN LA URNA", "INCINERADOS",
            "100", "95", "5",
            "X 7-27-12-28 X",  # End marker
            "EXTRA DATA SHOULD NOT BE PARSED"
        ]

        result = self.parser.parse(lines)

        assert result["TotalSufragantesE14"] == "100"
        assert result["TotalVotosEnUrna"] == "95"
        assert result["TotalIncinerados"] == "5"

    def test_empty_lines_list(self):
        """Test handling of empty input."""
        result = self.parser.parse([])

        assert result["TotalSufragantesE14"] == ""
        assert result["TotalVotosEnUrna"] == ""
        assert result["TotalIncinerados"] == ""
        assert "input_vacio" in self.parser.warnings

    def test_none_input(self):
        """Test handling of None input."""
        result = self.parser.parse(None)

        assert result["TotalSufragantesE14"] == ""
        assert result["TotalVotosEnUrna"] == ""
        assert result["TotalIncinerados"] == ""
        assert "input_vacio" in self.parser.warnings

    def test_value_preservation_no_transformation(self):
        """Test that values are preserved exactly without transformation."""
        test_values = [
            ("134", "134"),      # Standard number
            ("***", "***"),      # Asterisks
            ("  50  ", "50"),    # Whitespace (should strip)
            ("//*", "//*"),      # Mixed symbols
            ("0", "0"),          # Zero
            ("12345", "12345"),  # Large number
        ]

        for input_val, expected_val in test_values:
            lines = [
                "TOTAL", "TOTAL", "TOTAL",
                "SUFRAGANTES", "VOTOS", "VOTOS",
                "FORMATO E-11", "EN LA URNA", "INCINERADOS",
                "100", "95", input_val,
                "CIRCUNSCRIPCIÓN"
            ]

            result = self.parser.parse(lines)

            assert result["TotalIncinerados"] == expected_val, \
                f"Value transformation failed: {input_val} -> {result['TotalIncinerados']}"

    def test_reset_warnings(self):
        """Test that reset_warnings clears accumulated warnings."""
        lines = []
        self.parser.parse(lines)

        assert len(self.parser.warnings) > 0

        self.parser.reset_warnings()

        assert len(self.parser.warnings) == 0

    def test_real_ocr_data(self):
        """Test with actual OCR data pattern from real E-14."""
        lines = [
            "NIVELACION DE LA MESA",
            "TOTAL",
            "TOTAL",
            "TOTAL",
            "SUFRAGANTES",
            "VOTOS",
            "VOTOS",
            "FORMATO E-11",
            "EN LA URNA",
            "INCINERADOS",
            "134",
            "131",
            "***",
            "CIRCUNSCRIPCIÓN TERRITORIAL"
        ]

        result = self.parser.parse(lines)

        assert result["TotalSufragantesE14"] == "134"
        assert result["TotalVotosEnUrna"] == "131"
        assert result["TotalIncinerados"] == "***"
        assert len(self.parser.warnings) == 0

    def test_columns_in_different_order(self):
        """Test extraction when columns appear in different order (order-independent)."""
        # Real E-14 scenario where physical column order is different
        # OCR reads horizontally: VOTOS → SUFRAGANTES → VOTOS → FORMATO E-11 → EN LA URNA → INCINERADOS → 244 → 240 → - - -
        #
        # With modulo pattern (every 3 lines = 1 column):
        # Col 1 (i%3==0): [VOTOS, FORMATO E-11, 244]         → Has FORMATO but no SUFRAGANTES
        # Col 2 (i%3==1): [SUFRAGANTES, EN LA URNA, 240]     → Has SUFRAGANTES + URNA
        # Col 3 (i%3==2): [VOTOS, INCINERADOS, - - -]        → Has INCINERADOS
        #
        # New algorithm:
        # - Col 2 has SUFRAGANTES → TotalSufragantesE14 = 240
        # - Col 2 has SUFRAGANTES, so col 1 cannot be votos_urna even if it has FORMATO
        # - Need to find column with VOTOS + URNA but NOT SUFRAGANTES
        #
        # Wait, col 2 has SUFRAGANTES + EN LA URNA together!
        # So col 2 matches both patterns. Need to prioritize SUFRAGANTES.

        lines = [
            "NIVELACION DELAMESA",
            "TOTAL",
            "TOTAL",
            "TOTAL",
            "VOTOS",             # Line 0 → Col 1
            "SUFRAGANTES",       # Line 1 → Col 2
            "VOTOS",             # Line 2 → Col 3
            "FORMATO E-11",      # Line 3 → Col 1
            "EN LA URNA",        # Line 4 → Col 2
            "INCINERADOS",       # Line 5 → Col 3
            "244",               # Line 6 → Col 1
            "240",               # Line 7 → Col 2
            "- - -",             # Line 8 → Col 3
            "CIRCUNSCRIPCIÓN TERRITORIAL"
        ]

        result = self.parser.parse(lines)

        # Expected with new algorithm (FORMATO as primary identifier):
        # Col 1 [VOTOS, FORMATO E-11, 244] → Matches FORMATO → TotalSufragantesE14 = 244 (specificity 10)
        # Col 2 [SUFRAGANTES, EN LA URNA, 240] → Matches SUFRAGANTES (fallback, specificity 7) AND VOTOS+URNA (specificity 3)
        #                                       → Loses to Col 1 for sufragantes, but wins for votos_urna
        # Col 3 [VOTOS, INCINERADOS, - - -] → Matches INCINERADOS → TotalIncinerados = - - - (specificity 10)

        assert result["TotalSufragantesE14"] == "244"  # From col 1 (FORMATO E-11, specificity 10)
        assert result["TotalVotosEnUrna"] == "240"     # From col 2 (VOTOS+URNA, specificity 3)
        assert result["TotalIncinerados"] == "- - -"   # From col 3 (INCINERADOS, specificity 10)

    def test_real_ocr_different_column_order_fixed(self):
        """Test with corrected real OCR pattern where all three columns are identifiable."""
        # Adjusted to match a valid E-14 structure where:
        # - Column with VOTOS + FORMATO has value for sufragantes
        # - Column with VOTOS + EN LA URNA has value for votos en urna
        # - Column with VOTOS + INCINERADOS has value for incinerados

        # Scenario: Physical columns in document are:
        # [VOTOS/FORMATO E-11/244] | [SUFRAGANTES/EN LA URNA/240] | [VOTOS/INCINERADOS/---]
        # But OCR reads horizontally, so it becomes:
        # VOTOS, SUFRAGANTES, VOTOS, FORMATO E-11, EN LA URNA, INCINERADOS, 244, 240, ---

        # Actually, looking closer at the user's E-14, it seems like SUFRAGANTES and EN LA URNA
        # are in the same column. This is a special case where one column has both keywords.

        # Let me create a more standard test where columns don't overlap:
        lines = [
            "TOTAL", "TOTAL", "TOTAL",
            "VOTOS",           # Col 1
            "SUFRAGANTES",     # Col 2
            "VOTOS",           # Col 3
            "EN LA URNA",      # Col 1 (second row)
            "FORMATO E-11",    # Col 2 (second row)
            "INCINERADOS",     # Col 3 (second row)
            "131",             # Col 1 value
            "134",             # Col 2 value
            "***",             # Col 3 value
            "CIRCUNSCRIPCIÓN"
        ]

        result = self.parser.parse(lines)

        # Col 1: [VOTOS, EN LA URNA, 131] → TotalVotosEnUrna = 131
        # Col 2: [SUFRAGANTES, FORMATO E-11, 134] → TotalSufragantesE14 = 134
        # Col 3: [VOTOS, INCINERADOS, ***] → TotalIncinerados = ***

        assert result["TotalSufragantesE14"] == "134"
        assert result["TotalVotosEnUrna"] == "131"
        assert result["TotalIncinerados"] == "***"


class TestTotalesMesaParserPerformance:
    """Performance tests for TotalesMesaParser."""

    def test_large_document_performance(self):
        """Test parser performance with large document."""
        import time

        # Simulate large E-14 with many parties
        lines = ["TOTAL", "TOTAL", "TOTAL"]
        lines += ["SUFRAGANTES", "VOTOS", "VOTOS"]
        lines += ["FORMATO E-11", "EN LA URNA", "INCINERADOS"]
        lines += ["150", "145", "5"]
        lines += ["CIRCUNSCRIPCIÓN"]

        # Add 1000+ lines of party data
        for i in range(1000):
            lines.append(f"PARTIDO {i}")

        parser = TotalesMesaParser()

        start_time = time.time()
        result = parser.parse(lines)
        elapsed_ms = (time.time() - start_time) * 1000

        # Should complete in < 100ms
        assert elapsed_ms < 100, f"Parsing too slow: {elapsed_ms:.2f}ms"
        assert result["TotalSufragantesE14"] == "150"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
