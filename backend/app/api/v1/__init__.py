"""API v1 routes"""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.content import router as content_router
from app.api.v1.knowledge_base import router as knowledge_base_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.outbound import router as outbound_router
from app.api.v1.rfqs import router as rfqs_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.visitor_intent import router as visitor_intent_router
from app.api.v1.videos import router as videos_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.search import router as search_router
from app.api.v1.messages import router as messages_router
from app.api.v1.billing import router as billing_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.exhibitions import router as exhibitions_router
from app.api.v1.business_cards import router as business_cards_router

router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include routes
router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(content_router)
router.include_router(knowledge_base_router)
router.include_router(notifications_router)
router.include_router(outbound_router)
router.include_router(rfqs_router)
router.include_router(suppliers_router)
router.include_router(uploads_router)
router.include_router(visitor_intent_router)
router.include_router(videos_router)
router.include_router(webhooks_router)
router.include_router(search_router)
router.include_router(messages_router)
router.include_router(billing_router)
router.include_router(analytics_router)
router.include_router(exhibitions_router)
router.include_router(business_cards_router)


@router.get("/health")
async def health() -> dict:
    """Health check endpoint"""
    return {"status": "ok"}


__all__ = ["router"]
