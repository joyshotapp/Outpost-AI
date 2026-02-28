"""API v1 routes"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.uploads import router as uploads_router

router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include routes
router.include_router(auth_router)
router.include_router(suppliers_router)
router.include_router(uploads_router)


@router.get("/health")
async def health() -> dict:
    """Health check endpoint"""
    return {"status": "ok"}


__all__ = ["router"]
