"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.database import close_db, init_db
from src.core.redis import close_redis, get_redis
from src.schemas.common import HealthResponse

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if not settings.debug else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Tunisia Price Tracker API")

    # Initialize database (tables created via Alembic migrations)
    logger.info("Database connection ready")

    # Initialize Redis
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("Redis connection ready")
    except Exception as e:
        logger.warning("Redis connection failed", error=str(e))

    yield

    # Shutdown
    logger.info("Shutting down Tunisia Price Tracker API")
    await close_db()
    await close_redis()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## Tunisia Price Tracker API

    A scalable price tracking platform that scrapes competitor websites in Tunisia
    and exposes data via REST API for price comparison.

    ### Core Features

    - **Search-first API**: Provide a product name → get all competitor prices
    - **Fuzzy matching**: Handles typos, partial names, different word orders
    - **Real-time prices**: Track price changes across multiple websites
    - **Price history**: View historical price trends and analytics

    ### Primary Use Case

    ```
    GET /api/v1/search/prices?q=anua peach serum
    ```

    Returns all matching products from all tracked competitor websites
    with their current prices, sorted by relevance.

    ### Authentication

    Public endpoints (search, products) are available without authentication.
    Admin endpoints require an API key via the `X-API-Key` header.
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the status of the API and its dependencies.
    """
    db_status = "connected"
    redis_status = "connected"

    try:
        redis = await get_redis()
        await redis.ping()
    except Exception:
        redis_status = "disconnected"

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        database=db_status,
        redis=redis_status,
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root - redirect to docs."""
    return {
        "message": "Tunisia Price Tracker API",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }


# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)
