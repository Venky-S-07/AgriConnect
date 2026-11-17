"""Health check endpoint for AgriConnect."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    """Verify backend service availability."""
    return {
        "status": "ok",
        "app": "AgriConnect",
        "version": "1.3.1",
        "milestone": "Milestone 1 — Basic Website and Backend Foundation",
    }
