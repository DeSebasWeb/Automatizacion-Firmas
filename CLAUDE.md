# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Asistente de Digitación de Cédulas** - Professional automation system for collecting signatures in political and electoral campaigns in Colombia. Extracts and digitizes handwritten ID numbers (cédulas) with 98-99.5% accuracy using digit-level ensemble OCR technology combining multiple cloud OCR engines.

**Tech Stack:** Python 3.10+, PyQt6 (GUI), Google Cloud Vision API, Azure Computer Vision API, OpenCV, structlog

## Development Commands

### Running the Application

```bash
# Windows
run.bat

# Linux/macOS
python main.py
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_digit_level_ensemble.py -v

# Run specific test category
pytest tests/unit/ -v
```

### Code Quality

```bash
# Type checking
mypy src/

# Code formatting
black src/ tests/

# Linting
flake8 src/

# Import sorting
isort src/ tests/
```

### Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Authenticate Google Cloud Vision
gcloud auth application-default login
```

## Architecture

This project follows **Clean Architecture / Hexagonal Architecture** with strict separation of concerns and dependency inversion.

### Layer Structure

```
src/
├── domain/              # Business logic (pure Python, no external dependencies)
│   ├── entities/        # Business entities (CedulaRecord, RowData, ProcessingSession)
│   ├── value_objects/   # Immutable value objects (CedulaNumber, ConfidenceScore, Coordinate)
│   ├── specifications/  # Business rules as composable specifications
│   └── ports/          # Interfaces for external dependencies (OCRPort, ConfigPort, etc.)
│
├── application/         # Use cases and application services
│   ├── use_cases/      # Business workflows (CaptureScreenUseCase, ExtractCedulasUseCase)
│   ├── services/       # Application services (ProcessingOrchestrator, FuzzyValidator)
│   └── factories/      # Factories for complex object creation
│
├── infrastructure/      # External implementations
│   ├── ocr/            # OCR adapter implementations
│   ├── image/          # Image preprocessing
│   ├── capture/        # Screen capture
│   └── automation/     # GUI automation
│
├── presentation/        # UI layer
│   ├── ui/             # PyQt6 widgets
│   └── controllers/    # MVC controllers
│
└── shared/             # Shared utilities
    ├── logging/        # Structured logging
    └── config/         # Configuration management
