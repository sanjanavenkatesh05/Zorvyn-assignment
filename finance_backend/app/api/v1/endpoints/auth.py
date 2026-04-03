# =============================================================================
# Zorvyn Finance Backend — Authentication Endpoints
# =============================================================================
# Handles user registration and login with JWT token generation.
#
# Endpoints:
#   POST /api/v1/auth/register  — Create a new user account
#   POST /api/v1/auth/login     — Authenticate and receive a JWT token
#
# Feature 1: Authentication
#   - First registered user is auto-promoted to 'admin' role.
#   - Subsequent users default to 'viewer' role.
#   - Login returns a JWT containing user ID and role.
#   - Passwords are bcrypt-hashed before storage.
#
# Security Flow:
#   1. Client POST /register with email, password, full_name
#   2. Server validates → hashes password → creates User document
#   3. Client POST /login with email (as username) and password
#   4. Server verifies credentials → returns JWT
#   5. Client includes JWT in Authorization header for subsequent requests
# =============================================================================

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from app.core.rate_limit import limiter

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, Role
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserResponse


# ---------------------------------------------------------------------------
# Router Setup
# ---------------------------------------------------------------------------
router = APIRouter()


# ---------------------------------------------------------------------------
# POST /register — Create a new user account
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new user account. The first user registered in the system "
        "is automatically promoted to the 'admin' role. All subsequent users "
        "are assigned the 'viewer' role by default. Admins can later change "
        "roles via the /users/{id}/role endpoint."
    ),
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Email already registered or validation error"},
    },
)
@limiter.limit("3/minute")
async def register(request: Request, user_data: UserCreate):
    """
    Register a new user in the system.

    Steps:
    1. Check if the email is already taken (unique constraint).
    2. Hash the plaintext password with bcrypt.
    3. If this is the first user in the system, auto-promote to admin.
    4. Create and save the User document to MongoDB.
    5. Return the user profile (without password hash).

    Args:
        user_data: Validated registration data (email, password, full_name).

    Returns:
        UserResponse with the created user's profile data.

    Raises:
        HTTPException 400: If the email is already registered.
    """
    # ── Step 1: Check for duplicate email ────────────────────────────
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please use a different email or log in.",
        )

    # ── Step 2: Hash the password ────────────────────────────────────
    hashed = hash_password(user_data.password)

    # ── Step 3: Determine role (first user = admin) ──────────────────
    # Count existing users. If none exist, this is the first user
    # and should automatically get admin privileges.
    user_count = await User.count()
    role = Role.admin if user_count == 0 else Role.viewer

    # ── Step 4: Create and save the user document ────────────────────
    user = User(
        email=user_data.email,
        hashed_password=hashed,
        full_name=user_data.full_name,
        role=role,
    )
    await user.insert()

    # ── Step 5: Return response (excluding password hash) ────────────
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


# ---------------------------------------------------------------------------
# POST /login — Authenticate and get JWT token
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get access token",
    description=(
        "Authenticate with email and password to receive a JWT access token. "
        "Use this token in the Authorization header for all protected endpoints:\n\n"
        "```\nAuthorization: Bearer <access_token>\n```\n\n"
        "The token expires after the configured JWT_EXPIRE_MINUTES (default: 60 min)."
    ),
    responses={
        200: {"description": "Login successful, JWT token returned"},
        401: {"description": "Invalid email or password"},
        403: {"description": "Account is deactivated"},
    },
)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return a JWT access token.

    Uses OAuth2PasswordRequestForm which expects:
    - username: The user's email address
    - password: The user's password

    Steps:
    1. Find user by email (sent as 'username' in OAuth2 form).
    2. Verify the password against the stored bcrypt hash.
    3. Check if the account is active.
    4. Generate a JWT with user ID and role in the payload.

    Args:
        form_data: OAuth2 form with username (email) and password.

    Returns:
        TokenResponse with access_token and token_type.

    Raises:
        HTTPException 401: If email not found or password is wrong.
        HTTPException 403: If the user account is deactivated.
    """
    # ── Step 1: Find user by email ───────────────────────────────────
    # OAuth2PasswordRequestForm uses 'username' field — we treat it as email.
    user = await User.find_one(User.email == form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Step 2: Verify password ──────────────────────────────────────
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Step 3: Check account status ─────────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact an administrator.",
        )

    # ── Step 4: Generate JWT ─────────────────────────────────────────
    # Token payload includes the user ID (sub) and role for authorization.
    access_token = create_access_token(
        data={
            "sub": str(user.id),     # Subject: user's MongoDB ObjectId
            "role": user.role.value,  # Role: "admin", "analyst", or "viewer"
        }
    )

    return TokenResponse(access_token=access_token)
