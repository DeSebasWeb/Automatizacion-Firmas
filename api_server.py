"""Development server entry point for FastAPI application."""
import uvicorn

from src.infrastructure.api.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "src.infrastructure.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,  # Enable auto-reload in development
        log_level="info"
    )