```

### Key Architectural Patterns

#### Dependency Injection
All dependencies are injected through constructors. See [main.py:58-97](main.py#L58-L97) for the DI container setup. When creating new use cases or adapters, always inject dependencies rather than instantiating them directly.

#### Value Objects
Use immutable value objects for domain concepts:
- **CedulaNumber**: Self-validating (3-11 digits, numeric only)
- **ConfidenceScore**: Normalized 0.0-1.0 range
- **Coordinate**: 2D position

Create using factory methods: `CedulaNumber.from_string()`, `CedulaNumber.try_create()`, `CedulaNumbers.from_raw_ocr()`

#### Ports and Adapters
All external dependencies are abstracted behind ports (interfaces):
- **OCRPort** → Multiple adapters (GoogleVisionAdapter, AzureVisionAdapter, DigitLevelEnsembleOCR)
- **ConfigPort** → YAMLConfig
- **AutomationPort** → PyAutoGUIAutomation

When adding new external dependencies, create a port in `src/domain/ports/` first.

#### Specification Pattern
Business rules are composable specifications in `src/domain/specifications/`. Combine them with AND/OR/NOT operators.

## OCR System Architecture

### OCR Provider Selection

The system supports multiple OCR providers configured via `config/settings.yaml` (`ocr.provider`):

1. **google_vision** - Google Cloud Vision (95-98% accuracy, recommended for production)
2. **azure_vision** - Azure Computer Vision (96-98% accuracy, alternative)
3. **ensemble** - Traditional ensemble combining full cédulas (>99% accuracy)
4. **digit_ensemble** ⭐ - Digit-level ensemble (98-99.5% accuracy, RECOMMENDED)
5. **tesseract** - Tesseract OCR (70-85% accuracy, free fallback)

### Digit-Level Ensemble (Primary Feature)

The **DigitLevelEnsembleOCR** is the crown jewel of this system. Unlike traditional ensemble that picks the best complete cédula, it:

1. Runs Google Vision + Azure Vision in parallel
2. Pairs results by **position** (index-based, not similarity)
3. Compares **digit-by-digit** choosing highest confidence
4. Validates using configurable thresholds
5. Produces ultra-precise results (98-99.5% accuracy)

**Location:** [src/infrastructure/ocr/digit_level_ensemble_ocr.py](src/infrastructure/ocr/digit_level_ensemble_ocr.py)

**Key Components:**
- `DigitConfidenceExtractor` - Extracts per-digit confidence from OCR responses
- `DigitComparator` - Compares digits and selects best
- `ConflictResolver` - Handles ambiguous cases (1 vs 7, 5 vs 6)
- `LengthValidator` - Validates digit count consistency
- `EnsembleStatistics` - Calculates agreement metrics

### OCR Factory Pattern

The OCRFactory ([src/infrastructure/ocr/ocr_factory.py](src/infrastructure/ocr/ocr_factory.py)) handles:
- Provider creation based on configuration
- Automatic fallback if primary provider fails
- Availability checking
- Initialization logging

When adding a new OCR provider, update `_try_create_provider()` and `get_available_providers()`.

## Image Preprocessing Pipeline

**Location:** [src/infrastructure/image/preprocessor.py](src/infrastructure/image/preprocessor.py)

The preprocessing pipeline is configurable via `config/settings.yaml` under `image_preprocessing`. Each step can be toggled:

1. **Upscaling** (factor: 2) - Improves resolution
2. **Grayscale conversion** - Standard for OCR
3. **Denoising** (optional) - Removes noise
4. **CLAHE** (optional) - Enhances contrast
5. **Sharpening** (optional) - Improves edge definition
6. **Morphological operations** (optional) - Removes small artifacts

**Default:** Only upscaling + grayscale enabled for clean captures.

## Logging System

This project uses **structured logging** via `structlog` with JSON output.

### Logger Types

```python
from src.shared.logging import LoggerFactory

# Domain logger
logger = LoggerFactory.get_domain_logger("cedula_validator")

# Application logger
logger = LoggerFactory.get_application_logger("extract_use_case")

# Infrastructure logger
logger = LoggerFactory.get_infrastructure_logger("google_vision")

# Presentation logger
logger = LoggerFactory.get_presentation_logger("main_controller")
```

### Logging Helpers

Use helper functions for consistent logging:

```python
from src.shared.logging import log_info_message, log_error_message, log_warning_message

log_info_message(logger, "Processing cedula", cedula=cedula_number, confidence=0.95)
log_error_message(logger, "OCR extraction failed", error=str(e), provider="google_vision")
```

All logs are written to:
- **Console**: Human-readable colored output
- **File**: JSON format in `logs/` directory for analysis

## Configuration Management

### YAML Configuration

Configuration is managed via `config/settings.yaml`. Access using the ConfigPort:

```python
config = YAMLConfig("config/settings.yaml")

# Get with default
provider = config.get('ocr.provider', 'google_vision')

# Nested keys use dot notation
threshold = config.get('ocr.digit_ensemble.min_digit_confidence', 0.70)
```

### Environment Variables

Secrets are loaded from `.env` (use `.env.example` as template):

```bash
# Google Cloud Vision (uses Application Default Credentials)
# Run: gcloud auth application-default login

# Azure Computer Vision
AZURE_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_VISION_KEY=your_subscription_key
```

Variables in YAML can reference env vars: `${AZURE_VISION_KEY}`

## Domain Model

### Core Entities

**CedulaRecord** ([src/domain/entities/cedula_record.py](src/domain/entities/cedula_record.py))
- Represents an extracted ID number with metadata
- Contains: `cedula_number` (CedulaNumber), `confidence` (ConfidenceScore), `position` (Coordinate)

**RowData** ([src/domain/entities/row_data.py](src/domain/entities/row_data.py))
- Represents a complete form row (used in dual OCR mode)
- Contains: handwritten names + cedula + validation data

**ProcessingSession** ([src/domain/entities/processing_session.py](src/domain/entities/processing_session.py))
- Manages a digitization session
- Tracks: current index, processed count, errors, statistics

### Value Object Validation

CedulaNumber enforces business rules:
- 3-11 digits (configurable range)
- Numeric only
- Auto-validation on construction
- Raises ValueError if invalid

When working with cédulas from OCR:

```python
# Raw OCR output
raw_text = "  1234567  "

