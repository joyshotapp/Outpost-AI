"""API v1 routes"""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.knowledge_base import router as knowledge_base_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.rfqs import router as rfqs_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.visitor_intent import router as visitor_intent_router
from app.api.v1.videos import router as videos_router

router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include routes
router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(knowledge_base_router)
router.include_router(notifications_router)
router.include_router(rfqs_router)
router.include_router(suppliers_router)
router.include_router(uploads_router)
router.include_router(visitor_intent_router)
router.include_router(videos_router)


@router.get("/health")
async def health() -> dict:
    """Health check endpoint"""
    return {"status": "ok"}


__all__ = ["router"]
