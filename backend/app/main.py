"""Factory Insider Backend - Main Application Entry Point"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.config import settings
from app.database import dispose_db, init_db
from app.sentry_init import init_sentry

try:
    from app.socket_server import socket_app
except ModuleNotFoundError:
    socket_app = None

# Initialize Sentry error tracking
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown"""
    # Startup
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")

    yield

    # Shutdown
    try:
        await dispose_db()
        print("✅ Database disposed")
    except Exception as e:
        print(f"⚠️  Database disposal warning: {e}")


app = FastAPI(
    title="Factory Insider API",
    description="AI-Powered B2B Manufacturing Marketplace Backend",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routes
app.include_router(v1_router)
if socket_app is not None:
    app.mount("/ws", socket_app)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint - returns 200 OK"""
    return {
        "status": "healthy",
        "service": "factory-insider-api",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root() -> dict:
    """Root endpoint"""
    return {
        "message": "Factory Insider API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/api/v1/health")
async def api_health() -> dict:
    """API v1 health check"""
    return {"status": "ok", "service": "factory-insider-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
