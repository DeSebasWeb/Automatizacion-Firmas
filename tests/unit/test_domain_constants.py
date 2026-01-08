"""Tests for domain constants module."""
import pytest
from src.domain.constants import (
    MIN_CEDULA_LENGTH,
    MAX_CEDULA_LENGTH,
    MIN_CEDULA_LENGTH_STRICT,
    MAX_CEDULA_LENGTH_STRICT,
    DIGIT_CONFUSION_PAIRS,
    MIN_POSITIONAL_SIMILARITY,
    HIGH_SIMILARITY_THRESHOLD,
    FALLBACK_SIMILARITY_THRESHOLD,
    SEARCH_WINDOW_SIZE,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    DEFAULT_DPI,
    IMAGE_UPSCALE_FACTOR,
)


class TestCedulaValidationConstants:
    """Test cedula validation business rules."""

    def test_cedula_length_ranges_are_valid(self):
        """Cedula length ranges should be logical and valid."""
        # Min should be less than max
        assert MIN_CEDULA_LENGTH < MAX_CEDULA_LENGTH
        assert MIN_CEDULA_LENGTH_STRICT < MAX_CEDULA_LENGTH_STRICT

        # Strict range should be within permissive range
        assert MIN_CEDULA_LENGTH <= MIN_CEDULA_LENGTH_STRICT
        assert MAX_CEDULA_LENGTH_STRICT <= MAX_CEDULA_LENGTH

        # Values should be positive
        assert MIN_CEDULA_LENGTH > 0
        assert MAX_CEDULA_LENGTH > 0

    def test_cedula_lengths_match_colombian_standards(self):
        """Cedula lengths should match Colombian ID standards."""
        # Colombian cédulas are typically 6-11 digits
        assert MIN_CEDULA_LENGTH_STRICT == 6
        assert MAX_CEDULA_LENGTH_STRICT == 11

        # Permissive range allows edge cases
        assert MIN_CEDULA_LENGTH == 3  # Foreign IDs, special cases
        assert MAX_CEDULA_LENGTH == 11


class TestDigitConfusionMatrix:
    """Test digit confusion matrix domain knowledge."""

    def test_confusion_matrix_structure(self):
        """Confusion matrix should have valid structure."""
        assert isinstance(DIGIT_CONFUSION_PAIRS, dict)
        assert len(DIGIT_CONFUSION_PAIRS) > 0

    def test_confusion_pairs_are_symmetric(self):
        """For each (a, b) pair, (b, a) should also exist."""
        for (digit1, digit2), prob1 in DIGIT_CONFUSION_PAIRS.items():
            # Check reverse pair exists
            reverse_key = (digit2, digit1)
            assert reverse_key in DIGIT_CONFUSION_PAIRS, \
                f"Missing symmetric pair for ({digit1}, {digit2})"

            # Probabilities should be equal (symmetric confusion)
            prob2 = DIGIT_CONFUSION_PAIRS[reverse_key]
            assert prob1 == prob2, \
                f"Asymmetric probabilities for ({digit1}, {digit2}): {prob1} != {prob2}"

    def test_confusion_probabilities_are_valid(self):
        """Confusion probabilities should be between 0 and 1."""
        for (digit1, digit2), prob in DIGIT_CONFUSION_PAIRS.items():
            assert 0.0 <= prob <= 1.0, \
                f"Invalid probability {prob} for pair ({digit1}, {digit2})"

            # Should not be 0 (no point including it) or 1 (always confused)
            assert 0.0 < prob < 1.0, \
                f"Confusion probability should be between 0 and 1, got {prob}"

    def test_digit_keys_are_strings(self):
        """Digit keys should be single-character strings."""
        for (digit1, digit2) in DIGIT_CONFUSION_PAIRS.keys():
            assert isinstance(digit1, str) and len(digit1) == 1
            assert isinstance(digit2, str) and len(digit2) == 1
            assert digit1.isdigit()
            assert digit2.isdigit()

    def test_common_confusions_present(self):
        """Known common confusions should be in the matrix."""
        # 1 and 7 confusion (very common in handwriting)
        assert ('1', '7') in DIGIT_CONFUSION_PAIRS
        assert ('7', '1') in DIGIT_CONFUSION_PAIRS

        # 5 and 6 confusion
        assert ('5', '6') in DIGIT_CONFUSION_PAIRS
        assert ('6', '5') in DIGIT_CONFUSION_PAIRS

    def test_confusion_probabilities_ranked_correctly(self):
        """Higher confusion pairs should have higher probabilities."""
        # 1-7 confusion is very common (should be high)
        prob_1_7 = DIGIT_CONFUSION_PAIRS[('1', '7')]
        assert prob_1_7 >= 0.10, "1-7 confusion should have high probability"

        # 5-6 confusion is moderate
        prob_5_6 = DIGIT_CONFUSION_PAIRS[('5', '6')]
        assert prob_5_6 >= 0.05, "5-6 confusion should have moderate probability"


