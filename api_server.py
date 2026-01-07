"""Development server entry point for FastAPI application."""
import uvicorn

from src.infrastructure.api.config import settings
from src.infrastructure.logging import configure_structlog


if __name__ == "__main__":
    # Configure logging BEFORE starting the server
    configure_structlog(
        log_level=settings.LOG_LEVEL,
        use_json=(settings.LOG_FORMAT == "json"),
        log_file=settings.LOG_FILE
    )

    uvicorn.run(
        "src.infrastructure.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,  # Enable auto-reload in development
        log_level=settings.LOG_LEVEL.lower()
    )