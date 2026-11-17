"""AgriConnect FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.farms import router as farms_router
from app.api.health import router as health_router
from app.api.privacy import router as privacy_router
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: validates critical environment settings on startup."""
    # Strict SECRET_KEY validation: fail startup immediately if missing or weak
    if not settings.SECRET_KEY or len(settings.SECRET_KEY.strip()) < 32:
        raise RuntimeError(
            "CRITICAL: SECRET_KEY environment variable is missing, empty, or too short (minimum 32 characters required). "
            "Application cannot start securely. Please configure SECRET_KEY in your local .env file."
        )
    # Ensure all registered tables are created in SQLite
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.1.2",
    description="AgriConnect API — Multilingual Agricultural Decision Support Platform",
    lifespan=lifespan,
)

# CORS configuration allowing local frontend development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api/v1
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(farms_router, prefix=settings.API_V1_STR)
app.include_router(privacy_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    """Root info endpoint."""
    return {
        "message": "Welcome to AgriConnect API",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health",
    }
