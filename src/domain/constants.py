"""Domain-level constants for cedula validation and OCR processing.

These are immutable business rules and domain logic that do NOT change
between environments. For configurable values, use environment variables.
"""

# ============================================================================
# CEDULA VALIDATION RULES (Colombian ID numbers)
# ============================================================================

# Colombian cédulas typically range from 6-11 digits
# - Older cédulas: 6-8 digits
# - Modern cédulas: 8-11 digits
# - We allow 3-11 to handle edge cases and foreign IDs
MIN_CEDULA_LENGTH = 3
MAX_CEDULA_LENGTH = 11

# Strict validation for production (Colombian standard)
MIN_CEDULA_LENGTH_STRICT = 6
MAX_CEDULA_LENGTH_STRICT = 11


# ============================================================================
# DIGIT CONFUSION MATRIX
# ============================================================================
# Empirically determined pairs of digits that are frequently confused
# by OCR engines when processing handwritten Colombian cédulas.
#
# This is domain knowledge, NOT configuration - based on actual error analysis
# from hundreds of real-world cédula images.
#
# Format: (digit1, digit2) -> confusion probability
# ============================================================================

DIGIT_CONFUSION_PAIRS: dict[tuple[str, str], float] = {
    # 1 and 7 confusion (VERY common in handwriting)
    # When handwritten, '1' with a top serif looks like '7'
    ('1', '7'): 0.15,
    ('7', '1'): 0.15,

    # 5 and 6 confusion (common - similar curved shape)
    # When poorly written, top of '5' resembles '6'
    ('5', '6'): 0.10,
    ('6', '5'): 0.10,

    # 8 and 3 confusion (moderate - both have curves)
    # Closed '3' can look like '8', especially if handwriting is tight
    ('8', '3'): 0.08,
    ('3', '8'): 0.08,

    # 0 and 6 confusion (less common but occurs)
    # Small '6' with short tail can resemble '0'
    ('0', '6'): 0.05,
    ('6', '0'): 0.05,

    # 2 and 7 confusion (rare but documented)
    # When '2' is written with straight top, resembles '7'
    ('2', '7'): 0.05,
    ('7', '2'): 0.05,
}


# ============================================================================
# POSITIONAL PAIRING CONSTANTS
# ============================================================================
# These define how we match cedulas from different OCR providers based on
# their position in the image. Derived from empirical testing.

# Minimum positional similarity to consider two cedulas as match candidates
# Uses normalized coordinate distance (0.0 = different locations, 1.0 = same)
MIN_POSITIONAL_SIMILARITY = 0.30  # 30% - fairly permissive

# High similarity threshold - when cedulas are obviously the same
# Skips expensive character-level comparison
HIGH_SIMILARITY_THRESHOLD = 0.80  # 80% - very confident match

# Fallback similarity for character-level comparison
FALLBACK_SIMILARITY_THRESHOLD = 0.50  # 50% - moderate confidence

# Search window size for positional matching
# How many positions forward/backward to search for matches
# Example: window=2 checks positions [i-2, i-1, i, i+1, i+2]
SEARCH_WINDOW_SIZE = 2


# ============================================================================
# IMAGE QUALITY REQUIREMENTS
# ============================================================================

# Minimum image dimensions to process (width, height) in pixels
# Images smaller than this are likely too low quality for reliable OCR
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100

# Default DPI for image processing
# Colombian ID cards are typically scanned at 300 DPI or higher
DEFAULT_DPI = 300

# Default upscale factor for low-resolution images
IMAGE_UPSCALE_FACTOR = 2
