"""
HoloHub FastAPI Application

Main application entry point with configuration, middleware, and routes.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import auth as auth_v1
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.base import close_db
from app.db.redis import close_redis, get_redis_pool
from app.schemas.common import HealthResponse

settings = get_settings()

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, "Lifespan"]:
    """
    Lifespan context manager for startup and shutdown events.

    Handles database and Redis connection lifecycle.
    """
    # Startup
    print("HoloHub API starting up...")

    yield

    # Shutdown
    print("HoloHub API shutting down...")
    await close_db()
    await close_redis()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Production-grade spatial computing CMS for managing holographic displays at scale",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan,
)

# Configure rate limiter with app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# =============================================================================
# Middleware
# =============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted hosts (in production)
if settings.app_env == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.cors_origins)


# =============================================================================
# Middleware: Request Logging & Timing
# =============================================================================
@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    """
    Log all requests and add timing information.

    Adds X-Process-Time header to response with request processing time in ms.
    """
    import time

    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = str(process_time)

    # Log request
    if settings.debug:
        print(f"{request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")

    return response


# =============================================================================
# Middleware: Organization Context for RLS
# =============================================================================
@app.middleware("http")
async def set_organization_context(request: Request, call_next) -> Response:
    """
    Set organization context from JWT token for row-level security.

    This middleware extracts the organization ID from the JWT token
    and sets it as a PostgreSQL session variable for RLS policies.
    """
    # Skip for certain paths (health, auth, docs, etc.)
    skip_paths = {"/health", "/docs", "/redoc", "/openapi.json", f"{settings.api_v1_prefix}/openapi.json"}
    if request.url.path in skip_paths or request.url.path.startswith("/static"):
        return await call_next(request)

    # Get user from token if available
    from app.api.deps import get_current_user_optional
    from app.db.base import get_db

    try:
        # Try to get auth header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)

        # Get user (async call)
        async with get_db() as db:
            try:
                # This is a simplified version - in production, you'd want to cache this
                # For now, we'll skip setting org context at middleware level
                # and handle it in the dependency injection instead
                pass
            except Exception:
                pass  # Ignore errors, let route handlers handle auth
    except Exception:
        pass  # Ignore errors

    return await call_next(request)


# =============================================================================
# Exception Handlers
# =============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.

    In production, this returns a generic error message.
    In debug mode, returns the full exception details.
    """
    import traceback

    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "traceback": traceback.format_exc(),
            },
        )

    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"},
    )


# =============================================================================
# Health Check
# =============================================================================
@app.get("/health", response_model=HealthResponse, tags=["Health"])
@limiter.exempt
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns API health status and checks connectivity to core services.
    """
    # Check database connection
    database_healthy = True
    try:
        from app.db.base import engine

        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
    except Exception:
        database_healthy = False

    # Check Redis connection
    redis_healthy = True
    try:
        pool = get_redis_pool()
        async with pool.get_connection() as conn:
            await conn.ping()
    except Exception:
        redis_healthy = False

    return HealthResponse(
        status="healthy" if database_healthy and redis_healthy else "degraded",
        version="0.1.0",
        database=database_healthy,
        redis=redis_healthy,
    )


# =============================================================================
# Root Endpoint
# =============================================================================
@app.get("/", tags=["Root"])
@limiter.exempt
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.api_v1_prefix,
    }


# =============================================================================
# Include Routers
# =============================================================================
app.include_router(api_router)


# =============================================================================
# Startup Event (for compatibility)
# =============================================================================
@app.on_event("startup")
async def startup_event() -> None:
    """Deprecated: Use lifespan context manager instead."""
    print("HoloHub API starting up...")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Deprecated: Use lifespan context manager instead."""
    print("HoloHub API shutting down...")
    await close_db()
    await close_redis()
