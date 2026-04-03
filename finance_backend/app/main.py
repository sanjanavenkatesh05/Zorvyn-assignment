# =============================================================================
# Zorvyn Finance Backend — Application Entry Point
# =============================================================================
# This is the main FastAPI application factory. It configures:
#   1. Lifespan events (database initialization on startup)
#   2. CORS middleware (allowing cross-origin requests for development)
#   3. Swagger/OpenAPI metadata for API documentation
#   4. Health check endpoint for container orchestration
#
# Run locally:
#   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
#
# Access docs:
#   Swagger UI:  http://localhost:8000/docs
#   ReDoc:       http://localhost:8000/redoc
# =============================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.rate_limit import limiter
from app.db.init_db import init_db
from app.api.v1.api_router import api_router


# ---------------------------------------------------------------------------
# Lifespan — runs on startup and shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager for application lifespan events.
    - Startup: Initialize database connection and Beanie ODM.
    - Shutdown: (cleanup happens automatically when context exits)
    """
    # ── Startup ───────────────────────────────────────────────────────
    print("🚀 Starting Zorvyn Finance API...")
    await init_db()  # Connect to MongoDB and initialize Beanie
    yield
    # ── Shutdown ──────────────────────────────────────────────────────
    print("🛑 Shutting down Zorvyn Finance API...")


# ---------------------------------------------------------------------------
# OpenAPI Tag Metadata — organizes endpoints in Swagger UI
# ---------------------------------------------------------------------------
tags_metadata = [
    {
        "name": "Health",
        "description": "Application health check endpoints.",
    },
    {
        "name": "Auth",
        "description": "User registration, login, and JWT token management.",
    },
    {
        "name": "Records",
        "description": (
            "Financial records CRUD operations with pagination, "
            "filtering, search, and soft delete support."
        ),
    },
    {
        "name": "Dashboard",
        "description": "Aggregated analytics, summaries, and trend data for the finance dashboard.",
    },
    {
        "name": "Users",
        "description": "User management endpoints (admin only). View, update roles, and manage user status.",
    },
]


# ---------------------------------------------------------------------------
# FastAPI Application Instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Zorvyn Finance API",
    description=(
        "Finance Data Processing & Access Control Backend.\n\n"
        "This API provides endpoints for managing financial records, "
        "user roles, dashboard analytics, and access control. "
        "Built with FastAPI, MongoDB (Beanie ODM), and JWT authentication."
    ),
    version="1.0.0",
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc alternative
    openapi_tags=tags_metadata, # Tag grouping for docs
    lifespan=lifespan,          # Startup/shutdown events
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=400,
        content={"detail": "Validation failed", "errors": errors}
    )


# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
# Allow all origins during development. In production, restrict this to
# your frontend's domain(s) for security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)


# ---------------------------------------------------------------------------
# API Routes — Include all versioned endpoint routers
# ---------------------------------------------------------------------------
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Returns the current health status of the API. Used by Docker and monitoring tools.",
    response_description="Health status object",
)
async def health_check():
    """
    Simple health check endpoint.

    Returns a JSON object indicating the API is running and healthy.
    Useful for:
    - Docker HEALTHCHECK directives
    - Load balancer health probes
    - Monitoring dashboards
    """
    return {
        "status": "healthy",
        "service": "Zorvyn Finance API",
        "version": "1.0.0",
    }