class TestPositionalPairingConstants:
    """Test positional pairing thresholds."""

    def test_similarity_thresholds_are_ordered(self):
        """Similarity thresholds should be properly ordered."""
        assert MIN_POSITIONAL_SIMILARITY < FALLBACK_SIMILARITY_THRESHOLD
        assert FALLBACK_SIMILARITY_THRESHOLD < HIGH_SIMILARITY_THRESHOLD

    def test_similarity_thresholds_are_percentages(self):
        """Similarity thresholds should be between 0 and 1."""
        assert 0.0 <= MIN_POSITIONAL_SIMILARITY <= 1.0
        assert 0.0 <= HIGH_SIMILARITY_THRESHOLD <= 1.0
        assert 0.0 <= FALLBACK_SIMILARITY_THRESHOLD <= 1.0

    def test_search_window_size_is_reasonable(self):
        """Search window should be small but positive."""
        assert isinstance(SEARCH_WINDOW_SIZE, int)
        assert 0 < SEARCH_WINDOW_SIZE <= 5  # Larger values = expensive


class TestImageQualityConstants:
    """Test image quality requirements."""

    def test_minimum_image_dimensions_positive(self):
        """Minimum image dimensions should be positive."""
        assert MIN_IMAGE_WIDTH > 0
        assert MIN_IMAGE_HEIGHT > 0

    def test_minimum_dimensions_are_reasonable(self):
        """Minimum dimensions should be reasonable for OCR."""
        # Too small = unusable for OCR
        assert MIN_IMAGE_WIDTH >= 50
        assert MIN_IMAGE_HEIGHT >= 50

        # Not too large (should be minimums)
        assert MIN_IMAGE_WIDTH <= 500
        assert MIN_IMAGE_HEIGHT <= 500

    def test_dpi_is_reasonable(self):
        """Default DPI should be suitable for document scanning."""
        assert isinstance(DEFAULT_DPI, int)
        assert 72 <= DEFAULT_DPI <= 600  # Typical range for documents

    def test_upscale_factor_is_valid(self):
        """Upscale factor should be reasonable."""
        assert isinstance(IMAGE_UPSCALE_FACTOR, (int, float))
        assert 1 <= IMAGE_UPSCALE_FACTOR <= 4  # Too high = quality loss


class TestConstantsImmutability:
    """Test that constants are not mutable collections."""

    def test_confusion_pairs_is_immutable_type(self):
        """Confusion pairs should use immutable keys."""
        # Dict itself is mutable, but keys should be immutable tuples
        for key in DIGIT_CONFUSION_PAIRS.keys():
            assert isinstance(key, tuple)
            # Tuples contain immutable strings
            assert all(isinstance(d, str) for d in key)


class TestDocumentationPresence:
    """Verify domain constants have proper documentation."""

    def test_module_has_docstring(self):
        """Domain constants module should have a docstring."""
        import src.domain.constants as constants_module
        assert constants_module.__doc__ is not None
        assert len(constants_module.__doc__) > 50  # Substantial doc


class TestConstantsUsageExample:
    """Integration-style tests showing how constants are used."""

    def test_cedula_validation_example(self):
        """Example: Using constants to validate cedula length."""
        def is_valid_cedula(cedula: str, strict: bool = False) -> bool:
            length = len(cedula)
            if strict:
                return MIN_CEDULA_LENGTH_STRICT <= length <= MAX_CEDULA_LENGTH_STRICT
            return MIN_CEDULA_LENGTH <= length <= MAX_CEDULA_LENGTH

        # Valid cedulas
        assert is_valid_cedula("1234567890", strict=True)  # 10 digits
        assert is_valid_cedula("123456", strict=True)      # 6 digits
        assert is_valid_cedula("123", strict=False)        # 3 digits (permissive)

        # Invalid cedulas
        assert not is_valid_cedula("12", strict=False)     # Too short
        assert not is_valid_cedula("123", strict=True)     # Too short (strict)
        assert not is_valid_cedula("123456789012", strict=False)  # Too long

    def test_confusion_check_example(self):
        """Example: Checking if two digits are commonly confused."""
        def are_confusable(digit1: str, digit2: str) -> bool:
            return (digit1, digit2) in DIGIT_CONFUSION_PAIRS

        # Common confusions
        assert are_confusable('1', '7')
        assert are_confusable('7', '1')
        assert are_confusable('5', '6')

        # Not confused
        assert not are_confusable('1', '2')
        assert not are_confusable('0', '9')
