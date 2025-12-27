"""Shared pytest fixtures for all tests."""
import sys
from pathlib import Path
import pytest

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that require database or external services"
    )
    config.addinivalue_line(
        "markers", "repository: Tests for repository pattern implementation"
    )


@pytest.fixture(autouse=True, scope="function")
def reset_sqlalchemy_metadata():
    """
    Reset SQLAlchemy metadata before each test.

    This prevents "Table 'X' is already defined" errors when
    models are imported multiple times across different test files.
    """
    # Clear metadata before test
    from infrastructure.database.base import Base
    Base.metadata.clear()

    yield

    # Clear metadata after test
    Base.metadata.clear()
