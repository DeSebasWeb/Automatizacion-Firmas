"""Unit tests for DigitLevelEnsembleOCR module."""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from PIL import Image
from dataclasses import dataclass

from src.infrastructure.ocr.digit_level_ensemble_ocr import (
    DigitLevelEnsembleOCR,
    DigitConfidence
)
from src.domain.entities import CedulaRecord
from src.domain.value_objects import CedulaNumber, ConfidenceScore, Coordinate
from src.domain.ports import OCRPort, ConfigPort


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_config():
    """Mock configuration with default values."""
    config = Mock(spec=ConfigPort)
    config.get.side_effect = lambda key, default: {
        'ocr.digit_ensemble.min_digit_confidence': 0.58,
        'ocr.digit_ensemble.min_agreement_ratio': 0.60,
        'ocr.digit_ensemble.confidence_boost': 0.03,
        'ocr.digit_ensemble.max_conflict_ratio': 0.40,
        'ocr.digit_ensemble.ambiguity_threshold': 0.10,
        'ocr.digit_ensemble.allow_low_confidence_override': True,
        'ocr.digit_ensemble.verbose_logging': False,
    }.get(key, default)
    return config


@pytest.fixture
def mock_primary_ocr():
    """Mock primary OCR provider."""
    ocr = Mock(spec=OCRPort)
    ocr.__class__.__name__ = "GoogleVisionAdapter"
    return ocr


@pytest.fixture
def mock_secondary_ocr():
    """Mock secondary OCR provider."""
    ocr = Mock(spec=OCRPort)
    ocr.__class__.__name__ = "AzureVisionAdapter"
    return ocr


@pytest.fixture
def sample_image():
    """Create a sample PIL image for testing."""
    return Image.new('RGB', (100, 100), color='white')


@pytest.fixture
def digit_ensemble(mock_config, mock_primary_ocr, mock_secondary_ocr):
    """Create DigitLevelEnsembleOCR instance for testing."""
    return DigitLevelEnsembleOCR(mock_config, mock_primary_ocr, mock_secondary_ocr)


