# =============================================================================
# Zorvyn Finance Backend — API Dependencies (Auth & RBAC)
# =============================================================================
# This module provides the core authentication and authorization dependencies
# used across all protected endpoints.
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │                    RBAC Architecture Overview                          │
# │                                                                        │
# │  Request → OAuth2 Bearer Token → get_current_user() → RoleChecker()   │
# │                                                                        │
# │  1. Extract JWT from Authorization header (OAuth2PasswordBearer)       │
# │  2. Decode token → fetch User from DB (get_current_user)              │
# │  3. Check user's role against allowed roles (RoleChecker)             │
# │  4. If role is not allowed → 403 Forbidden                            │
# │  5. If everything passes → endpoint receives the current user         │
# └─────────────────────────────────────────────────────────────────────────┘
#
# KEY DESIGN PRINCIPLE:
#   Role-based access control is NEVER done inside endpoint functions.
#   Instead, endpoints declare their role requirements via dependencies:
#
#       @router.post("/", dependencies=[Depends(allow_admin)])
#       async def create_record(...):
#           # No role checking here — RoleChecker already handled it
#           ...
#
#   This keeps endpoint logic clean and access control centralized.
#
# Feature 1: Auth — JWT extraction & role checking
# =============================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

import jwt

from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User, Role
from beanie import PydanticObjectId


# ---------------------------------------------------------------------------
# OAuth2 Scheme — Extracts Bearer token from Authorization header
# ---------------------------------------------------------------------------
# The tokenUrl points to the login endpoint. This is used by Swagger UI
# to show the "Authorize" button with a login form.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT",
    description="Enter the JWT token obtained from POST /api/v1/auth/login",
)


# ---------------------------------------------------------------------------
# get_current_user — Core authentication dependency
# ---------------------------------------------------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Extract and validate the JWT token, then return the authenticated user.

    This dependency is the first layer of protection. It ensures:
    1. A valid JWT token is present in the Authorization header.
    2. The token has not expired.
    3. The user referenced by the token exists in the database.
    4. The user's account is active.

    Args:
        token: JWT string automatically extracted from the
               "Authorization: Bearer <token>" header by OAuth2PasswordBearer.

    Returns:
        The authenticated User document from MongoDB.

    Raises:
        HTTPException 401: If token is missing, expired, invalid, or
                           the user doesn't exist.
        HTTPException 403: If the user's account is deactivated.
    """
    # ── Step 1: Decode the JWT token ─────────────────────────────────
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Step 2: Extract user ID from token payload ───────────────────
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing 'sub' (subject) claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Step 3: Fetch user from database ─────────────────────────────
    try:
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        user = None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Account may have been deleted.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Step 4: Check if account is active ───────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact an administrator.",
        )

    return user


# ---------------------------------------------------------------------------
# RoleChecker — Reusable role-based access control dependency
# ---------------------------------------------------------------------------
class RoleChecker:
    """
    A callable dependency class that enforces role-based access control.

    Instead of littering every endpoint with `if user.role != "admin": raise ...`,
    this class provides a clean, declarative way to specify which roles are
    allowed to access an endpoint.

    How it works:
    1. Initialize with a list of allowed roles.
    2. Use as a FastAPI dependency: `Depends(RoleChecker([Role.admin]))`.
    3. It automatically calls `get_current_user()` to authenticate.
    4. If the user's role is in the allowed list → passes through.
    5. If not → raises 403 Forbidden with a clear error message.

    Usage:
        # As a route dependency (recommended — cleanest):
        @router.post("/", dependencies=[Depends(allow_admin)])
        async def create_record(...):
            ...

        # Or to also get the user in the endpoint:
        @router.get("/")
        async def list_records(user: User = Depends(allow_all_roles)):
            ...

    Attributes:
        allowed_roles: List of Role enum values that can access the endpoint.
    """

    def __init__(self, allowed_roles: list[Role]):
        """
        Initialize RoleChecker with the list of roles allowed to access
        the protected resource.

        Args:
            allowed_roles: List of Role enum values (e.g., [Role.admin]).
        """
        self.allowed_roles = allowed_roles

    async def __call__(
        self, current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Check if the authenticated user's role is in the allowed list.

        Args:
            current_user: Automatically injected by Depends(get_current_user).

        Returns:
            The authenticated user if their role is allowed.

        Raises:
            HTTPException 403: If the user's role is not in allowed_roles.
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Role '{current_user.role.value}' is not authorized "
                    f"for this action. Required roles: "
                    f"{[r.value for r in self.allowed_roles]}"
                ),
            )
        return current_user


# ---------------------------------------------------------------------------
# Pre-built Role Checker Instances — Use these in endpoints
# ---------------------------------------------------------------------------
# These are the convenience instances you should use in most cases.
# They make endpoint declarations clean and self-documenting.

# Only admins can access (create, update, delete records; manage users)
allow_admin = RoleChecker([Role.admin])

# Analysts and admins can access (advanced analytics, trends)
allow_analyst_and_above = RoleChecker([Role.analyst, Role.admin])

# All authenticated users can access (view records, basic dashboard)
allow_all_roles = RoleChecker([Role.viewer, Role.analyst, Role.admin])


# =============================================================================
# Usage Examples in Endpoints:
#
# 1. Admin-only endpoint (e.g., create a record):
#    @router.post("/", dependencies=[Depends(allow_admin)])
#    async def create_record(data: RecordCreate):
#        ...
#
# 2. Any authenticated user (e.g., view dashboard):
#    @router.get("/summary")
#    async def get_summary(user: User = Depends(allow_all_roles)):
#        ...
#
# 3. Analyst and above (e.g., monthly trends):
#    @router.get("/trends", dependencies=[Depends(allow_analyst_and_above)])
#    async def get_trends():
#        ...
#
# 4. Custom role check (e.g., new role added later):
#    custom_check = RoleChecker([Role.admin, Role.some_new_role])
#    @router.put("/", dependencies=[Depends(custom_check)])
#    async def update_something():
#        ...
# =============================================================================
