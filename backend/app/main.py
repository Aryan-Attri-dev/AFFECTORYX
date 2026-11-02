import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.api import api_router
from app.models import *  # noqa: F401, F403

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("affactoryx")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation and database schema verification
    logger.info("Initializing AFFECTORYX Engine...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Loaded safely with masked settings: {repr(settings)}")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified.")
    yield
    logger.info("Shutting down AFFECTORYX Engine...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Engineering Intelligence Platform for Change Impact Analysis",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforce strict enterprise security headers on every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for container orchestrators and monitoring agents."""
    return {
        "status": "healthy",
        "service": "affactoryx-core",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "purpose": "Engineering Intelligence Platform",
        "docs": f"{settings.API_V1_STR}/docs",
    }


app.include_router(api_router, prefix=settings.API_V1_STR)