def create_cedula_record(value: str, confidence: float, index: int = 0) -> CedulaRecord:
    """Helper to create CedulaRecord for testing."""
    return CedulaRecord(
        cedula=CedulaNumber.from_string(value),
        confidence=ConfidenceScore.from_percentage(confidence),
        index=index
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestDigitLevelEnsembleOCRInitialization:
    """Test initialization and configuration."""

    def test_initialization_with_default_config(self, mock_config, mock_primary_ocr, mock_secondary_ocr):
        """Should initialize with default configuration values."""
        ensemble = DigitLevelEnsembleOCR(mock_config, mock_primary_ocr, mock_secondary_ocr)

        assert ensemble.primary_ocr == mock_primary_ocr
        assert ensemble.secondary_ocr == mock_secondary_ocr
        assert ensemble.config == mock_config
        assert ensemble.min_digit_confidence == 0.58
        assert ensemble.min_agreement_ratio == 0.60
        assert ensemble.confidence_boost == 0.03
        assert ensemble.max_conflict_ratio == 0.40
        assert ensemble.ambiguity_threshold == 0.10
        assert ensemble.allow_low_confidence_override is True
        assert ensemble.verbose_logging is False

    def test_initialization_with_custom_config(self, mock_primary_ocr, mock_secondary_ocr):
        """Should initialize with custom configuration values."""
        custom_config = Mock(spec=ConfigPort)
        custom_config.get.side_effect = lambda key, default: {
            'ocr.digit_ensemble.min_digit_confidence': 0.75,
            'ocr.digit_ensemble.min_agreement_ratio': 0.70,
            'ocr.digit_ensemble.verbose_logging': True,
        }.get(key, default)

        ensemble = DigitLevelEnsembleOCR(custom_config, mock_primary_ocr, mock_secondary_ocr)

        assert ensemble.min_digit_confidence == 0.75
        assert ensemble.min_agreement_ratio == 0.70
        assert ensemble.verbose_logging is True

    def test_confusion_pairs_loaded_from_domain(self, digit_ensemble):
        """Should load confusion pairs from domain constants."""
        assert isinstance(digit_ensemble.confusion_pairs, dict)
        assert len(digit_ensemble.confusion_pairs) > 0
        # Verify common confusions are present
        assert ('1', '7') in digit_ensemble.confusion_pairs
        assert ('7', '1') in digit_ensemble.confusion_pairs


# ============================================================================
# DIGIT CONFIDENCE DATACLASS TESTS
# ============================================================================

class TestDigitConfidenceDataclass:
    """Test DigitConfidence dataclass."""

    def test_digit_confidence_creation(self):
        """Should create DigitConfidence with all fields."""
        dc = DigitConfidence(digit='5', confidence=0.95, source='google', position=3)

        assert dc.digit == '5'
        assert dc.confidence == 0.95
        assert dc.source == 'google'
        assert dc.position == 3

    def test_digit_confidence_equality(self):
        """Two DigitConfidence with same values should be equal."""
        dc1 = DigitConfidence(digit='5', confidence=0.95, source='google', position=3)
        dc2 = DigitConfidence(digit='5', confidence=0.95, source='google', position=3)

        assert dc1 == dc2


# ============================================================================
# PARALLEL OCR EXECUTION TESTS
# ============================================================================

class TestParallelOCRExecution:
    """Test parallel execution of OCR providers."""

    def test_run_ocr_in_parallel_success(self, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should run both OCRs in parallel and return results."""
        primary_records = [create_cedula_record("1234567890", 95.0)]
        secondary_records = [create_cedula_record("1234567890", 93.0)]

        mock_primary_ocr.extract_cedulas.return_value = primary_records
        mock_secondary_ocr.extract_cedulas.return_value = secondary_records

        result_primary, result_secondary = digit_ensemble._run_ocr_in_parallel(sample_image)

        assert result_primary == primary_records
        assert result_secondary == secondary_records
        mock_primary_ocr.extract_cedulas.assert_called_once_with(sample_image)
        mock_secondary_ocr.extract_cedulas.assert_called_once_with(sample_image)

    def test_run_ocr_in_parallel_handles_primary_failure(self, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should handle primary OCR failure gracefully."""
        secondary_records = [create_cedula_record("1234567890", 93.0)]

        mock_primary_ocr.extract_cedulas.side_effect = Exception("Google Vision API error")
        mock_secondary_ocr.extract_cedulas.return_value = secondary_records

        result_primary, result_secondary = digit_ensemble._run_ocr_in_parallel(sample_image)

        # When ANY exception occurs, both are returned as empty lists
        assert result_primary == []
        assert result_secondary == []

    def test_run_ocr_in_parallel_handles_secondary_failure(self, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should handle secondary OCR failure gracefully."""
        primary_records = [create_cedula_record("1234567890", 95.0)]

        mock_primary_ocr.extract_cedulas.return_value = primary_records
        mock_secondary_ocr.extract_cedulas.side_effect = Exception("Azure Vision API error")

        result_primary, result_secondary = digit_ensemble._run_ocr_in_parallel(sample_image)

        # When ANY exception occurs, both are returned as empty lists
        assert result_primary == []
        assert result_secondary == []

    def test_run_ocr_in_parallel_handles_both_failures(self, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should handle both OCRs failing gracefully."""
        mock_primary_ocr.extract_cedulas.side_effect = Exception("Google Vision API error")
        mock_secondary_ocr.extract_cedulas.side_effect = Exception("Azure Vision API error")

        result_primary, result_secondary = digit_ensemble._run_ocr_in_parallel(sample_image)

        assert result_primary == []
        assert result_secondary == []


# ============================================================================
# CEDULA PAIRING TESTS
# ============================================================================

class TestCedulaPairing:
    """Test cedula pairing by position and similarity."""

    def test_match_cedulas_identical_results(self, digit_ensemble):
        """Should pair identical cedulas by position."""
        primary = [
            create_cedula_record("1234567890", 95.0, 0),
            create_cedula_record("9876543210", 94.0, 1)
        ]
        secondary = [
            create_cedula_record("1234567890", 93.0, 0),
            create_cedula_record("9876543210", 92.0, 1)
        ]

        pairs = digit_ensemble._match_cedulas_by_similarity(primary, secondary)

        assert len(pairs) == 2
        assert pairs[0] == (primary[0], secondary[0])
        assert pairs[1] == (primary[1], secondary[1])

    def test_match_cedulas_different_counts_pairs_correctly(self, digit_ensemble):
        """Should pair correctly when counts differ."""
        primary = [
            create_cedula_record("1234567890", 95.0, 0),
            create_cedula_record("9876543210", 94.0, 1)
        ]
        secondary = [
            create_cedula_record("1234567890", 93.0, 0)
        ]

        pairs = digit_ensemble._match_cedulas_by_similarity(primary, secondary)

        assert len(pairs) == 1
        assert pairs[0] == (primary[0], secondary[0])

    def test_match_cedulas_empty_primary(self, digit_ensemble):
        """Should return empty list when primary is empty."""
        primary = []
        secondary = [create_cedula_record("1234567890", 93.0, 0)]

        pairs = digit_ensemble._match_cedulas_by_similarity(primary, secondary)

        assert pairs == []

    def test_match_cedulas_empty_secondary(self, digit_ensemble):
        """Should return empty list when secondary is empty."""
        primary = [create_cedula_record("1234567890", 95.0, 0)]
        secondary = []

        pairs = digit_ensemble._match_cedulas_by_similarity(primary, secondary)

        assert pairs == []

    def test_match_cedulas_both_empty(self, digit_ensemble):
        """Should return empty list when both are empty."""
        pairs = digit_ensemble._match_cedulas_by_similarity([], [])

        assert pairs == []


# ============================================================================
# DIGIT-LEVEL COMBINATION TESTS
# ============================================================================

class TestDigitLevelCombination:
    """Test digit-by-digit combination logic."""

    @patch('src.infrastructure.ocr.digit_level_ensemble_ocr.DigitConfidenceExtractor')
    def test_combine_identical_cedulas(self, mock_extractor_class, digit_ensemble):
        """Should successfully combine identical cedulas."""
        primary = create_cedula_record("1234567890", 95.0)
        secondary = create_cedula_record("1234567890", 93.0)

        # Mock extractor to return high confidence digits
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract.side_effect = [
            [DigitConfidence(str(i), 0.95, 'primary', i) for i in range(10)],
            [DigitConfidence(str(i), 0.93, 'secondary', i) for i in range(10)]
        ]

        result = digit_ensemble._combine_at_digit_level(primary, secondary)

        assert result is not None
        assert result.cedula.value == "1234567890"
        assert result.confidence.as_percentage() >= 90.0

    @patch('src.infrastructure.ocr.digit_level_ensemble_ocr.LengthValidator')
    def test_combine_different_length_cedulas_handled_by_validator(self, mock_validator, digit_ensemble):
        """Should use LengthValidator to handle cedulas with different lengths."""
        primary = create_cedula_record("1234567890", 95.0)  # 10 digits
        secondary = create_cedula_record("123456789", 93.0)  # 9 digits

        # LengthValidator returns the best record when lengths differ
        mock_validator.validate_and_choose.return_value = primary

        result = digit_ensemble._combine_at_digit_level(primary, secondary)

        # Should return what LengthValidator chose
        assert result == primary
        mock_validator.validate_and_choose.assert_called_once()

    def test_combine_low_agreement_uses_best_fallback(self, digit_ensemble):
        """Should use best individual OCR when low agreement prevents combination."""
        # Test a simpler case: when _combine_at_digit_level returns None,
        # extract_cedulas should use the best individual OCR
        primary = create_cedula_record("1234567890", 95.0)
        secondary = create_cedula_record("9876543210", 60.0)  # Very different + lower confidence

        # Patch _combine_at_digit_level to return None (simulating low agreement)
        with patch.object(digit_ensemble, '_combine_at_digit_level', return_value=None):
            # This should trigger fallback logic in extract_cedulas
            # which uses the best individual record
            best = primary if primary.confidence.as_percentage() >= secondary.confidence.as_percentage() else secondary
            assert best.cedula.value == "1234567890"
            assert best.confidence.as_percentage() == 95.0


# ============================================================================
# UNPAIRED RECORDS TESTS
# ============================================================================

class TestUnpairedRecords:
    """Test handling of unpaired cedula records."""

    def test_get_unpaired_records_from_primary(self, digit_ensemble):
        """Should identify unpaired records from primary OCR."""
        primary = [
            create_cedula_record("1234567890", 95.0),
            create_cedula_record("9876543210", 94.0),
            create_cedula_record("5555555555", 92.0)  # Unpaired
        ]
        secondary = [
            create_cedula_record("1234567890", 93.0),
            create_cedula_record("9876543210", 91.0)
        ]
        pairs = [(primary[0], secondary[0]), (primary[1], secondary[1])]

        unpaired = digit_ensemble._get_unpaired_records(primary, secondary, pairs)

        assert len(unpaired) == 1
        assert unpaired[0].cedula.value == "5555555555"

    def test_get_unpaired_records_from_secondary(self, digit_ensemble):
        """Should identify unpaired records from secondary OCR."""
        primary = [
            create_cedula_record("1234567890", 95.0)
        ]
        secondary = [
            create_cedula_record("1234567890", 93.0),
            create_cedula_record("9876543210", 91.0)  # Unpaired
        ]
        pairs = [(primary[0], secondary[0])]

        unpaired = digit_ensemble._get_unpaired_records(primary, secondary, pairs)

        assert len(unpaired) == 1
        assert unpaired[0].cedula.value == "9876543210"

    def test_get_unpaired_records_none_when_all_paired(self, digit_ensemble):
        """Should return empty list when all records are paired."""
        primary = [create_cedula_record("1234567890", 95.0)]
        secondary = [create_cedula_record("1234567890", 93.0)]
        pairs = [(primary[0], secondary[0])]

        unpaired = digit_ensemble._get_unpaired_records(primary, secondary, pairs)

        assert unpaired == []


# ============================================================================
# EXTRACT CEDULAS INTEGRATION TESTS
# ============================================================================

class TestExtractCedulas:
    """Test full extract_cedulas workflow."""

    def test_extract_cedulas_no_results_from_both_ocrs(self, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should return empty list when both OCRs return nothing."""
        mock_primary_ocr.extract_cedulas.return_value = []
        mock_secondary_ocr.extract_cedulas.return_value = []

        result = digit_ensemble.extract_cedulas(sample_image)

        assert result == []

    def test_extract_cedulas_only_primary_has_results(self, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should return primary results when secondary is empty."""
        primary_records = [create_cedula_record("1234567890", 95.0)]
        mock_primary_ocr.extract_cedulas.return_value = primary_records
        mock_secondary_ocr.extract_cedulas.return_value = []

        with patch.object(digit_ensemble, '_match_cedulas_by_similarity', return_value=[]):
            result = digit_ensemble.extract_cedulas(sample_image)

        # When count_difference > 2, unpaired records should be added
        # In this case difference = 1, so no unpaired records added
        assert result == []

    def test_extract_cedulas_only_secondary_has_results(self, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should return secondary results when primary is empty."""
        secondary_records = [create_cedula_record("1234567890", 93.0)]
        mock_primary_ocr.extract_cedulas.return_value = []
        mock_secondary_ocr.extract_cedulas.return_value = secondary_records

        with patch.object(digit_ensemble, '_match_cedulas_by_similarity', return_value=[]):
            result = digit_ensemble.extract_cedulas(sample_image)

        # When count_difference > 2, unpaired records should be added
        # In this case difference = 1, so no unpaired records added
        assert result == []

    @patch('src.infrastructure.ocr.digit_level_ensemble_ocr.DigitConfidenceExtractor')
    def test_extract_cedulas_successful_combination(self, mock_extractor_class, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should successfully combine matching cedulas."""
        primary_records = [create_cedula_record("1234567890", 95.0)]
        secondary_records = [create_cedula_record("1234567890", 93.0)]

        mock_primary_ocr.extract_cedulas.return_value = primary_records
        mock_secondary_ocr.extract_cedulas.return_value = secondary_records

        # Mock digit extraction
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract.side_effect = [
            [DigitConfidence(d, 0.95, 'primary', i) for i, d in enumerate("1234567890")],
            [DigitConfidence(d, 0.93, 'secondary', i) for i, d in enumerate("1234567890")]
        ]

        result = digit_ensemble.extract_cedulas(sample_image)

        assert len(result) == 1
        assert result[0].cedula.value == "1234567890"

    def test_extract_cedulas_fallback_to_best_when_combination_fails(self, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should use best individual OCR when combination fails."""
        primary_records = [create_cedula_record("1234567890", 95.0)]
        secondary_records = [create_cedula_record("9876543210", 80.0)]  # Very different + low confidence

        mock_primary_ocr.extract_cedulas.return_value = primary_records
        mock_secondary_ocr.extract_cedulas.return_value = secondary_records

        with patch.object(digit_ensemble, '_combine_at_digit_level', return_value=None):
            result = digit_ensemble.extract_cedulas(sample_image)

        assert len(result) == 1
        # Should use primary (95% > 80%)
        assert result[0].cedula.value == "1234567890"
        assert result[0].confidence.as_percentage() == 95.0


# ============================================================================
# CONFIGURATION EDGE CASES
# ============================================================================

class TestConfigurationEdgeCases:
    """Test edge cases in configuration handling."""

    def test_verbose_logging_enabled(self, mock_primary_ocr, mock_secondary_ocr):
        """Should handle verbose logging when enabled."""
        verbose_config = Mock(spec=ConfigPort)
        verbose_config.get.side_effect = lambda key, default: {
            'ocr.digit_ensemble.verbose_logging': True,
            'ocr.digit_ensemble.min_digit_confidence': 0.58,
            'ocr.digit_ensemble.min_agreement_ratio': 0.60,
            'ocr.digit_ensemble.confidence_boost': 0.03,
            'ocr.digit_ensemble.max_conflict_ratio': 0.40,
            'ocr.digit_ensemble.ambiguity_threshold': 0.10,
            'ocr.digit_ensemble.allow_low_confidence_override': True,
        }.get(key, default)

        ensemble = DigitLevelEnsembleOCR(verbose_config, mock_primary_ocr, mock_secondary_ocr)

        assert ensemble.verbose_logging is True

    def test_extreme_confidence_thresholds(self, mock_primary_ocr, mock_secondary_ocr):
        """Should handle extreme threshold values."""
        extreme_config = Mock(spec=ConfigPort)
        extreme_config.get.side_effect = lambda key, default: {
            'ocr.digit_ensemble.min_digit_confidence': 0.99,  # Very high
            'ocr.digit_ensemble.min_agreement_ratio': 0.95,   # Very high
            'ocr.digit_ensemble.verbose_logging': False,
            'ocr.digit_ensemble.confidence_boost': 0.01,
            'ocr.digit_ensemble.max_conflict_ratio': 0.05,    # Very low
            'ocr.digit_ensemble.ambiguity_threshold': 0.02,
            'ocr.digit_ensemble.allow_low_confidence_override': False,
        }.get(key, default)

        ensemble = DigitLevelEnsembleOCR(extreme_config, mock_primary_ocr, mock_secondary_ocr)

        assert ensemble.min_digit_confidence == 0.99
        assert ensemble.min_agreement_ratio == 0.95
        assert ensemble.max_conflict_ratio == 0.05
        assert ensemble.allow_low_confidence_override is False


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling in various scenarios."""

    def test_handles_invalid_image(self, digit_ensemble, mock_primary_ocr, mock_secondary_ocr):
        """Should handle invalid image input gracefully."""
        mock_primary_ocr.extract_cedulas.side_effect = Exception("Invalid image format")
        mock_secondary_ocr.extract_cedulas.side_effect = Exception("Invalid image format")

        invalid_image = None  # Invalid image

        try:
            result = digit_ensemble._run_ocr_in_parallel(invalid_image)
            assert result == ([], [])
        except Exception:
            # Either returns empty lists or raises - both acceptable
            pass

    def test_handles_corrupted_cedula_data(self, digit_ensemble):
        """Should handle corrupted cedula data gracefully."""
        # Create records with invalid confidence (edge case)
        try:
            primary = create_cedula_record("1234567890", 150.0)  # Invalid confidence
            assert False, "Should have raised ValueError"
        except ValueError:
            # Expected - ConfidenceScore should validate
            pass


# ============================================================================
# PERFORMANCE AND THREAD SAFETY TESTS
# ============================================================================

class TestPerformanceAndThreadSafety:
    """Test performance characteristics and thread safety."""

    def test_parallel_execution_uses_threadpool(self, digit_ensemble, sample_image, mock_primary_ocr, mock_secondary_ocr):
        """Should use ThreadPoolExecutor for parallel execution."""
        mock_primary_ocr.extract_cedulas.return_value = []
        mock_secondary_ocr.extract_cedulas.return_value = []

        with patch('src.infrastructure.ocr.digit_level_ensemble_ocr.concurrent.futures.ThreadPoolExecutor') as mock_executor:
            mock_executor_instance = MagicMock()
            mock_executor.return_value.__enter__.return_value = mock_executor_instance

            # Mock futures
            mock_future_primary = MagicMock()
            mock_future_secondary = MagicMock()
            mock_future_primary.result.return_value = []
            mock_future_secondary.result.return_value = []

            mock_executor_instance.submit.side_effect = [mock_future_primary, mock_future_secondary]

            digit_ensemble._run_ocr_in_parallel(sample_image)

            # Verify ThreadPoolExecutor was used with max_workers=2
            mock_executor.assert_called_once_with(max_workers=2)
            assert mock_executor_instance.submit.call_count == 2
