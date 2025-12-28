"""Health check endpoints."""
from fastapi import APIRouter
from datetime import datetime

from ...config import settings
from ...database.session import check_database_connection

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Health check endpoint.

    Verifies:
    - API is running
    - Database connection is healthy

    Returns the API status, version, and database connectivity.
    """
    db_healthy = check_database_connection()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "VerifyID OCR API"
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Indicates if the service is ready to accept requests.
    """
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }