# =============================================================================
# Zorvyn Finance Backend — API v1 Router
# =============================================================================
# This module bundles all v1 endpoint routers into a single router that is
# included in the main FastAPI app with the /api/v1 prefix.
#
# Adding a new endpoint module:
#   1. Create your router in app/api/v1/endpoints/your_module.py
#   2. Import it here
#   3. Include it with api_router.include_router(...)
#
# Current Endpoint Modules:
#   - auth:      User registration and login (Feature 1)
#   - records:   Financial records CRUD (Module 5)
#   - dashboard: Aggregated analytics (Module 6)
#   - users:     User management (Module 7)
# =============================================================================

from fastapi import APIRouter

from app.api.v1.endpoints import auth, records
# ---------------------------------------------------------------------------
# Main API v1 Router
# ---------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1")

# ── Auth Routes ──────────────────────────────────────────────────────────────
# POST /api/v1/auth/register  — Create a new user account
# POST /api/v1/auth/login     — Authenticate and receive JWT
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)

# ── Records Routes ───────────────────────────────────────────────────────────
# POST /api/v1/records/       — Create record
# GET /api/v1/records/        — List records
# GET /api/v1/records/{id}    — Get record
# PUT /api/v1/records/{id}    — Update record
# DELETE /api/v1/records/{id} — Soft delete record
api_router.include_router(
    records.router,
    prefix="/records",
    tags=["Records"],
)

# NOTE: Additional routers (records, dashboard, users) will be added
# in subsequent modules as they are implemented.
