"""API v1 routes"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include auth routes
router.include_router(auth_router)


@router.get("/health")
async def health() -> dict:
    """Health check endpoint"""
    return {"status": "ok"}


__all__ = ["router"]
