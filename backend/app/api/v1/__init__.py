"""API v1 routes"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.get("/health")
async def health() -> dict:
    """Health check endpoint"""
    return {"status": "ok"}


__all__ = ["router"]
