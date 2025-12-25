"""Health check endpoints."""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Health check endpoint.

    Returns the API status and timestamp.
    """
    return {
        "status": "healthy",
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