# Use factory for cleaning
cedula = CedulaNumbers.from_raw_ocr(raw_text)  # Returns None if invalid

# Or explicit validation
try:
    cedula = CedulaNumber.from_string(raw_text.strip())
except ValueError as e:
    # Handle invalid cedula
    pass
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests (mock external dependencies)
└── test_azure.py      # Integration test for Azure Vision
```

### Writing Tests

Mock external dependencies using pytest fixtures:

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_config():
    config = Mock(spec=ConfigPort)
    config.get.return_value = "google_vision"
    return config

def test_extract_cedulas(mock_config):
    ocr = GoogleVisionAdapter(mock_config)
    # ... test logic
```

Always test:
1. Happy path
2. Invalid inputs (value objects raise ValueError)
3. Edge cases (empty lists, None values)
4. Business rule validation

## Common Development Tasks

### Adding a New OCR Provider

1. Create adapter implementing OCRPort in `src/infrastructure/ocr/`
2. Add provider to `ocr_factory.py` in `_try_create_provider()`
3. Update `get_available_providers()` with detection logic
4. Add configuration section to `config/settings.yaml`
5. Write unit tests in `tests/unit/`

### Modifying Cédula Validation Rules

Edit `CedulaNumber` class in [src/domain/value_objects/cedula_number.py](src/domain/value_objects/cedula_number.py):

```python
# Change length requirements
if not (6 <= length <= 10):  # Example: stricter Colombian format
    raise ValueError(...)
```

### Adding New Image Preprocessing Step

1. Add step to `ImagePreprocessor` in [src/infrastructure/image/preprocessor.py](src/infrastructure/image/preprocessor.py)
2. Add configuration option to `config/settings.yaml` under `image_preprocessing`
3. Update pipeline method to conditionally apply step
4. Test with sample images

### Debugging OCR Issues

1. Enable `save_processed_images: true` in config - saves to `temp/processed/`
2. Enable `verbose_logging: true` for digit_ensemble - shows digit comparison tables
3. Check logs in `logs/` directory for structured JSON data
4. Use `get_provider_comparison()` to compare provider performance

## Important Notes

### Immutability

Value objects are **frozen dataclasses** - they cannot be modified after creation. To change, create a new instance.

### Error Handling

- Value objects raise `ValueError` on invalid input
- OCR adapters catch and log exceptions, returning empty lists
- Use cases handle errors and report via logger
- UI displays errors in status panel

### Performance Considerations

- Digit ensemble runs 2 OCR calls in parallel (uses ThreadPoolExecutor)
- Image preprocessing is CPU-intensive (consider disabling unnecessary steps)
- Logs are async-friendly (structlog is thread-safe)

### Security

- Never commit `.env` file (contains API keys)
- Use Application Default Credentials for Google Cloud when possible
- API keys are loaded from environment, never hardcoded

## File Locations Quick Reference

- **Entry point:** [main.py](main.py)
- **Configuration:** [config/settings.yaml](config/settings.yaml)
- **OCR Factory:** [src/infrastructure/ocr/ocr_factory.py](src/infrastructure/ocr/ocr_factory.py)
- **Digit Ensemble:** [src/infrastructure/ocr/digit_level_ensemble_ocr.py](src/infrastructure/ocr/digit_level_ensemble_ocr.py)
- **Main Controller:** [src/presentation/controllers/main_controller.py](src/presentation/controllers/main_controller.py)
- **Value Objects:** [src/domain/value_objects/](src/domain/value_objects/)
- **Tests:** [tests/](tests/)
